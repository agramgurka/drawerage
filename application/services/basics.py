import asyncio as aio
import os.path
import sys
from enum import IntEnum

from Drawesome.settings import BASE_DIR

if sys.version_info < (3, 11):
    from strenum import StrEnum
else:
    from enum import StrEnum


DISPLAY_SELECTED_DURATION = 1  # in seconds (sync with frontend)
WAIT_BEFORE_FLIP_DURATION = 3  # in seconds (sync with frontend)
WAIT_BEFORE_NEXT_ANSWER = 5  # in seconds


class Timer:
    """ game timer """

    def __init__(self, start_time: int):
        self.time = start_time

    async def tick(self):
        await aio.sleep(1)
        self.time -= 1

    @property
    def exceed(self):
        return self.time < 0


class GameStage(StrEnum):
    pregame = 'pregame'
    preround = 'preround'
    round = 'round'
    finished = 'finished'


class RoundStage(StrEnum):
    not_started = 'not started'
    writing = 'writing'
    selecting = 'selecting'
    answers = 'answers'
    results = 'results'
    finished = 'finished'


class GameScreens(StrEnum):
    status = 'status'
    task = 'task'
    results = 'results'
    pause = 'pause'
    answers = 'answers'
    final_standings = 'final_standings'


class TaskType(StrEnum):
    drawing = 'drawing'
    selecting = 'selecting'
    writing = 'writing'


class GameRole(StrEnum):
    player = "player"
    host = "host"


class StageTime(IntEnum):
    preround = 120
    writing = 50
    selecting = 30
    results = 10
    for_one_answer = WAIT_BEFORE_FLIP_DURATION


class MediaType(StrEnum):
    painting_task = 'painting'
    variant = 'variant'
    answer = 'answer'
    likes = 'likes'


colors_file = os.path.join(
    BASE_DIR,
    'application/services/assets/drawing_colors.txt'
)
with open(colors_file) as f:
    DRAWING_COLORS = [color.strip('\n') for color in f]

CODE_CHARS = [chr(ord('A') + x) for x in range(26)]
GAME_CODE_LEN = 4
USERNAME_LEN = 10
NICKNAME_LEN = 100
POINTS_FOR_CORRECT_ANSWER = 1000
POINTS_FOR_CORRECT_RECOGNITION = 1000
POINTS_FOR_RECOGNITION = 250
MEDIA_UPLOAD_DELAY = 3
GAME_UPDATE_DELAY = 0.2
