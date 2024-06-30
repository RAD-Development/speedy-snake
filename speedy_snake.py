"""Thing."""

from __future__ import annotations

import logging
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import dataclass
from multiprocessing import cpu_count
from typing import TYPE_CHECKING, Any, Generic, Literal, TypeVar

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence

R = TypeVar("R")

modes = Literal["normal", "early_error"]


@dataclass
class ExecutorResults(Generic[R]):
    """Dataclass to store the results and exceptions of the parallel execution."""

    results: list[R]
    exceptions: list[Exception]

    def __repr__(self) -> str:
        """Return a string representation of the object."""
        return f"results={self.results} exceptions={self.exceptions}"


def _executor_base(
    executor_type: type[ProcessPoolExecutor | ThreadPoolExecutor],
    func: Callable[..., R],
    kwargs_list: Sequence[Mapping[str, Any]],
    max_workers: int | None,
    progress_tracker: int | None,
    mode: modes = "normal",
) -> ExecutorResults:
    total_work = len(kwargs_list)

    with executor_type(max_workers=max_workers) as executor:
        futures = [executor.submit(func, **kwarg) for kwarg in kwargs_list]

    results = []
    exceptions = []
    for index, future in enumerate(futures, 1):
        if exception := future.exception():
            logging.error(f"{future} raised {exception.__class__.__name__}")
            exceptions.append(exception)
            if mode == "early_error":
                executor.shutdown(wait=False)
                raise exception
            continue

        results.append(future.result())

        if progress_tracker and index % progress_tracker == 0:
            logging.info(f"Progress: {index}/{total_work}")

    return ExecutorResults(results, exceptions)


def thread_executor(
    func: Callable[..., R],
    kwargs_list: Sequence[Mapping[str, Any]],
    max_workers: int | None = None,
    progress_tracker: int | None = None,
    mode: modes = "normal",
) -> ExecutorResults:
    """Generic function to run a function with multiple arguments in threads.

    Args:
        func (Callable[..., R]): Function to run in threads.
        kwargs_list (Sequence[Mapping[str, Any]]): List of dictionaries with the arguments for the function.
        max_workers (int, optional): Number of workers to use. Defaults to 8.
        progress_tracker (int, optional): Number of tasks to complete before logging progress.
        mode (modes, optional): Mode to use. Defaults to "normal".

    Returns:
        tuple[list[R], list[Exception]]: List with the results and a list with the exceptions.
    """
    return _executor_base(
        executor_type=ThreadPoolExecutor,
        func=func,
        kwargs_list=kwargs_list,
        max_workers=max_workers,
        progress_tracker=progress_tracker,
        mode=mode,
    )


def process_executor(
    func: Callable[..., R],
    kwargs_list: Sequence[Mapping[str, Any]],
    max_workers: int | None = None,
    progress_tracker: int | None = None,
    mode: modes = "normal",
) -> ExecutorResults:
    """Generic function to run a function with multiple arguments in process.

    Args:
        func (Callable[..., R]): Function to run in process.
        kwargs_list (Sequence[Mapping[str, Any]]): List of dictionaries with the arguments for the function.
        max_workers (int, optional): Number of workers to use. Defaults to 4.
        progress_tracker (int, optional): Number of tasks to complete before logging progress.
        mode (modes, optional): Mode to use. Defaults to "normal".

    Returns:
        tuple[list[R], list[Exception]]: List with the results and a list with the exceptions.
    """
    if max_workers and max_workers > cpu_count():
        error = f"max_workers must be less than or equal to {cpu_count()}"
        raise RuntimeError(error)

    return process_executor_unchecked(
        func=func,
        kwargs_list=kwargs_list,
        max_workers=max_workers,
        progress_tracker=progress_tracker,
        mode=mode,
    )


def process_executor_unchecked(
    func: Callable[..., R],
    kwargs_list: Sequence[Mapping[str, Any]],
    max_workers: int | None,
    progress_tracker: int | None,
    mode: modes = "normal",
) -> ExecutorResults:
    """Generic function to run a function with multiple arguments in parallel.

    Note: this function does not check if the number of workers is greater than the number of CPUs.
    This can cause the system to become unresponsive.

    Args:
        func (Callable[..., R]): Function to run in parallel.
        kwargs_list (Sequence[Mapping[str, Any]]): List of dictionaries with the arguments for the function.
        max_workers (int, optional): Number of workers to use. Defaults to 8.
        progress_tracker (int, optional): Number of tasks to complete before logging progress.
        mode (modes, optional): Mode to use. Defaults to "normal".

    Returns:
        tuple[list[R], list[Exception]]: List with the results and a list with the exceptions.
    """
    return _executor_base(
        executor_type=ProcessPoolExecutor,
        func=func,
        kwargs_list=kwargs_list,
        max_workers=max_workers,
        progress_tracker=progress_tracker,
        mode=mode,
    )
