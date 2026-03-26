"""Two-period 11-variable equilibrium system from the TeX specification."""

from __future__ import annotations

from collections.abc import Mapping

import math
import numpy as np

from equilibrium.models.base import (
    ConstraintMap,
    EquationSystem,
    IntermediateMap,
    MetricMap,
    NDArrayFloat,
    Params,
)


class TwoPeriodModel(EquationSystem):
    """Two-period equilibrium system with 11 unknown coefficients."""

    @property
    def variable_names(self) -> tuple[str, ...]:
        return (
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

    @property
    def param_names(self) -> tuple[str, ...]:
        return (
            "J_I",
            "J_U",
            "sigma_v2",
            "sigma_u2",
            "sigma_epsilon2",
            "sigma_eta2",
            "rho",
        )

    def validate_params(self, params: Mapping[str, float]) -> None:
        super().validate_params(params)
        for name in ("sigma_v2", "sigma_u2", "sigma_epsilon2", "sigma_eta2"):
            if params[name] <= 0:
                raise ValueError(f"{name} must be positive")
        for name in ("J_I", "J_U"):
            if params[name] < 0:
                raise ValueError(f"{name} must be non-negative")
        if abs(params["rho"]) > 1:
            raise ValueError("rho must lie in [-1, 1]")

    def equations(self, x: NDArrayFloat, params: Params) -> NDArrayFloat:
        intermediates = self.intermediates(x, params)
        v = self.variable_dict(x)

        eq_beta_1 = v["beta_1"] - self._safe_div(
            "beta_1_rhs",
            2 * intermediates["total_alpha_2"] * intermediates["total_alpha_1"] ** 2
            + intermediates["total_alpha_1"]
            * intermediates["total_alpha_2"]
            * intermediates["total_delta"],
            4 * intermediates["total_alpha_2"] * intermediates["total_alpha_1"]
            - intermediates["total_delta"] ** 2,
        )
        eq_beta_2 = v["beta_2"] - 0.5 * (
            intermediates["total_alpha_2"]
            + v["beta_1"] * intermediates["drift_ratio_12"]
        )
        eq_delta_T = v["delta_T"] - 0.5 * (
            intermediates["total_delta"]
            - intermediates["drift_ratio_12"] * intermediates["total_alpha_1"]
        )

        eq_alpha_I_1 = v["alpha_I_1"] - self._safe_div(
            "alpha_I_1_rhs",
            2 * intermediates["F_informed"] * intermediates["G_informed"]
            - (v["delta_T"] - intermediates["D_informed"]) ** 2
            + intermediates["eq4_linear_term"]
            * intermediates["varphi_1"]
            * intermediates["G_informed"]
            - (v["delta_T"] - intermediates["D_informed"])
            * intermediates["psi_1"]
            * intermediates["G_informed"],
            intermediates["eq4_common_denom"],
        )
        eq_gamma_1 = v["gamma_1"] - self._safe_div(
            "gamma_1_rhs",
            intermediates["eq4_linear_term"]
            * (
                intermediates["varphi_1"] * (params["J_I"] - 1) * v["gamma_1"]
                + intermediates["varphi_2"]
            )
            - (v["delta_T"] - intermediates["D_informed"])
            * (
                intermediates["psi_1"] * (params["J_I"] - 1) * v["gamma_1"]
                + intermediates["psi_2"]
                - (params["J_I"] - 1) * v["gamma_2"]
            ),
            intermediates["eq4_common_denom"],
        )
        eq_alpha_I_2 = (
            intermediates["phi_1"] * intermediates["total_alpha_2"]
            + self._safe_div(
                "alpha_I_2_zero_eq", v["alpha_I_2"], intermediates["F_informed"]
            )
            - 1
        )
        eq_gamma_2 = v["gamma_2"] - self._safe_div(
            "gamma_2_rhs",
            -intermediates["F_informed"]
            * (
                intermediates["phi_2"] * params["J_I"] * v["gamma_1"]
                + intermediates["phi_3"]
            ),
            1 + intermediates["phi_1"] * params["J_I"] * intermediates["F_informed"],
        )
        eq_delta_I = v["delta_I"] - self._safe_div(
            "delta_I_rhs",
            -intermediates["F_informed"]
            * (
                intermediates["phi_1"] * (intermediates["D_informed"] - v["delta_T"])
                + intermediates["phi_2"] * intermediates["total_alpha_1"]
            ),
            1 + intermediates["phi_1"] * intermediates["F_informed"],
        )
        eq_alpha_U_1 = v["alpha_U_1"] - self._safe_div(
            "alpha_U_1_rhs",
            intermediates["alpha_U_1_num"] * intermediates["A_mixed"],
            intermediates["alpha_U_1_den"],
        )
        eq_alpha_U_2 = v["alpha_U_2"] - self._safe_div(
            "alpha_U_2_rhs",
            intermediates["B_mixed"]
            * (1 - intermediates["xi_2"] * params["J_I"] * v["alpha_I_2"]),
            intermediates["uninformed_update_den"],
        )
        eq_delta_U = v["delta_U"] - self._safe_div(
            "delta_U_rhs",
            -intermediates["B_mixed"]
            * (
                intermediates["xi_2"] * (params["J_I"] * v["delta_I"] - v["delta_T"])
                + intermediates["xi_1"] * intermediates["total_alpha_1"]
            ),
            intermediates["uninformed_update_den"],
        )

        return np.array(
            [
                eq_beta_1,
                eq_beta_2,
                eq_delta_T,
                eq_alpha_I_1,
                eq_gamma_1,
                eq_alpha_I_2,
                eq_gamma_2,
                eq_delta_I,
                eq_alpha_U_1,
                eq_alpha_U_2,
                eq_delta_U,
            ],
            dtype=float,
        )

    def intermediates(self, x: NDArrayFloat, params: Params) -> IntermediateMap:
        self.validate_params(params)
        vector = self.validate_x(x)
        v = self.variable_dict(vector)

        J_I = float(params["J_I"])
        J_U = float(params["J_U"])
        sigma_v2 = float(params["sigma_v2"])
        sigma_u2 = float(params["sigma_u2"])
        sigma_epsilon2 = float(params["sigma_epsilon2"])
        sigma_eta2 = float(params["sigma_eta2"])
        rho = float(params["rho"])

        beta_1 = v["beta_1"]
        beta_2 = v["beta_2"]
        delta_T = v["delta_T"]
        alpha_I_1 = v["alpha_I_1"]
        gamma_1 = v["gamma_1"]
        alpha_I_2 = v["alpha_I_2"]
        gamma_2 = v["gamma_2"]
        delta_I = v["delta_I"]
        alpha_U_1 = v["alpha_U_1"]
        alpha_U_2 = v["alpha_U_2"]
        delta_U = v["delta_U"]

        total_alpha_1 = J_I * alpha_I_1 + J_U * alpha_U_1
        total_alpha_2 = J_I * alpha_I_2 + J_U * alpha_U_2
        total_delta = J_I * delta_I + J_U * delta_U

        A_mixed = J_I * alpha_I_1 + (J_U - 1) * alpha_U_1
        B_mixed = J_I * alpha_I_2 + (J_U - 1) * alpha_U_2
        C_mixed = delta_T - J_I * delta_I - (J_U - 1) * delta_U
        D_informed = (J_I - 1) * delta_I + J_U * delta_U
        F_informed = (J_I - 1) * alpha_I_2 + J_U * alpha_U_2
        G_informed = (J_I - 1) * alpha_I_1 + J_U * alpha_U_1

        nu = self._safe_div("nu", sigma_u2, sigma_u2 + sigma_epsilon2)

        denom_varphi_psi = (beta_1**2 * sigma_v2 + sigma_u2) * (
            sigma_u2 + sigma_epsilon2
        ) - sigma_u2**2
        varphi_1 = self._safe_div(
            "varphi_1",
            beta_1 * sigma_v2 * (sigma_u2 + sigma_epsilon2),
            denom_varphi_psi,
        )
        varphi_2 = self._safe_div(
            "varphi_2",
            -beta_1 * sigma_v2 * sigma_u2,
            denom_varphi_psi,
        )
        psi_1 = self._safe_div(
            "psi_1",
            rho * sigma_u2 * sigma_epsilon2,
            denom_varphi_psi,
        )
        psi_2 = self._safe_div(
            "psi_2",
            rho * beta_1**2 * sigma_v2 * sigma_u2,
            denom_varphi_psi,
        )

        phi_noise_mix = ((1 - nu) ** 2) * sigma_u2 + (nu**2) * sigma_epsilon2
        denom_phi = sigma_v2 * phi_noise_mix * (
            beta_2 - rho * beta_1
        ) ** 2 + sigma_eta2 * (beta_1**2 * sigma_v2 + phi_noise_mix)
        phi_1 = self._safe_div(
            "phi_1",
            sigma_v2 * (beta_2 - rho * beta_1) * phi_noise_mix,
            denom_phi,
        )
        phi_2 = self._safe_div(
            "phi_2",
            sigma_v2
            * (rho * (beta_1 * rho - beta_2) * phi_noise_mix + beta_1 * sigma_eta2),
            denom_phi,
        )
        phi_3 = -nu * (rho * phi_1 + phi_2)

        cov11 = (
            beta_1**2 * sigma_v2
            + (1 - J_I * gamma_1) ** 2 * sigma_u2
            + J_I**2 * gamma_1**2 * sigma_epsilon2
        )
        cov12 = (
            beta_1 * beta_2 * sigma_v2
            + (1 - J_I * gamma_1) * (rho - J_I * gamma_2) * sigma_u2
            + J_I**2 * gamma_1 * gamma_2 * sigma_epsilon2
        )
        cov22 = (
            beta_2**2 * sigma_v2
            + (rho - J_I * gamma_2) ** 2 * sigma_u2
            + sigma_eta2
            + J_I**2 * gamma_2**2 * sigma_epsilon2
        )
        det_cov = cov11 * cov22 - cov12**2

        kappa_1 = self._safe_div("kappa_1", beta_1 * sigma_v2, cov11)
        # The TeX source uses J_1 in the denominator here; formula_audit treats that as a typo and
        # uses the same cov11 block as kappa_1.
        kappa_2 = self._safe_div("kappa_2", cov12, cov11)
        xi_1 = self._safe_div(
            "xi_1", beta_1 * sigma_v2 * cov22 - beta_2 * sigma_v2 * cov12, det_cov
        )
        xi_2 = self._safe_div(
            "xi_2", beta_2 * sigma_v2 * cov11 - beta_1 * sigma_v2 * cov12, det_cov
        )

        drift_ratio_12_den = (
            1 - J_I * gamma_1
        ) ** 2 * sigma_u2 + J_I**2 * gamma_1**2 * sigma_epsilon2
        drift_ratio_12 = self._safe_div(
            "drift_ratio_12",
            (rho - J_I * gamma_2) * (1 - J_I * gamma_1) * sigma_u2
            + J_I**2 * gamma_1 * gamma_2 * sigma_epsilon2,
            drift_ratio_12_den,
        )

        eq4_linear_term = F_informed * (
            delta_T - D_informed - 2 * G_informed
        ) - beta_2 * (delta_T - D_informed)
        eq4_common_denom = (
            2 * F_informed - varphi_1 * eq4_linear_term + psi_1 * (delta_T - D_informed)
        )

        alpha_U_1_num = (
            (2 * A_mixed * B_mixed - C_mixed**2)
            + A_mixed * B_mixed * (C_mixed - 2 * A_mixed) * kappa_1
            - A_mixed * C_mixed * kappa_2
        )
        alpha_U_1_den = (
            2 * A_mixed * B_mixed
            - A_mixed * B_mixed * (C_mixed - 2 * A_mixed) * kappa_1
            + A_mixed * C_mixed * kappa_2
        )
        uninformed_update_den = 1 + B_mixed * J_U * xi_2

        # The TeX source writes J_I * alpha_{U,1} in H's denominator; formula_audit records that as
        # a typo and uses total_alpha_1 = J_I * alpha_{I,1} + J_U * alpha_{U,1}.
        H_cov_v_p1 = self._safe_div("H_cov_v_p1", beta_1 * sigma_v2, total_alpha_1)
        J_cov_v_p2 = self._safe_div(
            "J_cov_v_p2",
            beta_2 * sigma_v2 + (delta_T - total_delta) * H_cov_v_p1,
            total_alpha_2,
        )
        K_var_p1 = self._safe_div("K_var_p1", cov11, total_alpha_1**2)
        L_cov_p1_p2 = self._safe_div(
            "L_cov_p1_p2_base",
            cov12,
            total_alpha_1 * total_alpha_2,
        ) + self._safe_div(
            "L_cov_p1_p2_feedback",
            (delta_T - total_delta) * K_var_p1,
            total_alpha_2,
        )
        S_price_feedback = self._safe_div(
            "S_price_feedback", delta_T - total_delta, total_alpha_1
        )
        M_var_p2 = self._safe_div(
            "M_var_p2",
            (beta_2 + beta_1 * S_price_feedback) ** 2 * sigma_v2
            + (rho - J_I * gamma_2 + (1 - J_I * gamma_1) * S_price_feedback) ** 2
            * sigma_u2
            + sigma_eta2
            + J_I**2 * (gamma_2 + gamma_1 * S_price_feedback) ** 2 * sigma_epsilon2,
            total_alpha_2**2,
        )
        N_cov_s_p1 = self._safe_div(
            "N_cov_s_p1",
            (1 - J_I * gamma_1) * sigma_u2 - J_I * gamma_1 * sigma_epsilon2,
            total_alpha_1,
        )
        Q_cov_s_p2 = self._safe_div(
            "Q_cov_s_p2",
            (rho - J_I * gamma_2) * sigma_u2
            - J_I * gamma_2 * sigma_epsilon2
            + (delta_T - total_delta) * N_cov_s_p1,
            total_alpha_2,
        )

        profit_insider = (
            beta_1 * (sigma_v2 - H_cov_v_p1)
            + beta_2 * (sigma_v2 - J_cov_v_p2)
            + delta_T * (H_cov_v_p1 - L_cov_p1_p2)
        )
        profit_informed_mm = (
            alpha_I_1 * (K_var_p1 - H_cov_v_p1)
            + gamma_1 * N_cov_s_p1
            + alpha_I_2 * (M_var_p2 - J_cov_v_p2)
            + gamma_2 * Q_cov_s_p2
            + delta_I * (L_cov_p1_p2 - H_cov_v_p1)
        )
        profit_uninformed_mm = (
            alpha_U_1 * (K_var_p1 - H_cov_v_p1)
            + alpha_U_2 * (M_var_p2 - J_cov_v_p2)
            + delta_U * (L_cov_p1_p2 - H_cov_v_p1)
        )

        intermediates: IntermediateMap = {
            "total_alpha_1": total_alpha_1,
            "total_alpha_2": total_alpha_2,
            "total_delta": total_delta,
            "A_mixed": A_mixed,
            "B_mixed": B_mixed,
            "C_mixed": C_mixed,
            "D_informed": D_informed,
            "F_informed": F_informed,
            "G_informed": G_informed,
            "nu": nu,
            "denom_varphi_psi": denom_varphi_psi,
            "varphi_1": varphi_1,
            "varphi_2": varphi_2,
            "psi_1": psi_1,
            "psi_2": psi_2,
            "phi_noise_mix": phi_noise_mix,
            "denom_phi": denom_phi,
            "phi_1": phi_1,
            "phi_2": phi_2,
            "phi_3": phi_3,
            "cov11": cov11,
            "cov12": cov12,
            "cov22": cov22,
            "det_cov": det_cov,
            "kappa_1": kappa_1,
            "kappa_2": kappa_2,
            "xi_1": xi_1,
            "xi_2": xi_2,
            "drift_ratio_12_den": drift_ratio_12_den,
            "drift_ratio_12": drift_ratio_12,
            "eq4_linear_term": eq4_linear_term,
            "eq4_common_denom": eq4_common_denom,
            "alpha_U_1_num": alpha_U_1_num,
            "alpha_U_1_den": alpha_U_1_den,
            "uninformed_update_den": uninformed_update_den,
            "H_cov_v_p1": H_cov_v_p1,
            "J_cov_v_p2": J_cov_v_p2,
            "K_var_p1": K_var_p1,
            "L_cov_p1_p2": L_cov_p1_p2,
            "S_price_feedback": S_price_feedback,
            "M_var_p2": M_var_p2,
            "N_cov_s_p1": N_cov_s_p1,
            "Q_cov_s_p2": Q_cov_s_p2,
            "profit_insider": profit_insider,
            "profit_informed_mm": profit_informed_mm,
            "profit_uninformed_mm": profit_uninformed_mm,
        }
        self._ensure_all_finite(intermediates)
        return intermediates

    def constraints(
        self,
        x: NDArrayFloat,
        params: Params,
        intermediates: IntermediateMap | None = None,
    ) -> ConstraintMap:
        if intermediates is None:
            intermediates = self.intermediates(x, params)
        v = self.variable_dict(x)

        return {
            "soc_total_alpha_2": intermediates["total_alpha_2"],
            "soc_total_determinant": 4
            * intermediates["total_alpha_2"]
            * intermediates["total_alpha_1"]
            - intermediates["total_delta"] ** 2,
            "soc_mixed_alpha_2": intermediates["B_mixed"],
            "soc_mixed_determinant": 4
            * intermediates["B_mixed"]
            * intermediates["A_mixed"]
            - intermediates["C_mixed"] ** 2,
            "soc_informed_alpha_2": intermediates["F_informed"],
            "soc_informed_determinant": 4
            * intermediates["F_informed"]
            * intermediates["G_informed"]
            - (
                v["delta_T"]
                - (params["J_I"] - 1) * v["delta_I"]
                - params["J_U"] * v["delta_U"]
            )
            ** 2,
        }

    def metrics(
        self,
        x: NDArrayFloat,
        params: Params,
        intermediates: IntermediateMap | None = None,
    ) -> MetricMap:
        if intermediates is None:
            intermediates = self.intermediates(x, params)
        return {
            "H_cov_v_p1": intermediates["H_cov_v_p1"],
            "J_cov_v_p2": intermediates["J_cov_v_p2"],
            "K_var_p1": intermediates["K_var_p1"],
            "L_cov_p1_p2": intermediates["L_cov_p1_p2"],
            "M_var_p2": intermediates["M_var_p2"],
            "N_cov_s_p1": intermediates["N_cov_s_p1"],
            "Q_cov_s_p2": intermediates["Q_cov_s_p2"],
            "S_price_feedback": intermediates["S_price_feedback"],
            "profit_insider": intermediates["profit_insider"],
            "profit_informed_mm": intermediates["profit_informed_mm"],
            "profit_uninformed_mm": intermediates["profit_uninformed_mm"],
        }

    def _safe_div(self, name: str, numerator: float, denominator: float) -> float:
        if not math.isfinite(denominator):
            raise ValueError(f"{name} denominator is not finite")
        if abs(denominator) < 1e-12:
            raise ValueError(f"{name} denominator is too close to zero")
        value = numerator / denominator
        if not math.isfinite(value):
            raise ValueError(f"{name} is not finite")
        return float(value)

    def _ensure_all_finite(self, values: Mapping[str, float]) -> None:
        for name, value in values.items():
            if not math.isfinite(value):
                raise ValueError(f"{name} is not finite")
