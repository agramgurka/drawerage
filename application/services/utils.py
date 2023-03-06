from asyncio import Task


def display_task_result(task: Task) -> None:
    """ if task is finished with exception, raise"""

    task.result()
