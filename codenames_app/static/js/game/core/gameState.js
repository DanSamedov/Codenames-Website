class GameState {
  constructor() {
    this.clockOffset = 0;
    this.timerInterval = null;
    this.phase = window.GameConstants.PHASES.HINT_PHASE;
    this.team = null;
    this.hintNum = 0;
    this.hintWord = null;
    this.hasWinnerBeenShown = false;
    this.chosenCount = 0;
  }

  updateFromStorage(storageManager) {
    const hintData = storageManager.getHintData();
    this.hintNum = hintData.hintNum;
    this.hintWord = hintData.hintWord;
  }

  clearTimer() {
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
      this.timerInterval = null;
    }
  }

  reset() {
    this.hintWord = null;
    this.hintNum = 0;
    this.chosenCount = 0;
  }
}

window.GameState = GameState;
