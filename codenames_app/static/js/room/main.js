document.addEventListener('DOMContentLoaded', () => {
    if (!window.roomConfig) {
        console.error('roomConfig is not defined');
        return;
    }

    const roomManager = new RoomManager(window.roomConfig);
    
    window.roomManager = roomManager;
});