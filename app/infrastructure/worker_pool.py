from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List

from app.execution.task_executor import execute_task
from app.infrastructure.resource_manager import ResourceManager
from app.models.task import Task


def execute_task_in_process(task: Task):
    """
    Top-level function required by ProcessPoolExecutor.

    Each task runs in a separate Python process,
    allowing true CPU parallelism.
    """

    return execute_task(task, None)


class WorkerPool:
    """
    Executes CPU-bound tasks using multiple processes.

    The number of processes is controlled by the
    ResourceManager infrastructure capacity.
    """

    def __init__(self, resource_manager: ResourceManager):
        self.resource_manager = resource_manager

    def execute_tasks(self, tasks: List[Task]) -> list:
        if not tasks:
            return []

        worker_count = min(
            self.resource_manager.max_workers,
            len(tasks)
        )

        results = []

        with ProcessPoolExecutor(
            max_workers=worker_count
        ) as executor:

            futures = [
                executor.submit(
                    execute_task_in_process,
                    task
                )
                for task in tasks
            ]

            for future in as_completed(futures):
                results.append(
                    future.result()
                )

        return results