# coding: utf-8
"""Python-specific behavior not covered by the shared vectors."""
import pytest

from simple_portable_numeric import EnumRoundingMode, PortableDecimal, PortableRational

D = PortableDecimal.parse
R = PortableRational.parse


def test_decimal_constructor_and_properties():
    d = PortableDecimal(-1234, 2)
    assert d.unscaled_value == -1234
    assert d.scale == 2
    assert str(d) == "-12.34"
    assert repr(d) == "PortableDecimal('-12.34')"
    assert PortableDecimal(5).to_string() == "5"


def test_decimal_constructor_rejects_invalid():
    with pytest.raises(ValueError):
        PortableDecimal(1, -1)
    with pytest.raises(TypeError):
        PortableDecimal(1.5, 0)
    with pytest.raises(TypeError):
        PortableDecimal(True, 0)
    with pytest.raises(TypeError):
        PortableDecimal(1, 1.0)
    with pytest.raises(TypeError):
        PortableDecimal.parse(1)


def test_rational_constructor_and_properties():
    r = PortableRational(4, -6)
    assert r.numerator == -2
    assert r.denominator == 3
    assert repr(r) == "PortableRational('-2/3')"
    with pytest.raises(ZeroDivisionError):
        PortableRational(1, 0)
    with pytest.raises(TypeError):
        PortableRational(1, False)


def test_hash_consistent_with_equality():
    assert hash(D("1.5")) == hash(D("1.50")) == hash(D("1.500"))
    assert hash(D("0")) == hash(D("-0.00"))
    assert hash(D("100")) == hash(D("100.0"))
    assert len({D("1.5"), D("1.50"), D("2")}) == 2
    assert hash(R("2/4")) == hash(R("0.5"))


def test_comparison_operators():
    assert D("1.49") < D("1.5") <= D("1.50") < D("2")
    assert D("2") > D("1.99") >= D("1.990")
    assert R("1/3") < R("1/2") <= R("2/4")
    assert R("1") > R("2/3") >= R("4/6")
    assert sorted([D("0.3"), D("-1"), D("0.25")]) == [D("-1"), D("0.25"), D("0.3")]


def test_no_implicit_mixing():
    assert D("1") != R("1")
    assert R("1") != D("1")
    assert D("1") != 1
    assert R("1") != 1
    for bad in (lambda: D("1") + 1, lambda: D("1") + R("1"), lambda: D("1") * 1.5,
                lambda: R("1") + 1, lambda: R("1") / D("1"), lambda: D("1") < 1,
                lambda: D("1") / D("1"), lambda: D("1").compare_to(R("1")),
                lambda: D("1").divide(R("1"), 2, EnumRoundingMode.halfEven)):
        with pytest.raises(TypeError):
            bad()


def test_immutability_of_results():
    a = D("1.5")
    b = a + D("1")
    assert a.to_string() == "1.5"
    assert b.to_string() == "2.5"


def test_huge_digit_strings_beyond_python_int_limit():
    digits = "1234567890" * 1000  # 10000 digits, over the default 4300 limit
    d = D(digits + "." + digits)
    assert d.to_string() == digits + "." + digits
    r = R(digits + "/7")
    assert r.to_string().endswith("/7") or r.denominator == 1
    assert R(digits).to_string() == digits
    assert (d * D("10")).to_string() == digits + digits[0] + "." + digits[1:] + "0"


def test_rounding_mode_values_match_dart_names():
    assert [m.value for m in EnumRoundingMode] == ["halfEven", "halfUp", "down", "floor", "ceiling", "up"]
    assert [m.name for m in EnumRoundingMode] == ["halfEven", "halfUp", "down", "floor", "ceiling", "up"]


def test_to_rational_round_trip():
    for s in ["0.125", "-3.50", "0", "123456789.987654321"]:
        assert D(s).to_rational().to_decimal(D(s).scale, EnumRoundingMode.halfEven) == D(s)


def test_pow_operator():
    assert D("1.5") ** 2 == D("2.25")
    assert (D("1.5") ** 2).scale == 2
    assert R("2/3") ** -2 == R("9/4")
    with pytest.raises(TypeError):
        D("2") ** D("2")
    with pytest.raises(TypeError):
        D("2") ** True
    with pytest.raises(TypeError):
        pow(D("2"), 2, 5)
    with pytest.raises(TypeError):
        pow(R("2"), 2, 5)
    with pytest.raises(TypeError):
        D("2").pow(2.0)
    with pytest.raises(ValueError):
        D("2") ** -1


def test_new_methods_return_documented_types():
    assert type(D("2.5").to_int(EnumRoundingMode.up)) is int
    assert R("-5/2").to_int(EnumRoundingMode.up) == -3
    assert D("1.00").is_integer() is True
    assert R("3/8").to_decimal_exact() == D("0.375")
    with pytest.raises(ValueError):
        R("1/3").to_decimal_exact()
    with pytest.raises(TypeError):
        PortableDecimal.parse_lenient(1.5)


def test_strip_trailing_zeros_keeps_equality_and_hash():
    for s in ["1.500", "-0.000", "100.00", "0.0100"]:
        assert D(s).strip_trailing_zeros() == D(s)
        assert hash(D(s).strip_trailing_zeros()) == hash(D(s))


def test_parse_lenient_reads_repr_back_to_the_same_float():
    for x in [0.1, 1e-7, 1.5e300, 5e-324, 1.7976931348623157e308, 1e16, 1e21, -2.2250738585072014e-308, 123456.789]:
        assert PortableDecimal.parse_lenient(repr(x)).to_float() == x


def test_parse_lenient_with_huge_mantissa_and_exponent():
    digits = "1234567890" * 1000
    d = PortableDecimal.parse_lenient(digits + "." + digits + "e-324")
    assert d.scale == len(digits) + 324
    assert d.to_string() == digits[:-324] + "." + digits[-324:] + digits
    with pytest.raises(ValueError):
        PortableDecimal.parse_lenient("1e" + "0" * 5000 + "325")
