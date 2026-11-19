# coding: utf-8
from enum import Enum


class EnumRoundingMode(Enum):
    """
    (en) Rounding modes used when an exact value must be reduced to fewer digits.
    The member names and behavior are identical to the Dart version.

    (ja) 正確な値を少ない桁数に丸める際の丸めモードです。
    メンバー名と動作はDart版と同一です。
    """
    halfEven = "halfEven"  # Nearest, ties to even (banker's rounding).
    halfUp = "halfUp"  # Nearest, ties away from zero.
    down = "down"  # Toward zero.
    floor = "floor"  # Toward negative infinity.
    ceiling = "ceiling"  # Toward positive infinity.
    up = "up"  # Away from zero.
