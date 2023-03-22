const DISPLAY_SELECTED_DURATION = 1;  // sync with backend
const WAIT_BEFORE_FLIP_DURATION = 3;  // sync with backend

function initAnswersScreen(variants) {
    const screen = document.getElementById("answers-screen");
    const variantsBlock = document.getElementById("variants-block");
    variantsBlock.innerHTML = "";
    for (let variant of variants) {
        let variantContainer = document.createElement("div");
        variantContainer.classList.add("d-flex", "align-items-baseline");
        let variantText = document.createElement("p");
        variantText.textContent = variant.text;
        variantContainer.append(variantText);
        if (variant.likable) {
            let like = document.createElement("input");
            like.type = "checkbox";
            like.classList.add("btn-check", "like");
            like.id = variant.id;
            let likeLable = document.createElement("label");
            likeLable.classList.add("btn", "like-btn", "fa", "fa-thumbs-up");
            likeLable.htmlFor=variant.id;
            variantContainer.append(like, likeLable);
        }
        variantsBlock.append(variantContainer);
    }
    let answerCard = document.querySelector(".answer-card-inner");
    answerCard.classList.add("invisible");
    answerCard.classList.remove("flipped");
    return screen;
}

function displayAnswer(answer, isCorrect) {
    let answerCard = document.querySelector(".answer-card-inner");
    let variantText = document.getElementById("answer-card-variant");

    variantText.textContent = answer.text;
    const variantSelects = document.getElementById("variant-selects");
    variantSelects.textContent = "";
    answerCard.classList.remove("flipped", "invisible");

    if (answer.selected_by.length) {
        answer.selected_by.forEach((answerSelectedImage, i) => {
            let delay = DISPLAY_SELECTED_DURATION * 1000 * (i + 1);
            setTimeout(() => displaySelectedBy(variantSelects, answerSelectedImage), delay);
            if (i === answer.selected_by.length - 1) {
                const delayBeforeFlip = delay + WAIT_BEFORE_FLIP_DURATION * 1000;
                setTimeout(initCardBack, delayBeforeFlip, answer, isCorrect);
                setTimeout(flipAnswerCard, delayBeforeFlip);
            }
        })
    }
    else {
        setTimeout(initCardBack, DISPLAY_SELECTED_DURATION * 1000, answer, isCorrect);
        setTimeout(flipAnswerCard, (DISPLAY_SELECTED_DURATION + WAIT_BEFORE_FLIP_DURATION) * 1000);
    }
}

function initCardBack(answer, isCorrect) {
    let variantAuthorContainer = document.getElementById("answer-card-author");
    variantAuthorContainer.textContent = "";
    let cardBack = document.querySelector(".answer-card-back");
    let cardCorrectness = document.getElementById("answer-card-correctness");

    if (answer.author.avatar) {
        const avatarEl = document.createElement('img');
        avatarEl.src = answer.author.avatar;
        variantAuthorContainer.append(avatarEl);
    }
    const authorNicknameEl = document.createElement('p');
    authorNicknameEl.append(answer.author.nickname)
    variantAuthorContainer.append(authorNicknameEl);

    if (isCorrect) {
        cardBack.classList.remove("answer-card-back-incorrect");
        cardBack.classList.add("answer-card-back-correct");
        cardCorrectness.textContent = "RIGHT";
    }
    else {
        cardBack.classList.add("answer-card-back-incorrect");
        cardBack.classList.remove("answer-card-back-correct");
        cardCorrectness.textContent = "WRONG";
    }
}

function flipAnswerCard() {
    let answerCard = document.querySelector(".answer-card-inner");
    answerCard.classList.toggle("flipped");
}

function displaySelectedBy(variant, player) {
        let selectedBlock = document.createElement("div");
        let playerImg = document.createElement("img");
        let playerNickname = document.createElement("p");
        playerImg.classList.add("selected-by-icon");
        playerImg.src = player.avatar;
        playerNickname.classList.add('nickname');
        playerNickname.textContent = player.nickname;
        selectedBlock.append(playerImg, playerNickname);
        variant.append(selectedBlock);
}