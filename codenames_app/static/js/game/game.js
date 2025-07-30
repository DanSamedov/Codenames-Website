document.addEventListener('DOMContentLoaded', () => {
    try {
        if (!document.getElementById('game-id-data')) {
            console.error('Required game-id-data element not found');
            return;
        }
        
        if (!window.gameConfig) {
            console.error('gameConfig is not defined in window');
            return;
        }

        const gameManager = new window.GameManager();
        
        window.gameManager = gameManager;
        
        window.addEventListener('beforeunload', () => {
            gameManager.destroy();
        });
        
        console.log('Game initialized successfully');
        
    } catch (error) {
        console.error('Failed to initialize game:', error);
    }
});