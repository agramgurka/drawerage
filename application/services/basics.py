from enum import StrEnum, IntEnum
import asyncio as aio


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
    results = 'results'
    finished = 'finished'


class GameScreens(StrEnum):
    status = 'status'
    task = 'task'
    results = 'results'
    pause = 'pause'


class TaskType(StrEnum):
    drawing = 'drawing'
    selecting = 'selecting'
    writing = 'writing'


class GameRole(StrEnum):
    player = "player"
    host = "host"


class StageTime(IntEnum):
    preround = 30
    writing = 20
    selecting = 10
    results = 10


class MediaType(StrEnum):
    painting_task = 'painting'
    variant = 'variant'
    answer = 'answer'


class DrawingColors(StrEnum):
    red = 'red'
    blue = 'blue'
    pink = 'pink'
    yellow = 'yellow'
    orange = 'orange'
    green = 'green'
    black = 'black'


CODE_CHARS = [chr(ord('A') + x) for x in range(26)]
GAME_CODE_LEN = 4
USERNAME_LEN = 10
POINTS_FOR_CORRECT_ANSWER = 250
POINTS_FOR_CORRECT_RECOGNITION = 1000
POINTS_FOR_RECOGNITION = 500
MEDIA_UPLOAD_DELAY = 3





