# coding: utf-8
"""
(en) Generates spec/vectors/*_generated.json and verifies *_manual.json.
The expected values are computed only with Python's standard library
(fractions.Fraction, decimal.Decimal formatting), independently of the
simple_portable_numeric implementations.
Run: python3 -I spec/tools/generate_vectors.py

(ja) spec/vectors/*_generated.json を生成し、*_manual.json を検算します。
期待値は Python 標準ライブラリ（fractions.Fraction と decimal.Decimal の書式化）のみで計算し、
simple_portable_numeric の実装とは独立しています。
"""
import decimal
import json
import math
import random
import sys
from fractions import Fraction
from pathlib import Path

VECTOR_DIR = Path(__file__).resolve().parent.parent / "vectors"
MODES = ["halfEven", "halfUp", "down", "floor", "ceiling"]
SEED = 20261114
CASES_PER_OP = 300

sys.set_int_max_str_digits(0)


# ---------- oracle ----------

def oracle_round(x: Fraction, mode: str) -> int:
    """Rounds an exact Fraction to an int by the spec's rounding mode."""
    lo = math.floor(x)
    frac = x - lo
    if frac == 0:
        return lo
    if mode == "floor":
        return lo
    if mode == "ceiling":
        return lo + 1
    if mode == "down":
        return lo if x > 0 else lo + 1
    half = Fraction(1, 2)
    if frac < half:
        return lo
    if frac > half:
        return lo + 1
    if mode == "halfUp":
        return lo + 1 if x > 0 else lo
    return lo if lo % 2 == 0 else lo + 1


def dec_value(s: str) -> tuple[Fraction, int]:
    """Returns (exact value, scale) of a decimal string."""
    scale = len(s.split(".")[1]) if "." in s else 0
    return Fraction(s), scale


def dec_format(value: Fraction, scale: int) -> str:
    """Formats an exact value that has at most `scale` fractional digits."""
    unscaled = value * 10 ** scale
    assert unscaled.denominator == 1
    ctx = decimal.Context(prec=decimal.MAX_PREC, Emax=decimal.MAX_EMAX, Emin=decimal.MIN_EMIN)
    text = format(ctx.scaleb(decimal.Decimal(unscaled.numerator), -scale), "f")
    return text[1:] if text.startswith("-") and unscaled == 0 else text


def float_repr(x: Fraction) -> str:
    try:
        f = float(x)
        return "0.0" if f == 0 else repr(f)  # sign of zero is not specified
    except OverflowError:
        return "inf" if x > 0 else "-inf"


def decimal_expected(case: dict):
    op = case["op"]
    a, sa = dec_value(case["a"])
    if op == "parse":
        return dec_format(a, sa)
    if op == "neg":
        return dec_format(-a, sa)
    if op == "abs":
        return dec_format(abs(a), sa)
    if op == "toRational":
        return str(a)
    if op == "toDouble":
        return float_repr(a)
    if op == "setScale":
        return dec_format(Fraction(oracle_round(a * 10 ** case["scale"], case["rounding"]), 10 ** case["scale"]),
                          case["scale"])
    b, sb = dec_value(case["b"])
    if op == "add":
        return dec_format(a + b, max(sa, sb))
    if op == "sub":
        return dec_format(a - b, max(sa, sb))
    if op == "mul":
        return dec_format(a * b, sa + sb)
    if op == "compare":
        return (a > b) - (a < b)
    if op == "equals":
        return a == b
    if op == "divide":
        q = oracle_round(a / b * 10 ** case["scale"], case["rounding"])
        return dec_format(Fraction(q, 10 ** case["scale"]), case["scale"])
    raise ValueError(op)


def rational_expected(case: dict):
    op = case["op"]
    a = Fraction(case["a"])
    if op == "parse":
        return str(a)
    if op == "neg":
        return str(-a)
    if op == "abs":
        return str(abs(a))
    if op == "toDouble":
        return float_repr(a)
    if op == "toDecimal":
        q = oracle_round(a * 10 ** case["scale"], case["rounding"])
        return dec_format(Fraction(q, 10 ** case["scale"]), case["scale"])
    b = Fraction(case["b"])
    if op == "add":
        return str(a + b)
    if op == "sub":
        return str(a - b)
    if op == "mul":
        return str(a * b)
    if op == "div":
        return str(a / b)
    if op == "compare":
        return (a > b) - (a < b)
    if op == "equals":
        return a == b
    raise ValueError(op)


# ---------- random inputs ----------

def rand_digits(rng: random.Random, max_len: int) -> str:
    return "".join(rng.choice("0123456789") for _ in range(rng.randint(1, max_len)))


def rand_decimal(rng: random.Random) -> str:
    kind = rng.random()
    max_len = 60 if kind < 0.15 else 12
    sign = rng.choice(["", "", "-", "+"])
    text = sign + rand_digits(rng, max_len)
    if rng.random() < 0.7:
        text += "." + rand_digits(rng, 25 if kind < 0.15 else 6)
    return text


def rand_tie_decimal(rng: random.Random) -> str:
    """A decimal ending in 5, to exercise ties when the last digit is dropped."""
    return rng.choice(["", "-"]) + rand_digits(rng, 4) + "." + rand_digits(rng, 3) + "5"


def rand_rational(rng: random.Random) -> str:
    sign = rng.choice(["", "", "-", "+"])
    big = rng.random() < 0.15
    n = rand_digits(rng, 40 if big else 6)
    if rng.random() < 0.2:
        return sign + n
    d = str(rng.randint(1, 10 ** (40 if big else 6)))
    return f"{sign}{n}/{d}"


def double_edge_strings() -> list[str]:
    """Exact decimal strings around double boundaries (subnormal, max, ties)."""
    ctx = decimal.Context(prec=decimal.MAX_PREC, Emax=decimal.MAX_EMAX, Emin=decimal.MIN_EMIN)
    values = []
    min_sub = Fraction(2) ** -1074
    max_d = Fraction(2) ** 1024 - Fraction(2) ** 971
    for v in [min_sub, min_sub / 2, min_sub * Fraction(3, 2), min_sub * Fraction(5, 2),
              min_sub / 2 + Fraction(1, 10 ** 400), Fraction(2) ** -1022, Fraction(2) ** -1022 - min_sub / 2,
              max_d, max_d + Fraction(2) ** 969, max_d + Fraction(2) ** 970 - 1, max_d + Fraction(2) ** 970,
              Fraction(2 ** 53 + 1), Fraction(2 ** 53 + 3), 1 + Fraction(1, 2 ** 53), 1 + Fraction(3, 2 ** 53)]:
        assert 10 ** 1100 % v.denominator == 0
        unscaled = v * 10 ** 1100
        text = format(ctx.scaleb(decimal.Decimal(unscaled.numerator), -1100), "f").rstrip("0")
        values.append(text.rstrip(".") if text.endswith(".") else text)
    return values


def build_decimal(rng: random.Random) -> list[dict]:
    cases = []
    for _ in range(CASES_PER_OP):
        cases.append({"op": "parse", "a": rand_decimal(rng)})
        for op in ["add", "sub", "mul", "compare", "equals"]:
            cases.append({"op": op, "a": rand_decimal(rng), "b": rand_decimal(rng)})
        a = rand_decimal(rng)
        cases.append({"op": "equals", "a": a, "b": a + ("0" if "." in a else ".000")})
        cases.append({"op": rng.choice(["neg", "abs", "toRational", "toDouble"]), "a": rand_decimal(rng)})
        b = rand_decimal(rng)
        if Fraction(b) != 0:
            cases.append({"op": "divide", "a": rand_decimal(rng), "b": b, "scale": rng.randint(0, 30),
                          "rounding": rng.choice(MODES)})
        cases.append({"op": "setScale", "a": rand_decimal(rng), "scale": rng.randint(0, 8),
                      "rounding": rng.choice(MODES)})
        t = rand_tie_decimal(rng)
        cases.append({"op": "setScale", "a": t, "scale": 3, "rounding": rng.choice(MODES)})
    for s in double_edge_strings():
        cases.append({"op": "toDouble", "a": s})
        cases.append({"op": "toDouble", "a": "-" + s})
    return cases


def build_rational(rng: random.Random) -> list[dict]:
    cases = []
    for _ in range(CASES_PER_OP):
        cases.append({"op": "parse", "a": rng.choice([rand_rational(rng), rand_decimal(rng)])})
        for op in ["add", "sub", "mul", "compare", "equals"]:
            cases.append({"op": op, "a": rand_rational(rng), "b": rand_rational(rng)})
        b = rand_rational(rng)
        if Fraction(b) != 0:
            cases.append({"op": "div", "a": rand_rational(rng), "b": b})
        cases.append({"op": rng.choice(["neg", "abs", "toDouble"]), "a": rand_rational(rng)})
        cases.append({"op": "toDecimal", "a": rand_rational(rng), "scale": rng.randint(0, 30),
                      "rounding": rng.choice(MODES)})
        k = rng.randint(1, 999)
        cases.append({"op": "toDecimal", "a": f"{rng.choice(['', '-'])}{2 * k + 1}/2", "scale": 0,
                      "rounding": rng.choice(MODES)})
        cases.append({"op": "toDouble", "a": rand_wide_rational(rng)})
    return cases


def rand_wide_rational(rng: random.Random) -> str:
    """A rational whose magnitude spans the subnormal, normal and overflow ranges."""
    n = rng.getrandbits(rng.randint(1, 120)) + 1
    d = rng.getrandbits(rng.randint(1, 120)) + 1
    k = rng.randint(-1130, 1080)
    if k >= 0:
        n <<= k
    else:
        d <<= -k
    return f"{rng.choice(['', '-'])}{n}/{d}"


def write(name: str, cases: list[dict], expected_fn) -> None:
    for case in cases:
        case["expected"] = expected_fn(case)
    path = VECTOR_DIR / name
    with path.open("w", encoding="utf-8") as f:
        f.write("[\n" + ",\n".join("  " + json.dumps(c, ensure_ascii=False) for c in cases) + "\n]\n")
    print(f"wrote {len(cases)} cases to {path.name}")


def verify_manual(name: str, expected_fn) -> int:
    cases = json.loads((VECTOR_DIR / name).read_text(encoding="utf-8"))
    bad = 0
    for case in cases:
        if "error" in case:
            continue
        got = expected_fn(case)
        if got != case["expected"]:
            bad += 1
            print(f"MISMATCH {name}: {case} oracle={got!r}")
    print(f"verified {name}: {len(cases)} cases, {bad} mismatches")
    return bad


def main() -> None:
    bad = verify_manual("decimal_manual.json", decimal_expected)
    bad += verify_manual("rational_manual.json", rational_expected)
    rng = random.Random(SEED)
    write("decimal_generated.json", build_decimal(rng), decimal_expected)
    write("rational_generated.json", build_rational(rng), rational_expected)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
