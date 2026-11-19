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
ALL_MODES = MODES + ["up"]  # spec version 2 added "up"
SEED = 20261114
SEED_V2 = 20261119
CASES_PER_OP = 300

sys.set_int_max_str_digits(0)


# ---------- oracle ----------

class OracleError(Exception):
    """The case is expected to fail with the spec error kind in args[0]."""

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
    if mode == "up":
        return lo + 1 if x > 0 else lo
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


def min_scale(x: Fraction, limit: int = 2000) -> int:
    """Returns the smallest k >= 0 with x * 10^k an integer, or raises OracleError."""
    for k in range(limit + 1):
        if (x * 10 ** k).denominator == 1:
            return k
    raise OracleError("argument")


def lenient_value(text: str) -> tuple[Fraction, int]:
    """Returns (exact value, scale) of a parseLenient string via decimal.Decimal."""
    d = decimal.Decimal(text)
    return Fraction(d), max(0, -d.as_tuple().exponent)


def float_repr(x: Fraction) -> str:
    try:
        f = float(x)
        return "0.0" if f == 0 else repr(f)  # sign of zero is not specified
    except OverflowError:
        return "inf" if x > 0 else "-inf"


def decimal_expected(case: dict):
    op = case["op"]
    if op == "parseLenient":
        return dec_format(*lenient_value(case["a"]))
    a, sa = dec_value(case["a"])
    if op == "parse":
        return dec_format(a, sa)
    if op == "pow":
        if case["n"] < 0:
            raise OracleError("argument")
        return dec_format(a ** case["n"], sa * case["n"])
    if op == "stripTrailingZeros":
        return dec_format(a, min_scale(a))
    if op == "isInteger":
        return a.denominator == 1
    if op == "toBigInt":
        return str(oracle_round(a, case["rounding"]))
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
    if op == "pow":
        if a == 0 and case["n"] < 0:
            raise OracleError("zeroDivision")
        return str(a ** case["n"])
    if op == "isInteger":
        return a.denominator == 1
    if op == "toBigInt":
        return str(oracle_round(a, case["rounding"]))
    if op == "toDecimalExact":
        d = a.denominator
        while d % 2 == 0:
            d //= 2
        while d % 5 == 0:
            d //= 5
        if d != 1:
            raise OracleError("argument")
        return dec_format(a, min_scale(a))
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


def rand_lenient(rng: random.Random) -> str:
    """A string in the parseLenient grammar (mantissa forms, e/E, exponent up to +-324)."""
    sign = rng.choice(["", "", "-", "+"])
    i = rand_digits(rng, 8)
    f = rand_digits(rng, 8)
    mantissa = rng.choice([i, i + ".", i + "." + f, "." + f])
    if rng.random() < 0.2:
        return sign + mantissa
    e = rng.choice([rng.randint(-20, 20), rng.randint(-324, 324), rng.choice([-324, 324])])
    e_text = str(abs(e)).zfill(rng.choice([1, 2, 3]))
    e_sign = "-" if e < 0 else rng.choice(["", "+"])
    return f"{sign}{mantissa}{rng.choice('eE')}{e_sign}{e_text}"


def rand_small_decimal(rng: random.Random) -> str:
    """A decimal with few digits, for pow."""
    text = rng.choice(["", "-"]) + rand_digits(rng, 3)
    if rng.random() < 0.7:
        text += "." + rand_digits(rng, 3)
    return text


def rand_trailing_zero_decimal(rng: random.Random) -> str:
    """A decimal that often ends with zeros or has an integer value."""
    text = rng.choice(["", "-"]) + rand_digits(rng, 6)
    if rng.random() < 0.8:
        text += "." + rng.choice(["", rand_digits(rng, 4)]) + "0" * rng.randint(0, 5)
        text = text.rstrip(".") if text.endswith(".") else text
    return text


def rand_terminating_rational(rng: random.Random) -> str:
    """A rational whose denominator is 2^p 5^q, sometimes times 3, 7 or a large prime."""
    d = 2 ** rng.randint(0, 40) * 5 ** rng.randint(0, 40)
    if rng.random() < 0.25:
        d *= rng.choice([3, 7, 9, 1000003])
    return f"{rng.choice(['', '-'])}{rand_digits(rng, 20)}/{d}"


def build_decimal_v2(rng: random.Random) -> list[dict]:
    """Cases for the operations added in spec version 2."""
    cases = []
    for _ in range(CASES_PER_OP):
        cases.append({"op": "parseLenient", "a": rand_lenient(rng)})
        cases.append({"op": "pow", "a": rand_small_decimal(rng), "n": rng.randint(0, 12)})
        cases.append({"op": "stripTrailingZeros", "a": rand_trailing_zero_decimal(rng)})
        cases.append({"op": "isInteger", "a": rand_trailing_zero_decimal(rng)})
        cases.append({"op": "toBigInt", "a": rng.choice([rand_decimal(rng), rand_tie_decimal(rng)]),
                      "rounding": rng.choice(ALL_MODES)})
        cases.append({"op": "setScale", "a": rand_tie_decimal(rng), "scale": rng.randint(0, 3), "rounding": "up"})
        b = rand_decimal(rng)
        if Fraction(b) != 0:
            cases.append({"op": "divide", "a": rand_decimal(rng), "b": b, "scale": rng.randint(0, 30),
                          "rounding": "up"})
    return cases


def build_rational_v2(rng: random.Random) -> list[dict]:
    """Cases for the operations added in spec version 2."""
    cases = []
    for _ in range(CASES_PER_OP):
        a = rand_rational(rng)
        n = rng.randint(-12, 12)
        if Fraction(a) == 0 and n < 0:
            n = -n
        cases.append({"op": "pow", "a": a, "n": n})
        cases.append({"op": "isInteger", "a": rng.choice([rand_rational(rng), str(rng.randint(-99, 99) * 7) + "/7"])})
        cases.append({"op": "toBigInt", "a": rand_rational(rng), "rounding": rng.choice(ALL_MODES)})
        k = rng.randint(1, 999)
        cases.append({"op": "toBigInt", "a": f"{rng.choice(['', '-'])}{2 * k + 1}/2", "rounding": rng.choice(ALL_MODES)})
        cases.append({"op": "toDecimalExact", "a": rand_terminating_rational(rng)})
        cases.append({"op": "toDecimal", "a": rand_rational(rng), "scale": rng.randint(0, 30), "rounding": "up"})
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
        try:
            case["expected"] = expected_fn(case)
        except OracleError as e:
            case["error"] = e.args[0]
    path = VECTOR_DIR / name
    with path.open("w", encoding="utf-8") as f:
        f.write("[\n" + ",\n".join("  " + json.dumps(c, ensure_ascii=False) for c in cases) + "\n]\n")
    print(f"wrote {len(cases)} cases to {path.name}")


def verify_manual(name: str, expected_fn) -> int:
    cases = json.loads((VECTOR_DIR / name).read_text(encoding="utf-8"))
    bad = 0
    for case in cases:
        try:
            got = expected_fn(case)
        except OracleError as e:
            got = {"error": e.args[0]}
        except Exception:  # invalid input that the oracle cannot evaluate
            got = None
        if "error" in case:
            # The oracle does not check the string grammar, so only errors it detects are compared.
            if isinstance(got, dict) and got != {"error": case["error"]}:
                bad += 1
                print(f"MISMATCH {name}: {case} oracle={got!r}")
            continue
        if got != case["expected"]:
            bad += 1
            print(f"MISMATCH {name}: {case} oracle={got!r}")
    print(f"verified {name}: {len(cases)} cases, {bad} mismatches")
    return bad


def main() -> None:
    bad = verify_manual("decimal_manual.json", decimal_expected)
    bad += verify_manual("rational_manual.json", rational_expected)
    rng = random.Random(SEED)
    decimal_cases = build_decimal(rng)
    rational_cases = build_rational(rng)
    rng_v2 = random.Random(SEED_V2)
    write("decimal_generated.json", decimal_cases + build_decimal_v2(rng_v2), decimal_expected)
    write("rational_generated.json", rational_cases + build_rational_v2(rng_v2), rational_expected)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
