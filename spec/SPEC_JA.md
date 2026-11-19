# simple_portable_numeric 仕様書

この仕様書の英語版は[ここ](SPEC.md)にあります。

仕様バージョン: 2（パッケージバージョン 0.1.0 以降、改訂されるまで適用）

この文書は、Dart版とPython版で共通の動作を定義します。
両実装は、ここで定義されるすべての演算について、同一の結果を返さなければなりません。
`spec/vectors/` の共通テストベクタは、この仕様を実行可能な形で表したものです。

## 1. 型

| 型 | Dart | Python |
|---|---|---|
| 10進数 | `PortableDecimal` | `PortableDecimal` |
| 有理数 | `PortableRational` | `PortableRational` |
| 丸めモード | `EnumRoundingMode` | `EnumRoundingMode` |

演算は任意精度の整数（Dartの `BigInt`、Pythonの `int`）のみで実装します。
各言語の10進数・分数ライブラリ（例：Pythonの `decimal`、`fractions`）は実装では使用しません。

### 1.1 PortableDecimal

10進数は `(unscaledValue, scale)` の組で、`unscaledValue * 10^(-scale)` を表します。

- `unscaledValue`：任意精度の整数。
- `scale`：整数で、`scale >= 0`。負のscaleは引数エラーです。

### 1.2 PortableRational

有理数は `(numerator, denominator)`（分子、分母）の組で、常に次の正規形で保持します。

- `gcd(|numerator|, denominator) == 1`
- `denominator > 0`
- ゼロは `0/1`

分母がゼロの場合はゼロ除算エラーです。

## 2. 文字列形式

ASCII文字のみ受け付けます。空白、`_`、ASCII以外の数字は受け付けません。
指数表記は 2.5 の `parseLenient` のみが受け付けます。

### 2.1 10進数の解析（parse）

文法：`^[+-]?[0-9]+(\.[0-9]+)?$`

- `scale` は `.` の後の桁数です（`.` が無い場合は0）。
- 整数部の先頭のゼロは許容します（`"007.5"` → unscaled 75、scale 1）。
- 受け付けない例：`""`、`"1."`、`".5"`、`"1e3"`、`" 1"`、`"1,000"`、`"NaN"`、`"Infinity"`。

### 2.2 10進数の文字列化（toString）

- 通常表記のみで、指数表記は使いません。
- `.` の後はちょうど `scale` 桁です。`scale == 0` の場合は `.` を付けません。
- 整数部に先頭のゼロは付けません（最低1桁）。
- `-` は値が負の場合のみ付けます。負のゼロは存在しません（`"-0.00"` → `"0.00"`）。
- `+` は付けません。

例（解析してから文字列化）：`"1.50"` → `"1.50"`、`"-0.0"` → `"0.0"`、`"+007"` → `"7"`。

### 2.3 有理数の解析（parse）

受け付ける形式：

- 分数：`^[+-]?[0-9]+/[0-9]+$`（符号は先頭のみ。分母はゼロ不可）
- 整数：`^[+-]?[0-9]+$`
- 10進数：`^[+-]?[0-9]+\.[0-9]+$`（正確に変換。例：`"0.75"` → `3/4`）

結果は正規形に約分されます（`"4/6"` → `2/3`、`"-0/5"` → `0`）。

### 2.4 有理数の文字列化（toString）

- `denominator == 1` の場合は `"n"`、それ以外は `"n/d"`。
- `-` は分子にのみ付けます。`+` は付けません。

### 2.5 10進数の緩い解析（parseLenient）

Pythonでは `parse_lenient` です。
`parse` では受け付けない、指数表記や整数部・小数部の省略を受け付けます。
`parse` の受け付ける範囲は変わりません。

文法：`^[+-]?([0-9]+(\.[0-9]*)?|\.[0-9]+)([eE][+-]?[0-9]+)?$`

- 仮数部の整数部の数字を `I`、小数部の数字を `F`（空でもよい）とします。
  `m = int(I + F)`（`I` が空なら `F` のみ）、`f = len(F)` とします。
- 指数部の値を `e` とします（指数部が無い場合は0）。指数部の先頭のゼロは許容します（`"E-05"`）。
- `|e| > 324` は不正な文字列です。上限は倍精度浮動小数点数の範囲（最小の非正規化数 約 `4.9e-324`）を
  受け付けるための値で、巨大な指数による過大な計算を防ぎます。
- 結果：`f - e >= 0` なら `(m, f - e)`、それ以外は `(m * 10^(e - f), 0)`。
  つまり scale は `max(0, f - e)` です。
- 指数部が無く `parse` でも受け付ける文字列は、`parse` と同じ結果になります。
- 受け付けない例：`""`、`"."`、`"e5"`、`"1e"`、`"1e+"`、`" 1"`、`"1,000"`、`"1_000"`、
  `"12%"`、`"NaN"`、`"Infinity"`、`"1e325"`、`"1e-325"`。

例（解析してから文字列化）：

| 入力 | 結果 |
|---|---|
| `"1.2E-05"` | `"0.000012"` |
| `"1.2E+05"` | `"120000"` |
| `"1.50e1"` | `"15.0"` |
| `".5"` | `"0.5"` |
| `"1."` | `"1"` |
| `"1.e2"` | `"100"` |
| `"-0e-3"` | `"0.000"` |
| `"5e-324"` | `"0.` + 323個の0 + `5"` |

注意：倍精度浮動小数点数の文字列表現は言語や実行環境で異なります
（例：`1e16` はDartでは `"10000000000000000.0"`、Pythonでは `"1e+16"`）。
これを解析した場合、値は一致しても scale が一致しないことがあります。

## 3. 等価判定、順序、ハッシュ

- 等価判定は数値で行います：`PortableDecimal.parse("1.50") == PortableDecimal.parse("1.5")`。
- `PortableDecimal` と `PortableRational` は互いに等しくなることはありません
  （型をまたいだ暗黙の比較はしません）。先に明示的に変換してください。
- 順序（`compareTo` / `<` など）は数値によるもので、同じ型同士のみです。
- ハッシュ値は、同じ言語内では等価判定と整合します。
  言語間でハッシュ値が一致する必要はありません。

## 4. 丸めモード

丸めは、正確な有理数の値 `x` を整数に変換します。

| モード | 規則 |
|---|---|
| `halfEven` | 最も近い整数。同距離の場合は偶数側（銀行丸め）。 |
| `halfUp` | 最も近い整数。同距離の場合は0から遠い側（四捨五入）。 |
| `down` | 0方向（切り捨て）。 |
| `floor` | 負の無限大方向。 |
| `ceiling` | 正の無限大方向。 |
| `up` | 0から遠い側（切り上げ）。 |

例（x → 結果）：

| x | halfEven | halfUp | down | floor | ceiling | up |
|---|---|---|---|---|---|---|
| 2.5 | 2 | 3 | 2 | 2 | 3 | 3 |
| -2.5 | -2 | -3 | -2 | -3 | -2 | -3 |
| 1.4 | 1 | 1 | 1 | 1 | 2 | 2 |
| -1.6 | -2 | -2 | -1 | -2 | -1 | -2 |
| 3 | 3 | 3 | 3 | 3 | 3 | 3 |

`up` は既存のメンバーの後ろに追加します（既存メンバーの並び順は変えません）。

## 5. PortableDecimal の演算

| 演算 | 結果のscale | 備考 |
|---|---|---|
| `a + b`、`a - b` | `max(a.scale, b.scale)` | 正確 |
| `a * b` | `a.scale + b.scale` | 正確 |
| `-a`、`abs(a)` | `a.scale` | 正確 |
| `a.divide(b, scale, rounding)` | `scale` | 正確な商を `rounding` で1回だけ丸める |
| `a.setScale(scale, rounding)` | `scale` | scaleを増やす場合は正確。減らす場合は1回だけ丸める |
| `a.pow(n)` | `a.scale * n` | 正確。`n` は0以上の整数 |
| `a.stripTrailingZeros()` | 末尾のゼロを除いた桁数 | 正確 |
| `a.isInteger` | - | 値が整数なら真 |
| `a.toBigInt(rounding)` | - | 正確な値を整数に1回だけ丸める |
| `a.toRational()` | - | 正確 |
| `a.toDouble()` | - | 7章を参照 |

- `b == 0` での `divide` はゼロ除算エラーです。
- `pow`：`n < 0` は引数エラーです（結果が有限小数にならない場合があるため。必要なら `a.toRational().pow(n)` を使います）。
  `a.pow(0)` は値1、scale 0 です（`a` がゼロの場合も同じ）。`n` の大きさに上限はありません。
- `stripTrailingZeros`：小数部の末尾のゼロを取り除きます。scaleは0未満にしません
  （`"1.500"` → `"1.5"`、`"0.000"` → `"0"`、`"100"` → `"100"`）。
- `isInteger`：`unscaledValue` が `10^scale` で割り切れる場合に真です（`"1.00"` は真）。
- `toBigInt`：結果は任意精度の整数（Dartの `BigInt`、Pythonの `int`）です。`setScale(0, rounding)` と同じ値になります。
- `PortableDecimal` には `/` を定義しません。
- 両オペランドとも `PortableDecimal` である必要があります（int / double / 有理数との暗黙の混在はしません）。

## 6. PortableRational の演算

| 演算 | 備考 |
|---|---|
| `a + b`、`a - b`、`a * b`、`a / b` | 正確。結果は正規形 |
| `-a`、`abs(a)` | 正確 |
| `a.pow(n)` | 正確。`n` は任意の整数。結果は正規形 |
| `a.isInteger` | 分母が1なら真 |
| `a.toBigInt(rounding)` | 正確な値を整数に1回だけ丸める |
| `a.toDecimal(scale, rounding)` | 正確な値を `scale` 桁に1回だけ丸める |
| `a.toDecimalExact()` | 有限小数として正確に変換する |
| `a.toDouble()` | 7章を参照 |

- `b == 0` での `a / b` はゼロ除算エラーです。
- `pow`：`n < 0` は `(1/a)^|n|` です。`a` がゼロで `n < 0` の場合はゼロ除算エラーです。
  `a.pow(0)` は `1` です（`a` がゼロの場合も同じ）。`n` の大きさに上限はありません。
- `toDecimalExact`：分母の素因数が2と5のみ（`2^p * 5^q`）の場合、scale `max(p, q)` の10進数を返します
  （`"3/8"` → `"0.375"`、`"5"` → `"5"`、`"-1/20"` → `"-0.05"`）。
  それ以外（`"1/3"` など）は引数エラーです。
- 両オペランドとも `PortableRational` である必要があります。

## 7. IEEE 754 倍精度浮動小数点数への変換

`toDouble()`（Pythonでは `to_float()`）は、正確な値に最も近いIEEE 754 binary64の値を返します。
同距離の場合は偶数側です（非正規化数を含め、正しく丸めます）。
有限の範囲を超える値は `+Infinity` / `-Infinity` を返します。
最小の非正規化数の半分より小さい値は `0.0` に丸められます（ゼロの符号は規定しません）。

倍精度浮動小数点数からの変換は、仕様バージョン1では提供しません。

## 8. エラー

| エラーの種類 | Dart | Python |
|---|---|---|
| 不正な文字列 | `FormatException` | `ValueError` |
| ゼロ除算 | `UnsupportedError` | `ZeroDivisionError` |
| 不正な引数（例：負のscale、`PortableDecimal.pow` の負の指数、`toDecimalExact` で有限小数にならない値） | `ArgumentError` | `ValueError` |
| オペランドの型が不正 | コンパイル時エラー | `TypeError` |

## 9. 言語ごとの名前

| 演算 | Dart | Python |
|---|---|---|
| 緩い解析 | `PortableDecimal.parseLenient(text)` | `PortableDecimal.parse_lenient(text)` |
| 整数乗 | `a.pow(n)` | `a.pow(n)`、`a ** n` |
| 末尾のゼロを除く | `a.stripTrailingZeros()` | `a.strip_trailing_zeros()` |
| 整数判定 | `a.isInteger`（getter） | `a.is_integer()` |
| 整数への丸め | `a.toBigInt(rounding)` | `a.to_int(rounding)` |
| 有限小数への正確な変換 | `a.toDecimalExact()` | `a.to_decimal_exact()` |
| 丸めモード | `EnumRoundingMode.up` | `EnumRoundingMode.up` |

Pythonの `**` は右辺が `int` の場合のみ定義します（3引数の `pow(a, n, mod)` は `TypeError`）。

## 10. テストベクタ

`spec/vectors/*.json` には、次の形式のケースが含まれます。

```json
{"op": "add", "a": "1.50", "b": "2.3", "expected": "3.80"}
{"op": "divide", "a": "1", "b": "3", "scale": 5, "rounding": "halfEven", "expected": "0.33333"}
{"op": "parse", "a": "1.", "error": "format"}
```

- `expected` は、結果の `toString()`（10進数・有理数の結果の場合）、
  整数 `-1/0/1`（`compare`）、真偽値（`equals`）、
  または倍精度浮動小数点数を往復変換可能な最短の表記（`toDouble`。無限大は `"inf"` / `"-inf"`）です。
- 仕様バージョン2で追加した演算の `op` は `parseLenient`、`pow`、`stripTrailingZeros`、`isInteger`、`toBigInt`、`toDecimalExact` です。
  `isInteger` の `expected` は真偽値、`toBigInt` の `expected` は整数の10進文字列です。
- `error` は `format`、`zeroDivision`、`argument` のいずれかです。
- `*_manual.json` は手書きの境界ケースです。
  `*_generated.json` は `spec/tools/generate_vectors.py` で生成されます。
  このスクリプトは、Python標準の `fractions.Fraction` を、実装から独立した正解の計算に使います。
