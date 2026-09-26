from typing import List

from fastapi import FastAPI, HTTPException

from app.infrastructure.resource_manager import ResourceManager
from app.infrastructure.worker_pool import WorkerPool
from app.infrastructure.dynamic_dispatcher import DynamicDispatcher

from app.task_source.task_generator import generate_tasks

from app.classification.task_classifier import classify_task

from app.execution.task_executor import (
    execute_task,
    execute_task_slice
)

from app.models.task import Task

from app.scheduler.round_robin import schedule_round_robin
from app.scheduler.scheduler_service import schedule_tasks
from app.scheduler.sjf import schedule_sjf


# =========================================================
# FastAPI Application
# =========================================================

app = FastAPI(
    title="FinOps Task Scheduling API",
    description="Task classification and CPU scheduling API",
    version="1.0.0"
)


# =========================================================
# Infrastructure Components
# =========================================================

resource_manager = ResourceManager()

worker_pool = WorkerPool(
    resource_manager
)

dynamic_dispatcher = DynamicDispatcher(
    resource_manager
)


# =========================================================
# Root Endpoint
# =========================================================

@app.get("/")
def root():
    return {
        "message": "FinOps Task Scheduling API is running"
    }


# =========================================================
# Task Classification
# =========================================================

@app.post("/classify")
def classify(tasks: List[Task]):
    """
    Classify incoming tasks as Critical or Non-Critical.
    """

    return [
        {
            "task_id": task.task_id,
            "task_name": task.task_name,
            "task_type": classify_task(task).value,
            "execution_mode": task.execution_mode.value
        }
        for task in tasks
    ]


# =========================================================
# SJF Scheduling
# =========================================================

@app.post("/schedule/sjf")
def run_sjf(tasks: List[Task]):
    """
    Schedule tasks using Shortest Job First.
    """

    scheduled_tasks = schedule_sjf(
        tasks
    )

    return {
        "algorithm": "SJF",

        "execution_order": [
            task.task_id
            for task in scheduled_tasks
        ],

        "tasks": [
            {
                "task_id": task.task_id,
                "task_name": task.task_name,
                "burst_time": task.burst_time,
                "task_type": task.task_type.value,
                "execution_mode": task.execution_mode.value
            }
            for task in scheduled_tasks
        ]
    }


# =========================================================
# Round Robin Scheduling
# =========================================================

@app.post("/schedule/round-robin")
def run_round_robin(
    tasks: List[Task],
    time_quantum: int = 2
):
    """
    Schedule tasks using Round Robin.
    """

    if time_quantum <= 0:

        raise HTTPException(
            status_code=400,
            detail="time_quantum must be greater than 0"
        )

    execution_order = schedule_round_robin(
        tasks,
        time_quantum
    )

    return {
        "algorithm": "Round Robin",
        "time_quantum": time_quantum,
        "execution_order": execution_order
    }


# =========================================================
# Unified Scheduling Endpoint
# =========================================================

@app.post("/schedule")
def schedule(
    tasks: List[Task],
    algorithm: str = "sjf",
    time_quantum: int = 2
):
    """
    Unified scheduling endpoint.

    Supported algorithms:
    - sjf
    - round-robin
    """

    if (
        algorithm.lower() == "round-robin"
        and time_quantum <= 0
    ):

        raise HTTPException(
            status_code=400,
            detail="time_quantum must be greater than 0"
        )

    try:

        result = schedule_tasks(
            tasks,
            algorithm,
            time_quantum
        )

        return {
            "algorithm": algorithm,

            "time_quantum": (
                time_quantum
                if algorithm.lower() == "round-robin"
                else None
            ),

            "execution_order": result
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


# =========================================================
# Direct Task Execution
# =========================================================

@app.post("/execute")
def execute(tasks: List[Task]):
    """
    Execute supplied tasks using available resources.

    This endpoint executes tasks sequentially.
    """

    results = []

    for task in tasks:

        results.append(
            execute_task(
                task,
                resource_manager
            )
        )

    return {
        "total_tasks": len(results),

        "completed_tasks": len(
            [
                result
                for result in results
                if result["status"] == "completed"
            ]
        ),

        "waiting_tasks": len(
            [
                result
                for result in results
                if result["status"] == "waiting"
            ]
        ),

        "results": results
    }


# =========================================================
# Schedule + Execute
# =========================================================

@app.post("/schedule-and-execute")
def schedule_and_execute(
    tasks: List[Task],
    algorithm: str = "sjf",
    time_quantum: int = 2
):
    """
    Schedule tasks and execute them according
    to the selected scheduling algorithm.

    SJF:
        Executes each task normally.

    Round Robin:
        Executes tasks one CPU time slice at a time.
    """

    if not tasks:

        raise HTTPException(
            status_code=400,
            detail="At least one task is required"
        )

    algorithm = algorithm.lower()

    if (
        algorithm == "round-robin"
        and time_quantum <= 0
    ):

        raise HTTPException(
            status_code=400,
            detail="time_quantum must be greater than 0"
        )

    try:

        # =================================================
        # SJF
        # =================================================

        if algorithm == "sjf":

            scheduled_tasks = schedule_tasks(
                tasks,
                algorithm,
                time_quantum
            )

            task_map = {
                task.task_id: task
                for task in tasks
            }

            execution_results = []

            for scheduled_task in scheduled_tasks:

                task_id = scheduled_task[
                    "task_id"
                ]

                task = task_map[
                    task_id
                ]

                result = execute_task(
                    task,
                    resource_manager
                )

                execution_results.append(
                    result
                )

            return {
                "algorithm": "SJF",

                "time_quantum": None,

                "total_tasks": len(
                    tasks
                ),

                "completed_tasks": len(
                    [
                        result
                        for result in execution_results
                        if result["status"] == "completed"
                    ]
                ),

                "execution_results": (
                    execution_results
                )
            }

        # =================================================
        # Round Robin
        # =================================================

        elif algorithm == "round-robin":

            execution_order = schedule_round_robin(
                tasks,
                time_quantum
            )

            task_map = {
                task.task_id: task
                for task in tasks
            }

            remaining_time = {
                task.task_id: task.burst_time
                for task in tasks
            }

            execution_results = []

            for task_id in execution_order:

                task = task_map[
                    task_id
                ]

                current_remaining = (
                    remaining_time[
                        task_id
                    ]
                )

                actual_slice = min(
                    current_remaining,
                    time_quantum
                )

                slice_task = task.model_copy(
                    update={
                        "burst_time": actual_slice
                    }
                )

                # ResourceManager added here
                result = execute_task_slice(
                    slice_task,
                    actual_slice,
                    resource_manager
                )

                remaining_time[
                    task_id
                ] -= actual_slice

                result[
                    "remaining_time"
                ] = remaining_time[
                    task_id
                ]

                result[
                    "completed"
                ] = (
                    remaining_time[
                        task_id
                    ] == 0
                )

                execution_results.append(
                    result
                )

            completed_task_ids = {
                result["task_id"]
                for result in execution_results
                if result["completed"]
            }

            return {
                "algorithm": "Round Robin",

                "time_quantum": time_quantum,

                "total_tasks": len(tasks),

                "completed_tasks": len(
                    completed_task_ids
                ),

                "total_time_slices": len(
                    execution_results
                ),

                "execution_results": (
                    execution_results
                )
            }

        # =================================================
        # Unsupported Algorithm
        # =================================================

        else:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Unsupported algorithm. "
                    "Use 'sjf' or 'round-robin'."
                )
            )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


# =========================================================
# Automatic Workload Processing
# =========================================================

@app.post("/auto-process")
def auto_process(
    task_count: int = 100,
    algorithm: str = "sjf",
    time_quantum: int = 2
):
    """
    Automatically generate incoming tasks,
    schedule them using the selected algorithm,
    and execute them using the infrastructure manager.

    Supported algorithms:
    - sjf
    - round-robin
    """

    # -----------------------------------------------------
    # Validate task count
    # -----------------------------------------------------

    if task_count <= 0:

        raise HTTPException(
            status_code=400,
            detail="task_count must be greater than 0"
        )

    if task_count > 10000:

        raise HTTPException(
            status_code=400,
            detail="Maximum 10000 tasks allowed per request"
        )

    # -----------------------------------------------------
    # Normalize algorithm
    # -----------------------------------------------------

    algorithm = algorithm.lower()

    if algorithm not in [
        "sjf",
        "round-robin"
    ]:

        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported algorithm. "
                "Use 'sjf' or 'round-robin'."
            )
        )

    # -----------------------------------------------------
    # Validate Round Robin quantum
    # -----------------------------------------------------

    if (
        algorithm == "round-robin"
        and time_quantum <= 0
    ):

        raise HTTPException(
            status_code=400,
            detail="time_quantum must be greater than 0"
        )

    # -----------------------------------------------------
    # Generate incoming workload
    # -----------------------------------------------------

    tasks = generate_tasks(
        task_count
    )

    # =====================================================
    # SJF
    # =====================================================

    if algorithm == "sjf":

        # ---------------------------------------------
        # Schedule using SJF
        # ---------------------------------------------

        scheduled_tasks = schedule_tasks(
            tasks,
            "sjf"
        )

        # ---------------------------------------------
        # Create task lookup
        # ---------------------------------------------

        task_map = {
            task.task_id: task
            for task in tasks
        }

        # ---------------------------------------------
        # Preserve SJF scheduling order
        # ---------------------------------------------

        ordered_tasks = [
            task_map[
                scheduled_task["task_id"]
            ]
            for scheduled_task in scheduled_tasks
        ]

        # ---------------------------------------------
        # Dynamic infrastructure dispatch
        # ---------------------------------------------

        dispatch_result = (
            dynamic_dispatcher.dispatch(
                ordered_tasks
            )
        )

        execution_results = (
            dispatch_result["results"]
        )

    # =====================================================
    # Round Robin
    # =====================================================

    else:

        # ---------------------------------------------
        # Generate Round Robin execution sequence
        # ---------------------------------------------

        execution_order = schedule_round_robin(
            tasks,
            time_quantum
        )

        task_map = {
            task.task_id: task
            for task in tasks
        }

        remaining_time = {
            task.task_id: task.burst_time
            for task in tasks
        }

        execution_results = []

        # ---------------------------------------------
        # Execute each Round Robin time slice
        # ---------------------------------------------

        for task_id in execution_order:

            task = task_map[
                task_id
            ]

            current_remaining = (
                remaining_time[
                    task_id
                ]
            )

            actual_slice = min(
                current_remaining,
                time_quantum
            )

            slice_task = task.model_copy(
                update={
                    "burst_time": actual_slice
                }
            )

            # ResourceManager added here
            result = execute_task_slice(
                slice_task,
                actual_slice,
                resource_manager
            )

            remaining_time[
                task_id
            ] -= actual_slice

            result[
                "remaining_time"
            ] = remaining_time[
                task_id
            ]

            result[
                "completed"
            ] = (
                remaining_time[
                    task_id
                ] == 0
            )

            execution_results.append(
                result
            )

        # ---------------------------------------------
        # Calculate RR performance
        # ---------------------------------------------

        dispatch_result = {
            "total_execution_time_seconds": 0,
            "throughput_tasks_per_second": 0
        }

    # -----------------------------------------------------
    # Calculate completed tasks
    # -----------------------------------------------------

    if algorithm == "sjf":

        completed_tasks = [
            result
            for result in execution_results
            if result["status"] == "completed"
        ]

        waiting_tasks = [
            result
            for result in execution_results
            if result["status"] == "waiting"
        ]

        tasks_completed = len(
            completed_tasks
        )

        tasks_waiting = len(
            waiting_tasks
        )

    else:

        completed_task_ids = {
            result["task_id"]
            for result in execution_results
            if result["completed"]
        }

        tasks_completed = len(
            completed_task_ids
        )

        tasks_waiting = 0

    # -----------------------------------------------------
    # Return response
    # -----------------------------------------------------

    response = {

        "tasks_received": len(
            tasks
        ),

        "tasks_completed": (
            tasks_completed
        ),

        "tasks_waiting": (
            tasks_waiting
        ),

        "algorithm": algorithm,

        "worker_count": (
            resource_manager.max_workers
        ),

        "infrastructure": (
            resource_manager.get_status()
        )
    }

    # -----------------------------------------------------
    # SJF performance information
    # -----------------------------------------------------

    if algorithm == "sjf":

        response["performance"] = {
            "total_execution_time_seconds": (
                dispatch_result[
                    "total_execution_time_seconds"
                ]
            ),

            "throughput_tasks_per_second": (
                dispatch_result[
                    "throughput_tasks_per_second"
                ]
            )
        }

    # -----------------------------------------------------
    # Round Robin information
    # -----------------------------------------------------

    else:

        response["time_quantum"] = (
            time_quantum
        )

        response["total_time_slices"] = (
            len(execution_results)
        )

    # -----------------------------------------------------
    # Execution results
    # -----------------------------------------------------

    response["execution_results"] = (
        execution_results
    )

    return response


# =========================================================
# Infrastructure Status
# =========================================================

@app.get("/infrastructure/status")
def infrastructure_status():
    """
    Return current local infrastructure capacity.
    """

    return resource_manager.get_status()