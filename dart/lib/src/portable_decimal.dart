import 'package:simple_portable_numeric/src/enum_rounding_mode.dart';
import 'package:simple_portable_numeric/src/portable_rational.dart';
import 'package:simple_portable_numeric/src/util_int_math.dart';

final RegExp _decimalPattern = RegExp(r'^[+-]?[0-9]+(\.[0-9]+)?$');
final RegExp _lenientPattern = RegExp(
  r'^([+-]?)([0-9]*)(?:\.([0-9]*))?(?:[eE]([+-]?)([0-9]+))?$',
);

/// The largest absolute exponent accepted by parseLenient (see SPEC 2.5).
const int _maxLenientExponent = 324;

void _checkScale(int scale) {
  if (scale < 0) {
    throw ArgumentError.value(scale, "scale", "must be 0 or more");
  }
}

/// (en) An arbitrary-precision decimal number, represented as
/// unscaledValue * 10^(-scale).
/// The results are identical to the Python version of this package.
/// Equality is by numeric value (1.50 == 1.5), while toString keeps the scale.
///
/// (ja) 任意精度の10進数です。unscaledValue * 10^(-scale) として表現されます。
/// 計算結果はこのパッケージのPython版と同一になります。
/// 等価判定は数値で行われ（1.50 == 1.5）、文字列化ではscaleが保持されます。
class PortableDecimal implements Comparable<PortableDecimal> {
  /// (en) The integer value with the decimal point removed.
  ///
  /// (ja) 小数点を取り除いた整数値です。
  final BigInt unscaledValue;

  /// (en) The number of digits after the decimal point.
  ///
  /// (ja) 小数点以下の桁数です。
  final int scale;

  /// (en) Creates a decimal whose value is unscaledValue * 10^(-scale).
  ///
  /// (ja) 値が unscaledValue * 10^(-scale) の10進数を作成します。
  ///
  /// * [unscaledValue] : The integer value with the decimal point removed.
  /// * [scale] : The number of digits after the decimal point.
  /// Must be 0 or more.
  ///
  /// Throws [ArgumentError] if [scale] is negative.
  PortableDecimal(this.unscaledValue, [this.scale = 0]) {
    _checkScale(scale);
  }

  /// (en) Creates a decimal from an int. Same as PortableDecimal(BigInt.from(value), scale).
  ///
  /// (ja) intから10進数を作成します。PortableDecimal(BigInt.from(value), scale) と同じです。
  ///
  /// * [value] : The integer value with the decimal point removed.
  /// * [scale] : The number of digits after the decimal point.
  /// Must be 0 or more.
  PortableDecimal.fromInt(int value, [int scale = 0])
    : this(BigInt.from(value), scale);

  /// (en) Parses a plain decimal string such as "-12.340".
  /// The number of fractional digits becomes the scale.
  /// Exponent notation, whitespace and non-ASCII digits are rejected.
  ///
  /// (ja) "-12.340" のような通常表記の10進文字列を解析します。
  /// 小数部の桁数がscaleになります。
  /// 指数表記、空白、ASCII以外の数字は受け付けません。
  ///
  /// * [text] : The string to parse.
  ///
  /// Throws [FormatException] if [text] is not a valid decimal.
  factory PortableDecimal.parse(String text) {
    if (!_decimalPattern.hasMatch(text)) {
      throw FormatException("Invalid decimal string", text);
    }
    final bool negative = text.startsWith("-");
    final String body = text.startsWith("-") || text.startsWith("+")
        ? text.substring(1)
        : text;
    final int dot = body.indexOf(".");
    final String digits = dot < 0
        ? body
        : body.substring(0, dot) + body.substring(dot + 1);
    final BigInt value = BigInt.parse(digits);
    return PortableDecimal(
      negative ? -value : value,
      dot < 0 ? 0 : body.length - dot - 1,
    );
  }

  /// (en) Parses a decimal string more leniently than [PortableDecimal.parse].
  /// In addition to the plain notation, it accepts exponent notation such as
  /// "1.2E-05" (e or E, absolute exponent up to 324) and an omitted integer or
  /// fractional part such as ".5" or "1.". The scale is
  /// max(0, number of fractional digits - exponent).
  /// Whitespace, "_", thousands separators, "%", NaN and Infinity are rejected.
  ///
  /// (ja) [PortableDecimal.parse] より緩く10進文字列を解析します。
  /// 通常表記に加えて、"1.2E-05" のような指数表記（e または E、指数の絶対値は324まで）と、
  /// ".5" や "1." のような整数部・小数部の省略を受け付けます。
  /// scaleは max(0, 小数部の桁数 - 指数) です。
  /// 空白、"_"、桁区切り、"%"、NaN、Infinity は受け付けません。
  ///
  /// * [text] : The string to parse.
  ///
  /// Throws [FormatException] if [text] is not a valid string.
  factory PortableDecimal.parseLenient(String text) {
    final RegExpMatch? m = _lenientPattern.firstMatch(text);
    final String intPart = m?.group(2) ?? "";
    final String fracPart = m?.group(3) ?? "";
    if (m == null || intPart.isEmpty && fracPart.isEmpty) {
      throw FormatException("Invalid decimal string", text);
    }
    int exp = 0;
    final String? expDigits = m.group(5);
    if (expDigits != null) {
      final String trimmed = expDigits.replaceFirst(RegExp(r'^0+'), "");
      if (trimmed.length > 3 || int.parse("0$trimmed") > _maxLenientExponent) {
        throw FormatException("Exponent out of range", text);
      }
      exp = int.parse("0$trimmed");
      if (m.group(4) == "-") exp = -exp;
    }
    BigInt value = BigInt.parse(intPart + fracPart);
    if (m.group(1) == "-") value = -value;
    final int scale = fracPart.length - exp;
    return scale >= 0
        ? PortableDecimal(value, scale)
        : PortableDecimal(value * pow10(-scale), 0);
  }

  /// Returns [unscaledValue] of this and [other] aligned to a common scale.
  (BigInt, BigInt, int) _aligned(PortableDecimal other) {
    final int s = scale > other.scale ? scale : other.scale;
    return (
      unscaledValue * pow10(s - scale),
      other.unscaledValue * pow10(s - other.scale),
      s,
    );
  }

  /// (en) Exact addition. The result scale is max(this.scale, other.scale).
  ///
  /// (ja) 正確な加算です。結果のscaleは max(this.scale, other.scale) です。
  PortableDecimal operator +(PortableDecimal other) {
    final (a, b, s) = _aligned(other);
    return PortableDecimal(a + b, s);
  }

  /// (en) Exact subtraction. The result scale is max(this.scale, other.scale).
  ///
  /// (ja) 正確な減算です。結果のscaleは max(this.scale, other.scale) です。
  PortableDecimal operator -(PortableDecimal other) {
    final (a, b, s) = _aligned(other);
    return PortableDecimal(a - b, s);
  }

  /// (en) Exact multiplication. The result scale is this.scale + other.scale.
  ///
  /// (ja) 正確な乗算です。結果のscaleは this.scale + other.scale です。
  PortableDecimal operator *(PortableDecimal other) =>
      PortableDecimal(unscaledValue * other.unscaledValue, scale + other.scale);

  /// (en) Negation. The scale is kept.
  ///
  /// (ja) 符号反転です。scaleは保持されます。
  PortableDecimal operator -() => PortableDecimal(-unscaledValue, scale);

  /// (en) Absolute value. The scale is kept.
  ///
  /// (ja) 絶対値です。scaleは保持されます。
  PortableDecimal abs() => PortableDecimal(unscaledValue.abs(), scale);

  /// (en) Divides this value by [other]. The exact quotient is rounded once
  /// to the specified number of fractional digits.
  ///
  /// (ja) この値を [other] で割ります。正確な商を、指定した小数点以下の桁数に
  /// 1回だけ丸めます。
  ///
  /// * [other] : The divisor.
  /// * [scale] : The number of digits after the decimal point of the result.
  /// Must be 0 or more.
  /// * [rounding] : The rounding mode.
  ///
  /// Throws [UnsupportedError] if [other] is zero.
  PortableDecimal divide(
    PortableDecimal other,
    int scale,
    EnumRoundingMode rounding,
  ) {
    _checkScale(scale);
    if (other.unscaledValue == BigInt.zero) {
      throw UnsupportedError("Division by zero");
    }
    // result = a * 10^(scale + sb - sa) / b
    final int exp = scale + other.scale - this.scale;
    BigInt n = unscaledValue;
    BigInt d = other.unscaledValue;
    if (exp >= 0) {
      n *= pow10(exp);
    } else {
      d *= pow10(-exp);
    }
    return PortableDecimal(roundDiv(n, d, rounding), scale);
  }

  /// (en) Returns a value with the specified scale. Increasing the scale is
  /// exact; decreasing it rounds once with [rounding].
  ///
  /// (ja) 指定したscaleの値を返します。scaleを増やす場合は正確に、
  /// 減らす場合は [rounding] で1回だけ丸めます。
  ///
  /// * [newScale] : The new number of digits after the decimal point.
  /// Must be 0 or more.
  /// * [rounding] : The rounding mode used when the scale decreases.
  PortableDecimal setScale(int newScale, EnumRoundingMode rounding) {
    _checkScale(newScale);
    if (newScale >= scale) {
      return PortableDecimal(unscaledValue * pow10(newScale - scale), newScale);
    }
    return PortableDecimal(
      roundDiv(unscaledValue, pow10(scale - newScale), rounding),
      newScale,
    );
  }

  /// (en) Returns this value raised to the power [n]. Exact.
  /// The result scale is scale * n. pow(0) is 1 with scale 0.
  ///
  /// (ja) この値の [n] 乗を返します。正確です。
  /// 結果のscaleは scale * n です。pow(0) はscale 0の1です。
  ///
  /// * [n] : The exponent. Must be 0 or more.
  /// Use toRational().pow(n) for a negative exponent.
  ///
  /// Throws [ArgumentError] if [n] is negative.
  PortableDecimal pow(int n) {
    if (n < 0) {
      throw ArgumentError.value(n, "n", "must be 0 or more");
    }
    return PortableDecimal(unscaledValue.pow(n), scale * n);
  }

  /// (en) Returns an equal value with the trailing zeros of the fractional
  /// part removed, e.g. 1.500 -> 1.5. The scale never goes below 0 (100 stays 100).
  ///
  /// (ja) 小数部の末尾のゼロを取り除いた、等しい値を返します（例: 1.500 -> 1.5）。
  /// scaleは0未満になりません（100 は 100 のまま）。
  PortableDecimal stripTrailingZeros() {
    final BigInt ten = BigInt.from(10);
    BigInt u = unscaledValue;
    int s = scale;
    while (s > 0 && u.remainder(ten) == BigInt.zero) {
      u = u ~/ ten;
      s--;
    }
    return PortableDecimal(u, s);
  }

  /// (en) Whether this value is an integer (1.00 is an integer).
  ///
  /// (ja) この値が整数かどうかです（1.00 は整数です）。
  bool get isInteger => unscaledValue.remainder(pow10(scale)) == BigInt.zero;

  /// (en) Rounds this value once to an integer.
  /// The value is the same as setScale(0, rounding).
  ///
  /// (ja) この値を1回だけ丸めて整数にします。
  /// 値は setScale(0, rounding) と同じです。
  ///
  /// * [rounding] : The rounding mode.
  BigInt toBigInt(EnumRoundingMode rounding) =>
      roundDiv(unscaledValue, pow10(scale), rounding);

  /// (en) Compares by numeric value.
  /// Returns -1 if this < other, 0 if equal, 1 if this > other.
  ///
  /// (ja) 数値で比較します。
  /// this < other なら -1、等しければ 0、this > other なら 1 を返します。
  @override
  int compareTo(PortableDecimal other) {
    final (a, b, _) = _aligned(other);
    return a.compareTo(b).sign;
  }

  bool operator <(PortableDecimal other) => compareTo(other) < 0;

  bool operator <=(PortableDecimal other) => compareTo(other) <= 0;

  bool operator >(PortableDecimal other) => compareTo(other) > 0;

  bool operator >=(PortableDecimal other) => compareTo(other) >= 0;

  /// (en) Equality by numeric value (1.50 == 1.5).
  /// A PortableRational is never equal to a PortableDecimal.
  ///
  /// (ja) 数値による等価判定です（1.50 == 1.5）。
  /// PortableRational とは常に等しくありません。
  @override
  bool operator ==(Object other) =>
      other is PortableDecimal && compareTo(other) == 0;

  @override
  int get hashCode {
    final PortableDecimal s = stripTrailingZeros();
    return Object.hash(s.unscaledValue, s.scale);
  }

  /// (en) Converts this value to an exactly equal rational.
  ///
  /// (ja) この値を、正確に等しい有理数に変換します。
  PortableRational toRational() =>
      PortableRational(unscaledValue, pow10(scale));

  /// (en) Converts this value to the nearest double (ties to even).
  /// Overflow returns +-infinity. The result is identical to to_float in Python.
  ///
  /// (ja) この値を最も近い倍精度浮動小数点数に変換します（同距離は偶数側）。
  /// 範囲外の場合は +-infinity を返します。結果はPython版の to_float と同一です。
  double toDouble() => ratioToDouble(unscaledValue, pow10(scale));

  /// (en) Returns the plain-notation string keeping the scale, e.g. "-1.50".
  /// Negative zero is never output.
  ///
  /// (ja) scaleを保持した通常表記の文字列を返します（例: "-1.50"）。
  /// 負のゼロは出力されません。
  @override
  String toString() {
    String digits = unscaledValue.abs().toString();
    if (scale > 0) {
      digits = digits.padLeft(scale + 1, "0");
      final int cut = digits.length - scale;
      digits = "${digits.substring(0, cut)}.${digits.substring(cut)}";
    }
    return unscaledValue.isNegative ? "-$digits" : digits;
  }
}
