import time
from concurrent.futures import ProcessPoolExecutor
from typing import List

from app.execution.task_executor import execute_task
from app.infrastructure.resource_manager import ResourceManager
from app.models.task import Task


def execute_dynamic_task(task: Task):
    """
    Execute a task inside a worker process.

    Resource allocation is controlled by the dispatcher,
    so the worker process only performs the actual task.
    """

    return execute_task(
        task,
        None
    )


class DynamicDispatcher:
    """
    Dynamically dispatches incoming tasks according to
    available infrastructure capacity.

    Tasks are submitted to a bounded process pool.
    The ResourceManager tracks logical infrastructure usage.
    """

    def __init__(
        self,
        resource_manager: ResourceManager
    ):
        self.resource_manager = resource_manager

    def dispatch(
        self,
        tasks: List[Task]
    ) -> dict:

        if not tasks:
            return {
                "results": [],
                "total_execution_time_seconds": 0,
                "tasks_completed": 0,
                "throughput_tasks_per_second": 0
            }

        # -------------------------------------------------
        # Determine infrastructure capacity
        # -------------------------------------------------

        worker_count = min(
            self.resource_manager.max_workers,
            len(tasks)
        )

        # -------------------------------------------------
        # Performance timer
        # -------------------------------------------------

        start_time = time.perf_counter()

        results = []

        pending_tasks = list(tasks)

        # -------------------------------------------------
        # Create process-based worker pool
        # -------------------------------------------------

        with ProcessPoolExecutor(
            max_workers=worker_count
        ) as executor:

            active_futures = {}

            # -------------------------------------------------
            # Dynamic dispatch loop
            # -------------------------------------------------

            while pending_tasks or active_futures:

                # ---------------------------------------------
                # Allocate available infrastructure
                # ---------------------------------------------

                while (
                    pending_tasks
                    and len(active_futures)
                    < worker_count
                ):

                    task = pending_tasks.pop(0)

                    # Wait until infrastructure has capacity
                    while not self.resource_manager.acquire():

                        time.sleep(0.001)

                    future = executor.submit(
                        execute_dynamic_task,
                        task
                    )

                    active_futures[future] = task

                # ---------------------------------------------
                # Check completed tasks
                # ---------------------------------------------

                completed_futures = []

                for future, task in list(
                    active_futures.items()
                ):

                    if future.done():

                        completed_futures.append(
                            (future, task)
                        )

                # ---------------------------------------------
                # Collect results and release resources
                # ---------------------------------------------

                for future, task in completed_futures:

                    try:

                        result = future.result()

                        results.append(
                            result
                        )

                    finally:

                        # Release infrastructure resource
                        self.resource_manager.release()

                        del active_futures[future]

                # ---------------------------------------------
                # Avoid unnecessary CPU spinning
                # ---------------------------------------------

                if active_futures:

                    time.sleep(0.001)

        # -------------------------------------------------
        # Calculate performance statistics
        # -------------------------------------------------

        total_execution_time = (
            time.perf_counter()
            - start_time
        )

        tasks_completed = len(
            results
        )

        throughput = (
            tasks_completed
            / total_execution_time
            if total_execution_time > 0
            else 0
        )

        # -------------------------------------------------
        # Return complete dispatcher result
        # -------------------------------------------------

        return {
            "results": results,

            "total_execution_time_seconds": round(
                total_execution_time,
                6
            ),

            "tasks_completed": tasks_completed,

            "throughput_tasks_per_second": round(
                throughput,
                2
            )
        }