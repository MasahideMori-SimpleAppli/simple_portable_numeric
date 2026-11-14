# coding: utf-8
"""Runs the shared test vectors in spec/vectors against the Python implementation."""
import json
from pathlib import Path

import pytest

from simple_portable_numeric import EnumRoundingMode, PortableDecimal, PortableRational

VECTOR_DIR = Path(__file__).resolve().parents[2] / "spec" / "vectors"
ERRORS = {"format": ValueError, "zeroDivision": ZeroDivisionError, "argument": ValueError}


def _load(name: str) -> list[dict]:
    return json.loads((VECTOR_DIR / name).read_text(encoding="utf-8"))


def _float_text(x: float) -> str:
    return repr(x).replace("-0.0", "0.0") if x == 0 else repr(x)


def _run_decimal(c: dict):
    D = PortableDecimal.parse
    op = c["op"]
    a = D(c["a"])
    if op == "parse":
        return a.to_string()
    if op == "neg":
        return (-a).to_string()
    if op == "abs":
        return abs(a).to_string()
    if op == "toRational":
        return a.to_rational().to_string()
    if op == "toDouble":
        return _float_text(a.to_float())
    if op == "setScale":
        return a.set_scale(c["scale"], EnumRoundingMode(c["rounding"])).to_string()
    b = D(c["b"])
    if op == "add":
        return (a + b).to_string()
    if op == "sub":
        return (a - b).to_string()
    if op == "mul":
        return (a * b).to_string()
    if op == "compare":
        return a.compare_to(b)
    if op == "equals":
        return a == b
    if op == "divide":
        return a.divide(b, c["scale"], EnumRoundingMode(c["rounding"])).to_string()
    raise ValueError(op)


def _run_rational(c: dict):
    R = PortableRational.parse
    op = c["op"]
    a = R(c["a"])
    if op == "parse":
        return a.to_string()
    if op == "neg":
        return (-a).to_string()
    if op == "abs":
        return abs(a).to_string()
    if op == "toDouble":
        return _float_text(a.to_float())
    if op == "toDecimal":
        return a.to_decimal(c["scale"], EnumRoundingMode(c["rounding"])).to_string()
    b = R(c["b"])
    if op == "add":
        return (a + b).to_string()
    if op == "sub":
        return (a - b).to_string()
    if op == "mul":
        return (a * b).to_string()
    if op == "div":
        return (a / b).to_string()
    if op == "compare":
        return a.compare_to(b)
    if op == "equals":
        return a == b
    raise ValueError(op)


def _check(run, case: dict) -> None:
    if "error" in case:
        with pytest.raises(ERRORS[case["error"]]):
            run(case)
    else:
        assert run(case) == case["expected"]


@pytest.mark.parametrize("name", ["decimal_manual.json", "decimal_generated.json"])
def test_decimal_vectors(name):
    for case in _load(name):
        try:
            _check(_run_decimal, case)
        except AssertionError as e:
            raise AssertionError(f"{case}") from e


@pytest.mark.parametrize("name", ["rational_manual.json", "rational_generated.json"])
def test_rational_vectors(name):
    for case in _load(name):
        try:
            _check(_run_rational, case)
        except AssertionError as e:
            raise AssertionError(f"{case}") from e
