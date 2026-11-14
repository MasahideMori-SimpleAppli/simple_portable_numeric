# simple_portable_numeric

(en)Japanese ver
is here ([Dart](https://github.com/MasahideMori-SimpleAppli/simple_portable_numeric/blob/main/dart/README_JA.md) / [Python](https://github.com/MasahideMori-SimpleAppli/simple_portable_numeric/blob/main/python/README_JA.md)).  
(ja)
この解説の日本語版はこちら（[Dart](https://github.com/MasahideMori-SimpleAppli/simple_portable_numeric/blob/main/dart/README_JA.md) / [Python](https://github.com/MasahideMori-SimpleAppli/simple_portable_numeric/blob/main/python/README_JA.md)）にあります。

## Overview

**Arbitrary-precision decimal and rational arithmetic that gives identical results in Dart and Python.**

This repository contains both language versions and the shared specification.
For usage, see the README of each language version.

| Language | Directory | Package |
|---|---|---|
| Dart | [dart/](dart/) | https://pub.dev/packages/simple_portable_numeric |
| Python | [python/](python/) | https://pypi.org/project/simple-portable-numeric/ |

## Repository structure

| Path | Contents |
|---|---|
| [spec/SPEC.md](spec/SPEC.md) | The specification shared by both versions ([Japanese](spec/SPEC_JA.md)) |
| [spec/vectors/](spec/vectors/) | Shared test vectors. Both versions are tested against the same cases |
| [spec/tools/generate_vectors.py](spec/tools/generate_vectors.py) | Generates the vectors using only Python's standard `fractions.Fraction`, independently of the implementations |
| [dart/](dart/) | Dart version |
| [python/](python/) | Python version |

Both packages always share the same version number.
The same version gives the same results in both languages.

## Development

```bash
# Regenerate / verify the shared test vectors (standard library only)
python3 -I spec/tools/generate_vectors.py

# Dart
cd dart && dart pub get && dart test

# Python
cd python && python3 -m venv .venv && .venv/bin/pip install pytest -e . && .venv/bin/python -m pytest
```

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
