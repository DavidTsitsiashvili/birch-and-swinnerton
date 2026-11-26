import Mathlib.AlgebraicGeometry.EllipticCurve.Affine.Point
import BsdProject.Curves

namespace BsdProject

theorem E389_point_00 : E389.toAffine.Equation 0 0 := by
  first
  | (rw [WeierstrassCurve.Affine.equation_iff]; norm_num [E389])
  | (simp [WeierstrassCurve.Affine.equation_iff, E389])
  | (rw [WeierstrassCurve.Affine.equation_iff]; simp [E389])

end BsdProject
