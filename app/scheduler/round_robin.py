from typing import List

from app.models.task import Task


def schedule_round_robin(
    tasks: List[Task],
    time_quantum: int
) -> List[str]:
    """
    Schedule tasks using Round Robin.

    Each task receives CPU time for at most the configured
    time quantum during each turn.

    Returns the actual execution sequence of task IDs.
    """

    if time_quantum <= 0:
        raise ValueError("Time quantum must be greater than 0")

    remaining_time = {
        task.task_id: task.burst_time
        for task in tasks
    }

    queue = [task.task_id for task in tasks]
    execution_sequence = []

    while queue:
        task_id = queue.pop(0)

        if remaining_time[task_id] <= time_quantum:
            execution_sequence.append(task_id)
            remaining_time[task_id] = 0
        else:
            execution_sequence.append(task_id)
            remaining_time[task_id] -= time_quantum
            queue.append(task_id)

    return execution_sequence