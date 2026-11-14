# coding: utf-8
from __future__ import annotations

import re
from typing import TYPE_CHECKING

from simple_portable_numeric.enum_rounding_mode import EnumRoundingMode
from simple_portable_numeric.util_int_math import digits_to_int, int_to_digits, ratio_to_float, round_div

if TYPE_CHECKING:
    from simple_portable_numeric.portable_rational import PortableRational

_DECIMAL_PATTERN = re.compile(r"[+-]?[0-9]+(\.[0-9]+)?")


def _check_int(value: object, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be int, got {type(value).__name__}")


class PortableDecimal:
    """
    (en) An arbitrary-precision decimal number, represented as
    unscaled_value * 10^(-scale).
    The results are identical to the Dart version of this package.
    Equality is by numeric value (1.50 == 1.5), while to_string keeps the scale.

    (ja) 任意精度の10進数です。unscaled_value * 10^(-scale) として表現されます。
    計算結果はこのパッケージのDart版と同一になります。
    等価判定は数値で行われ（1.50 == 1.5）、文字列化ではscaleが保持されます。
    """
    __slots__ = ("_unscaled_value", "_scale")

    def __init__(self, unscaled_value: int, scale: int = 0):
        """
        (en) Creates a decimal whose value is unscaled_value * 10^(-scale).

        (ja) 値が unscaled_value * 10^(-scale) の10進数を作成します。

        Parameters
        ----------
        unscaled_value: int
            The integer value with the decimal point removed.
        scale: int
            The number of digits after the decimal point. Must be 0 or more.
        """
        _check_int(unscaled_value, "unscaled_value")
        _check_int(scale, "scale")
        if scale < 0:
            raise ValueError(f"scale must be 0 or more, got {scale}")
        self._unscaled_value = unscaled_value
        self._scale = scale

    @classmethod
    def parse(cls, text: str) -> PortableDecimal:
        """
        (en) Parses a plain decimal string such as "-12.340".
        The number of fractional digits becomes the scale.
        Exponent notation, whitespace and non-ASCII digits are rejected.

        (ja) "-12.340" のような通常表記の10進文字列を解析します。
        小数部の桁数がscaleになります。
        指数表記、空白、ASCII以外の数字は受け付けません。

        Parameters
        ----------
        text: str
            The string to parse.

        Returns
        -------
        PortableDecimal
            The parsed value.

        Raises
        ------
        ValueError
            If the string is not a valid decimal.
        """
        if not isinstance(text, str):
            raise TypeError(f"text must be str, got {type(text).__name__}")
        if _DECIMAL_PATTERN.fullmatch(text) is None:
            raise ValueError(f"Invalid decimal string: {text!r}")
        int_part, _, frac_part = text.partition(".")
        negative = int_part.startswith("-")
        value = digits_to_int(int_part.lstrip("+-") + frac_part)
        return cls(-value if negative else value, len(frac_part))

    @property
    def unscaled_value(self) -> int:
        """
        (en) The integer value with the decimal point removed.

        (ja) 小数点を取り除いた整数値です。
        """
        return self._unscaled_value

    @property
    def scale(self) -> int:
        """
        (en) The number of digits after the decimal point.

        (ja) 小数点以下の桁数です。
        """
        return self._scale

    def _aligned(self, other: PortableDecimal) -> tuple[int, int, int]:
        """Returns (self unscaled, other unscaled, common scale)."""
        scale = max(self._scale, other._scale)
        return (self._unscaled_value * 10 ** (scale - self._scale),
                other._unscaled_value * 10 ** (scale - other._scale),
                scale)

    def __add__(self, other: object) -> PortableDecimal:
        if not isinstance(other, PortableDecimal):
            return NotImplemented
        a, b, scale = self._aligned(other)
        return PortableDecimal(a + b, scale)

    def __sub__(self, other: object) -> PortableDecimal:
        if not isinstance(other, PortableDecimal):
            return NotImplemented
        a, b, scale = self._aligned(other)
        return PortableDecimal(a - b, scale)

    def __mul__(self, other: object) -> PortableDecimal:
        if not isinstance(other, PortableDecimal):
            return NotImplemented
        return PortableDecimal(self._unscaled_value * other._unscaled_value, self._scale + other._scale)

    def __neg__(self) -> PortableDecimal:
        return PortableDecimal(-self._unscaled_value, self._scale)

    def __abs__(self) -> PortableDecimal:
        return PortableDecimal(abs(self._unscaled_value), self._scale)

    def divide(self, other: PortableDecimal, scale: int, rounding: EnumRoundingMode) -> PortableDecimal:
        """
        (en) Divides this value by other. The exact quotient is rounded once
        to the specified number of fractional digits.

        (ja) この値を other で割ります。正確な商を、指定した小数点以下の桁数に
        1回だけ丸めます。

        Parameters
        ----------
        other: PortableDecimal
            The divisor.
        scale: int
            The number of digits after the decimal point of the result. Must be 0 or more.
        rounding: EnumRoundingMode
            The rounding mode.

        Returns
        -------
        PortableDecimal
            The rounded quotient.

        Raises
        ------
        ZeroDivisionError
            If other is zero.
        """
        if not isinstance(other, PortableDecimal):
            raise TypeError(f"other must be PortableDecimal, got {type(other).__name__}")
        _check_int(scale, "scale")
        if scale < 0:
            raise ValueError(f"scale must be 0 or more, got {scale}")
        if other._unscaled_value == 0:
            raise ZeroDivisionError("Division by zero")
        # result = (a / 10^sa) / (b / 10^sb) * 10^scale = a * 10^(scale + sb - sa) / b
        exp = scale + other._scale - self._scale
        n = self._unscaled_value
        d = other._unscaled_value
        if exp >= 0:
            n *= 10 ** exp
        else:
            d *= 10 ** (-exp)
        return PortableDecimal(round_div(n, d, rounding), scale)

    def set_scale(self, scale: int, rounding: EnumRoundingMode) -> PortableDecimal:
        """
        (en) Returns a value with the specified scale. Increasing the scale is exact;
        decreasing it rounds once with the specified rounding mode.

        (ja) 指定したscaleの値を返します。scaleを増やす場合は正確に、
        減らす場合は指定した丸めモードで1回だけ丸めます。

        Parameters
        ----------
        scale: int
            The new number of digits after the decimal point. Must be 0 or more.
        rounding: EnumRoundingMode
            The rounding mode used when the scale decreases.

        Returns
        -------
        PortableDecimal
            The rescaled value.
        """
        _check_int(scale, "scale")
        if scale < 0:
            raise ValueError(f"scale must be 0 or more, got {scale}")
        if scale >= self._scale:
            return PortableDecimal(self._unscaled_value * 10 ** (scale - self._scale), scale)
        return PortableDecimal(round_div(self._unscaled_value, 10 ** (self._scale - scale), rounding), scale)

    def compare_to(self, other: PortableDecimal) -> int:
        """
        (en) Compares by numeric value.

        (ja) 数値で比較します。

        Parameters
        ----------
        other: PortableDecimal
            The value to compare with.

        Returns
        -------
        int
            -1 if this < other, 0 if equal, 1 if this > other.
        """
        if not isinstance(other, PortableDecimal):
            raise TypeError(f"other must be PortableDecimal, got {type(other).__name__}")
        a, b, _ = self._aligned(other)
        return (a > b) - (a < b)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PortableDecimal):
            return NotImplemented
        return self.compare_to(other) == 0

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, PortableDecimal):
            return NotImplemented
        return self.compare_to(other) < 0

    def __le__(self, other: object) -> bool:
        if not isinstance(other, PortableDecimal):
            return NotImplemented
        return self.compare_to(other) <= 0

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, PortableDecimal):
            return NotImplemented
        return self.compare_to(other) > 0

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, PortableDecimal):
            return NotImplemented
        return self.compare_to(other) >= 0

    def __hash__(self) -> int:
        u, s = self._unscaled_value, self._scale
        while s > 0 and u % 10 == 0:
            u //= 10
            s -= 1
        return hash((u, s))

    def to_rational(self) -> PortableRational:
        """
        (en) Converts this value to an exactly equal rational.

        (ja) この値を、正確に等しい有理数に変換します。

        Returns
        -------
        PortableRational
            The equal rational value.
        """
        from simple_portable_numeric.portable_rational import PortableRational
        return PortableRational(self._unscaled_value, 10 ** self._scale)

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
        return ratio_to_float(self._unscaled_value, 10 ** self._scale)

    def to_string(self) -> str:
        """
        (en) Returns the plain-notation string keeping the scale, e.g. "-1.50".
        Negative zero is never output.

        (ja) scaleを保持した通常表記の文字列を返します（例: "-1.50"）。
        負のゼロは出力されません。

        Returns
        -------
        str
            The string representation.
        """
        digits = int_to_digits(abs(self._unscaled_value))
        if self._scale > 0:
            digits = digits.rjust(self._scale + 1, "0")
            digits = digits[:-self._scale] + "." + digits[-self._scale:]
        return "-" + digits if self._unscaled_value < 0 else digits

    def __str__(self) -> str:
        return self.to_string()

    def __repr__(self) -> str:
        return f"PortableDecimal('{self.to_string()}')"
