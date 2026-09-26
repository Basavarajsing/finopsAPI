from typing import List

from app.models.task import Task


def schedule_round_robin(
    tasks: List[Task],
    time_quantum: int
) -> List[str]:
    """
    Schedule tasks using Round Robin.

    Returns the actual execution sequence of task IDs.
    Each occurrence represents one CPU time slice.
    """

    if time_quantum <= 0:
        raise ValueError(
            "Time quantum must be greater than 0"
        )

    remaining_time = {
        task.task_id: task.burst_time
        for task in tasks
    }

    queue = [
        task.task_id
        for task in tasks
    ]

    execution_sequence = []

    while queue:

        task_id = queue.pop(0)

        execution_sequence.append(
            task_id
        )

        remaining_time[task_id] -= time_quantum

        if remaining_time[task_id] > 0:
            queue.append(task_id)

    return execution_sequence