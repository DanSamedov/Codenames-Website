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
      //   case "player_join":
      //     this.handlePlayerJoin(data);
      //     break;
      case "player_leave":
        this.handlePlayerLeave(data);
        break;
      default:
        console.warn("Unknown action:", data.action);
    }
  }

  handleTeamChoice(data) {
    const { username, role, team } = data;
    const playerElement = document.querySelector(`#player-${username}`);

    if (playerElement) {
      playerElement.querySelector(
        ".player-role"
      ).textContent = `Leader: ${role}`;
      playerElement.querySelector(".player-team").textContent = `Team: ${team}`;
    }
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

  // handlePlayerJoin(data) {
  //     const { username } = data;

  //     if (!document.querySelector(`#player-${username}`)) {
  //         const playerList = document.querySelector('ul');
  //         const newPlayer = document.createElement('li');
  //         newPlayer.id = `player-${username}`;
  //         newPlayer.innerHTML = `
  //             <h3 class="player-nickname">Nickname: ${username}</h3>
  //             <p class="player-creator">Creator: False</p>
  //             <p class="player-role">Leader: False</p>
  //             <p class="player-team">Team: None</p>`;
  //         playerList.appendChild(newPlayer);
  //     }
  // }

  handlePlayerLeave(data) {
    const element = document.getElementById(`player-${data.username}`);
    if (element) {
      element.remove();
    }
  }
}
