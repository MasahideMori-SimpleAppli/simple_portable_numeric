/// (en) Rounding modes used when an exact value must be reduced to fewer
/// digits. The member names and behavior are identical to the Python version.
///
/// (ja) 正確な値を少ない桁数に丸める際の丸めモードです。
/// メンバー名と動作はPython版と同一です。
enum EnumRoundingMode {
  /// (en) Nearest, ties to even (banker's rounding).
  ///
  /// (ja) 最も近い値へ。同距離の場合は偶数側（銀行丸め）。
  halfEven,

  /// (en) Nearest, ties away from zero.
  ///
  /// (ja) 最も近い値へ。同距離の場合は0から遠い側（四捨五入）。
  halfUp,

  /// (en) Toward zero.
  ///
  /// (ja) 0方向へ（切り捨て）。
  down,

  /// (en) Toward negative infinity.
  ///
  /// (ja) 負の無限大方向へ。
  floor,

  /// (en) Toward positive infinity.
  ///
  /// (ja) 正の無限大方向へ。
  ceiling,

  /// (en) Away from zero.
  ///
  /// (ja) 0から遠い側へ（切り上げ）。
  up,
}
