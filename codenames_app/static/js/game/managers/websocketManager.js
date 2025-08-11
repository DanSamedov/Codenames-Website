class GameWebSocketManager {
  constructor(gameId, messageHandler) {
    this.gameId = gameId;
    this.messageHandler = messageHandler;
    this.socket = null;
    this.connect();
  }

  connect() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;
    this.socket = new WebSocket(`${protocol}//${host}/ws/game/${this.gameId}/`);

    this.socket.onopen = () => {
      console.log("Game WebSocket connection established");
    };

    this.socket.onclose = (e) => {
      console.error("Game WebSocket connection closed unexpectedly");
    };

    this.socket.onerror = (error) => {
      console.error("Game WebSocket error:", error);
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
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.close();
    }
  }
}

window.GameWebSocketManager = GameWebSocketManager;
