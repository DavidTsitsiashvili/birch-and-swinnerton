import BsdProject.Curves
import Mathlib.AlgebraicGeometry.EllipticCurve.Affine.Point

namespace BsdProject

theorem E37_point_22 : E37.toAffine.Equation 2 2 := by
  rw [WeierstrassCurve.Affine.equation_iff]
  first
    | (norm_num [E37]; done)
    | (simp [E37]; norm_num; done)
    | (simp [E37]; done)
    | (unfold E37; norm_num; done)
    | (unfold E37; simp; done)

end BsdProject
