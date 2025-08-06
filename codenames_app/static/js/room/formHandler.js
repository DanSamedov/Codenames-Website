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

    // Step 1: Clicking a Join button
    document.querySelectorAll(".join-team-btn").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        e.preventDefault();

        this.selectedTeam = btn.dataset.team; // Red or Blue
        if (teamInput) {
          teamInput.value = this.selectedTeam; // set hidden field
        }

        // Update UI to show selection state
        this.updateTeamSelectionUI(this.selectedTeam);
        this.insertRoleChooserIntoList(this.selectedTeam, tpl);
      });
    });

    // Step 2: When the user chooses a role, send via WebSocket instead of form submission
    if (form) {
      form.addEventListener("change", (e) => {
        if (e.target.matches('select[name="role"]') && e.target.value) {
          setTimeout(() => {
            this.handleTeamSelection(e.target.value, this.selectedTeam);
          }, 200);
        }
      });

      // Prevent traditional form submission
      form.addEventListener("submit", (e) => {
        e.preventDefault();
      });
    }
  }

  initializeStartGameForm() {
    const startGameForm = document.querySelector("#start-game-form");
    if (startGameForm) {
      startGameForm.addEventListener("submit", (e) => this.handleStartGame(e));
    }
  }

  // New method to handle team selection via WebSocket
  handleTeamSelection(selectedRole, selectedTeam) {
    if (selectedTeam === "None" || !selectedTeam) {
      alert("Please select a team");
      return;
    }

    // Send team change via WebSocket
    this.websocketManager.send({
      action: "change_team",
      role: selectedRole,
      team: selectedTeam,
    });

    // Auto-start game if conditions are met
    if (this.config.startingTeam !== "None") {
      this.startGame();
    }

    // Reset form
    const form = document.querySelector("#choose-team-form");
    if (form) {
      form.reset();
    }
  }

  // Keep the existing start game handler
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

  // Function to update UI when team is selected
  updateTeamSelectionUI(team) {
    const allContainers = document.querySelectorAll(".team-container");
    const allButtons = document.querySelectorAll(".join-team-btn");

    allContainers.forEach((container) => {
      const isSelected =
        container.querySelector(`[data-team="${team}"]`) !== null;

      if (isSelected) {
        container.classList.add("selected-team");
        // Optional: Add visual feedback for selected team
        container.style.transform = "scale(1.02)";
        container.style.boxShadow = "0 8px 25px rgba(0,0,0,0.15)";
      } else {
        container.classList.remove("selected-team");
        container.style.opacity = "0.6";
        container.style.transform = "scale(0.98)";
      }
    });

    // Disable all join buttons after selection
    allButtons.forEach((button) => {
      if (button.dataset.team === team) {
        button.textContent = `Selected: ${team} Team`;
        button.style.background = "#10b981";
        button.style.border = "0px";
        button.style.color = "white";
        button.style.cursor = "not-allowed";
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
}
