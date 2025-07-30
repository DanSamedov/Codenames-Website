class FormHandler {
    constructor(websocketManager, config) {
        this.websocketManager = websocketManager;
        this.config = config;
        this.initializeForms();
        this.makeRadiosTogglable();
    }

    initializeForms() {
        const teamForm = document.querySelector('#choose-team-form');
        if (teamForm) {
            teamForm.addEventListener('submit', (e) => this.handleTeamChoice(e));
        }

        const startGameForm = document.querySelector('#start-game-form');
        if (startGameForm) {
            startGameForm.addEventListener('submit', (e) => this.handleStartGame(e));
        }
    }

    handleTeamChoice(event) {
        event.preventDefault();
        
        const selectedRoleInput = document.querySelector('input[name="role"]:checked');
        const selectedTeamInput = document.querySelector('input[name="team"]:checked');
        const selectedRole = selectedRoleInput?.value || this.config.currentRole;
        const selectedTeam = selectedTeamInput?.value || this.config.currentTeam;

        if (selectedTeam === 'None') {
            alert('Please select a team');
            return;
        }

        this.websocketManager.send({
            action: 'change_team',
            role: selectedRole,
            team: selectedTeam,
        });

        if (this.config.startingTeam !== 'None') {
            this.startGame();
        }

        document.querySelector('#choose-team-form').reset();
    }

    handleStartGame(event) {
        event.preventDefault();
        this.startGame();
    }

    startGame() {
        this.websocketManager.send({
            action: 'start_game',
            room_id: this.config.roomId,
        });
    }

    makeRadiosTogglable() {
        this.makeRadioGroupTogglable('team');
        this.makeRadioGroupTogglable('role');
    }

    makeRadioGroupTogglable(name) {
        let lastChecked = null;
        document.querySelectorAll(`input[name="${name}"]`).forEach(radio => {
            radio.addEventListener('click', () => {
                if (radio === lastChecked) {
                    radio.checked = false;
                    lastChecked = null;
                } else {
                    lastChecked = radio;
                }
            });
        });
    }
}