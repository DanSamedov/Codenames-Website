class UIManager {
  constructor(config, gameState) {
    this.config = config;
    this.gameState = gameState;
    this.hintDisplay = document.getElementById("hint-display");
    this.hintWordElement = document.getElementById("hint-word");
    this.hintNumberElement = document.getElementById("hint-number");
  }

  updateHintDisplay(hintWord, hintNum) {
    if (!this.hintDisplay || !this.hintWordElement || !this.hintNumberElement) {
      console.warn("Hint display elements not found");
      return;
    }

    if (!hintWord || typeof hintWord !== "string") {
      console.warn("Invalid hint word provided");
      return;
    }

    if (!Number.isInteger(hintNum) || hintNum < 1) {
      console.warn("Invalid hint number provided");
      return;
    }

    this.hintWordElement.textContent = hintWord.trim().toUpperCase();
    this.hintNumberElement.textContent = hintNum;

    this.animateHintUpdate();
    this.showHintDisplay();
  }

  animateHintUpdate() {
    this.hintWordElement.style.transform = "scale(1.1)";
    this.hintNumberElement.style.transform = "scale(1.1)";

    setTimeout(() => {
      this.hintWordElement.style.transform = "scale(1)";
      this.hintNumberElement.style.transform = "scale(1)";
    }, 200);
  }

  clearHintDisplay() {
    if (!this.hintWordElement || !this.hintNumberElement) {
      console.warn("Hint display elements not found");
      return;
    }

    this.hintWordElement.textContent = "";
    this.hintNumberElement.textContent = "";
    this.hideHintDisplay();
  }

  showHintDisplay() {
    if (!this.hintDisplay) return;

    this.hintDisplay.classList.remove("hidden");
    this.hintDisplay.classList.add("flex");
  }

  hideHintDisplay() {
    if (!this.hintDisplay) return;

    this.hintDisplay.classList.remove("flex");
    this.hintDisplay.classList.add("hidden");
  }

  alertWinner(winner) {
    alert(`${winner} Team wins!`);
  }

  toggleHintFormVisibility() {
    const hintForm = document.getElementById("hint-form");
    if (!hintForm || this.config.currentTeam !== this.gameState.team) return;

    const isRoundPhase =
      this.gameState.phase === window.GameConstants.PHASES.ROUND_PHASE;
    if (isRoundPhase) {
      hintForm.classList.add("hidden");
      hintForm.classList.remove("flex");
    } else {
      hintForm.classList.add("flex");
      hintForm.classList.remove("hidden");
    }
  }

  redirectToHome() {
    setTimeout(() => {
      const redirectUrl = new URL(window.location.href);
      redirectUrl.pathname = "/";
      redirectUrl.search = "";
      window.location.href = redirectUrl.toString();
    }, 1000);
  }

  updateElementColors(el) {
    if (!el) return;

    this.clearElementColors(el);

    if (this.gameState.team === "Red") {
      el.classList.add(
        "text-[var(--primary-color)]",
        "border-[var(--primary-color)]"
      );
    } else if (this.gameState.team === "Blue") {
      el.classList.add(
        "text-[var(--secondary-color)]",
        "border-[var(--secondary-color)]"
      );
    } else {
      el.classList.add("text-[var(--light-text)]", "border-[var(--text-dark)]");
    }
  }

  clearElementColors(el) {
    if (!el) return;

    const colorClasses = [
      "text-[var(--primary-color)]",
      "text-[var(--secondary-color)]",
      "text-[var(--light-text)]",
      "border-[var(--primary-color)]",
      "border-[var(--secondary-color)]",
      "border-[var(--text-dark)]",
    ];

    colorClasses.forEach((className) => {
      el.classList.remove(className);
    });
  }
}

window.UIManager = UIManager;
