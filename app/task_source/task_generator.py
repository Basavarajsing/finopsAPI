import random
import time

from app.models.task import Task


class TaskGenerator:
    """
    Generates incoming tasks automatically.

    This simulates workloads arriving from an external system.
    """

    def __init__(self):
        self.task_counter = 0

    def generate_task(self) -> Task:
        self.task_counter += 1

        task_id = f"T{self.task_counter:06d}"

        task_type = random.choice(
            [
                "critical",
                "non-critical"
            ]
        )

        execution_mode = random.choice(
            [
                "on-demand",
                "host"
            ]
        )

        return Task(
            task_id=task_id,
            task_name=f"Task {self.task_counter}",
            burst_time=random.randint(1, 10),
            priority=random.randint(1, 5),
            task_type=task_type,
            execution_mode=execution_mode,
            arrival_time=int(time.time())
        )


def generate_tasks(count: int) -> list[Task]:
    """
    Generate the requested number of incoming tasks.
    """

    generator = TaskGenerator()

    return [
        generator.generate_task()
        for _ in range(count)
    ]