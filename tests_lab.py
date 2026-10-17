"""Независимые эталоны, границы и свойства лабораторной работы 5."""

import ast
import copy
import io
import math
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import lab
from lab05.tools import instrument


class ClassicalTests(unittest.TestCase):
    """Классические функции, включая контракты ошибочного ввода."""

    def test_factorial(self) -> None:
        """Сравнить диапазон значений с независимым math.factorial."""
        for n in range(101):
            self.assertEqual(lab.factorial(n), math.factorial(n))
            self.assertEqual(lab.factorial_tail(n), math.factorial(n))
            self.assertEqual(lab.factorial_while(n), math.factorial(n))
        with self.assertRaises(ValueError):
            lab.factorial(-1)

    def test_digits_and_bases(self) -> None:
        """Сравнить сумму цифр и перевод оснований с независимыми эталонами."""
        for n in (0, 1, 9, 10, 2026, 10**100 - 1):
            expected = sum(map(int, str(n)))
            self.assertEqual(lab.digit_sum(n), expected)
            self.assertEqual(lab.digit_sum_iter(n), expected)
            for base in range(2, 17):
                value = lab.to_base(n, base)
                self.assertEqual(int(value, base), n)
                self.assertEqual(value, lab.to_base_iter(n, base))
        for n, base in ((-1, 2), (2, 1), (2, 17)):
            with self.assertRaises(ValueError):
                lab.to_base(n, base)
        with self.assertRaises(ValueError):
            lab.digit_sum(-1)

    def test_powers(self) -> None:
        """Проверить знак, нулевой показатель и отрицательные степени."""
        for x in (-3, -1, 0, 1, 2):
            for n in range(-8, 9):
                if x == 0 and n < 0:
                    for func in (lab.power, lab.fast_power):
                        with self.assertRaises(ZeroDivisionError):
                            func(x, n)
                else:
                    self.assertAlmostEqual(lab.power(x, n), x**n)
                    self.assertAlmostEqual(lab.fast_power(x, n), x**n)

    def test_gcd_lcm_binomial(self) -> None:
        """Сравнить знаки и нули с math, Паскаля с math.comb."""
        for a in range(-12, 13):
            for b in range(-12, 13):
                self.assertEqual(lab.gcd(a, b), math.gcd(a, b))
                self.assertEqual(lab.lcm(a, b), math.lcm(a, b))
        for n in range(13):
            for k in range(n + 1):
                self.assertEqual(lab.binomial(n, k), math.comb(n, k))
        for n, k in ((-1, 0), (3, -1), (3, 4)):
            with self.assertRaises(ValueError):
                lab.binomial(n, k)

    def test_strings(self) -> None:
        """Проверить кириллицу, регистр, пунктуацию и пустые строки."""
        for s in ("", "a", "А роза упала на лапу Азора!", "Python", "ßSS", "!!!"):
            normal = "".join(c for c in s.casefold() if c.isalnum())
            self.assertEqual(lab.is_palindrome(s), normal == normal[::-1])
            self.assertEqual(lab.reverse(s), s[::-1])
            for ch in ("a", "А", "!", "s"):
                self.assertEqual(lab.count_occurrences(s, ch), s.count(ch))
        for ch in ("", "ab"):
            with self.assertRaises(ValueError):
                lab.count_occurrences("abc", ch)

    def test_recursive_restriction(self) -> None:
        """Убедиться, что в функциях задания 1 нет циклов."""
        tree = ast.parse(Path(lab.__file__).read_text(encoding="utf-8"))
        names = {
            "factorial",
            "digit_sum",
            "power",
            "fast_power",
            "gcd",
            "lcm",
            "binomial",
            "is_palindrome",
            "count_occurrences",
            "reverse",
        }
        forbidden = (
            ast.For,
            ast.While,
            ast.ListComp,
            ast.SetComp,
            ast.DictComp,
            ast.GeneratorExp,
        )
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name in names:
                self.assertFalse(
                    any(isinstance(child, forbidden) for child in ast.walk(node))
                )


class ListTests(unittest.TestCase):
    """Проверки схемы головы и хвоста, порядка и отсутствия мутации."""

    def test_list_operations(self) -> None:
        """Сравнить все операции с независимыми стандартными операциями."""
        for xs in ([], [1], [3, -2, 4, -2, 0]):
            original = xs.copy()
            self.assertEqual(lab.rec_sum(xs), sum(xs))
            self.assertEqual(lab.rec_sum_index(xs), sum(xs))
            self.assertEqual(lab.length(xs), len(xs))
            if xs:
                self.assertEqual(lab.maximum(xs), max(xs))
            else:
                with self.assertRaises(ValueError):
                    lab.maximum(xs)
            self.assertEqual(lab.rec_map(lambda x: x * x, xs), [x * x for x in xs])
            self.assertEqual(lab.map_fold(lambda x: x * x, xs), [x * x for x in xs])
            self.assertEqual(
                lab.rec_filter(lambda x: x > 0, xs), [x for x in xs if x > 0]
            )
            self.assertEqual(
                lab.filter_fold(lambda x: x > 0, xs), [x for x in xs if x > 0]
            )
            for ys in ([], [8], [1, 2, 3, 4, 5, 6]):
                self.assertEqual(lab.rec_zip(xs, ys), list(zip(xs, ys)))
            for n in (-2, 0, 1, 3, 99):
                self.assertEqual(lab.take(n, xs), xs[: max(n, 0)])
                self.assertEqual(lab.drop(n, xs), xs[max(n, 0) :])
            self.assertEqual(xs, original)

    def test_folds(self) -> None:
        """Неассоциативная операция обнаруживает перепутанное направление."""
        self.assertEqual(lab.fold_left(lambda a, b: a - b, 0, [1, 2, 3]), -6)
        self.assertEqual(lab.fold_right(lambda a, b: a - b, 0, [1, 2, 3]), 2)
        self.assertEqual(lab.fold_left(lambda a, b: a + b, 7, []), 7)
        self.assertEqual(lab.fold_right(lambda a, b: a + b, 7, []), 7)


class InstrumentTests(unittest.TestCase):
    """Проверки рекурсивного связывания и восстановления при исключении."""

    def test_counts_and_reset(self) -> None:
        """Сверить число вызовов с математическими формулами."""
        f, b, p = lab.measured_functions()
        for n in range(1, 11):
            f.reset()
            self.assertEqual(f(n), lab.fib_iter(n))
            self.assertEqual(f.stats()["calls"], 2 * lab.fib_iter(n + 1) - 1)
            self.assertEqual(f.stats()["max_depth"], n)
            b.reset()
            k = n // 2
            self.assertEqual(b(n, k), math.comb(n, k))
            self.assertEqual(b.stats()["calls"], 2 * math.comb(n, k) - 1)
            p.reset()
            self.assertEqual(p(2, n), 2**n)
            self.assertEqual(p.stats()["calls"], n.bit_length() + 1)
        f.reset()
        self.assertEqual(f.stats(), {"calls": 0, "max_depth": 0})

    def test_exception_cleanup_and_metadata(self) -> None:
        """После исключения глубина должна вернуться к нулю."""

        @instrument
        def failing(n: int) -> int:
            """Функция с намеренным исключением в базе."""
            if n == 0:
                raise ValueError("test")
            return failing(n - 1)

        self.assertEqual(failing.__name__, "failing")
        with self.assertRaises(ValueError):
            failing(2)
        self.assertEqual(failing.stats(), {"calls": 3, "max_depth": 3})
        failing.reset()
        with self.assertRaises(ValueError):
            failing(0)
        self.assertEqual(failing.stats(), {"calls": 1, "max_depth": 1})

    def test_tracer(self) -> None:
        """Трассировка должна сохранять вычисленный результат."""

        @lab.make_tracer(".")
        def count(n: int) -> int:
            """Небольшая рекурсия для проверки отступов."""
            return 0 if n == 0 else 1 + count(n - 1)

        stream = io.StringIO()
        with redirect_stdout(stream):
            self.assertEqual(count(2), 2)
        self.assertIn("..count(0,)", stream.getvalue())
        self.assertTrue(stream.getvalue().endswith("=> 2\n"))


class HanoiTests(unittest.TestCase):
    """Проверка корректности каждого хода и полного конечного состояния."""

    def test_full_range(self) -> None:
        """Проверить n=0..10, включая 1023 хода для десяти дисков."""
        for n in range(11):
            moves = lab.hanoi(n, "A", "C", "B")
            self.assertEqual(len(moves), 2**n - 1)
            self.assertEqual(
                lab.simulate(n, moves), {"A": (), "B": (), "C": tuple(range(n, 0, -1))}
            )

    def test_illegal_moves(self) -> None:
        """Проверить большой диск, пустой источник и неверные стержни."""
        cases = ((("A", "C"), ("A", "C")), (("B", "C"),), (("A", "A"),), (("D", "A"),))
        for moves in cases:
            with self.assertRaises(ValueError):
                lab.simulate(2, moves)
        with self.assertRaises(ValueError):
            lab.hanoi(-1, "A", "C", "B")


class VariantAndParserTests(unittest.TestCase):
    """Все три индивидуальные задачи и дополнительное задание."""

    def test_tribonacci(self) -> None:
        """Проверить независимо заданное начало последовательности."""
        expected = (0, 0, 1, 1, 2, 4, 7, 13, 24, 44, 81, 149)
        for n, value in enumerate(expected):
            self.assertEqual(lab.tribonacci(n), value)
            self.assertEqual(lab.tribonacci_iter(n), value)

    def test_substrings(self) -> None:
        """Проверить порядок, число и сохранение повторяющихся подстрок."""
        for s in ("", "a", "aba", "abcd", "ааа"):
            expected = tuple(
                s[i:j] for i in range(len(s)) for j in range(i + 1, len(s) + 1)
            )
            self.assertEqual(lab.substrings(s), expected)
            self.assertEqual(lab.substrings_iter(s), expected)
            self.assertEqual(len(expected), len(s) * (len(s) + 1) // 2)
        self.assertEqual(lab.substrings("aba").count("a"), 2)

    def test_grid_paths(self) -> None:
        """Сравнить с комбинаторной формулой для всех сеток до 7x7."""
        for m in range(1, 8):
            for n in range(1, 8):
                expected = math.comb(m + n - 2, m - 1)
                self.assertEqual(lab.grid_paths(m, n), expected)
                self.assertEqual(lab.grid_paths_iter(m, n), expected)
        with self.assertRaises(ValueError):
            lab.grid_paths(0, 3)

    def test_twenty_expressions(self) -> None:
        """Сравнить ровно 20 учебных выражений с eval."""
        self.assertEqual(len(lab.expression_samples()), 20)
        for expression in lab.expression_samples():
            self.assertAlmostEqual(
                lab.evaluate(expression), eval(expression, {"__builtins__": {}}, {})
            )

    def test_parser_purity_and_positions(self) -> None:
        """Проверить пару результат-позиция и неизменность списка токенов."""
        tokens = lab.tokenize("2+3*4")
        original = copy.deepcopy(tokens)
        self.assertEqual(lab.expr(tokens, 0), (14.0, 5))
        self.assertEqual(lab.term(tokens, 2), (12.0, 5))
        self.assertEqual(lab.factor(tokens, 2), (3.0, 3))
        self.assertEqual(tokens, original)

    def test_parser_errors(self) -> None:
        """Неверный синтаксис и нулевой делитель не маскируются."""
        for text in ("", "1+", "(1+2", "2 3", "a+1", "1$2", "1)", "()", "2**3"):
            with self.assertRaises(ValueError):
                lab.evaluate(text)
        with self.assertRaises(ZeroDivisionError):
            lab.evaluate("1/0")


if __name__ == "__main__":
    unittest.main(verbosity=2)
