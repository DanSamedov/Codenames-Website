class RoomManager {
    constructor(config) {
        this.config = config;
        this.messageHandler = new MessageHandler(config);
        this.websocketManager = new WebSocketManager(config.roomId, this.messageHandler);
        this.formHandler = new FormHandler(this.websocketManager, config);
        
        this.setupEventListeners();
    }

    setupEventListeners() {
        window.addEventListener('beforeunload', () => {
            this.websocketManager.send({
                action: 'leave',
                username: this.config.currentUser,
            });
        });

        window.addEventListener('pageshow', (event) => {
            const nav = performance.getEntriesByType('navigation')[0]?.type;
            if (event.persisted || nav === 'back_forward') {
                setTimeout(() => window.location.reload(), 50);
            }
        });
    }

    destroy() {
        this.websocketManager.close();
    }
}