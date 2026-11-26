import BsdProject.Curves
import Mathlib.AlgebraicGeometry.EllipticCurve.Affine.Point

namespace BsdProject

theorem E37_nonsingular_10 : E37.toAffine.Nonsingular 1 0 := by
  rw [WeierstrassCurve.Affine.nonsingular_iff]
  refine ⟨?_, ?_⟩
  · rw [WeierstrassCurve.Affine.equation_iff]
    norm_num [E37]
  · first
    | (right; norm_num [E37])
    | (left; norm_num [E37])
    | norm_num [E37]

end BsdProject
