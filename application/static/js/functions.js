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
        if (!roundPainting){
            roundPainting = document.createElement("img");
            roundPainting.id = "round-painting"
            document.getElementById("drawing-area").appendChild(roundPainting);
        }
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

function initFinalStandingsScreen(standings) {
    let playerCard = null
    let placeCardAvatar = null;
    let placeCardScore = null;
    const scoreTable = document.querySelector("#final-standings tbody");
    scoreTable.innerHTML = "";

    for (let i in standings) {
        if (i < 3) {
            const playerCardAvatar = document.createElement("img");
            playerCardAvatar.classList.add("player-card-img");
            let playerCardScore;
            if (i == 0) {
                 playerCard = document.querySelector("#first-place-card");
                 playerCardScore = document.querySelector("#first-place-card .player-card-text");
            }
            else if (i == 1) {
                 playerCard = document.querySelector("#second-place-card");
                 playerCardScore = document.querySelector("#second-place-card .player-card-text");
            }
            else if (i == 2) {
                playerCard = document.querySelector("#third-place-card");
                playerCardScore = document.querySelector("#third-place-card .player-card-text");
            }
            playerCard.insertBefore(playerCardAvatar, playerCard.children[1])
            playerCardAvatar.src = "/media/" + standings[i].player__avatar;
            playerCardScore.innerHTML = standings[i].result;
            playerCard.style.borderColor = standings[i].player__drawing_color;
            playerCard.classList.remove("invisible");
        }

        let newRow = document.createElement("tr");
        let place = document.createElement("td");
        let player = document.createElement("td");
        let avatar = document.createElement("img");
        let nickname = document.createElement("p");
        let score = document.createElement("td");

        place.innerHTML = parseInt(i) + 1;
        avatar.src = '/media/' + standings[i].player__avatar;
        nickname.innerHTML = standings[i].player__nickname;
        score.innerHTML = standings[i].result;


        player.classList.add("d-flex", "align-items-center", "justify-content-center");
        avatar.classList.add("rounded-circle", "mx-2");
        avatar.style.width = "45px";
        avatar.style.height = "45px";
        nickname.classList.add("fw-bold");

        player.appendChild(avatar);
        player.appendChild(nickname);
        newRow.appendChild(place);
        newRow.appendChild(player);
        newRow.appendChild(score);
        scoreTable.appendChild(newRow);
    }
    return document.getElementById("final-standings");
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
    const codeBlock = document.getElementById("game-code");
    codeBlock.innerHTML = gameCode;
}

function displayButtons(enabledButtons) {
    const controlBtns = document.querySelectorAll(".control-btn");
    controlBtns.forEach((button) => {
        if (enabledButtons.includes(button.id)) {
            button.classList.remove("invisible");
        }
        else {
            button.classList.add("invisible");
        }

})}

function displayPopup(popupId, text) {
    document.getElementById(popupId + '-text').innerHTML = text;
    document.getElementById(popupId).classList.remove("invisible");
}

function hidePopup() {
    document.querySelectorAll(".pop-up").forEach((popup) => {popup.classList.add("invisible")});
}

function submitPainting() {
    canvas = document.getElementById("drawing-canvas");
    const painting = canvas.toDataURL("image/png");
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
}

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

function initStage(stage) {
    let enabledButtons = [];
    if (stage === "pregame") enabledButtons = ["start-game", "cancel-game"];
    else if (stage !== "finished") enabledButtons = ["cancel-game", "resume-game", "pause-game"];
    else enabledButtons = ["restart-game"];
    displayButtons(enabledButtons);
}

function handleError(errorType, errorMessage) {
    if (errorType === "start_game") {
        console.log(errorMessage);
        displayButtons(["start-game"]);
    }
}

function reconnectServer() {
    reconnectionCnt = 0;
    connect();
}

function addLoadingSpinner(elementId) {
    if (document.querySelector(`#${elementId} > .spinner-border`)) return;
    const element = document.getElementById(elementId);
    let loadingSpinner = document.createElement("span");
    loadingSpinner.classList.add("spinner-border", "spinner-border-sm");
    element.appendChild(loadingSpinner);
}

function removeLoadingSpinner(elementId) {
    document.querySelector(`#${elementId} > .spinner-border`).remove();
}
