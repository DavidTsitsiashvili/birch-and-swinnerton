import Mathlib.AlgebraicGeometry.EllipticCurve.Weierstrass

set_option linter.style.header false
/-!
# First curves

Two elliptic curves from the LMFDB database:
* 37.a1  : y² + y = x³ - x         (rank 1, BSD proven)
* 389.a1 : y² + y = x³ + x² - 2x   (rank 2, BSD open)
-/

namespace BsdProject

/-- LMFDB 37.a1: y² + y = x³ - x -/
def E37 : WeierstrassCurve ℚ :=
  { a₁ := 0, a₂ := 0, a₃ := 1, a₄ := -1, a₆ := 0 }

/-- LMFDB 389.a1: y² + y = x³ + x² - 2x -/
def E389 : WeierstrassCurve ℚ :=
  { a₁ := 0, a₂ := 1, a₃ := 1, a₄ := -2, a₆ := 0 }

/-- The discriminant of 37.a1 is 37. -/
theorem E37_disc : E37.Δ = 37 := by
  norm_num [E37, WeierstrassCurve.Δ, WeierstrassCurve.b₂,
    WeierstrassCurve.b₄, WeierstrassCurve.b₆, WeierstrassCurve.b₈]

/-- The discriminant of 389.a1 is 389. -/
theorem E389_disc : E389.Δ = 389 := by
  norm_num [E389, WeierstrassCurve.Δ, WeierstrassCurve.b₂,
    WeierstrassCurve.b₄, WeierstrassCurve.b₆, WeierstrassCurve.b₈]

/-- Nonzero discriminant: 37.a1 really is an elliptic curve. -/
theorem E37_elliptic : IsUnit E37.Δ := by
  rw [E37_disc]; exact isUnit_iff_ne_zero.mpr (by norm_num)

/-- Nonzero discriminant: 389.a1 really is an elliptic curve. -/
theorem E389_elliptic : IsUnit E389.Δ := by
  rw [E389_disc]; exact isUnit_iff_ne_zero.mpr (by norm_num)

end BsdProject
