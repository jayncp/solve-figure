# Formula Audit

## Scope

This note is the hand-maintained coding guide for the 11-variable two-period system in [reference/tex_code.tex](/Users/jayncp/Desktop/jayncp_mac/tools/workapace/solve-figure0326/reference/tex_code.tex).

Covered source ranges:

- equilibrium system: `reference/tex_code.tex:217-356`
- expected profit section: `reference/tex_code.tex:358-430`

This document is intentionally operational:

- it separates unknowns, exogenous params, derived quantities, constraints, and metrics
- it proposes stable Python field names
- it records source issues that should not be guessed during implementation

## 1. Unknowns

Solve vector order from the TeX source:

1. `beta_1` for `\beta_1`
2. `beta_2` for `\beta_2`
3. `delta_T` for `\delta_T`
4. `alpha_I_1` for `\alpha_{I,1}`
5. `gamma_1` for `\gamma_1`
6. `alpha_I_2` for `\alpha_{I,2}`
7. `gamma_2` for `\gamma_2`
8. `delta_I` for `\delta_I`
9. `alpha_U_1` for `\alpha_{U,1}`
10. `alpha_U_2` for `\alpha_{U,2}`
11. `delta_U` for `\delta_U`

Recommended `variable_names`:

```python
(
    "beta_1",
    "beta_2",
    "delta_T",
    "alpha_I_1",
    "gamma_1",
    "alpha_I_2",
    "gamma_2",
    "delta_I",
    "alpha_U_1",
    "alpha_U_2",
    "delta_U",
)
```

## 2. Exogenous Parameters

Minimum parameter set implied by the formulas:

- `J_I`
- `J_U`
- `sigma_v2`
- `sigma_u2`
- `sigma_epsilon2`
- `sigma_eta2`
- `rho`

Derived, not exogenous:

- `nu = sigma_u2 / (sigma_u2 + sigma_epsilon2)`

Recommended `param_names`:

```python
(
    "J_I",
    "J_U",
    "sigma_v2",
    "sigma_u2",
    "sigma_epsilon2",
    "sigma_eta2",
    "rho",
)
```

## 3. Symbol Mapping

### 3.1 First-layer aggregates

- `A_mixed` for `A = J_I alpha_{I,1} + (J_U - 1) alpha_{U,1}`
- `B_mixed` for `B = J_I alpha_{I,2} + (J_U - 1) alpha_{U,2}`
- `C_mixed` for `C = delta_T - J_I delta_I - (J_U - 1) delta_U`
- `D_informed` for `D = (J_I - 1) delta_I + J_U delta_U`
- `F_informed` for `F = (J_I - 1) alpha_{I,2} + J_U alpha_{U,2}`
- `G_informed` for `G = (J_I - 1) alpha_{I,1} + J_U alpha_{U,1}`

Reason for suffixes:

- TeX uses single-letter symbols in different economic contexts.
- Python code should avoid bare `A`, `B`, `C`, `D`, `F`, `G`.

### 3.2 Auxiliary coefficients from period-1 filtering block

- `varphi_1` for `\varphi_1`
- `varphi_2` for `\varphi_2`
- `psi_1` for `\psi_1`
- `psi_2` for `\psi_2`

Shared denominator:

- `denom_varphi_psi = (beta_1**2 * sigma_v2 + sigma_u2) * (sigma_u2 + sigma_epsilon2) - sigma_u2**2`

### 3.3 Auxiliary coefficients from period-2 filtering block

- `phi_1` for `\phi_1`
- `phi_2` for `\phi_2`
- `phi_3` for `\phi_3`
- `nu` for `\nu`

Shared denominator:

- `denom_phi = sigma_v2 * (((1 - nu)**2) * sigma_u2 + (nu**2) * sigma_epsilon2) * (beta_2 - rho * beta_1)**2 + sigma_eta2 * (beta_1**2 * sigma_v2 + ((1 - nu)**2) * sigma_u2 + (nu**2) * sigma_epsilon2)`

### 3.4 Covariance-style coefficients

- `kappa_1` for `\kappa_1`
- `kappa_2` for `\kappa_2`
- `xi_1` for `\xi_1`
- `xi_2` for `\xi_2`

Recommended shared blocks:

- `cov11 = beta_1**2 * sigma_v2 + (1 - J_I * gamma_1)**2 * sigma_u2 + (J_I**2) * (gamma_1**2) * sigma_epsilon2`
- `cov12 = beta_1 * beta_2 * sigma_v2 + (1 - J_I * gamma_1) * (rho - J_I * gamma_2) * sigma_u2 + (J_I**2) * gamma_1 * gamma_2 * sigma_epsilon2`
- `cov22 = beta_2**2 * sigma_v2 + (rho - J_I * gamma_2)**2 * sigma_u2 + sigma_eta2 + (J_I**2) * (gamma_2**2) * sigma_epsilon2`
- `det_cov = cov11 * cov22 - cov12**2`

Those names are not in the TeX, but they are useful because both `xi_1` and `xi_2` are rational functions of the same three covariance-like pieces.

## 4. Equilibrium Equations

Implementation recommendation:

- store each equation as `lhs - rhs`
- name them `eq_beta_1`, `eq_beta_2`, ..., `eq_delta_U`
- return them in the same order as `variable_names`

### 4.1 Insider block

Equation 1:

- `beta_1 = [2 * total_alpha_2 * total_alpha_1**2 + total_alpha_1 * total_alpha_2 * total_delta] / [4 * total_alpha_2 * total_alpha_1 - total_delta**2]`

Suggested shared pieces:

- `total_alpha_1 = J_I * alpha_I_1 + J_U * alpha_U_1`
- `total_alpha_2 = J_I * alpha_I_2 + J_U * alpha_U_2`
- `total_delta = J_I * delta_I + J_U * delta_U`

Equation 2:

- `beta_2 = 0.5 * (total_alpha_2 + beta_1 * drift_ratio_12)`

Equation 3:

- `delta_T = 0.5 * (total_delta - drift_ratio_12 * total_alpha_1)`

Suggested shared ratio:

- `drift_ratio_12 = [(\rho - J_I gamma_2)(1 - J_I gamma_1) sigma_u2 + J_I**2 gamma_1 gamma_2 sigma_epsilon2] / [(1 - J_I gamma_1)**2 sigma_u2 + J_I**2 gamma_1**2 sigma_epsilon2]`

### 4.2 Informed market maker block

Equation 4:

- `alpha_I_1 = [2 F G - (delta_T - D)^2 + (F(delta_T - D - 2G) - beta_2(delta_T - D)) varphi_1 G - (delta_T - D) psi_1 G] / [2F - varphi_1(F(delta_T - D - 2G) - beta_2(delta_T - D)) + psi_1(delta_T - D)]`

Equation 5:

- `gamma_1 = {[F(delta_T - D - 2G) - beta_2(delta_T - D)] * (varphi_1 (J_I - 1) gamma_1 + varphi_2) - (delta_T - D) * (psi_1 (J_I - 1) gamma_1 + psi_2 - (J_I - 1) gamma_2)} / same_denom_as_eq4`

Equation 6:

- TeX writes this as a zero equation:
- `phi_1 * (J_I alpha_I_2 + J_U alpha_U_2) + alpha_I_2 / ((J_I - 1) alpha_I_2 + J_U alpha_U_2) - 1 = 0`

Equation 7:

- `gamma_2 = -F * (phi_2 * J_I * gamma_1 + phi_3) / (1 + phi_1 * J_I * F)`

Equation 8:

- `delta_I = -F * [phi_1(D - delta_T) + phi_2(J_I alpha_I_1 + J_U alpha_U_1)] / (1 + phi_1 F)`

### 4.3 Uninformed market maker block

Equation 9:

- `alpha_U_1 = numerator / denominator * (J_I alpha_I_1 + (J_U - 1) alpha_U_1)`
- numerator:
  `(2AB - C^2) + AB(C - 2A) kappa_1 - AC kappa_2`
- denominator:
  `2AB - AB(C - 2A) kappa_1 + AC kappa_2`

Equation 10:

- `alpha_U_2 = [(J_I alpha_I_2 + (J_U - 1) alpha_U_2) * (1 - xi_2 J_I alpha_I_2)] / [1 + (J_I alpha_I_2 + (J_U - 1) alpha_U_2) J_U xi_2]`

Equation 11:

- `delta_U = -[J_I alpha_I_2 + (J_U - 1) alpha_U_2] / [1 + (J_I alpha_I_2 + (J_U - 1) alpha_U_2) J_U xi_2] * [xi_2(J_I delta_I - delta_T) + xi_1(J_I alpha_I_1 + J_U alpha_U_1)]`

## 5. Derived Quantity Dependency Order

Recommended `intermediates()` evaluation order:

1. unpack variables and params
2. compute `total_alpha_1`, `total_alpha_2`, `total_delta`
3. compute `A_mixed`, `B_mixed`, `C_mixed`, `D_informed`, `F_informed`, `G_informed`
4. compute `nu`
5. compute `denom_varphi_psi`, then `varphi_1`, `varphi_2`, `psi_1`, `psi_2`
6. compute `denom_phi`, then `phi_1`, `phi_2`, `phi_3`
7. compute `cov11`, `cov12`, `cov22`, `det_cov`
8. compute `kappa_1`, `kappa_2`, `xi_1`, `xi_2`
9. compute price/profit metrics `H`, `J`, `K`, `L`, `M`, `N`, `Q`

This order matters because:

- equations 4 to 11 depend on layers 3 to 8
- metrics depend on the same algebra plus `H` to `Q`
- second-order conditions depend on layers 2 and 3

## 6. Second-Order Conditions

Recommended constraint names:

1. `soc_total_alpha_2`
2. `soc_total_determinant`
3. `soc_mixed_alpha_2`
4. `soc_mixed_determinant`
5. `soc_informed_alpha_2`
6. `soc_informed_determinant`

TeX forms:

1. `J_I alpha_I_2 + J_U alpha_U_2 > 0`
2. `4(J_I alpha_I_2 + J_U alpha_U_2)(J_I alpha_I_1 + J_U alpha_U_1) - (J_I delta_I + J_U delta_U)^2 > 0`
3. `J_I alpha_I_2 + (J_U - 1) alpha_U_2 > 0`
4. `4(J_I alpha_I_2 + (J_U - 1) alpha_U_2)(J_I alpha_I_1 + (J_U - 1) alpha_U_1) - (delta_T - J_I delta_I - (J_U - 1) delta_U)^2 > 0`
5. `(J_I - 1) alpha_I_2 + J_U alpha_U_2 > 0`
6. `4((J_I - 1) alpha_I_2 + J_U alpha_U_2)((J_I - 1) alpha_I_1 + J_U alpha_U_1) - (delta_T - (J_I - 1) delta_I - J_U delta_U)^2 > 0`

Implementation convention:

- `constraints()` should return the left-hand side value directly
- solver interprets `value > 0` as satisfied

## 7. Price and Profit Metrics

### 7.1 Price and covariance block

Recommended metric/intermediate names:

- `H_cov_v_p1`
- `J_cov_v_p2`
- `K_var_p1`
- `L_cov_p1_p2`
- `M_var_p2`
- `N_cov_s_p1`
- `Q_cov_s_p2`
- `S_price_feedback`

Definitions from TeX:

- `H = beta_1 sigma_v2 / (J_I alpha_I_1 + J_U alpha_U_1)`
- `J = [beta_2 sigma_v2 + (delta_T - total_delta) H] / (J_I alpha_I_2 + J_U alpha_U_2)`
- `K = [beta_1^2 sigma_v2 + (1 - J_I gamma_1)^2 sigma_u2 + J_I^2 gamma_1^2 sigma_epsilon2] / (J_I alpha_I_1 + J_U alpha_U_1)^2`
- `L = cov12 / [(J_I alpha_I_1 + J_U alpha_U_1)(J_I alpha_I_2 + J_U alpha_U_2)] + [(delta_T - total_delta) K] / (J_I alpha_I_2 + J_U alpha_U_2)`
- `S = (delta_T - total_delta) / (J_I alpha_I_1 + J_U alpha_U_1)`
- `M = [(\beta_2 + \beta_1 S)^2 sigma_v2 + (\rho - J_I gamma_2 + (1 - J_I gamma_1) S)^2 sigma_u2 + sigma_eta2 + J_I^2 (\gamma_2 + \gamma_1 S)^2 sigma_epsilon2] / (J_I alpha_I_2 + J_U alpha_U_2)^2`
- `N = [(1 - J_I gamma_1) sigma_u2 - J_I gamma_1 sigma_epsilon2] / (J_I alpha_I_1 + J_U alpha_U_1)`
- `Q = [(\rho - J_I gamma_2) sigma_u2 - J_I gamma_2 sigma_epsilon2 + (delta_T - total_delta) N] / (J_I alpha_I_2 + J_U alpha_U_2)`

### 7.2 Expected profit metrics

Recommended metric names:

- `profit_insider`
- `profit_informed_mm`
- `profit_uninformed_mm`

Definitions:

- insider: `beta_1 (sigma_v2 - H) + beta_2 (sigma_v2 - J) + delta_T (H - L)`
- informed MM: `alpha_I_1 (K - H) + gamma_1 N + alpha_I_2 (M - J) + gamma_2 Q + delta_I (L - H)`
- uninformed MM: `alpha_U_1 (K - H) + alpha_U_2 (M - J) + delta_U (L - H)`

## 8. Source Issues That Must Be Treated As Explicit Audit Notes

These should be preserved in code comments or in the final model docstring instead of being silently “fixed”.

### 8.1 Likely typo in `kappa_2` denominator

At `reference/tex_code.tex:334`, the denominator uses `J_1` twice:

- `(1 - J_1 gamma_1)^2`
- `J_1^2 gamma_1^2`

Inference:

- this is almost certainly meant to be `J_I`, matching every nearby expression and the `kappa_1` denominator

### 8.2 Likely typo in `H = C(v, p_1)` denominator

At `reference/tex_code.tex:376`, TeX writes:

- `J_I alpha_{I,1} + J_I alpha_{U,1}`

Inference:

- this is almost certainly meant to be `J_I alpha_{I,1} + J_U alpha_{U,1}`
- all later `p_1` denominators use the `J_U` form

### 8.3 `alpha_{U,1}` equation punctuation is malformed

At `reference/tex_code.tex:272-285`, the equation ends with:

- `(...)(J_I alpha_{I,1} + (J_U - 1) alpha_{U,1}),`
- then a standalone `,`

Interpretation to implement:

- treat the intended formula as one equation with no extra algebra after the trailing factor

### 8.4 `xi_1` and `xi_2` use custom `\splitfrac`

The document defines these over multiple broken lines with a custom macro.

Implementation note:

- do not attempt to parse these automatically
- rewrite them manually into standard numerator/denominator code before implementing

### 8.5 Boundary cases are not automatically safe

The TeX system includes terms with:

- `(J_I - 1)`
- `(J_U - 1)`
- denominators involving `F_informed`, `A_mixed`, `B_mixed`, `det_cov`

Implication:

- edge cases such as `J_I = 0`, `J_I = 1`, or `J_U = 0` must be treated as explicit numerical regimes
- continuation start points cannot be assumed from the full system without separate analysis

## 9. Recommended Implementation Split

When writing `TwoPeriodModel`, keep the code split into these private helpers:

1. `_unpack(x, params)`
2. `_core_aggregates(...)`
3. `_filter_block_period_1(...)`
4. `_filter_block_period_2(...)`
5. `_covariance_block(...)`
6. `_price_profit_block(...)`
7. `intermediates(...)`
8. `equations(...)`
9. `constraints(...)`
10. `metrics(...)`

This is mainly to keep the rational expressions debuggable.

## 10. Step 6 Coding Checklist

Before implementing the 11-variable model:

1. encode the symbol mapping from this file into Python field names
2. choose one explicit treatment for the suspected typos and record it in code comments
3. implement `intermediates()` first
4. unit-test each shared denominator for finiteness and expected failure behavior
5. implement equations second
6. implement constraints third
7. implement metrics last

This should prevent equation debugging and formula transcription from getting mixed together.
