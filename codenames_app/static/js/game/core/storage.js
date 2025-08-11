class GameStorageManager {
  constructor(gameId) {
    this.gameId = gameId;
    this.initializedKey = `game_${gameId}_initialized`;
  }

  initializeCards() {
    if (!sessionStorage.getItem(this.initializedKey)) {
      const cardsData = JSON.parse(
        document.getElementById("cards-data").textContent
      );
      const cardDict = {};

      cardsData.forEach((card) => {
        cardDict[card.word] = card.color;
      });

      sessionStorage.setItem(this.initializedKey, "true");
      sessionStorage.setItem(
        `cardDict_${this.gameId}`,
        JSON.stringify(cardDict)
      );
    }
  }

  getCardDict() {
    return JSON.parse(
      sessionStorage.getItem(`cardDict_${this.gameId}`) || "{}"
    );
  }

  getSelectedCards() {
    return JSON.parse(localStorage.getItem("selectedCards") || "[]");
  }

  setSelectedCards(cards) {
    localStorage.setItem("selectedCards", JSON.stringify(cards));
  }

  getHintData() {
    return {
      hintNum: parseInt(localStorage.getItem("hintNum")) || 0,
      hintWord: localStorage.getItem("hintWord") || null,
    };
  }

  setHintData(hintWord, hintNum) {
    localStorage.setItem("hintWord", hintWord);
    localStorage.setItem("hintNum", hintNum);
  }

  clearHintData() {
    localStorage.removeItem("selectedCards");
    localStorage.removeItem("hintWord");
    localStorage.removeItem("hintNum");
  }
}

window.GameStorageManager = GameStorageManager;
