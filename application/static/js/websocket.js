function connect() {
    return new WebSocket(
      (window.location.protocol === 'https:' ? 'wss://' : 'ws://') +
      window.location.host +
      '/ws/game/' +
      gameId +
      '/'
    );
}

const ws = connect();

ws.onopen = function () {
    ws.send(
        JSON.stringify({
            "command": "connected",
        })
    )};

ws.onmessage = function(response) {
    const res = JSON.parse(response.data);
    const command = res.command;
    if (command == "update") {
        const activeScreen = res.active_screen;
        let screen = null;
        if (activeScreen == "status") {
            screen = initStatusScreen(res.players, res.task_type)
        }
        if (activeScreen == "task") {
            screen = initTaskScreen(res.task_type, res.task);
        }
        if (activeScreen == "results") {
            screen = initResultsScreen(res.results);
        }
        if (activeScreen == "answers") {
            screen = initAnswersScreen(res.variants);
        }
        displayScreen(screen);
    }
    if (command == "display_answer") {
        displayAnswer(res.variant, res.is_correct);
    }
    if (command == "pause") {
        displayPausePopup(res.text);
    }
    if (command == "resume") {
        hidePausePopup();
    }
    if (command == "state") {
        if (res.stage) {
            let enabledButtons = ["cancel-game", "resume-game"];
            if (res.stage == "pregame") enabledButtons.push("start-game");
            else if (res.stage != "finished") enabledButtons.push("pause-game");
            displayButtons(enabledButtons);
        }
        if (res.game_code) displayGameCode(res.game_code);
        if (res.is_paused) displayPausePopup();
    }
    if (command == "timer") {
        setTimer(res.time);
    }
};