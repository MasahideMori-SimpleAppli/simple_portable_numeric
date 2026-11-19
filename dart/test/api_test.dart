import 'package:simple_portable_numeric/simple_portable_numeric.dart';
import 'package:test/test.dart';

/// Dart-specific behavior not covered by the shared vectors.
PortableDecimal d(String s) => PortableDecimal.parse(s);
PortableRational r(String s) => PortableRational.parse(s);

void main() {
  test("decimal constructors and properties", () {
    final x = PortableDecimal(BigInt.from(-1234), 2);
    expect(x.unscaledValue, BigInt.from(-1234));
    expect(x.scale, 2);
    expect(x.toString(), "-12.34");
    expect(PortableDecimal.fromInt(5).toString(), "5");
    expect(PortableDecimal.fromInt(-5, 3).toString(), "-0.005");
    expect(() => PortableDecimal(BigInt.one, -1), throwsArgumentError);
  });

  test("rational constructors and properties", () {
    final x = PortableRational(BigInt.from(4), BigInt.from(-6));
    expect(x.numerator, BigInt.from(-2));
    expect(x.denominator, BigInt.from(3));
    expect(PortableRational(BigInt.from(7)).toString(), "7");
    expect(PortableRational.fromInt(-4, 6).toString(), "-2/3");
    expect(() => PortableRational.fromInt(1, 0), throwsUnsupportedError);
  });

  test("hashCode is consistent with equality", () {
    expect(d("1.5").hashCode, d("1.50").hashCode);
    expect(d("0").hashCode, d("-0.00").hashCode);
    expect(d("100").hashCode, d("100.0").hashCode);
    expect({d("1.5"), d("1.50"), d("2")}.length, 2);
    expect(r("2/4").hashCode, r("0.5").hashCode);
  });

  test("comparison operators", () {
    expect(d("1.49") < d("1.5"), isTrue);
    expect(d("1.5") <= d("1.50"), isTrue);
    expect(d("2") > d("1.99"), isTrue);
    expect(d("1.99") >= d("1.990"), isTrue);
    expect(r("1/3") < r("1/2"), isTrue);
    expect(r("1/2") <= r("2/4"), isTrue);
    expect(r("1") > r("2/3"), isTrue);
    expect(r("2/3") >= r("4/6"), isTrue);
    final list = [d("0.3"), d("-1"), d("0.25")]..sort();
    expect(list, [d("-1"), d("0.25"), d("0.3")]);
  });

  test("no cross-type equality", () {
    // ignore: unrelated_type_equality_checks
    expect(d("1") == r("1"), isFalse);
    // ignore: unrelated_type_equality_checks
    expect(r("1") == d("1"), isFalse);
  });

  test("huge digit strings", () {
    final digits = "1234567890" * 1000;
    expect(d("$digits.$digits").toString(), "$digits.$digits");
    expect(r(digits).toString(), digits);
  });

  test("rounding mode names match Python values", () {
    expect(EnumRoundingMode.values.map((m) => m.name).toList(), [
      "halfEven",
      "halfUp",
      "down",
      "floor",
      "ceiling",
      "up",
    ]);
  });

  test("toRational round trip", () {
    for (final s in ["0.125", "-3.50", "0", "123456789.987654321"]) {
      expect(
        d(s).toRational().toDecimal(d(s).scale, EnumRoundingMode.halfEven),
        d(s),
      );
    }
  });

  test("new methods return the documented types", () {
    expect(d("2.5").toBigInt(EnumRoundingMode.up), BigInt.from(3));
    expect(r("-5/2").toBigInt(EnumRoundingMode.up), BigInt.from(-3));
    expect(d("1.00").isInteger, isTrue);
    expect(r("3/8").toDecimalExact(), d("0.375"));
    expect(() => r("1/3").toDecimalExact(), throwsArgumentError);
    expect(() => d("2").pow(-1), throwsArgumentError);
    expect(d("2").toRational().pow(-1), r("1/2"));
  });

  test("stripTrailingZeros keeps equality and hashCode", () {
    for (final s in ["1.500", "-0.000", "100.00", "0.0100"]) {
      expect(d(s).stripTrailingZeros(), d(s));
      expect(d(s).stripTrailingZeros().hashCode, d(s).hashCode);
    }
  });

  test("parseLenient reads double.toString() back to the same double", () {
    for (final x in [
      0.1,
      1e-7,
      1.5e300,
      5e-324,
      1.7976931348623157e308,
      1e16,
      1e21,
      -2.2250738585072014e-308,
      123456.789,
    ]) {
      expect(PortableDecimal.parseLenient(x.toString()).toDouble(), x);
    }
  });

  test("parseLenient with huge mantissa and exponent", () {
    final digits = "1234567890" * 1000;
    final x = PortableDecimal.parseLenient("$digits.${digits}e-324");
    expect(x.scale, digits.length + 324);
    expect(
      x.toString(),
      "${digits.substring(0, digits.length - 324)}.${digits.substring(digits.length - 324)}$digits",
    );
  });
}
