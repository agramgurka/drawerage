var ws;
var reconnectionCnt = 0;
const reconnectionDelay = 1000;
const maxReconnectionCnt = 5;

function connect() {
    ws = new WebSocket(
      (window.location.protocol === 'https:' ? 'wss://' : 'ws://') +
      window.location.host +
      '/ws/game/' +
      gameId +
      '/'
    );
    ws.onopen = function () {
        hidePopups();
        reconnectionCnt = 0;
        ws.send(
            JSON.stringify({
                "command": "connected",
            })
        );
    };
    ws.onmessage = function(response) {
        const res = JSON.parse(response.data);
        const command = res.command;
        if (command === "update") {
            const activeScreen = res.active_screen;
            let screen = null;
            if (activeScreen === "status") {
                screen = initStatusScreen(res.players, res.task_type, res.task)
            }
            if (activeScreen === "task") {
                screen = initTaskScreen(res.task_type, res.task);
            }
            if (activeScreen === "results") {
                screen = initResultsScreen(res.results);
            }
            if (activeScreen === "answers") {
                screen = initAnswersScreen(res.variants);
            }
            if (activeScreen === "final_standings") {
                screen = initFinalStandingsScreen(res.results);
                window.removeEventListener("beforeunload", beforeUnloadListener);
            }
            displayScreen(screen);
        }
        if (command === "display_answer") {
            displayAnswer(res.variant, res.is_correct);
        }
        if (command === "pause") {
            displayPopup("pause-popup", res.text);
        }
        if (command === "cancel") {
            displayPopup("cancel-popup", res.text);
            window.removeEventListener("beforeunload", beforeUnloadListener);
        }
        if (command === "resume") {
            hidePopups();
        }
        if (command === "init_stage") {
            initStage(res.stage);
        }
        if (command === "timer") {
            setTimer(res.initial, res.left);
        }
        if (command === "error") {
            handleError(res.error_type, res.error_message);
        }
        if (command === "collect_likes") {
            collectLikes();
        }
    };
    ws.onerror = function(err) {
        ws.close();
    };
    ws.onclose = function () {
        reconnectionCnt++;
        if (reconnectionCnt <= maxReconnectionCnt)
            setTimeout(function () {
                displayPopup("disconnect-popup", "Reconnecting to server");
                addLoadingSpinner("reconnect-server");
                connect();
            }, reconnectionDelay);
        else {
            displayPopup("disconnect-popup", "Server is unavailable");
            removeLoadingSpinner("reconnect-server");
        }
    };
}

connect();