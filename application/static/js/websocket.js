function connect() {
    return new WebSocket(
      (window.location.protocol === 'https:' ? 'wss://' : 'ws://') +
      window.location.host +
      '/ws/game/' +
      game_id +
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
        const active_screen = res.active_screen;
        if (active_screen == "status") {
            init_status_screen(res.players, res.task_type);
        }
        if (active_screen == "task") {
            init_task_screen(res.task_type, res.task);
        }
        if (active_screen == "results") {
            init_results_screen(res.results);
        }
    }
    if (command == "pause") {
        display_pause_popup(res.text);
    }
    if (command == "resume") {
        hide_pause_popup();
    }
    if (command == "state") {
        if (res.stage) {
            let enabled_buttons = ["cancel_game", "resume_game"];
            if (res.stage == "pregame") enabled_buttons.push("start_game");
            else if (res.stage != "finished") enabled_buttons.push("pause_game");
            display_buttons(enabled_buttons);
        }
        if (res.game_code) display_game_code(res.game_code);
        if (res.is_paused) display_pause_popup();
    }
    if (command == "timer") {
        set_timer(res.time);
    }
};