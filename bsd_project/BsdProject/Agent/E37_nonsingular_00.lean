import Mathlib.AlgebraicGeometry.EllipticCurve.Affine.Point
import BsdProject.Curves

namespace BsdProject

theorem E37_nonsingular_00 : E37.toAffine.Nonsingular 0 0 := by
  first
    | (rw [WeierstrassCurve.Affine.nonsingular_iff]
       constructor
       · rw [WeierstrassCurve.Affine.equation_iff]
         norm_num [E37]
       · norm_num [E37])
    | (rw [WeierstrassCurve.Affine.nonsingular_iff, WeierstrassCurve.Affine.equation_iff]
       norm_num [E37])
    | (rw [WeierstrassCurve.Affine.nonsingular_iff, WeierstrassCurve.Affine.equation_iff]
       simp [E37])
    | (simp [WeierstrassCurve.Affine.nonsingular_iff, WeierstrassCurve.Affine.equation_iff, E37])

end BsdProject
