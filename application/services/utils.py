import logging
from asyncio import Task


def setup_logger(name: str) -> logging.Logger:
    """ basic logger setup """

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    f = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(f)
    logger.addHandler(handler)
    return logger


def display_task_result(task: Task) -> None:
    """ if task is finished with exception, raise"""

    task.result()
