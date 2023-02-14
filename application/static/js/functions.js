function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function init_status_screen(players, stage) {
    const screen = document.getElementById("status_screen");
    screen.innerHTML = "";
    for (let i in players) {
        let status_block = document.createElement("div");
        status_block.classList.add("status_block", "col-md-5", "text-center", "py-4");
        let player_name = document.createElement("div");
        player_name.innerHTML = i;
        player_name.classList.add("player_name");
        let player_avatar = document.createElement("div");
        if (players[i].avatar){
            player_avatar = document.createElement("img");
            player_avatar.src = players[i].avatar;
            player_avatar.classList.add("player_avatar");
        }
        let status = document.createElement("img");
        if (players[i].finished) {
             status.src = static_url + "icons/status_ok.png";
        }
        else {
            status.src = static_url + "icons/status_" + stage + ".png";
        }
        status.innerHTML = players[i].finished;
        status.classList.add("status");
        status_block.appendChild(player_name);
        status_block.appendChild(player_avatar);
        status_block.appendChild(status);
        screen.appendChild(status_block);
    }
    display_screen(screen);
};

function init_task_screen(task_type, task){
    const screen = document.getElementById("task_screen");
    let drawing_task = document.getElementById("drawing_task");
    let writing_task = document.getElementById("writing_task");
    let types = document.querySelectorAll('.task_type');
    types.forEach(type => {
        if (!type.classList.contains("invisible")){
            type.classList.add("invisible");
        }
    })
    if (task_type == "drawing"){
        drawing_task.classList.remove("invisible");
        let canvas = document.getElementById("drawing_canvas");
        let context = canvas.getContext("2d");
        context.clearRect(0, 0, canvas.width, canvas.height);
        let task_area = document.getElementById("task");
        task_area.innerHTML = task;
    }
    if (task_type == "writing"){
        writing_task.classList.remove("invisible");
        let round_painting = document.getElementById("round_painting");
        round_painting.src = task;
        let variant = document.getElementById("variant");
        variant.value = "";
    }
    if (task_type == "selecting"){
        let selecting_task = document.getElementById("selecting_task");
        selecting_task.classList.remove("invisible");
        selecting_task.innerHTML = "";
        const ul = document.createElement("ul");
        ul.classList.add('list-group');
        for (let option in task) {
            let option_block = document.createElement("li");
            option_block.innerHTML = task[option].text;
            option_block.classList.add("option_block", "list-group-item");
            option_block.onclick = select_variant;
            ul.append(option_block);
        }
        selecting_task.append(ul);
    }
    display_screen(screen);
};

function init_results_screen(results){
    const screen = document.getElementById("results_screen");
    screen.innerHTML = "";
    for (let i in results) {
        let result_block = document.createElement("div");
        result_block.classList.add("result_block", "shadow-sm", "p-3", "mb-1", "bg-body", "rounded");
        let result_name = document.createElement("div");
        result_name.innerHTML = results[i].player__nickname;
        result_name.classList.add("result_name");
        let result = document.createElement("div");
        result.innerHTML = results[i].result;
        result.classList.add("result");
        let increment = document.createElement("div");
        increment.innerHTML = "+" + results[i].round_increment;
        increment.classList.add("increment");
        result_block.appendChild(result_name);
        result_block.appendChild(result);
        result_block.appendChild(increment);
        screen.appendChild(result_block);
    }
    display_screen(screen);
};

function display_screen(screen) {
    let all_screens = document.querySelectorAll('.game_screen');
    all_screens.forEach((scr) =>  {
       if (!scr.classList.contains('invisible')) {
                scr.classList.add('invisible');
            }
    })
    screen.classList.remove('invisible');

}

function display_game_code(game_code) {
    code_block = document.getElementById("game_code");
    code_block.innerHTML = game_code;
}

function display_buttons(enabled_buttons) {
    control_btns = document.querySelectorAll('.control_btn');
    control_btns.forEach((button) => {
        if (enabled_buttons.includes(button.id)) {
            if (button.classList.contains("invisible")) {
            button.classList.remove("invisible");
            }
        }
        else {
            if (!button.classList.contains("invisible")) {
                button.classList.add("invisible");
            }
        }

})}

function display_pause_popup(text){
    const pause_popup = document.getElementById("pause_popup");
    if (text) {
        let pause_text = document.getElementById("pause_text");
        pause_text.innerHTML = text;
    }
    if (pause_popup.classList.contains("invisible")){
         pause_popup.classList.remove("invisible");
    }
};

function hide_pause_popup() {
    const pause_popup = document.getElementById("pause_popup");
    if (!pause_popup.classList.contains("invisible")) {
         pause_popup.classList.add("invisible");
    }
}

function set_timer(time) {
    let timer = document.getElementById("timer");
    if (timer.classList.contains("invisible")) {
        timer.classList.remove("invisible");
    }
    timer.innerHTML = time;
    console.log(time);
    if (time == 0) {
        timer.classList.add("invisible");
        upload_media();
    }
}

function submit_painting() {
    canvas = document.getElementById("drawing_canvas");
    painting = canvas.toDataURL("image/png");
    let csrftoken = getCookie('csrftoken');
    fetch("/upload/", {
        method: "POST",
        credentials: "same-origin",
        headers: { "X-CSRFToken": csrftoken },
        body: JSON.stringify({
            "game_id": game_id,
            "media_type": "painting",
            "media": painting
        })
    })
    .then((response) => console.log(response));
}

function select_variant() {
    let answer = this.innerHTML;
    let csrftoken = getCookie('csrftoken');
    fetch(window.location.origin + "/upload/", {
        method: "POST",
        credentials: "same-origin",
        headers: { "X-CSRFToken": csrftoken },
        body: JSON.stringify({
            "game_id": game_id,
            "media_type": "answer",
            "media": answer
        })
    })
};

function submit_variant() {
    variant = document.getElementById("variant").value;
    let csrftoken = getCookie('csrftoken');
    fetch(window.location.origin + "/upload/", {
        method: "POST",
        credentials: "same-origin",
        headers: { "X-CSRFToken": csrftoken },
        body: JSON.stringify({
            "game_id": game_id,
            "media_type": "variant",
            "media": variant
        })
    })
    .then((response) => console.log(response));
}

function upload_media() {
    console.log("upload media function is called");
    let writing_task = document.getElementById("writing_task");
    let drawing_task = document.getElementById("drawing_task");

    if (!writing_task.classList.contains("invisible")) {
        submit_variant();
    }
    else if (!drawing_task.classList.contains("invisible")) {
        submit_painting();
    }
}

function start_game() {
    ws.send(
        JSON.stringify({
            "command": "start",
        })
    );
    display_buttons(['pause_game', 'cancel_game']);
}

function pause_game() {
    ws.send(
        JSON.stringify({
            "command": "pause",
        })
    );
    display_buttons(['resume_game', 'cancel_game']);
}

function resume_game() {
    ws.send(
        JSON.stringify({
            "command": "resume",
        })
    );
    display_buttons(['pause_game', 'cancel_game']);
}

function cancel_game() {
    ws.send(
        JSON.stringify({
            "command": "cancel",
        })
    );
    display_buttons([]);
}

