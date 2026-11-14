# simple_portable_numeric Specification

(en)Japanese ver is [here](SPEC_JA.md).  
(ja)この仕様書の日本語版は[ここ](SPEC_JA.md)にあります。

Spec version: 1 (applies to package version 0.x and later until revised)

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

Only ASCII characters are accepted. No whitespace, no exponent, no `_`,
no non-ASCII digits.

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

Examples (x -> result):

| x | halfEven | halfUp | down | floor | ceiling |
|---|---|---|---|---|---|
| 2.5 | 2 | 3 | 2 | 2 | 3 |
| -2.5 | -2 | -3 | -2 | -3 | -2 |
| 1.4 | 1 | 1 | 1 | 1 | 2 |
| -1.6 | -2 | -2 | -1 | -2 | -1 |

## 5. PortableDecimal operations

| Operation | Result scale | Notes |
|---|---|---|
| `a + b`, `a - b` | `max(a.scale, b.scale)` | exact |
| `a * b` | `a.scale + b.scale` | exact |
| `-a`, `abs(a)` | `a.scale` | exact |
| `a.divide(b, scale, rounding)` | `scale` | exact quotient rounded once with `rounding` |
| `a.setScale(scale, rounding)` | `scale` | exact when increasing scale; rounded once when decreasing |
| `a.toRational()` | - | exact |
| `a.toDouble()` | - | see section 7 |

- `divide` with `b == 0` is a division-by-zero error.
- `/` is NOT defined for `PortableDecimal`.
- Operands must both be `PortableDecimal` (no implicit mixing with int / double / rational).

## 6. PortableRational operations

| Operation | Notes |
|---|---|
| `a + b`, `a - b`, `a * b`, `a / b` | exact, result in canonical form |
| `-a`, `abs(a)` | exact |
| `a.toDecimal(scale, rounding)` | exact value rounded once to `scale` digits |
| `a.toDouble()` | see section 7 |

- `a / b` with `b == 0` is a division-by-zero error.
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
| Invalid argument (e.g. negative scale) | `ArgumentError` | `ValueError` |
| Wrong operand type | compile-time error | `TypeError` |

## 9. Test vectors

`spec/vectors/*.json` contain cases of the form:

```json
{"op": "add", "a": "1.50", "b": "2.3", "expected": "3.80"}
{"op": "divide", "a": "1", "b": "3", "scale": 5, "rounding": "halfEven", "expected": "0.33333"}
{"op": "parse", "a": "1.", "error": "format"}
```

- `expected` is the result's `toString()` (decimal / rational results),
  an integer `-1/0/1` (`compare`), a boolean (`equals`),
  or the shortest round-trip repr of the double (`toDouble`; `"inf"` / `"-inf"` for infinities).
- `error` is one of `format`, `zeroDivision`, `argument`.
- `*_manual.json` are hand-written edge cases.
  `*_generated.json` are produced by `spec/tools/generate_vectors.py`, which uses
  Python's standard `fractions.Fraction` as an independent oracle (not the implementations).
