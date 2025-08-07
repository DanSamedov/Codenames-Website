class MessageHandler {
  constructor(config) {
    this.config = config;
  }

  handleMessage(data) {
    switch (data.action) {
      case "team_choice":
        this.handleTeamChoice(data);
        break;
      case "restrict_choice":
        this.handleRestrictChoice();
        break;
      case "redirect":
        this.handleRedirect(data);
        break;
      case "unready":
        this.handleUnready(data);
        break;
      case "player_join":
        this.handlePlayerJoin(data);
        break;
      case "player_leave":
        this.handlePlayerLeave(data);
        break;
      default:
        console.warn("Unknown action:", data.action);
    }
  }

  handleTeamChoice(data) {
    const { username, role, team } = data;

    FormHandler.removeUserPreviousChoice(username);
    this.addPlayerElement(username, role, team);
  }

  handleRestrictChoice() {
    alert("You cant switch teams or roles when game has started");
  }

  handleRedirect(data) {
    window.location.href = `/game/${data.room_id}`;
  }

  handleUnready(data) {
    if (data.creator === this.config.currentUser) {
      alert("Wait until all players choose teams");
    }
  }

  handlePlayerJoin(data) {
    const { username, role, team } = data;
    if (!document.querySelector(`.${username}`)) {
      this.addPlayerElement(username, role, team);
    }
  }

  handlePlayerLeave(data) {
    const element = document.querySelector(`.${data.username}`);
    if (element) {
      element.remove();
    }
  }

  addPlayerElement(username, role, team) {
    const ul = document.getElementById(team);
    const li = document.createElement("li");
    li.classList.add("player-item", username);
    li.innerHTML = `
      <span class="player-name">${username}</span>
      <div class="role-selector"></div>`;

    const roleSelector = li.querySelector(".role-selector");
    const span = document.createElement("span");
    span.classList.add("text-[var(--text-light)]", "font-bold");
    if (role === "True") {
      span.textContent = "Spymaster";
    } else {
      span.textContent = "Operative";
    }

    roleSelector.appendChild(span);
    ul.appendChild(li);
  }
}
