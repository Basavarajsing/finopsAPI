from app.models.task import Task, TaskType


def classify_task(task: Task) -> TaskType:
    """
    Classify a task as Critical or Non-Critical.

    The task_type supplied by the incoming request is currently
    treated as the classification result. The classification
    component is kept separate so more sophisticated rules can
    be added later without changing the scheduler.
    """

    return task.task_type