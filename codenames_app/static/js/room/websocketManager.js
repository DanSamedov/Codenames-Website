class WebSocketManager {
    constructor(roomId, messageHandler) {
        this.roomId = roomId;
        this.messageHandler = messageHandler;
        this.socket = null;
        this.connect();
    }

    connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        this.socket = new WebSocket(`${protocol}//${host}/ws/room/${this.roomId}/`);

        this.socket.onopen = () => {
            console.log("WebSocket connection established");
        };

        this.socket.onclose = (e) => {
            console.log("WebSocket connection closed", e);
        };

        this.socket.onerror = (error) => {
            console.error("WebSocket error:", error);
        };

        this.socket.onmessage = (e) => {
            const data = JSON.parse(e.data);
            this.messageHandler.handleMessage(data);
        };
    }

    send(message) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify(message));
        }
    }

    close() {
        if (this.socket) {
            this.socket.close();
        }
    }
}