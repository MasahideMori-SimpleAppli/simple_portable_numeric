## 0.1.0

* Added `PortableDecimal.parse_lenient` (exponent notation such as `"1.2E-05"`, `".5"`, `"1."`).
* Added `pow` / `**`, `is_integer` and `to_int` to both types, and `strip_trailing_zeros` to `PortableDecimal`.
* Added `PortableRational.to_decimal_exact`.
* Added the rounding mode `EnumRoundingMode.up`.
* Spec version 2. Existing results do not change.

## 0.0.1

* Initial release.
