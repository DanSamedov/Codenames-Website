class GameManager {
    constructor() {
        try {
            this.config = new window.GameConfig();
            this.gameState = new window.GameState();
            this.storageManager = new window.GameStorageManager(this.config.gameId);
            this.uiManager = new window.UIManager(this.config, this.gameState);
            
            this.cardManager = new window.CardManager(
                this.config, 
                this.gameState, 
                this.storageManager, 
                null
            );
            
            this.timerManager = new window.TimerManager(this.gameState, null);
            this.hintManager = new window.HintManager(
                this.config, 
                this.gameState, 
                this.storageManager, 
                null
            );
            
            this.messageHandler = new window.GameMessageHandler(
                this.config,
                this.gameState,
                this.storageManager,
                this.cardManager,
                this.timerManager,
                this.uiManager
            );
            
            this.websocketManager = new window.GameWebSocketManager(
                this.config.gameId, 
                this.messageHandler
            );
            
            this.cardManager.websocketManager = this.websocketManager;
            this.timerManager.websocketManager = this.websocketManager;
            this.hintManager.websocketManager = this.websocketManager;
            
            this.initialize();
            
        } catch (error) {
            console.error('Error initializing GameManager:', error);
            throw error;
        }
    }

    initialize() {
        this.storageManager.initializeCards();
        this.gameState.updateFromStorage(this.storageManager);
        this.gameState.chosenCount = this.cardManager.getChosenCount();
        
        this.cardManager.initCards();
        this.hintManager.initializeForm();
        this.uiManager.toggleHintFormVisibility();
    }

    destroy() {
        this.gameState.clearTimer();
        this.websocketManager.close();
    }
}

window.GameManager = GameManager;