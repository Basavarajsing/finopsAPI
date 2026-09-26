import time
from typing import Dict

from app.models.task import Task


def execute_task(task: Task) -> Dict:
    """
    Execute a scheduled task.

    For now, execution is represented by a real Python workload
    that consumes approximately the configured burst time.
    """

    start_time = time.perf_counter()

    # Simulated CPU workload.
    # This is an actual Python computation rather than a sleep.
    iterations = task.burst_time * 100_000

    result = 0

    for i in range(iterations):
        result += (i * i) % 97

    end_time = time.perf_counter()

    return {
        "task_id": task.task_id,
        "task_name": task.task_name,
        "status": "completed",
        "task_type": task.task_type.value,
        "execution_mode": task.execution_mode.value,
        "burst_time": task.burst_time,
        "execution_time_seconds": round(
            end_time - start_time,
            6
        ),
        "result": result
    }