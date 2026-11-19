# coding: utf-8
from __future__ import annotations

import math
import re

from simple_portable_numeric.enum_rounding_mode import EnumRoundingMode
from simple_portable_numeric.portable_decimal import PortableDecimal
from simple_portable_numeric.util_int_math import digits_to_int, int_to_digits, ratio_to_float, round_div

_FRACTION_PATTERN = re.compile(r"([+-]?)([0-9]+)/([0-9]+)")
_DECIMAL_PATTERN = re.compile(r"[+-]?[0-9]+(\.[0-9]+)?")


def _check_int(value: object, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be int, got {type(value).__name__}")


class PortableRational:
    """
    (en) An exact rational number numerator / denominator.
    It is always kept in canonical form: reduced, with a positive denominator.
    The results are identical to the Dart version of this package.

    (ja) 分子 / 分母 で表される正確な有理数です。
    常に約分済みで分母が正の正規形で保持されます。
    計算結果はこのパッケージのDart版と同一になります。
    """
    __slots__ = ("_numerator", "_denominator")

    def __init__(self, numerator: int, denominator: int = 1):
        """
        (en) Creates numerator / denominator, reduced to canonical form.

        (ja) 分子 / 分母 を作成し、正規形に約分します。

        Parameters
        ----------
        numerator: int
            The numerator.
        denominator: int
            The denominator. Must not be zero.

        Raises
        ------
        ZeroDivisionError
            If denominator is zero.
        """
        _check_int(numerator, "numerator")
        _check_int(denominator, "denominator")
        if denominator == 0:
            raise ZeroDivisionError("Division by zero")
        if denominator < 0:
            numerator, denominator = -numerator, -denominator
        g = math.gcd(numerator, denominator)
        self._numerator = numerator // g
        self._denominator = denominator // g

    @classmethod
    def parse(cls, text: str) -> PortableRational:
        """
        (en) Parses "n/d", an integer such as "-3", or a plain decimal such as "0.75".
        The result is reduced to canonical form.

        (ja) "n/d"、"-3" のような整数、"0.75" のような通常表記の10進数を解析します。
        結果は正規形に約分されます。

        Parameters
        ----------
        text: str
            The string to parse.

        Returns
        -------
        PortableRational
            The parsed value.

        Raises
        ------
        ValueError
            If the string is not a valid format.
        ZeroDivisionError
            If the denominator is zero.
        """
        if not isinstance(text, str):
            raise TypeError(f"text must be str, got {type(text).__name__}")
        m = _FRACTION_PATTERN.fullmatch(text)
        if m is not None:
            n = digits_to_int(m.group(2))
            return cls(-n if m.group(1) == "-" else n, digits_to_int(m.group(3)))
        if _DECIMAL_PATTERN.fullmatch(text) is not None:
            return PortableDecimal.parse(text).to_rational()
        raise ValueError(f"Invalid rational string: {text!r}")

    @property
    def numerator(self) -> int:
        """
        (en) The numerator in canonical form.

        (ja) 正規形での分子です。
        """
        return self._numerator

    @property
    def denominator(self) -> int:
        """
        (en) The denominator in canonical form (always positive).

        (ja) 正規形での分母です（常に正）。
        """
        return self._denominator

    def __add__(self, other: object) -> PortableRational:
        if not isinstance(other, PortableRational):
            return NotImplemented
        return PortableRational(self._numerator * other._denominator + other._numerator * self._denominator,
                                self._denominator * other._denominator)

    def __sub__(self, other: object) -> PortableRational:
        if not isinstance(other, PortableRational):
            return NotImplemented
        return PortableRational(self._numerator * other._denominator - other._numerator * self._denominator,
                                self._denominator * other._denominator)

    def __mul__(self, other: object) -> PortableRational:
        if not isinstance(other, PortableRational):
            return NotImplemented
        return PortableRational(self._numerator * other._numerator, self._denominator * other._denominator)

    def __truediv__(self, other: object) -> PortableRational:
        if not isinstance(other, PortableRational):
            return NotImplemented
        if other._numerator == 0:
            raise ZeroDivisionError("Division by zero")
        return PortableRational(self._numerator * other._denominator, self._denominator * other._numerator)

    def __neg__(self) -> PortableRational:
        return PortableRational(-self._numerator, self._denominator)

    def __abs__(self) -> PortableRational:
        return PortableRational(abs(self._numerator), self._denominator)

    def pow(self, n: int) -> PortableRational:
        """
        (en) Returns this value raised to the power n. Exact, in canonical form.
        A negative n gives (1 / self)^|n|. pow(0) is 1, also for zero.
        a ** n is the same.

        (ja) この値の n 乗を返します。正確で、結果は正規形です。
        負の n は (1 / self)^|n| です。pow(0) はゼロの場合も1です。
        a ** n も同じです。

        Parameters
        ----------
        n: int
            The exponent. Any integer.

        Returns
        -------
        PortableRational
            The power.

        Raises
        ------
        ZeroDivisionError
            If this value is zero and n is negative.
        """
        _check_int(n, "n")
        if n >= 0:
            return PortableRational(self._numerator ** n, self._denominator ** n)
        if self._numerator == 0:
            raise ZeroDivisionError("Division by zero")
        return PortableRational(self._denominator ** -n, self._numerator ** -n)

    def __pow__(self, n: object, mod: object = None) -> PortableRational:
        if mod is not None:
            raise TypeError("pow() with a modulus is not supported")
        if isinstance(n, bool) or not isinstance(n, int):
            return NotImplemented
        return self.pow(n)

    def is_integer(self) -> bool:
        """
        (en) Returns whether this value is an integer (the denominator is 1).

        (ja) この値が整数（分母が1）かどうかを返します。

        Returns
        -------
        bool
            True if this value is an integer.
        """
        return self._denominator == 1

    def to_int(self, rounding: EnumRoundingMode) -> int:
        """
        (en) Rounds this value once to an integer.

        (ja) この値を1回だけ丸めて整数にします。

        Parameters
        ----------
        rounding: EnumRoundingMode
            The rounding mode.

        Returns
        -------
        int
            The rounded integer.
        """
        return round_div(self._numerator, self._denominator, rounding)

    def compare_to(self, other: PortableRational) -> int:
        """
        (en) Compares by numeric value.

        (ja) 数値で比較します。

        Parameters
        ----------
        other: PortableRational
            The value to compare with.

        Returns
        -------
        int
            -1 if this < other, 0 if equal, 1 if this > other.
        """
        if not isinstance(other, PortableRational):
            raise TypeError(f"other must be PortableRational, got {type(other).__name__}")
        a = self._numerator * other._denominator
        b = other._numerator * self._denominator
        return (a > b) - (a < b)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PortableRational):
            return NotImplemented
        return self._numerator == other._numerator and self._denominator == other._denominator

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, PortableRational):
            return NotImplemented
        return self.compare_to(other) < 0

    def __le__(self, other: object) -> bool:
        if not isinstance(other, PortableRational):
            return NotImplemented
        return self.compare_to(other) <= 0

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, PortableRational):
            return NotImplemented
        return self.compare_to(other) > 0

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, PortableRational):
            return NotImplemented
        return self.compare_to(other) >= 0

    def __hash__(self) -> int:
        return hash((self._numerator, self._denominator))

    def to_decimal(self, scale: int, rounding: EnumRoundingMode) -> PortableDecimal:
        """
        (en) Converts this value to a decimal with the specified scale,
        rounding the exact value once.

        (ja) この値を指定したscaleの10進数に変換します。正確な値を1回だけ丸めます。

        Parameters
        ----------
        scale: int
            The number of digits after the decimal point. Must be 0 or more.
        rounding: EnumRoundingMode
            The rounding mode.

        Returns
        -------
        PortableDecimal
            The converted value.
        """
        _check_int(scale, "scale")
        if scale < 0:
            raise ValueError(f"scale must be 0 or more, got {scale}")
        return PortableDecimal(round_div(self._numerator * 10 ** scale, self._denominator, rounding), scale)

    def to_decimal_exact(self) -> PortableDecimal:
        """
        (en) Converts this value exactly to a finite decimal with the smallest scale,
        e.g. 3/8 -> 0.375. This is possible only when the denominator is 2^p * 5^q.

        (ja) この値を、最小のscaleの有限小数に正確に変換します（例: 3/8 -> 0.375）。
        分母が 2^p * 5^q の場合のみ変換できます。

        Returns
        -------
        PortableDecimal
            The equal decimal value.

        Raises
        ------
        ValueError
            If this value is not a finite decimal (e.g. 1/3).
        """
        d = self._denominator
        p = q = 0
        while d % 2 == 0:
            d //= 2
            p += 1
        while d % 5 == 0:
            d //= 5
            q += 1
        if d != 1:
            raise ValueError("The value is not a finite decimal")
        scale = max(p, q)
        return PortableDecimal(self._numerator * 10 ** scale // self._denominator, scale)

    def to_float(self) -> float:
        """
        (en) Converts this value to the nearest double (ties to even).
        Overflow returns +-inf. The result is identical to toDouble in Dart.

        (ja) この値を最も近い倍精度浮動小数点数に変換します（同距離は偶数側）。
        範囲外の場合は +-inf を返します。結果はDart版の toDouble と同一です。

        Returns
        -------
        float
            The converted value.
        """
        return ratio_to_float(self._numerator, self._denominator)

    def to_string(self) -> str:
        """
        (en) Returns "n/d", or "n" when the denominator is 1.

        (ja) "n/d" を返します。分母が1の場合は "n" を返します。

        Returns
        -------
        str
            The string representation.
        """
        n = int_to_digits(abs(self._numerator))
        if self._numerator < 0:
            n = "-" + n
        if self._denominator == 1:
            return n
        return n + "/" + int_to_digits(self._denominator)

    def __str__(self) -> str:
        return self.to_string()

    def __repr__(self) -> str:
        return f"PortableRational('{self.to_string()}')"
