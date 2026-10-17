"""Лабораторная 5. Швачкина Виктория, вариант 3.

Запуск: python -X utf8 lab.py --section all
Чистые алгоритмы отделены от демонстраций и сохранения измерений.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import statistics
import sys
import timeit
from functools import reduce, wraps
from pathlib import Path
from typing import Any, Callable, TypeVar

from lab05.tools import instrument

T = TypeVar("T")
U = TypeVar("U")
DIGITS = "0123456789ABCDEF"


def rec_sum(xs: list[int]) -> int:
    """Суммировать список по схеме «голова и хвост»."""
    match xs:
        case []:  # Базовый случай.
            return 0
        case [head, *tail]:  # Рекурсивный шаг: список короче на один.
            return head + rec_sum(tail)
    raise TypeError("ожидается список")


def rec_sum_index(xs: list[int], i: int = 0) -> int:
    """Суммировать без копирования хвоста списка."""
    if i >= len(xs):  # База.
        return 0
    return xs[i] + rec_sum_index(xs, i + 1)  # Рекурсивный шаг.


def to_base(n: int, base: int) -> str:
    """Представить неотрицательное целое n в системе 2..16."""
    if n < 0 or not 2 <= base <= 16:
        raise ValueError("нужно n >= 0 и 2 <= base <= 16")
    if n < base:  # База: одна цифра, в том числе ноль.
        return DIGITS[n]
    return to_base(n // base, base) + DIGITS[n % base]  # Шаг.


def to_base_iter(n: int, base: int) -> str:
    """Перевести число последовательным делением с остатком."""
    if n < 0 or not 2 <= base <= 16:
        raise ValueError("нужно n >= 0 и 2 <= base <= 16")
    digits: list[str] = []
    while True:
        n, r = divmod(n, base)
        digits.append(DIGITS[r])
        if n == 0:
            return "".join(reversed(digits))


def factorial(n: int) -> int:
    """Вычислить n! рекурсивно для n >= 0."""
    if n < 0:
        raise ValueError("факториал отрицательного числа не определён")
    if n == 0:  # База: 0! = 1.
        return 1
    return n * factorial(n - 1)  # Шаг: n! = n * (n-1)!.


def digit_sum(n: int) -> int:
    """Сложить десятичные цифры неотрицательного целого."""
    if n < 0:
        raise ValueError("нужно неотрицательное число")
    if n < 10:  # База: одноразрядное число.
        return n
    return n % 10 + digit_sum(n // 10)  # Шаг: отбрасываем цифру.


def power(x: float, n: int) -> float:
    """Возвести x в целую степень за линейное число умножений."""
    if n == 0:  # База, включая соглашение 0**0 == 1.
        return 1
    if n < 0:
        if x == 0:
            raise ZeroDivisionError("ноль в отрицательной степени")
        return 1 / power(x, -n)  # Шаг: отрицательная степень.
    return x * power(x, n - 1)  # Шаг: показатель меньше на один.


def fast_power(x: float, n: int) -> float:
    """Возвести в целую степень методом деления показателя пополам."""
    if n == 0:  # База.
        return 1
    if n < 0:
        if x == 0:
            raise ZeroDivisionError("ноль в отрицательной степени")
        return 1 / fast_power(x, -n)
    half = fast_power(x, n // 2)  # Шаг: одна подзадача половинного размера.
    return half * half if n % 2 == 0 else x * half * half


def gcd(a: int, b: int) -> int:
    """Найти неотрицательный НОД алгоритмом Евклида."""
    if b == 0:  # База; gcd(0, 0) = 0.
        return abs(a)
    return gcd(abs(b), abs(a) % abs(b))  # Шаг: остаток меньше |b|.


def lcm(a: int, b: int) -> int:
    """Найти НОК через НОД, отдельно обработав нули."""
    if a == 0 or b == 0:
        return 0
    return abs((a // gcd(a, b)) * b)


def binomial(n: int, k: int) -> int:
    """Вычислить C(n,k) по рекурсивной формуле Паскаля."""
    if n < 0 or k < 0 or k > n:
        raise ValueError("нужно 0 <= k <= n")
    if k == 0 or k == n:  # База: край треугольника Паскаля.
        return 1
    return binomial(n - 1, k - 1) + binomial(n - 1, k)  # Шаг.


def is_palindrome(s: str) -> bool:
    """Проверить палиндром, пропуская всё кроме букв и цифр."""
    s = s.casefold()
    if len(s) <= 1:  # База.
        return True
    if not s[0].isalnum():
        return is_palindrome(s[1:])  # Шаг: пропуск слева.
    if not s[-1].isalnum():
        return is_palindrome(s[:-1])  # Шаг: пропуск справа.
    if s[0] != s[-1]:
        return False
    return is_palindrome(s[1:-1])  # Шаг: равные края удалены.


def count_occurrences(s: str, ch: str) -> int:
    """Подсчитать вхождения одного символа с учётом регистра."""
    if len(ch) != 1:
        raise ValueError("ch должен содержать ровно один символ")
    if not s:  # База.
        return 0
    # Шаг: учесть голову и подсчитать вхождения в более коротком хвосте.
    return (1 if s[0] == ch else 0) + count_occurrences(s[1:], ch)


def reverse(s: str) -> str:
    """Перевернуть строку без циклов и встроенного reversed."""
    if not s:  # База.
        return ""
    return reverse(s[1:]) + s[0]  # Шаг: хвост короче строки.


def length(xs: list[T]) -> int:
    """Подсчитать элементы через match."""
    match xs:
        case []:  # База.
            return 0
        case [_, *tail]:  # Шаг.
            return 1 + length(tail)
    raise TypeError("ожидается список")


def maximum(xs: list[int]) -> int:
    """Найти максимум непустого списка."""
    match xs:
        case []:
            raise ValueError("у пустого списка нет максимума")
        case [head]:  # База.
            return head
        case [head, *tail]:  # Шаг.
            rest = maximum(tail)
            return head if head > rest else rest
    raise TypeError("ожидается список")


def rec_map(f: Callable[[T], U], xs: list[T]) -> list[U]:
    """Применить функцию к каждому элементу, сохранив порядок."""
    match xs:
        case []:  # База.
            return []
        case [head, *tail]:  # Шаг.
            return [f(head)] + rec_map(f, tail)
    raise TypeError("ожидается список")


def rec_filter(p: Callable[[T], bool], xs: list[T]) -> list[T]:
    """Оставить элементы, для которых предикат истинен."""
    match xs:
        case []:  # База.
            return []
        case [head, *tail]:  # Шаг.
            return ([head] if p(head) else []) + rec_filter(p, tail)
    raise TypeError("ожидается список")


def rec_zip(xs: list[T], ys: list[U]) -> list[tuple[T, U]]:
    """Составить пары до конца более короткого списка."""
    match (xs, ys):
        case ([], _) | (_, []):  # База.
            return []
        case ([x, *xt], [y, *yt]):  # Шаг.
            return [(x, y)] + rec_zip(xt, yt)
    raise TypeError("ожидаются списки")


def take(n: int, xs: list[T]) -> list[T]:
    """Вернуть первые n элементов; при n <= 0 вернуть []."""
    match (n, xs):
        case (k, _) if k <= 0:  # База по n.
            return []
        case (_, []):  # База по списку.
            return []
        case (_, [head, *tail]):  # Шаг.
            return [head] + take(n - 1, tail)
    raise TypeError("ожидается список")


def drop(n: int, xs: list[T]) -> list[T]:
    """Удалить первые n элементов; входной список не изменяется."""
    match (n, xs):
        case (k, _) if k <= 0:  # База по n.
            return xs.copy()
        case (_, []):  # База по списку.
            return []
        case (_, [_, *tail]):  # Шаг.
            return drop(n - 1, tail)
    raise TypeError("ожидается список")


def fold_right(f: Callable[[T, U], U], init: U, xs: list[T]) -> U:
    """Свернуть справа: f(x1, f(x2, ... init))."""
    match xs:
        case []:  # База.
            return init
        case [head, *tail]:  # Шаг.
            return f(head, fold_right(f, init, tail))
    raise TypeError("ожидается список")


def fold_left(f: Callable[[U, T], U], init: U, xs: list[T]) -> U:
    """Свернуть слева: f(... f(f(init,x1),x2), ...)."""
    match xs:
        case []:  # База.
            return init
        case [head, *tail]:  # Шаг, аккумулятор содержит готовый префикс.
            return fold_left(f, f(init, head), tail)
    raise TypeError("ожидается список")


def map_fold(f: Callable[[T], U], xs: list[T]) -> list[U]:
    """Выразить map через правую свёртку."""
    return fold_right(lambda x, acc: [f(x)] + acc, [], xs)


def filter_fold(p: Callable[[T], bool], xs: list[T]) -> list[T]:
    """Выразить filter через правую свёртку."""
    return fold_right(lambda x, acc: [x] + acc if p(x) else acc, [], xs)


def fib(n: int) -> int:
    """Наивно вычислить число Фибоначчи, F0=0 и F1=1."""
    if n < 0:
        raise ValueError("нужно n >= 0")
    if n < 2:  # База.
        return n
    return fib(n - 1) + fib(n - 2)  # Шаг, две меньшие подзадачи.


def measured_functions() -> tuple[Any, Any, Any]:
    """Создать отдельные рекурсивные функции с инструментированием."""

    @instrument
    def measured_fib(n: int) -> int:
        """Фибоначчи; рекурсивное имя ссылается на обёртку."""
        if n < 2:  # База.
            return n
        return measured_fib(n - 1) + measured_fib(n - 2)  # Шаг.

    @instrument
    def measured_binomial(n: int, k: int) -> int:
        """Паскаль с подсчётом каждого входа."""
        if k == 0 or k == n:  # База.
            return 1
        # Шаг: перейти к двум задачам предыдущей строки Паскаля.
        return measured_binomial(n - 1, k - 1) + measured_binomial(n - 1, k)

    @instrument
    def measured_power(x: int, n: int) -> int:
        """Быстрая степень; половина вычисляется ровно один раз."""
        if n == 0:  # База.
            return 1
        half = measured_power(x, n // 2)  # Шаг.
        return half * half if n % 2 == 0 else x * half * half

    return measured_fib, measured_binomial, measured_power


def make_tracer(indent: str = "  ") -> Callable[[Callable[..., T]], Any]:
    """Вернуть декоратор, печатающий вход, результат и исключения."""
    depth = 0

    def decorate(func: Callable[..., T]) -> Callable[..., T]:
        """Обернуть функцию, сохранив метаданные через wraps."""

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            """Напечатать текущий узел и восстановить глубину."""
            nonlocal depth
            prefix = indent * depth
            print(f"{prefix}{func.__name__}{args}")
            depth += 1
            try:
                result = func(*args, **kwargs)
                print(f"{prefix}=> {result}")
                return result
            except Exception as error:
                print(f"{prefix}! {type(error).__name__}: {error}")
                raise
            finally:
                depth -= 1

        return wrapper

    return decorate


def hanoi(n: int, src: str, dst: str, via: str) -> tuple[tuple[str, str], ...]:
    """Вернуть неизменяемую последовательность допустимых ходов."""
    if n < 0 or len({src, dst, via}) != 3:
        raise ValueError("нужно n >= 0 и три разных стержня")
    if n == 0:  # База: переносить нечего.
        return ()
    # Шаг: освободить большой диск, перенести его, вернуть малые сверху.
    return hanoi(n - 1, src, via, dst) + ((src, dst),) + hanoi(n - 1, via, dst, src)


def simulate(n: int, moves: tuple[tuple[str, str], ...]) -> dict[str, tuple[int, ...]]:
    """Проверить ходы через reduce, создавая новое состояние на шаге."""
    if n < 0:
        raise ValueError("нужно n >= 0")

    def apply_move(
        state: dict[str, tuple[int, ...]], move: tuple[str, str]
    ) -> dict[str, tuple[int, ...]]:
        """Применить один ход, не меняя переданный словарь."""
        src, dst = move
        if src not in state or dst not in state or src == dst:
            raise ValueError("неверные стержни")
        if not state[src]:
            raise ValueError("исходный стержень пуст")
        disk = state[src][-1]
        if state[dst] and disk > state[dst][-1]:
            raise ValueError("нельзя положить больший диск на меньший")
        return {**state, src: state[src][:-1], dst: state[dst] + (disk,)}

    initial = {"A": tuple(range(n, 0, -1)), "B": (), "C": ()}
    return reduce(apply_move, moves, initial)


def factorial_iter(n: int) -> int:
    """Вычислить факториал циклом."""
    if n < 0:
        raise ValueError("нужно n >= 0")
    result = 1
    for k in range(1, n + 1):
        result *= k
    return result


def fib_iter(n: int) -> int:
    """Вычислить Фибоначчи с двумя текущими значениями."""
    if n < 0:
        raise ValueError("нужно n >= 0")
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def digit_sum_iter(n: int) -> int:
    """Сложить цифры последовательным делением на десять."""
    if n < 0:
        raise ValueError("нужно n >= 0")
    total = 0
    while n:
        n, digit = divmod(n, 10)
        total += digit
    return total


def factorial_tail(n: int, acc: int = 1) -> int:
    """Хвостовая рекурсия с аккумулятором произведения."""
    if n < 0:
        raise ValueError("нужно n >= 0")
    if n == 0:  # База.
        return acc
    return factorial_tail(n - 1, acc * n)  # Хвостовой шаг.


def factorial_while(n: int, acc: int = 1) -> int:
    """Механически заменить хвостовой вызов переназначением параметров."""
    if n < 0:
        raise ValueError("нужно n >= 0")
    while n != 0:
        n, acc = n - 1, acc * n
    return acc


def recursion_boundary(limit: int) -> dict[str, int]:
    """Найти первое n с RecursionError в одинаковом контексте вызова."""
    old = sys.getrecursionlimit()
    sys.setrecursionlimit(limit)

    def fails(n: int) -> bool:
        """Проверить ровно один аргумент без декоратора factorial."""
        try:
            factorial(n)
            return False
        except RecursionError:
            return True

    try:
        low, high = 0, limit + 100
        assert not fails(low) and fails(high)
        while high - low > 1:
            mid = (low + high) // 2
            if fails(mid):
                high = mid
            else:
                low = mid
        assert not fails(low) and fails(high)
        return {"limit": limit, "last_success": low, "first_error": high}
    finally:
        sys.setrecursionlimit(old)


def tribonacci(n: int) -> int:
    """Числа трибоначчи с началом T0=0, T1=0, T2=1."""
    if n < 0:
        raise ValueError("нужно n >= 0")
    if n < 3:  # База.
        return 1 if n == 2 else 0
    # Шаг: сложить три предыдущих значения.
    return tribonacci(n - 1) + tribonacci(n - 2) + tribonacci(n - 3)


def tribonacci_iter(n: int) -> int:
    """Вычислить трибоначчи за линейное число шагов."""
    if n < 0:
        raise ValueError("нужно n >= 0")
    a, b, c = 0, 0, 1
    for _ in range(n):
        a, b, c = b, c, a + b + c
    return a


def substrings(s: str, start: int = 0, end: int = 1) -> tuple[str, ...]:
    """Все непустые подстроки по позициям; повторения сохраняются."""
    if start >= len(s):  # База: все начальные позиции обработаны.
        return ()
    if end > len(s):
        return substrings(s, start + 1, start + 2)  # Следующее начало.
    return (s[start:end],) + substrings(s, start, end + 1)  # Следующий конец.


def substrings_iter(s: str) -> tuple[str, ...]:
    """Перечислить те же подстроки вложенными циклами."""
    result: list[str] = []
    for start in range(len(s)):
        for end in range(start + 1, len(s) + 1):
            result.append(s[start:end])
    return tuple(result)


def grid_paths(m: int, n: int) -> int:
    """Пути в m на n клетках: из верхней левой в нижнюю правую."""
    if m < 1 or n < 1:
        raise ValueError("размеры сетки должны быть положительными")
    if m == 1 or n == 1:  # База: один прямой путь.
        return 1
    return grid_paths(m - 1, n) + grid_paths(m, n - 1)  # Шаг.


def grid_paths_iter(m: int, n: int) -> int:
    """Динамическое программирование с одной строкой памяти."""
    if m < 1 or n < 1:
        raise ValueError("размеры сетки должны быть положительными")
    row = [1] * n
    for _ in range(1, m):
        for j in range(1, n):
            row[j] += row[j - 1]
    return row[-1]


def measured_variant() -> tuple[Any, Any, Any]:
    """Создать инструментированные рекурсивные функции варианта 3."""

    @instrument
    def tri(n: int) -> int:
        """Трибоначчи с подсчётом всех ветвей."""
        if n < 3:  # База.
            return 1 if n == 2 else 0
        return tri(n - 1) + tri(n - 2) + tri(n - 3)  # Шаг.

    @instrument
    def subs(s: str, start: int = 0, end: int = 1) -> tuple[str, ...]:
        """Подстроки с подсчётом переходов между позициями."""
        if start >= len(s):  # База.
            return ()
        if end > len(s):
            return subs(s, start + 1, start + 2)  # Шаг: следующее начало.
        return (s[start:end],) + subs(s, start, end + 1)  # Шаг: следующий конец.

    @instrument
    def paths(m: int, n: int) -> int:
        """Число путей с подсчётом всех вызовов."""
        if m == 1 or n == 1:  # База.
            return 1
        return paths(m - 1, n) + paths(m, n - 1)  # Шаг.

    return tri, subs, paths


def tokenize(text: str) -> list[str]:
    """Разбить выражение на числа, операции и скобки."""
    tokens: list[str] = []
    pattern = r"\s+|\d+(?:\.\d*)?|\.\d+|[()+*/-]"
    pos = 0
    for match in re.finditer(pattern, text):
        if match.start() != pos:
            raise ValueError(f"неизвестный символ в позиции {pos}")
        token = match.group()
        if not token.isspace():
            tokens.append(token)
        pos = match.end()
    if pos != len(text):
        raise ValueError(f"неизвестный символ в позиции {pos}")
    return tokens


def factor(tokens: list[str], pos: int) -> tuple[float, int]:
    """Разобрать число, скобки или унарный знак без изменения токенов."""
    if pos >= len(tokens):
        raise ValueError("ожидалось число или скобка")
    token = tokens[pos]
    if token in ("+", "-"):
        value, end = factor(tokens, pos + 1)  # Шаг после унарного знака.
        return (value if token == "+" else -value), end
    if token == "(":
        value, end = expr(tokens, pos + 1)  # Взаимная рекурсия.
        if end >= len(tokens) or tokens[end] != ")":
            raise ValueError("нет закрывающей скобки")
        return value, end + 1
    if re.fullmatch(r"\d+(?:\.\d*)?|\.\d+", token):  # База.
        return float(token), pos + 1
    raise ValueError(f"ожидалось число, получено {token!r}")


def term_tail(tokens: list[str], pos: int, value: float) -> tuple[float, int]:
    """Продолжить цепочку умножений и делений слева направо."""
    if pos >= len(tokens) or tokens[pos] not in ("*", "/"):  # База.
        return value, pos
    right, end = factor(tokens, pos + 1)
    result = value * right if tokens[pos] == "*" else value / right
    return term_tail(tokens, end, result)  # Шаг: токены потреблены.


def term(tokens: list[str], pos: int) -> tuple[float, int]:
    """Разобрать множитель и последующие операции высокого приоритета."""
    value, end = factor(tokens, pos)
    return term_tail(tokens, end, value)


def expr_tail(tokens: list[str], pos: int, value: float) -> tuple[float, int]:
    """Продолжить сложение и вычитание с левой ассоциативностью."""
    if pos >= len(tokens) or tokens[pos] not in ("+", "-"):  # База.
        return value, pos
    right, end = term(tokens, pos + 1)
    result = value + right if tokens[pos] == "+" else value - right
    return expr_tail(tokens, end, result)  # Шаг.


def expr(tokens: list[str], pos: int) -> tuple[float, int]:
    """Разобрать выражение, возвращая значение и новую позицию."""
    value, end = term(tokens, pos)
    return expr_tail(tokens, end, value)


def evaluate(text: str) -> float:
    """Разобрать всё выражение и запретить остаточные токены."""
    tokens = tokenize(text)
    value, pos = expr(tokens, 0)
    if pos != len(tokens):
        raise ValueError(f"лишний токен {tokens[pos]!r}")
    return value


def expression_samples() -> tuple[str, ...]:
    """Двадцать фиксированных безопасных выражений для сравнения."""
    return (
        "1+2",
        "2+3*4",
        "(2+3)*4",
        "10-3-2",
        "20/5/2",
        "18/(3*2)",
        "7+(8-3)*2",
        "((1+2)*(3+4))",
        "100/(2+3)+7",
        "3.5*2+1",
        "-5+3",
        "2*-3",
        "-(2+3)*4",
        "1-(2-(3-4))",
        "(8/4)+(9/3)",
        "0*(123+456)",
        "12.5/(1.5+1)",
        ".5 + .25",
        "(+6)-(-2)",
        "42",
    )


def benchmark(func: Callable[..., Any], args: tuple[Any, ...], number: int) -> float:
    """Медиана трёх timeit-пакетов, микросекунды на вызов."""
    samples = timeit.repeat(lambda: func(*args), number=number, repeat=3)
    return statistics.median(samples) / number * 1_000_000


def collect_results() -> dict[str, Any]:
    """Реально выполнить все измерения; вызывается при отсутствии кэша."""
    mf, mb, mp = measured_functions()
    analysis: list[dict[str, Any]] = []
    for n in (5, 10, 15, 20, 25):
        for name, func, args in (
            ("fib", mf, (n,)),
            ("binomial", mb, (n, n // 2)),
            ("fast_power", mp, (2, n)),
        ):
            func.reset()
            value = func(*args)
            analysis.append({"name": name, "n": n, "result": value, **func.stats()})
    timing: list[dict[str, Any]] = []
    for name, rec, iterative, values in (
        ("factorial", factorial, factorial_iter, (10, 100, 500)),
        ("fib", fib, fib_iter, (10, 20, 25)),
        ("digit_sum", digit_sum, digit_sum_iter, (10, 50, 300)),
    ):
        for value in values:
            arg = 10**value - 1 if name == "digit_sum" else value
            count = {10: 2000, 20: 50, 25: 5}[value] if name == "fib" else 1000
            iter_count = 20000 if name == "fib" else 1000
            assert rec(arg) == iterative(arg)
            timing.append(
                {
                    "name": name,
                    "n_or_digits": value,
                    "number": count,
                    "iter_number": iter_count,
                    "rec_us": benchmark(rec, (arg,), count),
                    "iter_us": benchmark(iterative, (arg,), iter_count),
                }
            )
    tri, subs, paths = measured_variant()
    variant: list[dict[str, Any]] = []
    for name, measured, rec, iterative, samples in (
        ("tribonacci", tri, tribonacci, tribonacci_iter, ((5,), (10,), (15,))),
        (
            "substrings",
            subs,
            substrings,
            substrings_iter,
            (("abc",), ("banana",), ("abcdefghij",)),
        ),
        ("grid_paths", paths, grid_paths, grid_paths_iter, ((3, 3), (5, 5), (8, 8))),
    ):
        for args in samples:
            measured.reset()
            value = measured(*args)
            assert value == rec(*args) == iterative(*args)
            variant.append(
                {
                    "name": name,
                    "args": args,
                    "result": len(value) if name == "substrings" else value,
                    **measured.stats(),
                    "number": 500,
                    "iter_number": 10000,
                    "rec_us": benchmark(rec, args, 500),
                    "iter_us": benchmark(iterative, args, 10000),
                }
            )
    return {
        "python": sys.version.split()[0],
        "analysis": analysis,
        "timing": timing,
        "variant": variant,
        "boundaries": [recursion_boundary(1000), recursion_boundary(5000)],
        "base_timing": {
            "number": 2000,
            "rec_us": benchmark(to_base, (10**50, 2), 2000),
            "iter_us": benchmark(to_base_iter, (10**50, 2), 2000),
        },
    }


def saved_results(refresh: bool = False) -> dict[str, Any]:
    """Сохранить измерения первого запуска и воспроизводить их в отчёте."""
    path = Path(__file__).with_name("lab_results.json")
    if refresh or not path.exists():
        data = collect_results()
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    return json.loads(path.read_text(encoding="utf-8"))


def show_timings(rows: list[dict[str, Any]]) -> None:
    """Показать таблицу ранее полученных реальных измерений."""
    print("Функция / аргумент | рекурсия, мкс | итерация, мкс | rec/iter")
    for row in rows:
        arg = row.get("n_or_digits", row.get("args"))
        print(
            f"{row['name']} {arg} | {row['rec_us']:.3f} | "
            f"{row['iter_us']:.3f} | {row['rec_us'] / row['iter_us']:.2f}"
        )


def demo(section: str) -> None:
    """Выполнить выбранный практический блок и его assert-проверки."""
    print(f"Лабораторная №5 | Вариант 3 | Швачкина Виктория | {section}")
    if section == "example_sum":
        print("rec_sum([3, 1, 4, 1, 5]) =", rec_sum([3, 1, 4, 1, 5]))
        assert rec_sum([3, 1, 4, 1, 5]) == rec_sum_index([3, 1, 4, 1, 5]) == 14
        assert rec_sum([]) == rec_sum_index([]) == 0
    elif section == "example_instrument":
        f, _, _ = measured_functions()
        print("fib(20) =", f(20), f.stats())
        assert f.stats() == {"calls": 21891, "max_depth": 20}
        f.reset()
        print("fib(10) =", f(10), f.stats())
        assert f.stats() == {"calls": 177, "max_depth": 10}
    elif section == "example_base":
        for n in (0, 7, 255, 2026, 10**12):
            assert to_base(n, 2) == bin(n)[2:]
            assert to_base(n, 16) == hex(n)[2:].upper()
            assert to_base(n, 7) == to_base_iter(n, 7)
        print(
            "2026 в основаниях 2, 8, 16:",
            to_base(2026, 2),
            to_base(2026, 8),
            to_base(2026, 16),
        )
        print("10**50 в основании 2: цифр =", len(to_base(10**50, 2)))
        row = saved_results()["base_timing"]
        print("Сохранённый фактический замер: 3 пакета по 2000 вызовов; медиана.")
        print(f"Рекурсия: {row['rec_us']:.3f} мкс; итерация: {row['iter_us']:.3f} мкс")
        print(f"Отношение rec/iter: {row['rec_us'] / row['iter_us']:.2f}")
    elif section == "factorial":
        for n in (0, 1, 5, 10):
            assert factorial(n) == math.factorial(n)
            print(f"factorial({n}) = {factorial(n)}")
        try:
            factorial(-1)
            raise AssertionError("нет ValueError")
        except ValueError as error:
            print("factorial(-1): ValueError:", error)
    elif section == "digit_sum":
        for n, expected in ((0, 0), (7, 7), (2026, 10), (123456789, 45)):
            assert digit_sum(n) == expected
            print(f"digit_sum({n}) = {digit_sum(n)}")
    elif section == "power":
        for x, n in ((2, 10), (2, -3), (-2, 5), (0, 0), (3, 0)):
            assert power(x, n) == fast_power(x, n) == x**n
            print(f"x={x}, n={n}: power={power(x, n)}, fast_power={fast_power(x, n)}")
        for func in (power, fast_power):
            try:
                func(0, -1)
                raise AssertionError("нет ZeroDivisionError")
            except ZeroDivisionError:
                print(func.__name__, "(0, -1): ZeroDivisionError подтверждён")
    elif section == "gcd_lcm":
        for a, b in ((48, 18), (-48, 18), (0, 7), (0, 0)):
            assert gcd(a, b) == math.gcd(a, b)
            assert lcm(a, b) == math.lcm(a, b)
            print(f"a={a}, b={b}: gcd={gcd(a, b)}, lcm={lcm(a, b)}")
    elif section == "binomial":
        for n, k in ((0, 0), (5, 0), (5, 5), (5, 2), (10, 5)):
            assert binomial(n, k) == math.comb(n, k)
            print(f"C({n},{k}) = {binomial(n, k)}")
    elif section == "palindrome":
        for s, expected in (
            ("А роза упала на лапу Азора!", True),
            ("", True),
            ("!!!", True),
            ("Python", False),
        ):
            assert is_palindrome(s) == expected
            print(f"is_palindrome({s!r}) = {is_palindrome(s)}")
    elif section == "occurrences":
        for s, ch, expected in (("banana", "a", 3), ("", "a", 0), ("АаА", "А", 2)):
            assert count_occurrences(s, ch) == expected
            print(f"count_occurrences({s!r}, {ch!r}) = {count_occurrences(s, ch)}")
    elif section == "reverse":
        for s in ("", "a", "Python", "рекурсия"):
            assert reverse(s) == s[::-1]
            print(f"reverse({s!r}) = {reverse(s)!r}")
    elif section in (
        "length",
        "maximum",
        "rec_map",
        "rec_filter",
        "rec_zip",
        "take",
        "drop",
    ):
        xs = [3, 1, 4, 1, 5]
        print("xs =", xs)
        if section == "length":
            assert length(xs) == 5 and length([]) == 0
            print("length(xs) =", length(xs), "; length([]) =", length([]))
        elif section == "maximum":
            assert maximum(xs) == 5 and maximum([-8, -2, -5]) == -2
            print("maximum(xs) =", maximum(xs))
            print("maximum([-8, -2, -5]) =", maximum([-8, -2, -5]))
            try:
                maximum([])
                raise AssertionError("нет ValueError")
            except ValueError:
                print("maximum([]): ValueError подтверждён")
        elif section == "rec_map":
            assert rec_map(lambda x: x * 2, xs) == [6, 2, 8, 2, 10]
            assert rec_map(str, []) == []
            print("rec_map(x*2, xs) =", rec_map(lambda x: x * 2, xs))
            print("rec_map(str, []) =", rec_map(str, []))
        elif section == "rec_filter":
            assert rec_filter(lambda x: x % 2 == 1, xs) == [3, 1, 1, 5]
            assert rec_filter(bool, []) == []
            print("Нечётные элементы:", rec_filter(lambda x: x % 2 == 1, xs))
            print("rec_filter(bool, []) =", rec_filter(bool, []))
        elif section == "rec_zip":
            assert rec_zip(xs, ["a", "b"]) == [(3, "a"), (1, "b")]
            assert rec_zip([], xs) == [] and rec_zip(xs, []) == []
            print("rec_zip(xs, ['a', 'b']) =", rec_zip(xs, ["a", "b"]))
            print("Пустой список с любой стороны: []")
        elif section == "take":
            for n in (-1, 0, 3, 99):
                expected = xs[: max(n, 0)]
                assert take(n, xs) == expected
                print(f"take({n}, xs) = {take(n, xs)}")
        else:
            for n in (-1, 0, 3, 99):
                expected = xs[max(n, 0) :]
                assert drop(n, xs) == expected
                print(f"drop({n}, xs) = {drop(n, xs)}")
        assert xs == [3, 1, 4, 1, 5]
        print("Исходный список сохранён.")
    elif section == "lists":
        xs = [3, 1, 4, 1, 5]
        print("xs =", xs)
        operations = (
            ("length", length(xs), 5),
            ("maximum", maximum(xs), 5),
            ("rec_map(x*2)", rec_map(lambda x: x * 2, xs), [6, 2, 8, 2, 10]),
            ("rec_filter(odd)", rec_filter(lambda x: x % 2 == 1, xs), [3, 1, 1, 5]),
            ("rec_zip", rec_zip(xs, ["a", "b"]), [(3, "a"), (1, "b")]),
            ("take(3)", take(3, xs), [3, 1, 4]),
            ("drop(3)", drop(3, xs), [1, 5]),
        )
        for name, value, expected in operations:
            assert value == expected
            print(name, "=", value)
        assert length([]) == 0 and take(-1, xs) == [] and drop(99, xs) == []
        assert take(99, xs) == xs and drop(0, xs) == xs
        assert rec_zip([], xs) == [] and rec_map(str, []) == []
        assert rec_filter(bool, []) == []
        try:
            maximum([])
            raise AssertionError("нет ValueError")
        except ValueError:
            print("maximum([]): ValueError подтверждён")
    elif section in ("fold_left", "fold_right"):
        f = lambda a, b: f"({a} - {b})"  # noqa: E731 - точная форма из задания.
        func = fold_left if section == "fold_left" else fold_right
        text = func(f, "0", ["1", "2", "3"])
        value = func(lambda a, b: a - b, 0, [1, 2, 3])
        assert value == (-6 if section == "fold_left" else 2)
        assert func(lambda a, b: a + b, 10, []) == 10
        print(section, "=", text)
        print("Числовой результат =", value)
        print("Пустой список возвращает начальное значение 10.")
    elif section in ("map_fold", "filter_fold"):
        xs = [1, 2, 3, 4]
        if section == "map_fold":
            result = map_fold(lambda x: x * x, xs)
            assert result == rec_map(lambda x: x * x, xs) == [1, 4, 9, 16]
            assert map_fold(str, []) == []
            print("map через fold_right:", result)
        else:
            result = filter_fold(lambda x: x % 2 == 0, xs)
            assert result == rec_filter(lambda x: x % 2 == 0, xs) == [2, 4]
            assert filter_fold(bool, []) == []
            print("filter через fold_right:", result)
        print("Совпадение с прямой рекурсией и пустой случай проверены.")
    elif section == "folds":
        f = lambda a, b: f"({a} - {b})"  # noqa: E731 - точная форма из задания.
        print("fold_left =", fold_left(f, "0", ["1", "2", "3"]))
        print("fold_right =", fold_right(f, "0", ["1", "2", "3"]))
        assert fold_left(f, "0", ["1", "2", "3"]) == "(((0 - 1) - 2) - 3)"
        assert fold_right(f, "0", ["1", "2", "3"]) == "(1 - (2 - (3 - 0)))"
        print(
            "Вычитание чисел: слева",
            fold_left(lambda a, b: a - b, 0, [1, 2, 3]),
            "; справа",
            fold_right(lambda a, b: a - b, 0, [1, 2, 3]),
        )
        print("map через fold_right:", map_fold(lambda x: x * x, [1, 2, 3, 4]))
        print(
            "filter через fold_right:", filter_fold(lambda x: x % 2 == 0, [1, 2, 3, 4])
        )
        assert map_fold(lambda x: x * x, [1, 2, 3, 4]) == [1, 4, 9, 16]
        assert filter_fold(lambda x: x % 2 == 0, [1, 2, 3, 4]) == [2, 4]
    elif section == "analysis":
        print("Фактически выполненные измерения, сохранены в lab_results.json")
        print("n | функция | значение | вызовы | максимальная глубина")
        for row in saved_results()["analysis"]:
            print(
                f"{row['n']:2} | {row['name']:10} | {row['result']:8} | "
                f"{row['calls']:8} | {row['max_depth']:2}"
            )
    elif section in ("trace_fib", "trace_binomial"):

        @make_tracer()
        def fib_trace(n: int) -> int:
            """Фибоначчи для демонстрации дерева."""
            if n < 2:  # База.
                return n
            return fib_trace(n - 1) + fib_trace(n - 2)  # Шаг.

        @make_tracer()
        def binomial_trace(n: int, k: int) -> int:
            """Биномиальный коэффициент для демонстрации дерева."""
            if k in (0, n):  # База.
                return 1
            return binomial_trace(n - 1, k - 1) + binomial_trace(n - 1, k)  # Шаг.

        if section == "trace_fib":
            assert fib_trace(4) == 3
        else:
            assert binomial_trace(4, 2) == 6
    elif section == "hanoi":
        print("Ходы для n=3:", hanoi(3, "A", "C", "B"))
        print("n | ходов | конечный C | результат проверки")
        for n in range(1, 11):
            moves = hanoi(n, "A", "C", "B")
            state = simulate(n, moves)
            assert len(moves) == 2**n - 1
            assert state == {"A": (), "B": (), "C": tuple(range(n, 0, -1))}
            print(n, "|", len(moves), "|", state["C"], "| OK")
        try:
            simulate(2, (("A", "C"), ("A", "C")))
            raise AssertionError("нет ValueError")
        except ValueError as error:
            print("Недопустимый ход: ValueError:", error)
    elif section == "timings":
        print("Медиана 3 пакетов timeit, время одного вызова. Без декораторов.")
        print("Для digit_sum аргумент таблицы означает количество цифр 9.")
        show_timings(saved_results()["timing"])
    elif section == "limits":
        print("Граница найдена двоичным поиском и проверена по обе стороны.")
        for row in saved_results()["boundaries"]:
            print(
                f"limit={row['limit']}: последнее успешное n={row['last_success']}; "
                f"первый RecursionError при n={row['first_error']}"
            )
        print("Текущий восстановленный предел:", sys.getrecursionlimit())
    elif section == "tail":
        for n in (0, 1, 5, 10, 100):
            assert factorial_tail(n) == factorial_while(n) == factorial_iter(n)
            if n < 100:
                print(f"n={n}: tail={factorial_tail(n)}, while={factorial_while(n)}")
            else:
                print(
                    "n=100: все три результата совпали; цифр =",
                    len(str(factorial_tail(n))),
                )
    elif section in ("tribonacci", "substrings", "grid_paths"):
        if section == "tribonacci":
            print("T0..T10:", [tribonacci(n) for n in range(11)])
            for n in range(16):
                assert tribonacci(n) == tribonacci_iter(n)
        elif section == "substrings":
            for s in ("", "abc", "aba"):
                result = substrings(s)
                assert result == substrings_iter(s)
                assert len(result) == len(s) * (len(s) + 1) // 2
                print(f"{s!r}: {result}")
            with_empty = ("",) + substrings("abc")
            assert with_empty == ("", "a", "ab", "abc", "b", "bc", "c")
            assert ("",) + substrings("") == ("",)
            print("С единственной пустой подстрокой:", with_empty)
        else:
            for m, n in ((1, 1), (1, 5), (3, 3), (3, 4), (5, 5)):
                assert (
                    grid_paths(m, n)
                    == grid_paths_iter(m, n)
                    == math.comb(m + n - 2, m - 1)
                )
                print(f"{m}x{n} клеток: {grid_paths(m, n)} путей")
        rows = [r for r in saved_results()["variant"] if r["name"] == section]
        for row in rows:
            print(
                f"{row['args']}: значение/число подстрок={row['result']}; "
                f"вызовы={row['calls']}; глубина={row['max_depth']}"
            )
        show_timings(rows)
    elif section == "tests":
        import unittest

        import tests_lab

        suite = unittest.defaultTestLoader.loadTestsFromModule(tests_lab)
        result = unittest.TextTestRunner(stream=sys.stdout, verbosity=1).run(suite)
        assert result.wasSuccessful()
        print("Независимые эталоны: math.factorial, math.comb, срезы, eval.")
        print("Проверены ошибки, границы, отсутствие мутации и сброс замыканий.")
    elif section == "parser":
        for number, text in enumerate(expression_samples(), 1):
            actual = evaluate(text)
            expected = eval(text, {"__builtins__": {}}, {})
            assert math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-12)
            print(f"{number:2}. {text:24} parser={actual:8g}; eval={expected:8g}; OK")
        for text in ("1+", "(1+2", "2 3", "1$2", ""):
            try:
                evaluate(text)
                raise AssertionError("нет ValueError")
            except ValueError:
                print(f"{text!r}: ValueError подтверждён")
        try:
            evaluate("1/0")
            raise AssertionError("нет ZeroDivisionError")
        except ZeroDivisionError:
            print("'1/0': ZeroDivisionError подтверждён")
    else:
        raise ValueError(f"неизвестный раздел {section}")
    print("Все проверки блока пройдены.")


def main() -> None:
    """Выбрать блок; all выполняет все практические задания."""
    sections = (
        "example_sum",
        "example_instrument",
        "example_base",
        "factorial",
        "digit_sum",
        "power",
        "gcd_lcm",
        "binomial",
        "palindrome",
        "occurrences",
        "reverse",
        "length",
        "maximum",
        "rec_map",
        "rec_filter",
        "rec_zip",
        "take",
        "drop",
        "fold_left",
        "fold_right",
        "folds",
        "map_fold",
        "filter_fold",
        "analysis",
        "trace_fib",
        "trace_binomial",
        "hanoi",
        "timings",
        "limits",
        "tail",
        "tribonacci",
        "substrings",
        "grid_paths",
        "parser",
        "tests",
    )
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--section", default="all", choices=("all",) + sections)
    parser.add_argument(
        "--refresh", action="store_true", help="повторить все измерения"
    )
    options = parser.parse_args()
    if options.refresh:
        saved_results(refresh=True)
    for section in sections if options.section == "all" else (options.section,):
        demo(section)
        print()


if __name__ == "__main__":
    main()
