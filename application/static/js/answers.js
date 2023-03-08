function initAnswersScreen(variants) {
    const screen = document.getElementById("answers-screen");
    const variantsBlock = document.getElementById("variants-block");
    variantsBlock.innerHTML = "";
    for (let i in variants) {
        let variant = document.createElement("div");
        variant.innerHTML = variants[i];
        variantsBlock.append(variant);
    }
    let answerCard = document.querySelector(".answer-card-inner");
    answerCard.classList.add("invisible");
    answerCard.classList.remove("flipped");
    return screen;
}

function displayAnswer(answer, isCorrect) {
    let answerCard = document.querySelector(".answer-card-inner");
    let variantText = document.getElementById("answer-card-variant");

    variantText.innerHTML = answer.text;
    const variantSelects = document.getElementById("variant-selects");
    variantSelects.innerHTML = "";
    answerCard.classList.remove("flipped", "invisible");

    if (answer.selected_by.length) {
        for (let i in answer.selected_by) {
            var delay = 1000 * (parseInt(i) + 1);
            setTimeout(() => displaySelectedBy(variantSelects, answer.selected_by[i]), delay);
            if (parseInt(i) === answer.selected_by.length - 1) {
                setTimeout(initCardBack, delay + 1000, answer, isCorrect);
                setTimeout(flipAnswerCard, delay + 1000);
            }
        }
    }
    else {
        setTimeout(() => initCardBack(answer, isCorrect), 1000);
        setTimeout(flipAnswerCard, 2000);
    }
}

function initCardBack(answer, isCorrect) {
    let variantAuthorContainer = document.getElementById("answer-card-author");
    variantAuthorContainer.innerHTML = '';
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
        cardCorrectness.innerHTML = "RIGHT";
    }
    else {
        cardBack.classList.add("answer-card-back-incorrect");
        cardBack.classList.remove("answer-card-back-correct");
        cardCorrectness.innerHTML = "WRONG";
    }
}

function flipAnswerCard() {
    let answerCard = document.querySelector(".answer-card-inner");
    answerCard.classList.toggle("flipped");
}

function displaySelectedBy(variant, player) {
        let playerImg = document.createElement('img');
        playerImg.classList.add('selected-by-icon');
        playerImg.src = player;
        variant.appendChild(playerImg);
}