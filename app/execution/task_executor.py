import time
from typing import Dict

from app.infrastructure.resource_manager import ResourceManager
from app.models.task import Task


def execute_task(
    task: Task,
    resource_manager: ResourceManager | None = None
) -> Dict:
    """
    Execute a complete task using an available
    infrastructure resource.

    If a ResourceManager is supplied, a worker resource
    is acquired before execution and released after
    completion.
    """

    resource_acquired = False

    # -----------------------------------------------------
    # Acquire infrastructure resource
    # -----------------------------------------------------

    if resource_manager is not None:

        resource_acquired = (
            resource_manager.acquire()
        )

        if not resource_acquired:

            return {
                "task_id": task.task_id,
                "task_name": task.task_name,
                "status": "waiting",
                "reason": (
                    "No execution resource available"
                ),
                "task_type": task.task_type.value,
                "execution_mode": (
                    task.execution_mode.value
                )
            }

    start_time = time.perf_counter()

    try:

        # -------------------------------------------------
        # Simulated CPU-bound workload
        # -------------------------------------------------

        iterations = (
            task.burst_time * 100_000
        )

        result = 0

        for i in range(iterations):

            result += (
                (i * i) % 97
            )

        end_time = time.perf_counter()

        return {
            "task_id": task.task_id,
            "task_name": task.task_name,
            "status": "completed",
            "task_type": task.task_type.value,
            "execution_mode": (
                task.execution_mode.value
            ),
            "burst_time": task.burst_time,
            "execution_time_seconds": round(
                end_time - start_time,
                6
            ),
            "result": result
        }

    finally:

        # -------------------------------------------------
        # Release infrastructure resource
        # -------------------------------------------------

        if (
            resource_manager is not None
            and resource_acquired
        ):

            resource_manager.release()


def execute_task_slice(
    task: Task,
    time_slice: int,
    resource_manager: ResourceManager | None = None
) -> Dict:
    """
    Execute one Round Robin time slice.

    A resource is acquired before executing the slice
    and released after the slice completes.
    """

    if time_slice <= 0:

        raise ValueError(
            "time_slice must be greater than 0"
        )

    resource_acquired = False

    # -----------------------------------------------------
    # Acquire infrastructure resource
    # -----------------------------------------------------

    if resource_manager is not None:

        resource_acquired = (
            resource_manager.acquire()
        )

        if not resource_acquired:

            return {
                "task_id": task.task_id,
                "task_name": task.task_name,
                "executed_time": 0,
                "remaining_time": task.burst_time,
                "completed": False,
                "status": "waiting",
                "reason": (
                    "No execution resource available"
                )
            }

    try:

        # -------------------------------------------------
        # Determine actual CPU slice
        # -------------------------------------------------

        actual_slice = min(
            task.burst_time,
            time_slice
        )

        start_time = time.perf_counter()

        # -------------------------------------------------
        # Simulated CPU-bound workload
        # -------------------------------------------------

        iterations = (
            actual_slice * 100_000
        )

        result = 0

        for i in range(iterations):

            result += (
                (i * i) % 97
            )

        end_time = time.perf_counter()

        remaining_time = (
            task.burst_time
            - actual_slice
        )

        return {
            "task_id": task.task_id,
            "task_name": task.task_name,
            "executed_time": actual_slice,
            "remaining_time": remaining_time,
            "completed": (
                remaining_time == 0
            ),
            "status": "completed",
            "execution_time_seconds": round(
                end_time - start_time,
                6
            ),
            "result": result
        }

    finally:

        # -------------------------------------------------
        # Release infrastructure resource
        # -------------------------------------------------

        if (
            resource_manager is not None
            and resource_acquired
        ):

            resource_manager.release()