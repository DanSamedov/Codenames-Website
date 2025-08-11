class GameConfig {
  constructor() {
    this.gameId = this.getGameId();
    this.currentUser = window.gameConfig?.currentUser || "";
    this.currentTeam = window.gameConfig?.currentTeam || "";
    this.currentRole = window.gameConfig?.currentRole || "";
    this.initializedKey = `game_${this.gameId}_initialized`;
  }

  getGameId() {
    const gameIdElement = document.getElementById("game-id-data");
    if (!gameIdElement) {
      throw new Error("game-id-data element not found");
    }
    return JSON.parse(gameIdElement.textContent);
  }

  isLeader() {
    return this.currentRole === "True";
  }
}

window.GameConfig = GameConfig;
