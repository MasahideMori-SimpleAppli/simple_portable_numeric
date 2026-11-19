# coding: utf-8
import math

from simple_portable_numeric.enum_rounding_mode import EnumRoundingMode


def round_div(n: int, d: int, rounding: EnumRoundingMode) -> int:
    """
    (en) Divides n by d exactly and rounds the quotient to an integer once.

    (ja) n を d で正確に割り、商を1回だけ丸めて整数にします。

    Parameters
    ----------
    n: int
        The dividend.
    d: int
        The divisor. Must not be zero.
    rounding: EnumRoundingMode
        The rounding mode.

    Returns
    -------
    int
        The rounded quotient.
    """
    if d == 0:
        raise ZeroDivisionError("Division by zero")
    if d < 0:
        n, d = -n, -d
    q, r = divmod(n, d)  # q = floor(n / d), 0 <= r < d
    if r == 0:
        return q
    if rounding is EnumRoundingMode.floor:
        return q
    if rounding is EnumRoundingMode.ceiling:
        return q + 1
    if rounding is EnumRoundingMode.down:
        return q if n >= 0 else q + 1
    if rounding is EnumRoundingMode.up:
        return q + 1 if n >= 0 else q
    twice = 2 * r
    if twice < d:
        return q
    if twice > d:
        return q + 1
    if rounding is EnumRoundingMode.halfUp:
        return q + 1 if n >= 0 else q
    if rounding is EnumRoundingMode.halfEven:
        return q if q % 2 == 0 else q + 1
    raise ValueError(f"Unsupported rounding mode: {rounding}")


def ratio_to_float(n: int, d: int) -> float:
    """
    (en) Converts the exact ratio n / d to the nearest IEEE 754 double
    (ties to even). Overflow returns +-inf.

    (ja) 正確な比 n / d を最も近いIEEE 754倍精度浮動小数点数に変換します
    （同距離は偶数側）。範囲外の場合は +-inf を返します。

    Parameters
    ----------
    n: int
        The numerator.
    d: int
        The denominator. Must be positive.

    Returns
    -------
    float
        The correctly rounded double value.
    """
    try:
        # CPython's int / int is correctly rounded, including subnormals.
        return n / d
    except OverflowError:
        return math.inf if n > 0 else -math.inf


_CHUNK = 1000
_CHUNK_BASE = 10 ** _CHUNK


def digits_to_int(digits: str) -> int:
    """
    (en) Converts a string of ASCII digits to a non-negative int.
    Unlike int(), this is not limited by sys.get_int_max_str_digits(),
    so the same strings are accepted as in the Dart version.

    (ja) ASCII数字の文字列を非負の整数に変換します。
    int() と異なり sys.get_int_max_str_digits() の制限を受けないため、
    Dart版と同じ文字列を受け付けます。

    Parameters
    ----------
    digits: str
        A non-empty string consisting only of "0"-"9".

    Returns
    -------
    int
        The converted value.
    """
    result = 0
    for i in range(0, len(digits), _CHUNK):
        chunk = digits[i:i + _CHUNK]
        result = result * 10 ** len(chunk) + int(chunk)
    return result


def int_to_digits(value: int) -> str:
    """
    (en) Converts a non-negative int to a decimal digit string.
    Unlike str(), this is not limited by sys.get_int_max_str_digits().

    (ja) 非負の整数を10進数字の文字列に変換します。
    str() と異なり sys.get_int_max_str_digits() の制限を受けません。

    Parameters
    ----------
    value: int
        A non-negative integer.

    Returns
    -------
    str
        The digit string without leading zeros ("0" for zero).
    """
    if value < _CHUNK_BASE:
        return str(value)
    chunks = []
    while value >= _CHUNK_BASE:
        value, low = divmod(value, _CHUNK_BASE)
        chunks.append(str(low).rjust(_CHUNK, "0"))
    chunks.append(str(value))
    return "".join(reversed(chunks))
