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

function initStatusScreen(players, stage) {
    const screen = document.getElementById("status-screen");
    screen.innerHTML = "";
    for (let i in players) {
        let statusBlock = document.createElement("div");
        statusBlock.classList.add("status-block", "col-md-5", "text-center", "py-4");
        let playerName = document.createElement("div");
        playerName.innerHTML = i;
        playerName.classList.add("player-name");
        let playerAvatar = document.createElement("div");
        if (players[i].avatar){
            playerAvatar = document.createElement("img");
            playerAvatar.src = players[i].avatar;
            playerAvatar.classList.add("player-avatar");
        }
        let status = document.createElement("img");
        if (players[i].finished) {
             status.src = staticUrl + "icons/status_ok.png";
        }
        else {
            status.classList.add('status-' + stage);
            status.src = staticUrl + "icons/status_" + stage + ".png";
        }
        status.innerHTML = players[i].finished;
        status.classList.add("status");
        statusBlock.appendChild(playerName);
        statusBlock.appendChild(playerAvatar);
        statusBlock.appendChild(status);
        screen.appendChild(statusBlock);
    }
    return screen;
};

function initTaskScreen(taskType, task){
    let screen = document.getElementById("task-screen");
    let types = document.querySelectorAll('.task-type');
    types.forEach(type => {
        if (!type.classList.contains("invisible")){
            type.classList.add("invisible");
        }
    })
    if (taskType === "drawing"){
        let drawingTask = document.getElementById("drawing-task");
        drawingTask.classList.remove("invisible");
        let canvas = document.getElementById("drawing-canvas");
        let context = canvas.getContext("2d");
        context.clearRect(0, 0, canvas.width, canvas.height);
        let taskArea = document.getElementById("task");
        taskArea.innerHTML = task;
    }
    if (taskType === "writing"){
        let writingTask = document.getElementById("writing-task");
        writingTask.classList.remove("invisible");
        let roundPainting = document.getElementById("round-painting");
        roundPainting.src = task;
        let variant = document.getElementById("variant");
        variant.value = "";
    }
    if (taskType === "selecting"){
        let selectingTask = document.getElementById("selecting-task");

        const img = document.createElement('img');
        img.src = task.painting;
        const imgContainer = document.createElement('div')
        imgContainer.append(img);
        const ul = document.createElement("ul");
        ul.classList.add("list-group");
        task.variants.forEach((option) => {
            let optionBlock = document.createElement("li");
            optionBlock.innerHTML = option;
            optionBlock.classList.add("option-block", "list-group-item");
            optionBlock.addEventListener("click", selectVariant);
            ul.append(optionBlock);
        })
        selectingTask.classList.remove("invisible");
        selectingTask.innerHTML = "";
        selectingTask.append(imgContainer);
        selectingTask.append(ul);
    }
    return screen;
}



function initAnswersScreen(variants) {
    const screen = document.getElementById("answers-screen");
    const variantsBlock = document.getElementById("variants-block");
    setTimer(0);
    variantsBlock.innerHTML = "";
    for (let i in variants) {
        let variant = document.createElement("div");
        variant.innerHTML = variants[i];
        variantsBlock.append(variant);
    }
    const variantText = document.getElementById("variant-text");
    variantText.innerHTML = "";
    const variantSelects = document.getElementById("variant-selects");
    variantSelects.innerHTML = "";
    const variantDetails = document.getElementById("variant-details");
    variantDetails.classList.remove('incorrect-answer');
    variantDetails.classList.remove('correct-answer');
    return screen;
}

function displayAnswer(answer, isCorrect) {
    let variantDetails = document.getElementById("variant-details");
    variantDetails.classList.remove('incorrect-answer');
    variantDetails.classList.remove('correct-answer');
    const variantText = document.getElementById("variant-text");
    variantText.innerHTML = answer.text;
    const variantSelects = document.getElementById("variant-selects");
    variantSelects.innerHTML = ""
    if (answer.selected_by.length) {
        for (let i in answer.selected_by) {
            delay = 1000 * (parseInt(i) + 1);
            setTimeout(displaySelectedBy, delay, variantSelects, answer.selected_by[i]);
            if (i == answer.selected_by.length - 1)
            setTimeout(displayCorrectness, delay + 1000, isCorrect);
        }
    }
    else
        setTimeout(displayCorrectness, 1000, isCorrect);
}

function displayCorrectness(isCorrect) {
    let variantDetails = document.getElementById("variant-details");
    if (isCorrect) {
        variantDetails.classList.add("correct-answer");
        variantDetails.classList.remove("incorrect-answer");
    }
    else {
        variantDetails.classList.remove("correct-answer");
        variantDetails.classList.add("incorrect-answer");
    }
}

function displaySelectedBy(variant, player) {
        let playerImg = document.createElement('img');
        playerImg.classList.add('selected-by-icon');
        playerImg.src = player;
        variant.appendChild(playerImg);
}

function displayScreen(screen) {
    let allScreens = document.querySelectorAll(".game-screen");
    allScreens.forEach((scr) =>  {
       if (!scr.classList.contains("invisible")) {
                scr.classList.add("invisible");
            }
    })
    screen.classList.remove("invisible");

}

function displayGameCode(gameCode) {
    codeBlock = document.getElementById("game-code");
    codeBlock.innerHTML = gameCode;
}

function displayButtons(enabledButtons) {
    controlBtns = document.querySelectorAll(".control-btn");
    controlBtns.forEach((button) => {
        if (enabledButtons.includes(button.id)) {
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

function displayPausePopup(text){
    const pausePopup = document.getElementById("pause-popup");
    if (text) {
        let pauseText = document.getElementById("pause-text");
        pauseText.innerHTML = text;
    }
    if (pausePopup.classList.contains("invisible")){
         pausePopup.classList.remove("invisible");
    }
};

function hidePausePopup() {
    const pausePopup = document.getElementById("pause-popup");
    if (!pausePopup.classList.contains("invisible")) {
         pausePopup.classList.add("invisible");
    }
}

function setTimer(time) {
    let timer = document.getElementById("timer");
    if (timer.classList.contains("invisible")) {
        timer.classList.remove("invisible");
    }
    timer.innerHTML = time;
    if (time === 0) {
        timer.classList.add("invisible");
        uploadMedia();
    }
}

function submitPainting() {
    canvas = document.getElementById("drawing-canvas");
    painting = canvas.toDataURL("image/png");
    let csrftoken = getCookie('csrftoken');
    fetch("/upload/", {
        method: "POST",
        credentials: "same-origin",
        headers: { "X-CSRFToken": csrftoken },
        body: JSON.stringify({
            "game_id": gameId,
            "media_type": "painting",
            "media": painting
        })
    });
}

function selectVariant() {
    let answer = this.innerHTML;
    let csrftoken = getCookie('csrftoken');
    fetch(window.location.origin + "/upload/", {
        method: "POST",
        credentials: "same-origin",
        headers: { "X-CSRFToken": csrftoken },
        body: JSON.stringify({
            "game_id": gameId,
            "media_type": "answer",
            "media": answer
        })
    })
};

function submitVariant(e) {
    if (e) {e.preventDefault();}
    const errorEl = document.querySelector('#variant-form .validation-error');
    errorEl.innerHTML = '';

    const variant = document.getElementById("variant").value;
    let csrftoken = getCookie('csrftoken');
    if (variant && (variant.length > 5 || e)) {
        fetch(window.location.origin + "/upload/", {
            method: "POST",
            credentials: "same-origin",
            headers: {"X-CSRFToken": csrftoken},
            body: JSON.stringify({
                "game_id": gameId,
                "media_type": "variant",
                "media": variant
            })
        })
        .then((response) => {
             if (response.status !== 200) {
                console.error(response);
             }
            return response.json();
        })
        .then((data) => {
            if (data.status === 'duplicate' && !!e) {
                errorEl.innerHTML = "You variant is too close to someone's variant or to the correct answer";
            }
        });
    }
}

function uploadMedia() {
    let writingTask = document.getElementById("writing-task");
    let drawingTask = document.getElementById("drawing-task");

    if (!writingTask.classList.contains("invisible")) {
        submitVariant();
    }
    else if (!drawingTask.classList.contains("invisible")) {
        submitPainting();
    }
}

function startGame() {
    ws.send(
        JSON.stringify({
            "command": "start",
        })
    );
    displayButtons(['pause-game', 'cancel-game']);
}

function pauseGame() {
    ws.send(
        JSON.stringify({
            "command": "pause",
        })
    );
    displayButtons(['resume-game', 'cancel-game']);
}

function resumeGame() {
    ws.send(
        JSON.stringify({
            "command": "resume",
        })
    );
    displayButtons(['pause-game', 'cancel-game']);
}

function cancelGame() {
    ws.send(
        JSON.stringify({
            "command": "cancel",
        })
    );
    displayButtons([]);
}
