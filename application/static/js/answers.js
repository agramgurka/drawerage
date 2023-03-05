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
            delay = 1000 * (parseInt(i) + 1);
            setTimeout(displaySelectedBy, delay, variantSelects, answer.selected_by[i]);
            if (i == answer.selected_by.length - 1) {
                setTimeout(initCardBack, delay + 1000, answer, isCorrect);
                setTimeout(flipAnswerCard, delay + 1000);
            }
        }
    }
    else {
        setTimeout(initCardBack, 1000, answer, isCorrect);
        setTimeout(flipAnswerCard, 2000);
    }
}

function initCardBack(answer, isCorrect) {
    let variantAuthor = document.getElementById("answer-card-author");
    let variantAuthorAvatar = document.getElementById("answer-card-author-avatar");
    let cardBack = document.querySelector(".answer-card-back");
    let cardCorrectness = document.getElementById("answer-card-correctness");

    variantAuthor.innerHTML = answer.author.nickname;
    variantAuthorAvatar.src = answer.author.avatar;

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