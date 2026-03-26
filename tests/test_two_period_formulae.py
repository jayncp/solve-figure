import numpy as np
import pytest

from equilibrium.models import TwoPeriodModel


def build_sample_params() -> dict[str, float]:
    return {
        "J_I": 2.0,
        "J_U": 3.0,
        "sigma_v2": 1.5,
        "sigma_u2": 0.8,
        "sigma_epsilon2": 0.4,
        "sigma_eta2": 0.6,
        "rho": 0.3,
    }


def build_sample_x() -> np.ndarray:
    return np.array(
        [0.8, 0.9, 0.1, 0.4, 0.05, 0.35, 0.02, 0.03, 0.25, 0.2, 0.04],
        dtype=float,
    )


def test_two_period_model_names_match_audit_order() -> None:
    model = TwoPeriodModel()

    assert model.n_vars == 11
    assert model.variable_names[0] == "beta_1"
    assert model.variable_names[-1] == "delta_U"
    assert model.param_names == (
        "J_I",
        "J_U",
        "sigma_v2",
        "sigma_u2",
        "sigma_epsilon2",
        "sigma_eta2",
        "rho",
    )


def test_two_period_intermediates_match_selected_manual_formulae() -> None:
    model = TwoPeriodModel()
    params = build_sample_params()
    x = build_sample_x()

    intermediates = model.intermediates(x, params)

    total_alpha_1 = params["J_I"] * 0.4 + params["J_U"] * 0.25
    total_alpha_2 = params["J_I"] * 0.35 + params["J_U"] * 0.2
    total_delta = params["J_I"] * 0.03 + params["J_U"] * 0.04
    nu = params["sigma_u2"] / (params["sigma_u2"] + params["sigma_epsilon2"])

    cov11 = (
        0.8**2 * params["sigma_v2"]
        + (1 - params["J_I"] * 0.05) ** 2 * params["sigma_u2"]
        + params["J_I"] ** 2 * 0.05**2 * params["sigma_epsilon2"]
    )
    cov12 = (
        0.8 * 0.9 * params["sigma_v2"]
        + (1 - params["J_I"] * 0.05)
        * (params["rho"] - params["J_I"] * 0.02)
        * params["sigma_u2"]
        + params["J_I"] ** 2 * 0.05 * 0.02 * params["sigma_epsilon2"]
    )
    expected_kappa_2 = cov12 / cov11
    expected_h = 0.8 * params["sigma_v2"] / total_alpha_1

    assert intermediates["total_alpha_1"] == pytest.approx(total_alpha_1)
    assert intermediates["total_alpha_2"] == pytest.approx(total_alpha_2)
    assert intermediates["total_delta"] == pytest.approx(total_delta)
    assert intermediates["nu"] == pytest.approx(nu)
    assert intermediates["kappa_2"] == pytest.approx(expected_kappa_2)
    assert intermediates["H_cov_v_p1"] == pytest.approx(expected_h)


def test_two_period_equations_are_finite_and_have_expected_shape() -> None:
    model = TwoPeriodModel()

    equations = model.equations(build_sample_x(), build_sample_params())

    assert equations.shape == (11,)
    assert np.isfinite(equations).all()


def test_two_period_constraints_and_metrics_expose_expected_keys() -> None:
    model = TwoPeriodModel()
    params = build_sample_params()
    x = build_sample_x()
    intermediates = model.intermediates(x, params)

    constraints = model.constraints(x, params, intermediates=intermediates)
    metrics = model.metrics(x, params, intermediates=intermediates)

    assert set(constraints) == {
        "soc_total_alpha_2",
        "soc_total_determinant",
        "soc_mixed_alpha_2",
        "soc_mixed_determinant",
        "soc_informed_alpha_2",
        "soc_informed_determinant",
    }
    assert {
        "H_cov_v_p1",
        "J_cov_v_p2",
        "K_var_p1",
        "L_cov_p1_p2",
        "M_var_p2",
        "N_cov_s_p1",
        "Q_cov_s_p2",
        "profit_insider",
        "profit_informed_mm",
        "profit_uninformed_mm",
    }.issubset(metrics)


def test_two_period_intermediates_raise_clear_error_for_zero_price_denominator() -> (
    None
):
    model = TwoPeriodModel()
    params = build_sample_params()
    x = np.array(
        [0.2, 0.3, 0.1, 1.5, 0.0, 0.2, 0.0, 0.1, -1.0, 0.2, 0.1],
        dtype=float,
    )

    with pytest.raises(ValueError, match="H_cov_v_p1 denominator is too close to zero"):
        model.intermediates(x, params)


def test_two_period_validate_params_checks_basic_ranges() -> None:
    model = TwoPeriodModel()

    with pytest.raises(ValueError, match="sigma_v2 must be positive"):
        model.validate_params({**build_sample_params(), "sigma_v2": 0.0})

    with pytest.raises(ValueError, match="rho must lie in \\[-1, 1\\]"):
        model.validate_params({**build_sample_params(), "rho": 1.5})
