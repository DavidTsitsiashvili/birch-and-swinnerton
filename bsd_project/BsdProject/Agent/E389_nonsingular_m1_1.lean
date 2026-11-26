import BsdProject.Curves

/-- Compatibility shim: `toAffine` is no longer provided; the curve is its own affine model. -/
abbrev WeierstrassCurve.toAffine {R : Type*} [CommRing R] (W : WeierstrassCurve R) :
    WeierstrassCurve R := W

namespace BsdProject

theorem E389_nonsingular_m1_1 : E389.toAffine.Nonsingular (-1) 1 := by
  first
  | rw [WeierstrassCurve.nonsingular_iff]
  | unfold WeierstrassCurve.Nonsingular
  refine ⟨?_, Or.inr ?_⟩
  · first
    | (rw [WeierstrassCurve.equation_iff]; norm_num [E389])
    | (unfold WeierstrassCurve.Equation; norm_num [E389])
    | (simp [WeierstrassCurve.equation_iff, E389]; norm_num)
  · norm_num [E389]

end BsdProject
