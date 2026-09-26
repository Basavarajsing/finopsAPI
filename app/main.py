from typing import List

from fastapi import FastAPI, HTTPException

from app.classification.task_classifier import classify_task
from app.execution.task_executor import execute_task
from app.models.task import Task
from app.scheduler.round_robin import schedule_round_robin
from app.scheduler.scheduler_service import schedule_tasks
from app.scheduler.sjf import schedule_sjf


app = FastAPI(
    title="FinOps Task Scheduling API",
    description="Task classification and CPU scheduling API",
    version="1.0.0"
)


@app.get("/")
def root():
    return {
        "message": "FinOps Task Scheduling API is running"
    }


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


@app.post("/schedule/sjf")
def run_sjf(tasks: List[Task]):
    """
    Schedule tasks using Shortest Job First.
    """

    scheduled_tasks = schedule_sjf(tasks)

    return {
        "algorithm": "SJF",
        "execution_order": [
            task.task_id for task in scheduled_tasks
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


@app.post("/schedule")
def schedule(
    tasks: List[Task],
    algorithm: str = "sjf",
    time_quantum: int = 2
):
    """
    Unified scheduling endpoint.
    """

    if algorithm.lower() == "round-robin" and time_quantum <= 0:
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


@app.post("/execute")
def execute(tasks: List[Task]):
    """
    Execute the supplied tasks sequentially.
    """

    results = []

    for task in tasks:
        results.append(
            execute_task(task)
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
        "results": results
    }
@app.post("/schedule-and-execute")
def schedule_and_execute(
    tasks: List[Task],
    algorithm: str = "sjf",
    time_quantum: int = 2
):
    """
    Schedule tasks and then execute them
    according to the selected scheduling algorithm.
    """

    if not tasks:
        raise HTTPException(
            status_code=400,
            detail="At least one task is required"
        )

    if algorithm.lower() == "round-robin" and time_quantum <= 0:
        raise HTTPException(
            status_code=400,
            detail="time_quantum must be greater than 0"
        )

    try:
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
            task_id = scheduled_task["task_id"]

            task = task_map[task_id]

            result = execute_task(task)

            execution_results.append(result)

        return {
            "algorithm": algorithm,
            "time_quantum": (
                time_quantum
                if algorithm.lower() == "round-robin"
                else None
            ),
            "total_tasks": len(execution_results),
            "completed_tasks": len(
                [
                    result
                    for result in execution_results
                    if result["status"] == "completed"
                ]
            ),
            "execution_results": execution_results
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )