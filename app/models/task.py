from enum import Enum
from pydantic import BaseModel, Field


class TaskType(str, Enum):
    CRITICAL = "critical"
    NON_CRITICAL = "non-critical"


class ExecutionMode(str, Enum):
    ON_DEMAND = "on-demand"
    HOST = "host"


class Task(BaseModel):
    task_id: str
    task_name: str

    burst_time: int = Field(gt=0, description="Required execution time")
    priority: int = Field(default=1, ge=1, description="Task priority")

    task_type: TaskType
    execution_mode: ExecutionMode

    arrival_time: int = Field(default=0, ge=0)