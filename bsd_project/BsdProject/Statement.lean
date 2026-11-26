import Mathlib.AlgebraicGeometry.EllipticCurve.LFunction
import Mathlib.Analysis.Analytic.Order
import Mathlib.LinearAlgebra.Dimension.Finrank

/-!
# The weak Birch and Swinnerton-Dyer conjecture

Mathlib defines the L-series `E.LSeries s` of an elliptic curve. It only
converges for `re s > 3/2`. Its extension to all of ℂ follows from the
modularity theorem, which mathlib does not prove.

So, following advice on the Lean Zulip, weak BSD is stated as an implication:
for every entire function `f` that agrees with the L-series where it
converges (an analytic continuation), the order of vanishing of `f` at
`s = 1` equals the algebraic rank. By the identity theorem such an `f` is
unique, and modularity says it exists.
-/

namespace BsdProject

/-- The algebraic rank: the rank of the group of rational points E(ℚ). -/
noncomputable def algRank (E : WeierstrassCurve ℚ) : ℕ :=
  Module.finrank ℤ E.toAffine.Point

/-- Weak BSD for one curve `E`: every analytic continuation of `L(E, s)`
vanishes at `s = 1` to order exactly `algRank E`. -/
def WeakBSDFor (E : WeierstrassCurve ℚ) : Prop :=
  ∀ f : ℂ → ℂ, Differentiable ℂ f →
    (∀ s : ℂ, 3 / 2 < s.re → f s = E.LSeries s) →
    analyticOrderAt f 1 = (algRank E : ℕ∞)

/-- Weak BSD: holds for every elliptic curve over ℚ. -/
def WeakBSD : Prop :=
  ∀ E : WeierstrassCurve ℚ, IsUnit E.Δ → WeakBSDFor E

end BsdProject
