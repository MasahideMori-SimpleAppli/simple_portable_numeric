import 'package:simple_portable_numeric/simple_portable_numeric.dart';

void main() {
  // Decimal: exact + - * with no digit limit. The string keeps the scale.
  final a = PortableDecimal.parse("1.50");
  final b = PortableDecimal.parse("2.3");
  print(a + b); // 3.80
  print(a - b); // -0.80
  print(a * b); // 3.450
  print(PortableDecimal.parse("0.1") + PortableDecimal.parse("0.2")); // 0.3

  // Equality and ordering are by value.
  print(a == PortableDecimal.parse("1.5")); // true
  final list = ["0.3", "-1", "0.25"].map(PortableDecimal.parse).toList()
    ..sort();
  print(list); // [-1, 0.25, 0.3]

  // Division always takes the result scale and the rounding mode.
  final one = PortableDecimal.parse("1");
  final three = PortableDecimal.parse("3");
  print(one.divide(three, 5, EnumRoundingMode.halfEven)); // 0.33333

  // Rounding modes.
  final x = PortableDecimal.parse("-2.5");
  for (final mode in EnumRoundingMode.values) {
    print("${mode.name}: ${x.setScale(0, mode)}");
  }
  // halfEven: -2, halfUp: -3, down: -2, floor: -3, ceiling: -2

  // Rational: exact + - * /, always reduced.
  final r = PortableRational.parse("1/3") + PortableRational.parse("1/6");
  print(r); // 1/2
  print(PortableRational.parse("0.75")); // 3/4
  print(r.toDecimal(2, EnumRoundingMode.halfUp)); // 0.50

  // Conversion.
  print(PortableDecimal.parse("0.1").toRational()); // 1/10
  print(PortableRational.parse("1/3").toDouble()); // 0.3333333333333333

  // Invalid strings are rejected.
  try {
    PortableDecimal.parse("1e3");
  } on FormatException catch (e) {
    print(e.message); // Invalid decimal string
  }
}
