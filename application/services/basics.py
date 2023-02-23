from enum import IntEnum
import asyncio as aio
import sys

if sys.version_info < (3, 11):
    from strenum import StrEnum
else:
    from enum import StrEnum


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


class TaskType(StrEnum):
    drawing = 'drawing'
    selecting = 'selecting'
    writing = 'writing'


class GameRole(StrEnum):
    player = "player"
    host = "host"


class StageTime(IntEnum):
    preround = 120
    writing = 40
    selecting = 30
    results = 10
    for_one_select = 3


class MediaType(StrEnum):
    painting_task = 'painting'
    variant = 'variant'
    answer = 'answer'


DRAWING_COLORS = [
    '#4A466D',  # blue
    '#99454D',  # red
    '#69536D',  # purple
    '#3F8F8D',  # green
    '#855419',  # orange
    '#877241',  # yellow
    '#6E4C4E',  # pink
    '#451e3e',  # dark purple
    '#7d5d54',  # brown
]


CODE_CHARS = [chr(ord('A') + x) for x in range(26)]
GAME_CODE_LEN = 4
USERNAME_LEN = 10
POINTS_FOR_CORRECT_ANSWER = 1000
POINTS_FOR_CORRECT_RECOGNITION = 1000
POINTS_FOR_RECOGNITION = 250
MEDIA_UPLOAD_DELAY = 3
GAME_UPDATE_DELAY = 0.2





