const submit_painting_btn = document.getElementById("submit_painting");
submit_painting_btn.onclick = submit_painting;

document.getElementById('variantForm').addEventListener('submit', submit_variant);

const start_game_btn = document.getElementById("start_game");
start_game_btn.onclick = start_game;

const pause_game_btn = document.getElementById("pause_game");
pause_game_btn.onclick = pause_game;

const resume_game_btn = document.getElementById("resume_game");
resume_game_btn.onclick = resume_game;

const cancel_game_btn = document.getElementById("cancel_game");
cancel_game_btn.onclick = cancel_game;
