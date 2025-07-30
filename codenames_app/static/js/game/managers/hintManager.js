class HintManager {
    constructor(config, gameState, storageManager, websocketManager) {
        this.config = config;
        this.gameState = gameState;
        this.storageManager = storageManager;
        this.websocketManager = websocketManager;
    }

    initializeForm() {
        const hintForm = document.getElementById('hint-form');
        if (hintForm) {
            hintForm.addEventListener('submit', (e) => this.submitHint(e));
        }
    }

    submitHint(event) {
        event.preventDefault();
        
        if (this.gameState.phase === window.GameConstants.PHASES.HINT_PHASE && 
            this.config.currentTeam === this.gameState.team) {
            
            const hintWordInput = document.getElementById('hintWordInput');
            const hintNumInput = document.getElementById('hintNumInput');

            if (!hintWordInput || !hintNumInput || !hintWordInput.value || !hintNumInput.value) {
                alert('Please fill in both hint fields');
                return;
            }

            this.websocketManager.send({
                action: 'hint_submit',
                hintWord: hintWordInput.value,
                hintNum: parseInt(hintNumInput.value),
                leaderTeam: this.config.currentTeam,
            });

            document.getElementById('hint-form').reset();
        }
    }
}

window.HintManager = HintManager;