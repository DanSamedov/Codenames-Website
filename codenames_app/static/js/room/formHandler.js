class FormHandler {
  constructor(websocketManager, config) {
    this.websocketManager = websocketManager;
    this.config = config;
    this.selectedTeam = null;
    this.initializeForms();
  }

  initializeForms() {
    this.initializeTeamSelection();
    this.initializeStartGameForm();
  }

  initializeTeamSelection() {
    const form = document.getElementById("choose-team-form");
    const teamInput = form?.querySelector('input[name="team"]');
    const tpl = document.getElementById("role-template");

    document.querySelectorAll(".join-team-btn").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        e.preventDefault();

        this.selectedTeam = btn.dataset.team;
        if (teamInput) {
          teamInput.value = this.selectedTeam;
        }

        this.updateTeamSelectionUI(this.selectedTeam);
        this.insertRoleChooserIntoList(this.selectedTeam, tpl);
      });
    });

    if (form) {
      form.addEventListener("change", (e) => {
        if (e.target.matches('select[name="role"]') && e.target.value) {
          setTimeout(() => {
            this.handleTeamSelection(e.target.value, this.selectedTeam);
          }, 200);
        }
      });

      form.addEventListener("submit", (e) => {
        e.preventDefault();
      });
    }

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && this.selectedTeam) {
        this.cancelTeamSelection();
      }
    });
  }

  initializeStartGameForm() {
    const startGameForm = document.querySelector("#start-game-form");
    if (startGameForm) {
      startGameForm.addEventListener("submit", (e) => this.handleStartGame(e));
    }
  }

  handleTeamSelection(selectedRole, selectedTeam) {
    if (selectedTeam === "None" || !selectedTeam) {
      alert("Please select a team");
      return;
    }

    this.websocketManager.send({
      action: "change_team",
      role: selectedRole,
      team: selectedTeam,
    });

    if (this.config.startingTeam !== "None") {
      this.startGame();
    }

    const form = document.querySelector("#choose-team-form");
    if (form) {
      form.reset();
    }

    this.resetTeamSelectionUI();

    this.removeRoleChooser(this.selectedTeam);
  }

  handleStartGame(event) {
    event.preventDefault();
    this.startGame();
  }

  startGame() {
    this.websocketManager.send({
      action: "start_game",
      room_id: this.config.roomId,
    });
  }

  updateTeamSelectionUI(team) {
    const allContainers = document.querySelectorAll(".team-container");
    const allButtons = document.querySelectorAll(".join-team-btn");

    allContainers.forEach((container) => {
      const isSelected =
        container.querySelector(`[data-team="${team}"]`) !== null;

      if (isSelected) {
        container.classList.add("selected-team");
        container.style.transform = "scale(1.02)";
        container.style.boxShadow = "0 8px 25px rgba(0,0,0,0.15)";
      } else {
        container.classList.remove("selected-team");
        container.style.opacity = "0.6";
        container.style.transform = "scale(0.98)";
      }
    });

    allButtons.forEach((button) => {
      if (button.dataset.team === team) {
        button.textContent = `Selected: ${team} Team`;
        button.style.background = "#10b981";
        button.style.border = "0px";
        button.style.color = "white";
        button.style.cursor = "not-allowed";
        button.disabled = true;
        button.style.pointerEvents = "none";
      } else {
        button.disabled = true;
        button.style.opacity = "0.5";
        button.style.cursor = "not-allowed";
      }
    });
  }

  insertRoleChooserIntoList(team, tpl) {
    const ul = document.getElementById(team);

    if (!ul || !tpl) return;

    const clone = tpl.content.firstElementChild.cloneNode(true);
    clone.disabled = false;
    clone.closest(".role-selector").style.display = "block";

    const li = document.createElement("li");
    li.className = "player-item";
    li.innerHTML = `
      <span class="player-name">${this.config.currentUser}</span>
      <div class="role-selector"></div>
    `;
    li.querySelector(".role-selector").appendChild(clone);
    console.log(ul, li);

    ul.appendChild(li);
    clone.focus();
  }

  cancelTeamSelection() {
    if (!this.selectedTeam) return;

    this.resetTeamSelectionUI();

    this.removeRoleChooser(this.selectedTeam);

    const form = document.getElementById("choose-team-form");
    const teamInput = form?.querySelector('input[name="team"]');
    if (teamInput) {
      teamInput.value = "";
    }

    this.selectedTeam = null;

    console.log("Team selection canceled");
  }

  resetTeamSelectionUI() {
    const allContainers = document.querySelectorAll(".team-container");
    const allButtons = document.querySelectorAll(".join-team-btn");

    allContainers.forEach((container) => {
      container.classList.remove("selected-team");
      container.style.transform = "";
      container.style.boxShadow = "";
      container.style.opacity = "";
    });

    allButtons.forEach((button) => {
      button.disabled = false;
      button.style.opacity = "";
      button.style.cursor = "";
      button.style.background = "";
      button.style.border = "";
      button.style.color = "";
      button.style.pointerEvents = "auto";

      const team = button.dataset.team;
      button.textContent = `Join ${team} Team`;
    });
  }

  removeRoleChooser(team) {
    const ul = document.getElementById(team);
    if (!ul) return;

    const playerItems = ul.querySelectorAll(".player-item");
    playerItems.forEach((item) => {
      const roleSelector = item.querySelector(".role-selector");
      if (roleSelector) {
        item.remove();
      }
    });
  }
}
