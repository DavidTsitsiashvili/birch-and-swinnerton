import Mathlib.AlgebraicGeometry.EllipticCurve.Affine.Point
import Mathlib.LinearAlgebra.Dimension.Finrank

/-!
# The BSD rank statement (draft for expert review)

The algebraic rank is defined from mathlib's group of rational points.
Mathlib does not yet define L-functions of elliptic curves, so the
analytic rank is taken as an input `analyticRank`.
-/

namespace BsdProject

/-- The algebraic rank: the rank of the group of rational points E(ℚ). -/
noncomputable def algRank (E : WeierstrassCurve ℚ) : ℕ :=
  Module.finrank ℤ E.toAffine.Point

/-- BSD, rank part: for every elliptic curve over ℚ, the algebraic rank
equals the analytic rank (order of vanishing of L(E, s) at s = 1). -/
def BSDRank (analyticRank : WeierstrassCurve ℚ → ℕ) : Prop :=
  ∀ E : WeierstrassCurve ℚ, IsUnit E.Δ → algRank E = analyticRank E

end BsdProject
