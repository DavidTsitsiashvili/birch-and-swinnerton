import Mathlib
import BsdProject.Curves

namespace BsdProject

theorem E5077_disc : ({ a₁ := 0, a₂ := 0, a₃ := 1, a₄ := -7, a₆ := 6 } : WeierstrassCurve ℚ).Δ = 5077 := by
  norm_num [WeierstrassCurve.Δ, WeierstrassCurve.b₂, WeierstrassCurve.b₄,
    WeierstrassCurve.b₆, WeierstrassCurve.b₈]

end BsdProject
