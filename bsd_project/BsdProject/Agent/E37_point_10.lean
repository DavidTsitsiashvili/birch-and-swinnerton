import BsdProject.Curves
import Mathlib.AlgebraicGeometry.EllipticCurve.Affine.Point

namespace BsdProject

theorem E37_point_10 : E37.toAffine.Equation 1 0 := by
  rw [WeierstrassCurve.Affine.equation_iff]
  simp [E37] <;> norm_num

end BsdProject
