import os
import threading
from typing import Dict


class ResourceManager:
    """
    Manages local CPU execution capacity.

    The ResourceManager represents the infrastructure layer
    responsible for allocating and releasing execution resources.
    """

    def __init__(self, max_workers: int | None = None):

        self.max_workers = (
            max_workers
            if max_workers is not None
            else (os.cpu_count() or 1)
        )

        self.active_workers = 0

        self.total_tasks_executed = 0

        self.total_tasks_rejected = 0

        self.lock = threading.Lock()

    # -----------------------------------------------------
    # Resource Status
    # -----------------------------------------------------

    def get_status(self) -> Dict:
        """
        Return the current infrastructure status.
        """

        with self.lock:

            available_workers = (
                self.max_workers
                - self.active_workers
            )

            return {
                "total_workers": self.max_workers,
                "active_workers": self.active_workers,
                "available_workers": available_workers,
                "total_tasks_executed": (
                    self.total_tasks_executed
                ),
                "total_tasks_rejected": (
                    self.total_tasks_rejected
                )
            }

    # -----------------------------------------------------
    # Check Capacity
    # -----------------------------------------------------

    def has_capacity(self) -> bool:
        """
        Check whether infrastructure has an available worker.
        """

        with self.lock:

            return (
                self.active_workers
                < self.max_workers
            )

    # -----------------------------------------------------
    # Acquire Resource
    # -----------------------------------------------------

    def acquire(self) -> bool:
        """
        Allocate one execution resource.

        Returns True if a resource was successfully
        allocated, otherwise False.
        """

        with self.lock:

            if self.active_workers >= self.max_workers:

                self.total_tasks_rejected += 1

                return False

            self.active_workers += 1

            return True

    # -----------------------------------------------------
    # Release Resource
    # -----------------------------------------------------

    def release(self) -> None:
        """
        Release one execution resource.
        """

        with self.lock:

            if self.active_workers > 0:

                self.active_workers -= 1

                self.total_tasks_executed += 1