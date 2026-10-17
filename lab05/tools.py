"""Декоратор со счётчиками в замыкании, без глобального состояния."""

from functools import wraps
from typing import Any, Callable, Protocol, TypeVar, cast

R = TypeVar("R", covariant=True)


class Instrumented(Protocol[R]):
    """Вызываемый объект с чтением и сбросом статистики."""

    def __call__(self, *args: Any, **kwargs: Any) -> R:
        """Выполнить исследуемую функцию."""
        ...

    def stats(self) -> dict[str, int]:
        """Получить копию статистики."""
        ...

    def reset(self) -> None:
        """Сбросить статистику вне активного вызова."""
        ...


def instrument(func: Callable[..., R]) -> Instrumented[R]:
    """Считать все входы и максимум одновременно активных вызовов."""
    calls = 0
    depth = 0
    max_depth = 0

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> R:
        """Изменить счётчики и гарантированно восстановить глубину."""
        nonlocal calls, depth, max_depth
        calls += 1
        depth += 1
        max_depth = max(max_depth, depth)
        try:
            return func(*args, **kwargs)
        finally:
            depth -= 1

    def stats() -> dict[str, int]:
        """Вернуть независимый словарь значений счётчиков."""
        return {"calls": calls, "max_depth": max_depth}

    def reset() -> None:
        """Начать новый эксперимент, если вызовов в работе нет."""
        nonlocal calls, max_depth
        if depth:
            raise RuntimeError("нельзя сбросить активное измерение")
        calls = max_depth = 0

    wrapper.stats = stats
    wrapper.reset = reset
    return cast(Instrumented[R], wrapper)
