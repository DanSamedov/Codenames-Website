class TimerManager {
    constructor(gameState, websocketManager) {
        this.gameState = gameState;
        this.websocketManager = websocketManager;
    }

    startCountdown(duration, startTime) {
        const timerDisplay = document.getElementById('timer');

        this.gameState.clearTimer();

        const endTime = startTime + duration * 1000;
        this.gameState.timerInterval = setInterval(() => {
            const now = Date.now();
            const timeRemaining = Math.max(0, Math.floor((endTime - now) / 1000));

            if (timeRemaining <= 0) {
                this.gameState.clearTimer();
                if (timerDisplay) timerDisplay.textContent = "Time's up!";

                this.websocketManager.send({
                    action: 'start_timer',
                    type: 'timer_cycle',
                });
            } else {
                if (timerDisplay) timerDisplay.textContent = `Time remaining: ${timeRemaining}s`;
            }
        }, 1000);
    }

    syncTime(phaseData) {
        const { phase, duration, start_time } = phaseData;
        
        const clientTimeAtSync = Date.now() / 1000;
        this.gameState.clockOffset = start_time - clientTimeAtSync;

        const syncedCurrentTime = Date.now() / 1000 + this.gameState.clockOffset;
        const passedSeconds = syncedCurrentTime - start_time;
        const remainingTime = Math.max(duration - passedSeconds, 0);

        this.gameState.clearTimer();
        this.startCountdown(remainingTime, start_time * 1000);
    }
}

window.TimerManager = TimerManager;