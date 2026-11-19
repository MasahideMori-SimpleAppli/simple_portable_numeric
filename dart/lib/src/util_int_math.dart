import 'dart:typed_data';

import 'package:simple_portable_numeric/src/enum_rounding_mode.dart';

final BigInt _ten = BigInt.from(10);

/// (en) Returns 10^exponent as a BigInt.
///
/// (ja) 10^exponent をBigIntで返します。
///
/// * [exponent] : A non-negative exponent.
BigInt pow10(int exponent) => _ten.pow(exponent);

/// (en) Divides [n] by [d] exactly and rounds the quotient to an integer once.
///
/// (ja) [n] を [d] で正確に割り、商を1回だけ丸めて整数にします。
///
/// * [n] : The dividend.
/// * [d] : The divisor. Must not be zero.
/// * [rounding] : The rounding mode.
///
/// Throws [UnsupportedError] if [d] is zero.
BigInt roundDiv(BigInt n, BigInt d, EnumRoundingMode rounding) {
  if (d == BigInt.zero) {
    throw UnsupportedError("Division by zero");
  }
  if (d.isNegative) {
    n = -n;
    d = -d;
  }
  // BigInt.% is Euclidean, so 0 <= r < d and q = floor(n / d).
  final BigInt r = n % d;
  final BigInt q = (n - r) ~/ d;
  if (r == BigInt.zero) {
    return q;
  }
  final BigInt up = q + BigInt.one;
  switch (rounding) {
    case EnumRoundingMode.floor:
      return q;
    case EnumRoundingMode.ceiling:
      return up;
    case EnumRoundingMode.down:
      return n.isNegative ? up : q;
    case EnumRoundingMode.up:
      return n.isNegative ? q : up;
    case EnumRoundingMode.halfUp:
    case EnumRoundingMode.halfEven:
      final int c = (r << 1).compareTo(d);
      if (c < 0) return q;
      if (c > 0) return up;
      if (rounding == EnumRoundingMode.halfUp) {
        return n.isNegative ? q : up;
      }
      return q.isEven ? q : up;
  }
}

/// (en) Converts the exact ratio [n] / [d] to the nearest IEEE 754 double
/// (ties to even, including subnormals). Overflow returns +-infinity.
/// The result is identical to Python's int / int.
///
/// (ja) 正確な比 [n] / [d] を最も近いIEEE 754倍精度浮動小数点数に変換します
/// （同距離は偶数側、非正規化数を含む）。範囲外の場合は +-infinity を返します。
/// 結果はPythonの int / int と同一です。
///
/// * [n] : The numerator.
/// * [d] : The denominator. Must be positive.
double ratioToDouble(BigInt n, BigInt d) {
  if (n == BigInt.zero) {
    return 0.0;
  }
  final bool negative = n.isNegative;
  final BigInt a = n.abs();
  // Scale so that the integer quotient q has 55 or 56 bits.
  final int shift = 55 - (a.bitLength - d.bitLength);
  final BigInt top = shift >= 0 ? a << shift : a;
  final BigInt bottom = shift >= 0 ? d : d << -shift;
  final BigInt q = top ~/ bottom;
  final bool sticky = q * bottom != top;
  // value = (q + sticky part) * 2^-shift, with 2^e <= value < 2^(e+1).
  final int qBits = q.bitLength;
  final int e = qBits - 1 - shift;
  if (e > 1023) {
    return negative ? double.negativeInfinity : double.infinity;
  }
  // Significant bits available: 53 for normal numbers, fewer for subnormals.
  final int precision = e < -1022 ? 53 - (-1022 - e) : 53;
  final int drop = qBits - precision;
  BigInt kept = q >> drop;
  final BigInt rem = q - (kept << drop);
  final int c = rem.compareTo(BigInt.one << (drop - 1));
  if (c > 0 || (c == 0 && (sticky || kept.isOdd))) {
    kept += BigInt.one;
  }
  if (kept == BigInt.zero) {
    return negative ? -0.0 : 0.0;
  }
  // kept <= 2^53, so toDouble is exact. The result kept * 2^exp is exactly
  // representable (or overflows to infinity), so power-of-two scaling is exact.
  double result = kept.toDouble();
  int exp = drop - shift;
  while (exp > 1023) {
    result *= _pow2(1023);
    exp -= 1023;
  }
  while (exp < -1022) {
    result *= _pow2(-1022);
    exp += 1022;
  }
  result *= _pow2(exp);
  return negative ? -result : result;
}

/// Returns exactly 2^k for -1022 <= k <= 1023 by setting the exponent bits.
double _pow2(int k) {
  final ByteData bytes = ByteData(8);
  bytes.setUint32(0, (k + 1023) << 20);
  bytes.setUint32(4, 0);
  return bytes.getFloat64(0);
}
