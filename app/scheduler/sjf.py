from typing import List

from app.models.task import Task


def schedule_sjf(tasks: List[Task]) -> List[Task]:
    """
    Schedule tasks using non-preemptive Shortest Job First.

    Tasks with the shortest burst time are executed first.
    For equal burst times, arrival time is used as the tie-breaker.
    """

    return sorted(
        tasks,
        key=lambda task: (task.burst_time, task.arrival_time)
    )