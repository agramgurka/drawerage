if (gameCode) {
    displayGameCode(gameCode);
}

function beforeUnloadListener(event) {
    event.preventDefault();
    return event.returnValue = "Are you sure you want to leave the page?";
}

window.addEventListener("beforeunload", beforeUnloadListener);
