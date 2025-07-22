const room_id = window.roomConfig.roomId;
const currentUser = window.roomConfig.currentUser;
const currentRole = window.roomConfig.currentRole;
const currentTeam = window.roomConfig.currentTeam;
const startingTeam = window.roomConfig.startingTeam;

const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const host = window.location.host;
const roomSocket = new WebSocket(
    `${protocol}//${host}/ws/room/${room_id}/`
);

roomSocket.onopen = function(e) {
    console.log("WebSocket connection established");
};

roomSocket.onclose = function(e) {
    console.log("WebSocket connection closed", e);
};

roomSocket.onerror = function(error) {
    console.error("WebSocket error:", error);
};

roomSocket.onmessage = function (e) {
    const data = JSON.parse(e.data);

    if (data.action === 'team_choice') {
        const username = data['username'];
        const role = data['role'];
        const team = data['team'];

        let playerElement = document.querySelector('#player-' + username);

        if (playerElement) {
        playerElement.querySelector('.player-role').textContent =
            'Leader: ' + role;
        playerElement.querySelector('.player-team').textContent =
            'Team: ' + team;
        }
    } else if (data.action === 'restrict_choice') {
        alert('You cant switch teams or roles when game has started');
    } else if (data.action === 'redirect') {
        window.location.href = '/game/' + data.room_id;
    } else if (data.action === 'unready') {
        const creator = data['creator'];

        if (creator === currentUser) {
        alert('Wait until all players choose teams');
        }
    } else if (data.action === 'player_join') {
        const username = data['username'];

        if (!document.querySelector(`#player-${username}`)) {
        let playerList = document.querySelector('ul');

        let newPlayer = document.createElement('li');
        newPlayer.id = `player-${username}`;
        newPlayer.innerHTML = `
                <h3 class="player-nickname">Nickname: ${username}</h3>
                <p class="player-creator">Creator: False</p>
                <p class="player-role">Leader: False</p>
                <p class="player-team">Team: None</p>`;
        playerList.appendChild(newPlayer);
        }
    } else if (data.action === 'player_leave') {
        const el = document.getElementById(`player-${data.username}`);
        if (el) el.remove();
    }
};

window.addEventListener('beforeunload', () => {
    roomSocket.send(
        JSON.stringify({
        action: 'leave',
        username: currentUser,
        }),
    );
});

window.addEventListener('pageshow', event => {
    const nav = performance.getEntriesByType('navigation')[0]?.type;
    if (event.persisted || nav === 'back_forward') {
        setTimeout(() => window.location.reload(), 50);
        // document.getElementById('start-game-form').classList.add('visually-hidden');
    }
});

document.addEventListener('DOMContentLoaded', function () {
    const form = document.querySelector('#start-game-form');
    if (form) {
        form.onsubmit = function (event) {
        event.preventDefault();

        startGameMessage();
        };
    }
    makeRadiosTogglable('team');
    makeRadiosTogglable('role');
});

document.querySelector('#choose-team-form').onsubmit = function (event) {
    submitTeamChoice(event);
};

function submitTeamChoice(event) {
    event.preventDefault();
    
    const selectedRoleInput = document.querySelector('input[name="role"]:checked');
    const selectedTeamInput = document.querySelector('input[name="team"]:checked');
    const selectedRole = selectedRoleInput?.value || currentRole;
    const selectedTeam = selectedTeamInput?.value || currentTeam;

    if (selectedTeam === 'None') {
        alert('Please select a team');
        return;
    }

    roomSocket.send(
        JSON.stringify({
        action: 'change_team',
        role: selectedRole,
        team: selectedTeam,
        }),
    );

    if (startingTeam !== 'None') {
        startGameMessage();
    }

    document.querySelector('#choose-team-form').reset();
}

const startGameMessage = () => {
    roomSocket.send(
        JSON.stringify({
        action: 'start_game',
        room_id: room_id,
        }),
    );
};

function makeRadiosTogglable(name) {
    let lastChecked = null;
    document.querySelectorAll(`input[name="${name}"]`).forEach(radio => {
        radio.addEventListener('click', () => {
        if (radio === lastChecked) {
            radio.checked = false;
            lastChecked = null;
        } else {
            lastChecked = radio;
        }
        });
    });
}

function updatePlayerList(players) {
    const playerList = document.querySelector('ul');
    playerList.innerHTML = '';

    players.forEach(player => {
        const newPlayer = document.createElement('li');
        newPlayer.id = `player-${player.username}`;
        newPlayer.className = `player-card ${player.team || ''}`;
        newPlayer.innerHTML = `
        <h3 class="player-nickname">${player.username}</h3>
        <p class="player-meta">
            <span class="badge creator-${player.is_creator}">Creator</span>
            <span class="badge leader-${player.is_leader}">Leader</span>
            <span class="badge team-${player.team}">${player.team || 'No Team'}</span>
        </p>
        `;
        playerList.appendChild(newPlayer);
    });
}