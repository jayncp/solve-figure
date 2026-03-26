"""
古诺双寡头 (Cournot Duopoly) — 用框架求解并画图的完整示例
============================================================

经济背景:
  两家企业在同一个市场中竞争，各自选择产量 q1, q2。
  逆需求函数: P = a - b*(q1 + q2)
  成本函数:   C_i = c * q_i

  每家企业最大化利润: π_i = (P - c) * q_i
  一阶条件 (FOC) 构成方程组:
    a - 2b*q1 - b*q2 - c = 0
    a - b*q1 - 2b*q2 - c = 0

  解析解: q1 = q2 = (a - c) / (3b)

我们用框架:
  1. 定义方程组
  2. 求解
  3. 扫描参数 c (成本) 从 0 到 8，观察均衡产量和利润变化
  4. 画图
"""

from pathlib import Path

import numpy as np

from equilibrium.models.base import EquationSystem, NDArrayFloat, Params
from equilibrium.plotting.figures import FigurePlotter
from equilibrium.plotting.sweep import ParameterSweep
from equilibrium.solvers.composite import CompositeSolver
from equilibrium.solvers.scipy_root import ScipyRootSolver


# ── Step 1: 定义方程组 ──────────────────────────────────────────────


class CournotDuopoly(EquationSystem):
    """两家企业的古诺竞争模型。"""

    @property
    def variable_names(self) -> tuple[str, ...]:
        return ("q1", "q2")

    @property
    def param_names(self) -> tuple[str, ...]:
        return ("a", "b", "c")  # a: 需求截距, b: 需求斜率, c: 边际成本

    def equations(self, x: NDArrayFloat, params: Params) -> NDArrayFloat:
        q1, q2 = x[0], x[1]
        a, b, c = params["a"], params["b"], params["c"]
        return np.array(
            [
                a - 2 * b * q1 - b * q2 - c,  # 企业1的FOC
                a - b * q1 - 2 * b * q2 - c,  # 企业2的FOC
            ]
        )

    def intermediates(self, x: NDArrayFloat, params: Params) -> dict[str, float]:
        q1, q2 = float(x[0]), float(x[1])
        a, b = params["a"], params["b"]
        price = a - b * (q1 + q2)
        return {"price": price, "total_quantity": q1 + q2}

    def constraints(
        self,
        x: NDArrayFloat,
        params: Params,
        intermediates: dict[str, float] | None = None,
    ) -> dict[str, float]:
        if intermediates is None:
            intermediates = self.intermediates(x, params)
        return {
            "q1_positive": float(x[0]),  # q1 > 0
            "q2_positive": float(x[1]),  # q2 > 0
            "price_positive": intermediates["price"],  # P > 0
        }

    def metrics(
        self,
        x: NDArrayFloat,
        params: Params,
        intermediates: dict[str, float] | None = None,
    ) -> dict[str, float]:
        if intermediates is None:
            intermediates = self.intermediates(x, params)
        q1, q2 = float(x[0]), float(x[1])
        c = params["c"]
        price = intermediates["price"]
        return {
            "q1": q1,
            "q2": q2,
            "price": price,
            "profit1": (price - c) * q1,
            "profit2": (price - c) * q2,
            "total_quantity": intermediates["total_quantity"],
        }


# ── Step 2: 求解单个点 ──────────────────────────────────────────────

model = CournotDuopoly()
solver = CompositeSolver(
    [
        ScipyRootSolver(method="hybr", require_constraints=True),
        ScipyRootSolver(method="lm", require_constraints=True),
    ]
)

params = {"a": 10.0, "b": 1.0, "c": 2.0}
result = solver.solve(model, params, initial_guess=np.array([1.0, 1.0]))

print("=" * 50)
print("单点求解结果")
print("=" * 50)
print(f"  解:      q1={result.variables['q1']:.4f}, q2={result.variables['q2']:.4f}")
print(f"  解析解:  q1=q2={(params['a'] - params['c']) / (3 * params['b']):.4f}")
print(f"  价格:    P={result.metrics['price']:.4f}")
print(f"  利润:    π1={result.metrics['profit1']:.4f}")
print(f"  残差:    {result.residual_norm:.2e}")
print(f"  约束满足: {result.constraints_ok}")
print()


# ── Step 3: 参数扫描 ────────────────────────────────────────────────

sweep = ParameterSweep()

# 扫描 c (边际成本) 从 0 到 8，看产量和利润如何变化
sweep_result = sweep.sweep_1d(
    system=model,
    solver=solver,
    base_params={"a": 10.0, "b": 1.0, "c": 2.0},
    sweep_param="c",
    sweep_values=np.linspace(0.5, 8.0, 16),
    metric_names=["q1", "price", "profit1", "total_quantity"],
    initial_guess=np.array([3.0, 3.0]),
    mode="path",
)

print("=" * 50)
print("参数扫描结果 (c 从 0.5 到 8.0)")
print("=" * 50)
print(f"  成功点: {int(sweep_result.success_mask().sum())}/{len(sweep_result.points)}")
print(f"  失败点: {len(sweep_result.failure_points())}")
print()


# ── Step 4: 画图 ─────────────────────────────────────────────────────

plotter = FigurePlotter()

fig = plotter.plot_1d(
    sweep_result,
    metrics=["q1", "price", "profit1"],
    title="Cournot Duopoly: Effect of Marginal Cost",
    xlabel="Marginal Cost (c)",
    ylabel="Value",
)

output_path = plotter.save(fig, Path("output/cournot_example.png"))
print(f"图像已保存: {output_path}")
