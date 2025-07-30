class UIManager {
    constructor(config, gameState) {
        this.config = config;
        this.gameState = gameState;
    }

    updateHintDisplay(hintWord, hintNum) {
        const hintDisplay = document.getElementById('hintDisplay');
        if (hintDisplay) {
            hintDisplay.innerText = `Hint: ${hintWord} \n Number of words: ${hintNum}`;
        }
    }

    clearHintDisplay() {
        const hintDisplay = document.getElementById('hintDisplay');
        if (hintDisplay) {
            hintDisplay.textContent = '';
        }
    }

    showWinner(winner) {
        const hintDisplay = document.getElementById('hintDisplay');
        const timer = document.getElementById('timer');
        
        if (hintDisplay) {
            hintDisplay.innerHTML = `<h2>🎉 Team ${winner} Wins! Redirecting...</h2>`;
        }
        if (timer) {
            timer.textContent = '';
        }
        
        alert(`${winner} Team wins!`);
    }

    toggleHintFormVisibility() {
        const hintForm = document.getElementById('hint-form');
        if (!hintForm || this.config.currentTeam !== this.gameState.team) return;

        const isRoundPhase = this.gameState.phase === window.GameConstants.PHASES.ROUND_PHASE;
        if (isRoundPhase) {
            hintForm.classList.add('visually-hidden');
        } else {
            hintForm.classList.remove('visually-hidden');
        }
    }

    redirectToHome() {
        setTimeout(() => {
            const redirectUrl = new URL(window.location.href);
            redirectUrl.pathname = '/';
            redirectUrl.search = '';
            window.location.href = redirectUrl.toString();
        }, 1000);
    }
}

window.UIManager = UIManager;