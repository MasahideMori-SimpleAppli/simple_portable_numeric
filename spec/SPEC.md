# simple_portable_numeric Specification

(en)Japanese ver is [here](SPEC_JA.md).  
(ja)この仕様書の日本語版は[ここ](SPEC_JA.md)にあります。

Spec version: 2 (applies to package version 0.1.0 and later until revised)

This document defines the behavior shared by the Dart and Python implementations.
Both implementations MUST produce identical results for every operation defined here.
The shared test vectors in `spec/vectors/` are the executable form of this spec.

## 1. Types

| Type | Dart | Python |
|---|---|---|
| Decimal | `PortableDecimal` | `PortableDecimal` |
| Rational | `PortableRational` | `PortableRational` |
| Rounding mode | `EnumRoundingMode` | `EnumRoundingMode` |

Arithmetic is implemented on arbitrary-precision integers only
(Dart `BigInt`, Python `int`). Platform decimal / fraction libraries
(e.g. Python `decimal`, `fractions`) are NOT used by the implementations.

### 1.1 PortableDecimal

A decimal is the pair `(unscaledValue, scale)` and represents `unscaledValue * 10^(-scale)`.

- `unscaledValue`: arbitrary-precision integer.
- `scale`: integer, `scale >= 0`. A negative scale is an argument error.

### 1.2 PortableRational

A rational is the pair `(numerator, denominator)`, always stored in canonical form:

- `gcd(|numerator|, denominator) == 1`
- `denominator > 0`
- zero is `0/1`

A zero denominator is a division-by-zero error.

## 2. String format

Only ASCII characters are accepted. No whitespace, no `_`, no non-ASCII digits.
Exponent notation is accepted only by `parseLenient` (2.5).

### 2.1 Decimal parse

Grammar: `^[+-]?[0-9]+(\.[0-9]+)?$`

- `scale` = number of digits after `.` (0 if no `.`).
- Leading zeros of the integer part are allowed (`"007.5"` -> unscaled 75, scale 1).
- Rejected examples: `""`, `"1."`, `".5"`, `"1e3"`, `" 1"`, `"1,000"`, `"NaN"`, `"Infinity"`.

### 2.2 Decimal toString

- Plain notation, never exponent notation.
- Exactly `scale` digits after `.`; no `.` when `scale == 0`.
- Integer part has no leading zeros (at least one digit).
- `-` only when the value is negative. Negative zero does not exist (`"-0.00"` -> `"0.00"`).
- No `+` sign.

Examples (parse then toString): `"1.50"` -> `"1.50"`, `"-0.0"` -> `"0.0"`, `"+007"` -> `"7"`.

### 2.3 Rational parse

Accepted forms:

- Fraction: `^[+-]?[0-9]+/[0-9]+$` (sign only at the front; denominator must not be zero)
- Integer: `^[+-]?[0-9]+$`
- Decimal: `^[+-]?[0-9]+\.[0-9]+$` (converted exactly, e.g. `"0.75"` -> `3/4`)

The result is reduced to canonical form (`"4/6"` -> `2/3`, `"-0/5"` -> `0`).

### 2.4 Rational toString

- `"n"` when `denominator == 1`, otherwise `"n/d"`.
- `-` only on the numerator. No `+` sign.

### 2.5 Decimal lenient parse (parseLenient)

Python: `parse_lenient`.
Accepts exponent notation and an omitted integer or fractional part, which `parse` rejects.
What `parse` accepts does not change.

Grammar: `^[+-]?([0-9]+(\.[0-9]*)?|\.[0-9]+)([eE][+-]?[0-9]+)?$`

- Let `I` be the integer-part digits and `F` the fraction digits (may be empty) of the mantissa.
  `m = int(I + F)` (only `F` if `I` is empty), `f = len(F)`.
- Let `e` be the exponent value (0 if there is no exponent). Leading zeros in the exponent are allowed (`"E-05"`).
- `|e| > 324` is an invalid string. The limit covers the double range (smallest subnormal about `4.9e-324`)
  and prevents excessive computation from huge exponents.
- Result: `(m, f - e)` if `f - e >= 0`, otherwise `(m * 10^(e - f), 0)`.
  That is, the scale is `max(0, f - e)`.
- A string without exponent that `parse` also accepts gives the same result as `parse`.
- Rejected examples: `""`, `"."`, `"e5"`, `"1e"`, `"1e+"`, `" 1"`, `"1,000"`, `"1_000"`,
  `"12%"`, `"NaN"`, `"Infinity"`, `"1e325"`, `"1e-325"`.

Examples (parse then toString):

| Input | Result |
|---|---|
| `"1.2E-05"` | `"0.000012"` |
| `"1.2E+05"` | `"120000"` |
| `"1.50e1"` | `"15.0"` |
| `".5"` | `"0.5"` |
| `"1."` | `"1"` |
| `"1.e2"` | `"100"` |
| `"-0e-3"` | `"0.000"` |
| `"5e-324"` | `"0.` + 323 zeros + `5"` |

Note: the string form of a double differs between languages and runtimes
(e.g. `1e16` is `"10000000000000000.0"` in Dart and `"1e+16"` in Python).
Parsing such strings gives equal values, but the scale may differ.

## 3. Equality, ordering, hashing

- Equality is by numeric value: `PortableDecimal.parse("1.50") == PortableDecimal.parse("1.5")`.
- A `PortableDecimal` and a `PortableRational` are never equal to each other
  (no implicit cross-type comparison). Convert explicitly first.
- Ordering (`compareTo` / `<` etc.) is by numeric value, same type only.
- Hash codes are consistent with equality within one language.
  Hash values are NOT required to match across languages.

## 4. Rounding modes

Rounding converts an exact rational value `x` to an integer.

| Mode | Rule |
|---|---|
| `halfEven` | Nearest integer; ties go to the even integer (banker's rounding). |
| `halfUp` | Nearest integer; ties go away from zero. |
| `down` | Toward zero (truncate). |
| `floor` | Toward negative infinity. |
| `ceiling` | Toward positive infinity. |
| `up` | Away from zero. |

Examples (x -> result):

| x | halfEven | halfUp | down | floor | ceiling | up |
|---|---|---|---|---|---|---|
| 2.5 | 2 | 3 | 2 | 2 | 3 | 3 |
| -2.5 | -2 | -3 | -2 | -3 | -2 | -3 |
| 1.4 | 1 | 1 | 1 | 1 | 2 | 2 |
| -1.6 | -2 | -2 | -1 | -2 | -1 | -2 |
| 3 | 3 | 3 | 3 | 3 | 3 | 3 |

`up` is appended after the existing members (the order of existing members does not change).

## 5. PortableDecimal operations

| Operation | Result scale | Notes |
|---|---|---|
| `a + b`, `a - b` | `max(a.scale, b.scale)` | exact |
| `a * b` | `a.scale + b.scale` | exact |
| `-a`, `abs(a)` | `a.scale` | exact |
| `a.divide(b, scale, rounding)` | `scale` | exact quotient rounded once with `rounding` |
| `a.setScale(scale, rounding)` | `scale` | exact when increasing scale; rounded once when decreasing |
| `a.pow(n)` | `a.scale * n` | exact; `n` is an integer >= 0 |
| `a.stripTrailingZeros()` | digits without trailing zeros | exact |
| `a.isInteger` | - | true if the value is an integer |
| `a.toBigInt(rounding)` | - | exact value rounded once to an integer |
| `a.toRational()` | - | exact |
| `a.toDouble()` | - | see section 7 |

- `divide` with `b == 0` is a division-by-zero error.
- `pow`: `n < 0` is an argument error (the result may not be a finite decimal; use `a.toRational().pow(n)` if needed).
  `a.pow(0)` is the value 1 with scale 0 (also when `a` is zero). There is no limit on the size of `n`.
- `stripTrailingZeros`: removes trailing zeros of the fractional part. The scale never goes below 0
  (`"1.500"` -> `"1.5"`, `"0.000"` -> `"0"`, `"100"` -> `"100"`).
- `isInteger`: true if `unscaledValue` is divisible by `10^scale` (`"1.00"` is true).
- `toBigInt`: the result is an arbitrary-precision integer (Dart `BigInt`, Python `int`), equal to `setScale(0, rounding)`.
- `/` is NOT defined for `PortableDecimal`.
- Operands must both be `PortableDecimal` (no implicit mixing with int / double / rational).

## 6. PortableRational operations

| Operation | Notes |
|---|---|
| `a + b`, `a - b`, `a * b`, `a / b` | exact, result in canonical form |
| `-a`, `abs(a)` | exact |
| `a.pow(n)` | exact; `n` is any integer; result in canonical form |
| `a.isInteger` | true if the denominator is 1 |
| `a.toBigInt(rounding)` | exact value rounded once to an integer |
| `a.toDecimal(scale, rounding)` | exact value rounded once to `scale` digits |
| `a.toDecimalExact()` | exact conversion to a finite decimal |
| `a.toDouble()` | see section 7 |

- `a / b` with `b == 0` is a division-by-zero error.
- `pow`: `n < 0` means `(1/a)^|n|`. Zero with `n < 0` is a division-by-zero error.
  `a.pow(0)` is `1` (also when `a` is zero). There is no limit on the size of `n`.
- `toDecimalExact`: if the denominator has no prime factors other than 2 and 5 (`2^p * 5^q`),
  returns the decimal with scale `max(p, q)` (`"3/8"` -> `"0.375"`, `"5"` -> `"5"`, `"-1/20"` -> `"-0.05"`).
  Otherwise (e.g. `"1/3"`) it is an argument error.
- Operands must both be `PortableRational`.

## 7. Conversion to IEEE 754 double

`toDouble()` (Python: `to_float()`) returns the IEEE 754 binary64 value nearest to the exact
value, ties to even (correct rounding, including subnormals).
Values beyond the finite range return `+Infinity` / `-Infinity`.
Values smaller than half of the smallest subnormal round to `0.0` (sign of zero is not specified).

Conversion FROM double is not provided in spec version 1.

## 8. Errors

| Error kind | Dart | Python |
|---|---|---|
| Invalid string | `FormatException` | `ValueError` |
| Division by zero | `UnsupportedError` | `ZeroDivisionError` |
| Invalid argument (e.g. negative scale, negative exponent of `PortableDecimal.pow`, non-finite decimal in `toDecimalExact`) | `ArgumentError` | `ValueError` |
| Wrong operand type | compile-time error | `TypeError` |

## 9. Names per language

| Operation | Dart | Python |
|---|---|---|
| Lenient parse | `PortableDecimal.parseLenient(text)` | `PortableDecimal.parse_lenient(text)` |
| Integer power | `a.pow(n)` | `a.pow(n)`, `a ** n` |
| Strip trailing zeros | `a.stripTrailingZeros()` | `a.strip_trailing_zeros()` |
| Integer check | `a.isInteger` (getter) | `a.is_integer()` |
| Round to integer | `a.toBigInt(rounding)` | `a.to_int(rounding)` |
| Exact finite decimal | `a.toDecimalExact()` | `a.to_decimal_exact()` |
| Rounding mode | `EnumRoundingMode.up` | `EnumRoundingMode.up` |

Python `**` is defined only for an `int` right operand (3-argument `pow(a, n, mod)` is a `TypeError`).

## 10. Test vectors

`spec/vectors/*.json` contain cases of the form:

```json
{"op": "add", "a": "1.50", "b": "2.3", "expected": "3.80"}
{"op": "divide", "a": "1", "b": "3", "scale": 5, "rounding": "halfEven", "expected": "0.33333"}
{"op": "parse", "a": "1.", "error": "format"}
```

- `expected` is the result's `toString()` (decimal / rational results),
  an integer `-1/0/1` (`compare`), a boolean (`equals`),
  or the shortest round-trip repr of the double (`toDouble`; `"inf"` / `"-inf"` for infinities).
- The `op` names added in spec version 2 are `parseLenient`, `pow`, `stripTrailingZeros`, `isInteger`, `toBigInt`, `toDecimalExact`.
  `expected` of `isInteger` is a boolean, and of `toBigInt` is the integer as a decimal string.
- `error` is one of `format`, `zeroDivision`, `argument`.
- `*_manual.json` are hand-written edge cases.
  `*_generated.json` are produced by `spec/tools/generate_vectors.py`, which uses
  Python's standard `fractions.Fraction` as an independent oracle (not the implementations).
