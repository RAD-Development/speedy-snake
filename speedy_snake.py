"""Thing."""

from __future__ import annotations

import logging
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import dataclass
from functools import partial
from multiprocessing import cpu_count
from typing import TYPE_CHECKING, Any, Generic, ParamSpec, TypeVar

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence
    from concurrent.futures import Executor

P = ParamSpec("P")
R = TypeVar("R")


@dataclass
class ExecutorResults(Generic[R]):
    """Dataclass to store the results and exceptions of the parallel execution."""

    results: list[R]
    exceptions: list[Exception]

    def __repr__(self) -> str:
        """Return a string representation of the object."""
        return f"results={self.results} exceptions={self.exceptions}"


def _executor_base(
    executor_type: type[Executor],
    func: Callable[..., R],
    kwargs_list: Sequence[Mapping[str, Any]],
    kwargs: Mapping[str, Any] | None,
    max_workers: int,
    progress_tracker: int | None,
) -> ExecutorResults:
    total_work = len(kwargs_list)

    if kwargs:
        func = partial(func, **kwargs)

    with executor_type(max_workers=max_workers) as executor:
        futures = [executor.submit(func, **kwarg) for kwarg in kwargs_list]

    results = []
    exceptions = []
    for index, future in enumerate(futures, 1):
        try:
            results.append(future.result())
        except Exception as error:
            msg = f"{future} raised {error.__class__.__name__}"
            logging.exception(msg)
            exceptions.append(error)

        if progress_tracker and index % progress_tracker == 0:
            logging.info(f"Progress: {index}/{total_work}")

    return ExecutorResults(results, exceptions)


def thread_executor(
    func: Callable[..., R],
    kwargs_list: Sequence[Mapping[str, Any]],
    kwargs: Mapping[str, Any] | None = None,
    max_workers: int = 8,
    progress_tracker: int | None = None,
) -> ExecutorResults:
    """Generic function to run a function with multiple arguments in threads.

    Note: when using currying the arguments being curried can be overwritten by the arguments in kwargs_list.

    Args:
        func (Callable[..., R]): Function to run in threads.
        kwargs_list (Sequence[Mapping[str, Any]]): List of dictionaries with the arguments for the function.
        kwargs (Mapping[str, Any], optional): Default arguments for the function. Defaults to None.
        max_workers (int, optional): Number of workers to use. Defaults to 8.
        exception_behavior (str, optional): How to handle exceptions. Defaults to "group".
        progress_tracker (int, optional): Number of tasks to complete before logging progress.

    Returns:
        tuple[list[R], list[Exception]]: List with the results and a list with the exceptions.
    """
    return _executor_base(
        executor_type=ThreadPoolExecutor,
        func=func,
        kwargs_list=kwargs_list,
        kwargs=kwargs,
        max_workers=max_workers,
        progress_tracker=progress_tracker,
    )


def process_executor(
    func: Callable[..., R],
    kwargs_list: Sequence[Mapping[str, Any]],
    kwargs: Mapping[str, Any] | None = None,
    max_workers: int = 4,
    progress_tracker: int | None = None,
) -> ExecutorResults:
    """Generic function to run a function with multiple arguments in process.

    Note: when using currying the arguments being curried can be overwritten by the arguments in kwargs_list.

    Args:
        func (Callable[..., R]): Function to run in process.
        kwargs_list (Sequence[Mapping[str, Any]]): List of dictionaries with the arguments for the function.
        kwargs (Mapping[str, Any], optional): Default arguments for the function. Defaults to None.
        max_workers (int, optional): Number of workers to use. Defaults to 4.
        exception_behavior (str, optional): How to handle exceptions. Defaults to "group".
        progress_tracker (int, optional): Number of tasks to complete before logging progress.

    Returns:
        tuple[list[R], list[Exception]]: List with the results and a list with the exceptions.
    """
    if max_workers > cpu_count():
        error = f"max_workers must be less than or equal to {cpu_count()}"
        raise RuntimeError(error)

    return process_executor_unchecked(
        func=func,
        kwargs_list=kwargs_list,
        kwargs=kwargs,
        max_workers=max_workers,
        progress_tracker=progress_tracker,
    )


def process_executor_unchecked(
    func: Callable[..., R],
    kwargs_list: Sequence[Mapping[str, Any]],
    kwargs: Mapping[str, Any] | None,
    max_workers: int,
    progress_tracker: int | None,
) -> ExecutorResults:
    """Generic function to run a function with multiple arguments in parallel.

    Note: when using currying the arguments being curried can be overwritten by the arguments in kwargs_list.
    Note: this function does not check if the number of workers is greater than the number of CPUs.
    This can cause the system to become unresponsive.

    Args:
        func (Callable[..., R]): Function to run in parallel.
        kwargs_list (Sequence[Mapping[str, Any]]): List of dictionaries with the arguments for the function.
        kwargs (Mapping[str, Any], optional): Default arguments for the function. Defaults to None.
        max_workers (int, optional): Number of workers to use. Defaults to 8.
        exception_behavior (str, optional): How to handle exceptions. Defaults to "group".
        progress_tracker (int, optional): Number of tasks to complete before logging progress.

    Returns:
        tuple[list[R], list[Exception]]: List with the results and a list with the exceptions.
    """
    return _executor_base(
        executor_type=ProcessPoolExecutor,
        func=func,
        kwargs_list=kwargs_list,
        kwargs=kwargs,
        max_workers=max_workers,
        progress_tracker=progress_tracker,
    )
