from typing import List

from app.models.task import Task, TaskType, ExecutionMode
from app.scheduler.sjf import schedule_sjf
from app.scheduler.round_robin import schedule_round_robin


def schedule_tasks(
    tasks: List[Task],
    algorithm: str,
    time_quantum: int = 2
):
    """
    Main scheduling decision layer.

    Priority of execution:
    1. Critical tasks before Non-Critical tasks
    2. On-Demand tasks before Host tasks
    3. Selected scheduling algorithm within the group
    """

    if not tasks:
        return []

    algorithm = algorithm.lower()

    # First divide tasks according to criticality
    critical_tasks = [
        task for task in tasks
        if task.task_type == TaskType.CRITICAL
    ]

    non_critical_tasks = [
        task for task in tasks
        if task.task_type == TaskType.NON_CRITICAL
    ]

    # Critical tasks are handled first.
    # Inside each criticality group, On-Demand tasks are handled
    # before Host tasks.
    ordered_groups = [
        [
            task for task in critical_tasks
            if task.execution_mode == ExecutionMode.ON_DEMAND
        ],
        [
            task for task in critical_tasks
            if task.execution_mode == ExecutionMode.HOST
        ],
        [
            task for task in non_critical_tasks
            if task.execution_mode == ExecutionMode.ON_DEMAND
        ],
        [
            task for task in non_critical_tasks
            if task.execution_mode == ExecutionMode.HOST
        ]
    ]

    result = []

    for group in ordered_groups:

        if not group:
            continue

        if algorithm == "sjf":

            scheduled = schedule_sjf(group)

            result.extend(
                {
                    "task_id": task.task_id,
                    "task_name": task.task_name,
                    "burst_time": task.burst_time,
                    "priority": task.priority,
                    "task_type": task.task_type.value,
                    "execution_mode": task.execution_mode.value
                }
                for task in scheduled
            )

        elif algorithm == "round-robin":

            execution_order = schedule_round_robin(
                group,
                time_quantum
            )

            task_map = {
                task.task_id: task
                for task in group
            }

            result.extend(
                {
                    "task_id": task_id,
                    "task_name": task_map[task_id].task_name,
                    "burst_time": task_map[task_id].burst_time,
                    "priority": task_map[task_id].priority,
                    "task_type": task_map[task_id].task_type.value,
                    "execution_mode": task_map[task_id].execution_mode.value
                }
                for task_id in execution_order
            )

        else:
            raise ValueError(
                "Unsupported algorithm. Use 'sjf' or 'round-robin'."
            )

    return result