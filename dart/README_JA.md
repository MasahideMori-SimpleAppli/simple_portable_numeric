# simple_portable_numeric

## 概要

**simple_portable_numeric は、DartとPythonで同一の計算結果を返す、
任意精度の10進数・有理数演算ライブラリです。**

どちらの言語版も任意精度の整数（Dartの `BigInt`、Pythonの `int`）のみで実装され、
共通の[仕様書](https://github.com/MasahideMori-SimpleAppli/simple_portable_numeric/blob/main/spec/SPEC_JA.md)に従います。
Pythonの `decimal`（デフォルトで有効桁数28桁）のような各言語の標準ライブラリは使用しないため、
桁数・丸め・文字列形式が言語間で食い違うことはありません。

## 特徴

- `PortableDecimal`：桁数の上限なしで `+ - *` を正確に計算します。
  割り算では、結果の桁数と丸めモードを必ず指定します。
- `PortableRational`：`+ - * /` を正確に計算し、常に約分された状態を保ちます。
- 5種類の丸めモード：`halfEven`、`halfUp`、`down`、`floor`、`ceiling`。
- 厳密で安定した文字列形式のため、値をテキストとして（データベースなどに）保存するのに適しています。
- 等価判定は値で行い（`1.50 == 1.5`）、文字列化では桁数を保持します（`"1.50"`）。
- 倍精度浮動小数点数への変換は正しく丸められ、両言語で同一の結果になります。
- 依存パッケージはありません。
- Python版もあります。  
  → https://pypi.org/project/simple-portable-numeric/

## クイックスタート

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

## 注意事項

- 文字列は `"-12.340"` や `"3/4"` のような通常表記である必要があります。
  指数表記（`"1e3"`）、空白、ASCII以外の数字は受け付けません。
- `PortableDecimal` と `PortableRational` を混ぜた計算はできません。
  `toRational()` / `toDecimal(scale, rounding)` で明示的に変換してください。
- 倍精度浮動小数点数からの変換は提供していません。言語間で浮動小数点数の文字列表現が異なるためです。
- ハッシュ値は等価判定と整合しますが、言語間では一致しません。

## サポート

このパッケージは、オープンソースプロジェクトとして私が個人的に開発・保守しています。
バグ報告や機能リクエストについては、GitHub Issues をご利用ください。

**有料サポート、コンサルティング、カスタム開発**
（例：優先サポート、設計アドバイス、実装支援）が必要な場合は、
下記までご連絡ください。

**合同会社シンプルアプリ**
https://simpleappli.com/index.html

## バージョン管理について

それぞれ、Cの部分が変更されます。
ただし、バージョン1.0.0未満は以下のルールに関係無く計算結果や文字列形式が変化する場合があります。

- 仕様の変更により、計算結果や文字列形式が変わるような変更
    - C.X.X
- メソッドの追加など
    - X.C.X
- 軽微な変更やバグ修正
    - X.X.C

## ライセンス

このソフトウェアはApache-2.0ライセンスの元配布されます。LICENSEファイルの内容をご覧ください。

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
