"""
Threading utilities
"""

import concurrent.futures
from typing import Callable, List, Any
import threading
import functools


def run_in_thread_pool(task: Callable, tasks_args: List, max_workers: int = 100) -> List:
    """
    Runs a list of Callables in a ThreadPoolExecutor
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        return [
            complete_task_future.result()
            for complete_task_future in concurrent.futures.as_completed(
                [executor.submit(task, *task_args) for task_args in tasks_args]
            )
        ]


def thread_safe(function: Callable) -> Any:
    """
    Decorator to block the the main thread while the decorated function runs. Used for ensuring data consistency of
    objects shared across threads.
    """
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        lock = threading.Lock()
        lock.acquire()
        function_return = function(*args, **kwargs)
        lock.release()

        return function_return

    return wrapper
