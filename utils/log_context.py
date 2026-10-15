from __future__ import annotations

from contextvars import ContextVar
from typing import Any

_test_name: ContextVar[str] = ContextVar("test_name", default="")
_step_name: ContextVar[str] = ContextVar("step_name", default="")
_object_name: ContextVar[str] = ContextVar("object_name", default="")
_method_name: ContextVar[str] = ContextVar("method_name", default="")
_action_name: ContextVar[str] = ContextVar("action_name", default="")
_last_step: ContextVar[str] = ContextVar("last_step", default="")
_last_object: ContextVar[str] = ContextVar("last_object", default="")
_last_method: ContextVar[str] = ContextVar("last_method", default="")
_last_action: ContextVar[str] = ContextVar("last_action", default="")
_last_data: ContextVar[str] = ContextVar("last_data", default="")


def set_test(name: str) -> None:
    _test_name.set(name)


def set_step(name: str) -> None:
    _step_name.set(name)
    _last_step.set(name)


def set_object(name: str) -> None:
    _object_name.set(name)
    _last_object.set(name)


def set_method(name: str) -> None:
    _method_name.set(name)
    _last_method.set(name)


def set_action(name: str) -> None:
    _action_name.set(name)
    _last_action.set(name)


def set_data(data: str) -> None:
    _last_data.set(data)


def extra() -> dict[str, Any]:
    return {
        "test": _test_name.get(),
        "step": _step_name.get(),
        "object": _object_name.get(),
        "method": _method_name.get(),
        "action": _action_name.get(),
    }


def failure_context() -> dict[str, str]:
    return {
        "test": _test_name.get(),
        "step": _last_step.get(),
        "object": _last_object.get(),
        "method": _last_method.get(),
        "action": _last_action.get(),
        "data": _last_data.get(),
    }
