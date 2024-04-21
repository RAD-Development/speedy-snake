"""test_executors."""

import pytest
from pytest_mock import MockerFixture

from speedy_snake import process_executor, thread_executor


def add(a: int, b: int) -> int:
    """Add."""
    return a + b


def test_thread_executor() -> None:
    """test_thread_executor."""
    kwargs_list = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
    results = thread_executor(func=add, kwargs_list=kwargs_list, progress_tracker=1)
    assert results.results == [3, 7]
    assert not results.exceptions


def test_thread_executor_currying() -> None:
    """test_thread_executor."""
    kwargs = {"b": 2}
    kwargs_list = [{"a": 1}, {"a": 3}, {"a": 3, "b": 4}]
    results = thread_executor(func=add, kwargs_list=kwargs_list, kwargs=kwargs)
    assert results.results == [3, 5, 7]
    assert not results.exceptions


def test_thread_executor_exception() -> None:
    """test_thread_executor."""
    kwargs_list = [{"a": 1, "b": 2}, {"a": 3, "b": None}]
    results = thread_executor(func=add, kwargs_list=kwargs_list)
    assert results.results == [3]
    output = """[TypeError("unsupported operand type(s) for +: 'int' and 'NoneType'")]"""
    assert str(results.exceptions) == output


def test_process_executor() -> None:
    """test_process_executor."""
    kwargs_list = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
    results = process_executor(func=add, kwargs_list=kwargs_list)
    assert results.results == [3, 7]
    assert not results.exceptions


def test_process_executor_to_many_max_workers(mocker: MockerFixture) -> None:
    """test_process_executor."""
    mocker.patch(target="speedy_snake.cpu_count", return_value=1)

    with pytest.raises(RuntimeError) as exc_info:
        process_executor(func=add, kwargs_list=[{"a": 1, "b": 2}], max_workers=8)

    assert str(exc_info.value) == "max_workers must be less than or equal to 1"


def test_executor_results_repr() -> None:
    """test_ExecutorResults_repr."""
    results = thread_executor(func=add, kwargs_list=[{"a": 1, "b": 2}])
    assert repr(results) == "results=[3] exceptions=[]"