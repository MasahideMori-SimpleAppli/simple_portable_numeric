import 'dart:convert';
import 'dart:io';

import 'package:simple_portable_numeric/simple_portable_numeric.dart';
import 'package:test/test.dart';

/// Runs the shared test vectors in spec/vectors against the Dart implementation.
List<Map<String, dynamic>> _load(String name) =>
    (jsonDecode(File('../spec/vectors/$name').readAsStringSync()) as List)
        .cast<Map<String, dynamic>>();

EnumRoundingMode _mode(Map<String, dynamic> c) =>
    EnumRoundingMode.values.byName(c["rounding"] as String);

double _parseDouble(String s) => switch (s) {
  "inf" => double.infinity,
  "-inf" => double.negativeInfinity,
  _ => double.parse(s),
};

Object _runDecimal(Map<String, dynamic> c) {
  final a = PortableDecimal.parse(c["a"] as String);
  switch (c["op"]) {
    case "parse":
      return a.toString();
    case "neg":
      return (-a).toString();
    case "abs":
      return a.abs().toString();
    case "toRational":
      return a.toRational().toString();
    case "toDouble":
      return a.toDouble();
    case "setScale":
      return a.setScale(c["scale"] as int, _mode(c)).toString();
  }
  final b = PortableDecimal.parse(c["b"] as String);
  return switch (c["op"]) {
    "add" => (a + b).toString(),
    "sub" => (a - b).toString(),
    "mul" => (a * b).toString(),
    "compare" => a.compareTo(b),
    "equals" => a == b,
    "divide" => a.divide(b, c["scale"] as int, _mode(c)).toString(),
    _ => throw ArgumentError(c["op"]),
  };
}

Object _runRational(Map<String, dynamic> c) {
  final a = PortableRational.parse(c["a"] as String);
  switch (c["op"]) {
    case "parse":
      return a.toString();
    case "neg":
      return (-a).toString();
    case "abs":
      return a.abs().toString();
    case "toDouble":
      return a.toDouble();
    case "toDecimal":
      return a.toDecimal(c["scale"] as int, _mode(c)).toString();
  }
  final b = PortableRational.parse(c["b"] as String);
  return switch (c["op"]) {
    "add" => (a + b).toString(),
    "sub" => (a - b).toString(),
    "mul" => (a * b).toString(),
    "div" => (a / b).toString(),
    "compare" => a.compareTo(b),
    "equals" => a == b,
    _ => throw ArgumentError(c["op"]),
  };
}

final Map<String, Matcher> _errors = {
  "format": throwsFormatException,
  "zeroDivision": throwsUnsupportedError,
  "argument": throwsArgumentError,
};

void _check(Object Function(Map<String, dynamic>) run, Map<String, dynamic> c) {
  if (c.containsKey("error")) {
    expect(() => run(c), _errors[c["error"]], reason: "$c");
  } else if (c["op"] == "toDouble") {
    // Compared numerically, so the sign of zero is not checked (see SPEC 7).
    expect(run(c), _parseDouble(c["expected"] as String), reason: "$c");
  } else {
    expect(run(c), c["expected"], reason: "$c");
  }
}

void main() {
  for (final name in ["decimal_manual.json", "decimal_generated.json"]) {
    test("decimal vectors: $name", () {
      for (final c in _load(name)) {
        _check(_runDecimal, c);
      }
    });
  }
  for (final name in ["rational_manual.json", "rational_generated.json"]) {
    test("rational vectors: $name", () {
      for (final c in _load(name)) {
        _check(_runRational, c);
      }
    });
  }
}
