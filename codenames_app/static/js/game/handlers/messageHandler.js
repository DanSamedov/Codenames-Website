class GameMessageHandler {
  constructor(
    config,
    gameState,
    storageManager,
    cardManager,
    timerManager,
    uiManager,
    websocketManager
  ) {
    this.config = config;
    this.gameState = gameState;
    this.storageManager = storageManager;
    this.cardManager = cardManager;
    this.timerManager = timerManager;
    this.uiManager = uiManager;
    this.websocketManager = websocketManager;
  }

  handleMessage(data) {
    try {
      const constants = window.GameConstants.WEBSOCKET.ACTIONS;

      switch (data.action) {
        case constants.PLAYER_JOIN:
        case constants.REVEAL_GUESSED_CARDS:
          this.cardManager.initCards(data);
          break;
        case constants.SELECTED_CARDS:
          this.cardManager.updateSelectedCards(data.cards);
          break;
        case constants.CHOOSE_CARD:
          this.cardManager.updateCardChoice(data.card_id, data.card_status);
          break;
        case constants.HINT_DISPLAY:
          this.handleHintDisplay(data);
          break;
        case constants.ROUND_PHASE:
          this.handleRoundPhase(data);
          break;
        case constants.HINT_PHASE:
          this.handleHintPhase(data);
          break;
        case constants.SYNC_TIME:
          this.handleSyncTime(data);
          break;
        case constants.GAME_OVER:
          this.handleGameOver(data);
          break;
        default:
          console.warn("Unknown action:", data.action);
      }
    } catch (error) {
      console.error("Error handling message:", error, data);
    }
  }

  handleHintDisplay(data) {
    this.gameState.hintWord = data.hint_word;
    this.gameState.hintNum = Number(data.hint_num);
    this.storageManager.setHintData(
      this.gameState.hintWord,
      this.gameState.hintNum
    );
    this.uiManager.updateHintDisplay(
      this.gameState.hintWord,
      this.gameState.hintNum
    );
  }

  handleRoundPhase(data) {
    this.gameState.phase = window.GameConstants.PHASES.ROUND_PHASE;
    this.gameState.team = data.team;
    this.timerManager.startCountdown(data.duration, data.start_time * 1000);
    this.uiManager.toggleHintFormVisibility();
  }

  handleHintPhase(data) {
    this.gameState.phase = window.GameConstants.PHASES.HINT_PHASE;
    this.gameState.team = data.team;
    this.gameState.reset();

    this.storageManager.clearHintData();
    this.timerManager.startCountdown(data.duration, data.start_time * 1000);
    this.uiManager.clearHintDisplay();
    this.uiManager.toggleHintFormVisibility();
  }

  handleSyncTime(data) {
    const phase = data.phase;
    const storedHintData = this.storageManager.getHintData();

    this.gameState.phase = phase.phase;
    this.gameState.team = phase.team;

    if (
      storedHintData.hintNum &&
      this.gameState.phase === window.GameConstants.PHASES.ROUND_PHASE
    ) {
      this.uiManager.updateHintDisplay(
        storedHintData.hintWord,
        storedHintData.hintNum
      );
    } else {
      this.uiManager.clearHintDisplay();
    }

    this.timerManager.syncTime(phase);
    this.uiManager.toggleHintFormVisibility();
  }

  handleGameOver(data) {
    if (!this.gameState.hasWinnerBeenShown) {
      this.gameState.hasWinnerBeenShown = true;
      this.gameState.clearTimer();
      this.uiManager.showWinner(data.winner);
      this.websocketManager.close();
      this.uiManager.redirectToHome();
    }
  }
}

window.GameMessageHandler = GameMessageHandler;
