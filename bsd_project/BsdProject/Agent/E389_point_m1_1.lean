import Mathlib.AlgebraicGeometry.EllipticCurve.Affine.Point
import BsdProject.Curves

namespace BsdProject

theorem E389_point_m1_1 : E389.toAffine.Equation (-1) 1 := by
  rw [WeierstrassCurve.Affine.equation_iff]
  first
    | norm_num [E389]
    | simp [E389]
    | (unfold E389; norm_num)

end BsdProject
