import 'package:simple_portable_numeric/src/enum_rounding_mode.dart';
import 'package:simple_portable_numeric/src/portable_decimal.dart';
import 'package:simple_portable_numeric/src/util_int_math.dart';

final RegExp _fractionPattern = RegExp(r'^([+-]?)([0-9]+)/([0-9]+)$');
final RegExp _decimalPattern = RegExp(r'^[+-]?[0-9]+(\.[0-9]+)?$');

/// (en) An exact rational number numerator / denominator.
/// It is always kept in canonical form: reduced, with a positive denominator.
/// The results are identical to the Python version of this package.
///
/// (ja) 分子 / 分母 で表される正確な有理数です。
/// 常に約分済みで分母が正の正規形で保持されます。
/// 計算結果はこのパッケージのPython版と同一になります。
class PortableRational implements Comparable<PortableRational> {
  /// (en) The numerator in canonical form.
  ///
  /// (ja) 正規形での分子です。
  final BigInt numerator;

  /// (en) The denominator in canonical form (always positive).
  ///
  /// (ja) 正規形での分母です（常に正）。
  final BigInt denominator;

  PortableRational._canonical(this.numerator, this.denominator);

  /// (en) Creates numerator / denominator, reduced to canonical form.
  ///
  /// (ja) 分子 / 分母 を作成し、正規形に約分します。
  ///
  /// * [numerator] : The numerator.
  /// * [denominator] : The denominator. Must not be zero.
  ///
  /// Throws [UnsupportedError] if [denominator] is zero.
  factory PortableRational(BigInt numerator, [BigInt? denominator]) {
    BigInt n = numerator;
    BigInt d = denominator ?? BigInt.one;
    if (d == BigInt.zero) {
      throw UnsupportedError("Division by zero");
    }
    if (d.isNegative) {
      n = -n;
      d = -d;
    }
    final BigInt g = n.gcd(d);
    return PortableRational._canonical(n ~/ g, d ~/ g);
  }

  /// (en) Creates numerator / denominator from ints, reduced to canonical form.
  ///
  /// (ja) intから 分子 / 分母 を作成し、正規形に約分します。
  ///
  /// * [numerator] : The numerator.
  /// * [denominator] : The denominator. Must not be zero.
  factory PortableRational.fromInt(int numerator, [int denominator = 1]) =>
      PortableRational(BigInt.from(numerator), BigInt.from(denominator));

  /// (en) Parses "n/d", an integer such as "-3", or a plain decimal such as
  /// "0.75". The result is reduced to canonical form.
  ///
  /// (ja) "n/d"、"-3" のような整数、"0.75" のような通常表記の10進数を解析します。
  /// 結果は正規形に約分されます。
  ///
  /// * [text] : The string to parse.
  ///
  /// Throws [FormatException] if [text] is not a valid format,
  /// or [UnsupportedError] if the denominator is zero.
  factory PortableRational.parse(String text) {
    final RegExpMatch? m = _fractionPattern.firstMatch(text);
    if (m != null) {
      final BigInt n = BigInt.parse(m.group(2)!);
      return PortableRational(
        m.group(1) == "-" ? -n : n,
        BigInt.parse(m.group(3)!),
      );
    }
    if (_decimalPattern.hasMatch(text)) {
      return PortableDecimal.parse(text).toRational();
    }
    throw FormatException("Invalid rational string", text);
  }

  /// (en) Exact addition.
  ///
  /// (ja) 正確な加算です。
  PortableRational operator +(PortableRational other) => PortableRational(
    numerator * other.denominator + other.numerator * denominator,
    denominator * other.denominator,
  );

  /// (en) Exact subtraction.
  ///
  /// (ja) 正確な減算です。
  PortableRational operator -(PortableRational other) => PortableRational(
    numerator * other.denominator - other.numerator * denominator,
    denominator * other.denominator,
  );

  /// (en) Exact multiplication.
  ///
  /// (ja) 正確な乗算です。
  PortableRational operator *(PortableRational other) => PortableRational(
    numerator * other.numerator,
    denominator * other.denominator,
  );

  /// (en) Exact division.
  ///
  /// (ja) 正確な除算です。
  ///
  /// Throws [UnsupportedError] if [other] is zero.
  PortableRational operator /(PortableRational other) {
    if (other.numerator == BigInt.zero) {
      throw UnsupportedError("Division by zero");
    }
    return PortableRational(
      numerator * other.denominator,
      denominator * other.numerator,
    );
  }

  /// (en) Negation.
  ///
  /// (ja) 符号反転です。
  PortableRational operator -() =>
      PortableRational._canonical(-numerator, denominator);

  /// (en) Absolute value.
  ///
  /// (ja) 絶対値です。
  PortableRational abs() =>
      PortableRational._canonical(numerator.abs(), denominator);

  /// (en) Returns this value raised to the power [n]. Exact, in canonical form.
  /// A negative [n] gives (1 / this)^|n|. pow(0) is 1, also for zero.
  ///
  /// (ja) この値の [n] 乗を返します。正確で、結果は正規形です。
  /// 負の [n] は (1 / this)^|n| です。pow(0) はゼロの場合も1です。
  ///
  /// * [n] : The exponent. Any integer.
  ///
  /// Throws [UnsupportedError] if this is zero and [n] is negative.
  PortableRational pow(int n) {
    if (n >= 0) {
      return PortableRational._canonical(numerator.pow(n), denominator.pow(n));
    }
    if (numerator == BigInt.zero) {
      throw UnsupportedError("Division by zero");
    }
    return PortableRational(denominator.pow(-n), numerator.pow(-n));
  }

  /// (en) Whether this value is an integer (the denominator is 1).
  ///
  /// (ja) この値が整数（分母が1）かどうかです。
  bool get isInteger => denominator == BigInt.one;

  /// (en) Rounds this value once to an integer.
  ///
  /// (ja) この値を1回だけ丸めて整数にします。
  ///
  /// * [rounding] : The rounding mode.
  BigInt toBigInt(EnumRoundingMode rounding) =>
      roundDiv(numerator, denominator, rounding);

  /// (en) Compares by numeric value.
  /// Returns -1 if this < other, 0 if equal, 1 if this > other.
  ///
  /// (ja) 数値で比較します。
  /// this < other なら -1、等しければ 0、this > other なら 1 を返します。
  @override
  int compareTo(PortableRational other) => (numerator * other.denominator)
      .compareTo(other.numerator * denominator)
      .sign;

  bool operator <(PortableRational other) => compareTo(other) < 0;

  bool operator <=(PortableRational other) => compareTo(other) <= 0;

  bool operator >(PortableRational other) => compareTo(other) > 0;

  bool operator >=(PortableRational other) => compareTo(other) >= 0;

  /// (en) Equality by numeric value.
  /// A PortableDecimal is never equal to a PortableRational.
  ///
  /// (ja) 数値による等価判定です。
  /// PortableDecimal とは常に等しくありません。
  @override
  bool operator ==(Object other) =>
      other is PortableRational &&
      numerator == other.numerator &&
      denominator == other.denominator;

  @override
  int get hashCode => Object.hash(numerator, denominator);

  /// (en) Converts this value to a decimal with the specified scale,
  /// rounding the exact value once.
  ///
  /// (ja) この値を指定したscaleの10進数に変換します。正確な値を1回だけ丸めます。
  ///
  /// * [scale] : The number of digits after the decimal point.
  /// Must be 0 or more.
  /// * [rounding] : The rounding mode.
  ///
  /// Throws [ArgumentError] if [scale] is negative.
  PortableDecimal toDecimal(int scale, EnumRoundingMode rounding) {
    if (scale < 0) {
      throw ArgumentError.value(scale, "scale", "must be 0 or more");
    }
    return PortableDecimal(
      roundDiv(numerator * pow10(scale), denominator, rounding),
      scale,
    );
  }

  /// (en) Converts this value exactly to a finite decimal with the smallest
  /// scale, e.g. 3/8 -> 0.375.
  /// This is possible only when the denominator is 2^p * 5^q.
  ///
  /// (ja) この値を、最小のscaleの有限小数に正確に変換します（例: 3/8 -> 0.375）。
  /// 分母が 2^p * 5^q の場合のみ変換できます。
  ///
  /// Throws [ArgumentError] if this value is not a finite decimal (e.g. 1/3).
  PortableDecimal toDecimalExact() {
    final BigInt five = BigInt.from(5);
    BigInt d = denominator;
    int p = 0;
    int q = 0;
    while (d.isEven) {
      d = d >> 1;
      p++;
    }
    while (d.remainder(five) == BigInt.zero) {
      d = d ~/ five;
      q++;
    }
    if (d != BigInt.one) {
      throw ArgumentError("The value is not a finite decimal");
    }
    final int scale = p > q ? p : q;
    return PortableDecimal(numerator * pow10(scale) ~/ denominator, scale);
  }

  /// (en) Converts this value to the nearest double (ties to even).
  /// Overflow returns +-infinity. The result is identical to to_float in Python.
  ///
  /// (ja) この値を最も近い倍精度浮動小数点数に変換します（同距離は偶数側）。
  /// 範囲外の場合は +-infinity を返します。結果はPython版の to_float と同一です。
  double toDouble() => ratioToDouble(numerator, denominator);

  /// (en) Returns "n/d", or "n" when the denominator is 1.
  ///
  /// (ja) "n/d" を返します。分母が1の場合は "n" を返します。
  @override
  String toString() => denominator == BigInt.one
      ? numerator.toString()
      : "$numerator/$denominator";
}
