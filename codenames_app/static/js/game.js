document.addEventListener('DOMContentLoaded', () => {
    const gameIdElement = document.getElementById('game-id-data');
    if (!gameIdElement) {
        console.error('game-id-data element not found');
        return;
    }
    const gameId = JSON.parse(gameIdElement.textContent);

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const gameSocket = new WebSocket(`${protocol}//${host}/ws/game/${gameId}/`);

    const initializedKey = `game_${gameId}_initialized`;

    const currentUserName = window.gameConfig.currentUser;
    const currentUserTeam = window.gameConfig.currentTeam;
    const currentUserLeader = window.gameConfig.currentRole;

    if (!sessionStorage.getItem(initializedKey)) {
        const cardsData = JSON.parse(
            document.getElementById('cards-data').textContent,
        );
        const cardDict = {};

        cardsData.forEach(card => {
            cardDict[card.word] = card.color;
        });

        sessionStorage.setItem(initializedKey, 'true');
        sessionStorage.setItem(`cardDict_${gameId}`, JSON.stringify(cardDict));
    }

    window.gameState = {
        clockOffset: 0,
        timerInterval: null,
        phase: 'hint_phase',
        team: null,
        hintNum: parseInt(localStorage.getItem('hintNum')) || 0,
        hintWord: localStorage.getItem('hintWord') || null,
        hasWinnerBeenShown: false,
    };

    gameSocket.onclose = function (e) {
        console.error('Room was closed unexpectedly');
    };

    gameSocket.onopen = function (e) {
        console.log("WebSocket connection established");
    };

    gameSocket.onerror = function (error) {
        console.error("WebSocket error:", error);
    };

    gameSocket.onmessage = function (e) {
        const data = JSON.parse(e.data);

        if (
            data.action === 'player_join' ||
            data.action == 'reveal_guessed_cards'
        ) {
            initCards(data);
        } else if (data.action === 'selected_cards') {
            const selectedCards = data.cards;
            const cards = document.querySelectorAll('[data-is-chosen]');
            if (cards.length > 0) {
                cards.forEach(card => {
                    const isGuessed = card.dataset.isChosen === 'guessed';
                    card.dataset.isChosen = isGuessed ? 'guessed' : 'false';
                    card.style.border = '';
                });
                
                selectedCards.forEach(id => {
                    const card = document.getElementById(id);
                    if (card) {
                        card.dataset.isChosen = 'true';
                        card.style.border = '2px solid yellow';
                    }
                });
            }
        } else if (data.action === 'choose_card') {
            const username = data.username;
            const card_id = data.card_id;
            const card_status = data.card_status;
            const card = document.getElementById(card_id);

            if (currentUserTeam === window.gameState.team) {
                if (card_status === true) {
                    card.style.border = '2px solid yellow';
                    card.dataset.isChosen = 'true';
                } else {
                    card.style.border = '';
                    card.dataset.isChosen = 'false';
                }
            }
        } else if (data.action === 'hint_display') {
            window.gameState.hintWord = data.hint_word;
            window.gameState.hintNum = Number(data.hint_num);
            localStorage.setItem('hintWord', window.gameState.hintWord);
            localStorage.setItem('hintNum', window.gameState.hintNum);

            document.getElementById(
                'hintDisplay',
            ).innerText = `Hint: ${window.gameState.hintWord} \n Number of words: ${window.gameState.hintNum}`;
        } else if (data.action === 'round_phase') {
            window.gameState.phase = 'round_phase';
            window.gameState.team = data.team;

            const roundDuration = data.duration;
            const startTime = data.start_time * 1000;

            startCountdown(roundDuration, startTime);
            toggleHintFormVisibility();
        } else if (data.action === 'hint_phase') {
            window.gameState.phase = 'hint_phase';
            window.gameState.team = data.team;

            window.gameState.hintWord = null;
            window.gameState.hintNum = 0;
            window.gameState.chosenCount = 0;

            localStorage.removeItem('selectedCards');
            localStorage.removeItem('hintWord');
            localStorage.removeItem('hintNum');

            const roundDuration = data.duration;
            const startTime = data.start_time * 1000;
            startCountdown(roundDuration, startTime);

            document.getElementById('hintDisplay').textContent = '';
            toggleHintFormVisibility();
        } else if (data.action === 'sync_time') {
            const phase = data.phase;

            const storedHintNum = parseInt(localStorage.getItem('hintNum'));
            const storedHintWord = localStorage.getItem('hintWord');

            window.gameState.phase = data.phase.phase;
            window.gameState.team = phase.team;

            if (storedHintNum && window.gameState.phase === 'round_phase') {
                document.getElementById(
                    'hintDisplay',
                ).innerHTML = `Hint: ${storedHintWord}<br/>Number of words: ${storedHintNum}`;
            } else {
                document.getElementById('hintDisplay').textContent = '';
            }

            duration = phase.duration;
            startTime = phase.start_time;

            const clientTimeAtSync = Date.now() / 1000;
            window.gameState.clockOffset = startTime - clientTimeAtSync;

            const syncedCurrentTime =
                Date.now() / 1000 + window.gameState.clockOffset;
            const passedSeconds = syncedCurrentTime - startTime;
            const remainingTime = Math.max(duration - passedSeconds, 0);

            if (window.gameState.timerInterval) {
                clearInterval(window.gameState.timerInterval);
                window.gameState.timerInterval = null;
            }

            startCountdown(remainingTime, startTime * 1000);
            toggleHintFormVisibility();
        } else if (data.action === 'game_over') {
            if (!window.gameState.hasWinnerBeenShown) {
                window.gameState.hasWinnerBeenShown = true;

                if (window.gameState.timerInterval) {
                    clearInterval(window.gameState.timerInterval);
                    window.gameState.timerInterval = null;
                }

                document.getElementById('hintDisplay',).innerHTML = `<h2>🎉 Team ${data.winner} Wins! Redirecting...</h2>`;
                document.getElementById('timer').textContent = '';
                alert(`${data.winner} Team wins!`);

                if (gameSocket.readyState === WebSocket.OPEN) {
                    gameSocket.close();
                }

                setTimeout(() => {
                    const redirectUrl = new URL(window.location.href);
                    redirectUrl.pathname = '/';
                    redirectUrl.search = '';
                    window.location.href = redirectUrl.toString();
                }, 1000);
            }
        }
    };

    function getChosenCount() {
        return document.querySelectorAll('[data-is-chosen="true"]').length;
    }

    function card_choice(card_id) {
        const card = document.getElementById(card_id);
        if (!card) return;
        const maxSelections = (parseInt(localStorage.getItem('hintNum')) || 0) + 1;

        if (
            currentUserLeader === 'True' ||
            window.gameState.phase !== 'round_phase' ||
            currentUserTeam !== window.gameState.team
        ) {
            return;
        }

        const selectedCards = JSON.parse(localStorage.getItem('selectedCards')) || [];
        const isChosen = card.dataset.isChosen === 'true';

        if (isChosen) {
            card.dataset.isChosen = 'false';
            card.style.border = '';
            const idx = selectedCards.indexOf(card_id);
            if (idx > -1) selectedCards.splice(idx, 1);
        } else {
            if (getChosenCount() >= maxSelections) {
                return alert(`You can only choose ${maxSelections} cards.`);
            }
            card.dataset.isChosen = 'true';
            card.style.border = '2px solid yellow';
            if (!selectedCards.includes(card_id)) selectedCards.push(card_id);
        }

        localStorage.setItem('selectedCards', JSON.stringify(selectedCards));
        window.gameState.chosenCount = getChosenCount();
        gameSocket.send(
            JSON.stringify({
                action: 'card_choice',
                card_id: card_id,
                selected_cards: selectedCards,
                card_status: card.dataset.isChosen === 'true',
            }),
        );
    }

    function startCountdown(duration, startTime) {
        const timerDisplay = document.getElementById('timer');

        if (window.gameState.timerInterval) {
            clearInterval(window.gameState.timerInterval);
            window.gameState.timerInterval = null;
        }

        const endTime = startTime + duration * 1000;
        window.gameState.timerInterval = setInterval(() => {
            const now = Date.now();
            const timeRemaining = Math.max(0, Math.floor((endTime - now) / 1000));

            if (timeRemaining <= 0) {
                clearInterval(window.gameState.timerInterval);
                window.gameState.timerInterval = null;
                timerDisplay.textContent = "Time's up!";

                gameSocket.send(
                    JSON.stringify({
                        action: 'start_timer',
                        type: 'timer_cycle',
                    }),
                );
            } else {
                timerDisplay.textContent = `Time remaining: ${timeRemaining}s`;
            }
        }, 1000);
    }

    function submitHintWord(event) {
        event.preventDefault();
        if (
            window.gameState.phase === 'hint_phase' &&
            currentUserTeam === window.gameState.team
        ) {
            const hintWordInput = document.getElementById('hintWordInput');
            const hintNumInput = document.getElementById('hintNumInput');

            if (!hintWordInput.value || !hintNumInput.value) {
                alert('Please fill in both hint fields');
                return;
            }

            gameSocket.send(
                JSON.stringify({
                    action: 'hint_submit',
                    hintWord: hintWordInput.value,
                    hintNum: parseInt(hintNumInput.value),
                    leaderTeam: currentUserTeam,
                }),
            );

            document.getElementById('hint-form').reset();
        }
    }

    function initCards(data = {}) {
        const action = data.action || 'init';
        const leader_list = data.leader_list || [];
        const cards = document.querySelectorAll('[id^="card-"]');
        const cardDict = JSON.parse(sessionStorage.getItem(`cardDict_${gameId}`) || '{}',);
        const pickedCardWords = [];

        cards.forEach(card => {
            const id = card.id;
            const word = id.replace(/^card-/, '');
            const color = cardDict[word];

            if (leader_list.includes(currentUserName)) {
                card.style.backgroundColor = color.toLowerCase();
            }
            if (card.dataset.isChosen === 'guessed') {
                markGuessed(card, color);
                return;
            }
            if (
                action === 'reveal_guessed_cards' &&
                card.dataset.isChosen === 'true'
            ) {
                pickedCardWords.push(word);
                card.dataset.isChosen = 'guessed';
                markGuessed(card, color);
                return;
            }
            card.onclick = () => card_choice(id);
        });

        if (action === 'reveal_guessed_cards' && pickedCardWords.length) {
            gameSocket.send(
                JSON.stringify({
                    action: 'picked_words',
                    pickedCards: pickedCardWords,
                }),
            );

            window.gameState.chosenCount = 0;
            window.gameState.hintWord = null;
            window.gameState.hintNum = 0;
        }

        function markGuessed(card, color) {
            const bg = 'grey';
            const fg = color === 'Neutral' ? 'white' : color.toLowerCase();
            card.style.backgroundColor = bg;
            card.style.color = fg;
            card.style.border = '';
            card.onclick = null;
        }
    }

    function toggleHintFormVisibility() {
        const hintForm = document.getElementById('hint-form');
        if (!hintForm || currentUserTeam !== window.gameState.team) return;
        const isRoundPhase = window.gameState.phase === 'round_phase';
        if (isRoundPhase) {
            hintForm.classList.add('visually-hidden');
        } else {
            hintForm.classList.remove('visually-hidden');
        }
    }

    function initGameUI() {
        const hintForm = document.getElementById('hint-form');
        if (hintForm) hintForm.onsubmit = submitHintWord;

        window.gameState.chosenCount = getChosenCount();
        window.gameState.hintNum = parseInt(localStorage.getItem('hintNum')) || 0;
        
        initCards();
        toggleHintFormVisibility();
    }

    initGameUI();
});