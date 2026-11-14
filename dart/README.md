# simple_portable_numeric

(en)Japanese ver
is [here](https://github.com/MasahideMori-SimpleAppli/simple_portable_numeric/blob/main/dart/README_JA.md).  
(ja)
この解説の日本語版は[ここ](https://github.com/MasahideMori-SimpleAppli/simple_portable_numeric/blob/main/dart/README_JA.md)
にあります。

## Overview

**simple_portable_numeric is an arbitrary-precision decimal and rational arithmetic library
that gives identical results in Dart and Python.**

Both versions are built only on arbitrary-precision integers (Dart `BigInt`, Python `int`)
and follow one shared [specification](https://github.com/MasahideMori-SimpleAppli/simple_portable_numeric/blob/main/spec/SPEC.md).
Platform libraries such as Python's `decimal` (28 significant digits by default) are not used,
so the number of digits, rounding and string format never differ between the languages.

## Features

- `PortableDecimal`: exact `+ - *` with no digit limit.
  Division always takes an explicit scale and rounding mode.
- `PortableRational`: exact `+ - * /`, always kept reduced.
- Five rounding modes: `halfEven`, `halfUp`, `down`, `floor`, `ceiling`.
- Strict and stable string format, suitable for storing values as text (e.g. in a database).
- Equality by value (`1.50 == 1.5`), while the string keeps the scale (`"1.50"`).
- Correctly rounded conversion to double, identical in both languages.
- No dependencies.
- Python version available.  
  → https://pypi.org/project/simple-portable-numeric/

## Quick Start

```dart
import 'package:simple_portable_numeric/simple_portable_numeric.dart';

void main() {
  // Decimal
  final a = PortableDecimal.parse("1.50");
  final b = PortableDecimal.parse("2.3");
  print(a + b); // 3.80
  print(a * b); // 3.450
  print(a == PortableDecimal.parse("1.5")); // true
  print(PortableDecimal.parse("1").divide(
      PortableDecimal.parse("3"), 5, EnumRoundingMode.halfEven)); // 0.33333
  print(PortableDecimal.parse("2.5").setScale(0, EnumRoundingMode.halfEven)); // 2

  // Rational
  final r = PortableRational.parse("1/3") + PortableRational.parse("1/6");
  print(r); // 1/2
  print(r.toDecimal(2, EnumRoundingMode.halfUp)); // 0.50
  print(PortableRational.parse("0.75")); // 3/4

  // Conversion
  print(PortableDecimal.parse("0.1").toRational()); // 1/10
  print(PortableRational.parse("1/3").toDouble()); // 0.3333333333333333
}
```

## Notes

- Strings must be plain notation such as `"-12.340"` or `"3/4"`.
  Exponent notation (`"1e3"`), whitespace and non-ASCII digits are rejected.
- `PortableDecimal` and `PortableRational` are never mixed implicitly.
  Convert explicitly with `toRational()` / `toDecimal(scale, rounding)`.
- Conversion from double is not provided, because the string forms of doubles differ between languages.
- Hash values are consistent with equality, but are not the same across languages.

## Support

This package is developed and maintained by me personally as an open-source project.
For bug reports and feature requests, please use GitHub Issues.

If you need **paid support, consulting, or custom development**
(e.g. priority support, design advice, or implementation help),
please contact my company:

**SimpleAppli Inc.**
https://simpleappli.com/en/index_en.html

## About version control

The C part will be changed at the time of version upgrade.
However, versions less than 1.0.0 may change the calculation results or the string format regardless of the following rules.

- Specification changes that change the calculation results or the string format.
    - C.X.X
- Adding methods, etc.
    - X.C.X
- Minor changes and bug fixes.
    - X.X.C

## License

This software is released under the Apache-2.0 License, see LICENSE file.

Copyright 2026 Masahide Mori

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

## Trademarks

- “Dart” and “Flutter” are trademarks of Google LLC.
  *This package is not developed or endorsed by Google LLC.*

- “Python” is a trademark of the Python Software Foundation.
  *This package is not affiliated with the Python Software Foundation.*

- GitHub and the GitHub logo are trademarks of GitHub, Inc.
  *This package is not affiliated with GitHub, Inc.*
