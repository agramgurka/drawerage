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
        if (activeScreen == "final_standings") {
            screen = initFinalStandingsScreen(res.results);
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
    if (command == "init_stage") {
        initStage(res.stage);
    }
    if (command == "timer") {
        setTimer(res.initial, res.left);
    }
};