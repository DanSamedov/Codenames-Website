class CardManager {
    constructor(config, gameState, storageManager, websocketManager) {
        this.config = config;
        this.gameState = gameState;
        this.storageManager = storageManager;
        this.websocketManager = websocketManager;
        
        window.card_choice = (cardId) => this.handleCardChoice(cardId);
    }

    initCards(data = {}) {
        const action = data.action || 'init';
        const leader_list = data.leader_list || [];
        const cards = document.querySelectorAll('[id^="card-"]');
        const cardDict = this.storageManager.getCardDict();
        const pickedCardWords = [];

        cards.forEach(card => {
            const id = card.id;
            const word = id.replace(/^card-/, '');
            const color = cardDict[word];

            if (leader_list.includes(this.config.currentUser)) {
                card.style.backgroundColor = color.toLowerCase();
            }

            if (card.dataset.isChosen === window.GameConstants.CARD_STATES.GUESSED) {
                this.markGuessed(card, color);
                return;
            }

            if (action === window.GameConstants.WEBSOCKET.ACTIONS.REVEAL_GUESSED_CARDS && 
                card.dataset.isChosen === window.GameConstants.CARD_STATES.TRUE) {
                pickedCardWords.push(word);
                card.dataset.isChosen = window.GameConstants.CARD_STATES.GUESSED;
                this.markGuessed(card, color);
                return;
            }

            card.onclick = () => this.handleCardChoice(id);
        });

        if (action === window.GameConstants.WEBSOCKET.ACTIONS.REVEAL_GUESSED_CARDS && 
            pickedCardWords.length) {
            this.websocketManager.send({
                action: 'picked_words',
                pickedCards: pickedCardWords,
            });

            this.gameState.reset();
        }
    }

    handleCardChoice(cardId) {
        const card = document.getElementById(cardId);
        if (!card) return;

        const maxSelections = this.gameState.hintNum + 1;

        if (this.config.isLeader() || 
            this.gameState.phase !== window.GameConstants.PHASES.ROUND_PHASE ||
            this.config.currentTeam !== this.gameState.team) {
            return;
        }

        const selectedCards = this.storageManager.getSelectedCards();
        const isChosen = card.dataset.isChosen === window.GameConstants.CARD_STATES.TRUE;

        if (isChosen) {
            this.deselectCard(card, cardId, selectedCards);
        } else {
            if (this.getChosenCount() >= maxSelections) {
                return alert(`You can only choose ${maxSelections} cards.`);
            }
            this.selectCard(card, cardId, selectedCards);
        }

        this.storageManager.setSelectedCards(selectedCards);
        this.gameState.chosenCount = this.getChosenCount();
        
        this.websocketManager.send({
            action: 'card_choice',
            card_id: cardId,
            selected_cards: selectedCards,
            card_status: card.dataset.isChosen === window.GameConstants.CARD_STATES.TRUE,
        });
    }

    selectCard(card, cardId, selectedCards) {
        card.dataset.isChosen = window.GameConstants.CARD_STATES.TRUE;
        card.style.border = '2px solid yellow';
        if (!selectedCards.includes(cardId)) {
            selectedCards.push(cardId);
        }
    }

    deselectCard(card, cardId, selectedCards) {
        card.dataset.isChosen = window.GameConstants.CARD_STATES.FALSE;
        card.style.border = '';
        const idx = selectedCards.indexOf(cardId);
        if (idx > -1) {
            selectedCards.splice(idx, 1);
        }
    }

    markGuessed(card, color) {
        const bg = 'grey';
        const fg = color === 'Neutral' ? 'white' : color.toLowerCase();
        card.style.backgroundColor = bg;
        card.style.color = fg;
        card.style.border = '';
        card.onclick = null;
    }

    getChosenCount() {
        return document.querySelectorAll(`[data-is-chosen="${window.GameConstants.CARD_STATES.TRUE}"]`).length;
    }

    updateSelectedCards(selectedCards) {
        const cards = document.querySelectorAll('[data-is-chosen]');
        
        cards.forEach(card => {
            const isGuessed = card.dataset.isChosen === window.GameConstants.CARD_STATES.GUESSED;
            card.dataset.isChosen = isGuessed ? window.GameConstants.CARD_STATES.GUESSED : window.GameConstants.CARD_STATES.FALSE;
            card.style.border = '';
        });
        
        selectedCards.forEach(id => {
            const card = document.getElementById(id);
            if (card) {
                card.dataset.isChosen = window.GameConstants.CARD_STATES.TRUE;
                card.style.border = '2px solid yellow';
            }
        });
    }

    updateCardChoice(cardId, cardStatus) {
        const card = document.getElementById(cardId);
        if (!card) return;

        if (this.config.currentTeam === this.gameState.team) {
            if (cardStatus === true) {
                card.style.border = '2px solid yellow';
                card.dataset.isChosen = window.GameConstants.CARD_STATES.TRUE;
            } else {
                card.style.border = '';
                card.dataset.isChosen = window.GameConstants.CARD_STATES.FALSE;
            }
        }
    }
}

window.CardManager = CardManager;