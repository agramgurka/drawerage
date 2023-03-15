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

function initStatusScreen(players, taskType, task) {
    const gameStage = document.getElementById("round-stage");
    const currentTask = document.getElementById("current-task");
    currentTask.innerHTML = "";
    const playersStatuses = document.getElementById("players-statuses");
    playersStatuses.innerHTML = "";
    const statusScreenHeader = document.createElement("h4");
    statusScreenHeader.classList.add("text-center")
    currentTask.appendChild(statusScreenHeader);

    if (taskType === "writing") {
        statusScreenHeader.innerHTML = "Players are guessing what is drawn here";
        let painting = document.createElement("img");
        painting.classList.add("mx-auto", "d-block", "painting-miniature");
        painting.src = task;
        painting.addEventListener("click",
            function() {
            this.style.width === "50%" ? this.style.width = "100%" : this.style.width = "50%"
            }
        )
        currentTask.appendChild(painting);
    }
    else if (taskType === "selecting") {
        statusScreenHeader.innerHTML = "Players are selecting the correct answer";
        let variants = document.createElement("ul");
        variants.classList.add("my-3", "mx-5");
        for (let i in task) {
            let variant = document.createElement("li");
            variant.innerHTML = task[i];
            variant.classList.add("fs-5");
            variants.appendChild(variant);
        }
        currentTask.appendChild(variants);
    }

    for (let i in players) {
        let statusBlock = document.createElement("div");
        statusBlock.classList.add("col-md-3", "status-block", "text-center", "py-4");
        let playerName = document.createElement("p");
        playerName.innerHTML = i;
        playerName.classList.add("player-name");
        let playerAvatar;
        if (players[i].avatar){
            playerAvatar = document.createElement("img");
            playerAvatar.classList.add("player-avatar", "empty-avatar");
            playerAvatar.src = players[i].avatar;
            playerAvatar.classList.remove("empty-avatar");
        } else {
            playerAvatar = document.createElement("div");
            playerAvatar.classList.add("player-avatar", "empty-avatar");
        }
        let status = document.createElement("img");
        if (players[i].finished) {
             status.src = staticUrl + "icons/status_ok.png";
        }
        else {
            status.classList.add('status-' + taskType);
            status.src = staticUrl + "icons/status_" + taskType + ".png";
        }
        status.innerHTML = players[i].finished;
        status.classList.add("status");
        statusBlock.appendChild(playerAvatar);
        statusBlock.appendChild(status);
        statusBlock.appendChild(playerName);
        playersStatuses.appendChild(statusBlock);
    }
    return document.getElementById("status-screen");;
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

        const img = document.createElement("img");
        img.classList.add("mx-auto", "d-block");
        img.src = task.painting;
        const imgContainer = document.getElementById("selecting-task-image");
        imgContainer.innerHTML = "";
        imgContainer.append(img);
        const ul = document.getElementById("selecting-task-variants");
        ul.innerHTML = "";
        task.variants.forEach((option) => {
            let optionBlock = document.createElement("li");
            optionBlock.innerHTML = option;
            optionBlock.classList.add("option-block", "list-group-item");
            optionBlock.addEventListener("click", selectVariant);
            ul.append(optionBlock);
        })
        selectingTask.classList.remove("invisible");
    }
    return screen;
}

function initFinalStandingsScreen(standings) {
    const winners = document.getElementById("winners");
    winners.innerHTML = "";
    const scoreTable = document.querySelector("#final-standings tbody");
    scoreTable.innerHTML = "";
    let playerPlace = 1;

    for (let i in standings) {
        if (i < 3) {
            let placeCard = document.createElement("div");
            placeCard.classList.add("player-card");
            let placeBadge = document.createElement("span");
            placeBadge.classList.add("place-badge");
            placeCardBody = document.createElement("div");
            placeCardBody.classList.add("player-card-body");
            let placeCardText = document.createElement("p");
            placeCardText.classList.add("player-card-text");
            placeCardText.innerHTML = standings[i].result;
            let placeCardAvatar = document.createElement("img");
            placeCardAvatar.classList.add("player-card-img");
            placeCardAvatar.src = "/media/" + standings[i].player__avatar;
            placeCardBody.appendChild(placeCardText);

            if (playerPlace === 1) {
                placeCard.classList.add("first-place-card");
                placeBadge.classList.add("first-place-badge");
                placeBadge.innerHTML = "#1";
            }
            else if (playerPlace === 2) {
                placeCard.classList.add("second-place-card");
                placeBadge.classList.add("second-place-badge");
                placeBadge.innerHTML = "#2";
            }
            else if (playerPlace === 3) {
                placeCard.classList.add("third-place-card");
                placeBadge.classList.add("third-place-badge");
                placeBadge.innerHTML = "#3";
            }
            placeCard.appendChild(placeBadge);
            placeCard.appendChild(placeCardAvatar);
            placeCard.appendChild(placeCardBody);
            placeCard.style.borderColor = standings[i].player__drawing_color;
            winners.append(placeCard);
        }

        let newRow = document.createElement("tr");
        let place = document.createElement("td");
        let player = document.createElement("td");
        let avatar = document.createElement("img");
        let nickname = document.createElement("p");
        let score = document.createElement("td");

        place.innerHTML = playerPlace;
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
        if (parseInt(i) + 1 < standings.length && standings[i].result > standings[parseInt(i)+1].result) playerPlace++;
    }
    window.removeEventListener("beforeunload", beforeUnloadListener);
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
    hidePopups();
    document.getElementById(popupId + '-text').innerHTML = text;
    document.getElementById(popupId).classList.remove("invisible");
}

function hidePopups() {
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
            if (data.status !== 'success' && !!e) {
                errorEl.innerHTML = data.message;
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
