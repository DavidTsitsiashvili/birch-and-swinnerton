import Mathlib.AlgebraicGeometry.EllipticCurve.Affine.Point
import BsdProject.Curves

namespace BsdProject

theorem E37_point_00 : E37.toAffine.Equation 0 0 := by
  first
  | (rw [WeierstrassCurve.Affine.equation_iff]; norm_num [E37])
  | (simp [WeierstrassCurve.Affine.equation_iff, E37])
  | (unfold WeierstrassCurve.Affine.Equation WeierstrassCurve.Affine.polynomial
     simp [E37])

end BsdProject
