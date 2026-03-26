# 快速开始

本页带你在 5 分钟内跑通完整的「定义模型 → 求解 → 扫描 → 画图」流程。

## 环境要求

- Python ≥ 3.13
- [uv](https://docs.astral.sh/uv/) 包管理器

## 安装

```bash
# 克隆仓库后进入项目目录
cd solve-figure0326

# 同步所有依赖（含开发工具）
uv sync --all-groups
```

## 运行内置 Demo

```bash
uv run solve-figure0326
```

输出：

```
demo pipeline complete: figure saved to output/demo_equilibrium_sweep.png
```

该命令完成了以下全部步骤：

1. 实例化内置的 `DemoEquilibriumModel`（一个 2 变量方程组）
2. 用 `CompositeSolver` 求解
3. 用 `ParameterSweep.sweep_1d` 沿 `curvature` 参数扫描 8 个点
4. 用 `FigurePlotter.plot_1d` 画图并保存到 `output/demo_equilibrium_sweep.png`

> 备用入口：`uv run python main.py`

## 完整示例：古诺双寡头

项目自带一个更贴近实际的示例 `examples/cournot_duopoly.py`，演示两家企业的古诺竞争均衡。

运行：

```bash
uv run python examples/cournot_duopoly.py
```

以下是该示例的核心代码，展示框架的四步工作流。

### 第一步：定义方程组

```python
import numpy as np
from equilibrium.models.base import EquationSystem, NDArrayFloat, Params

class CournotDuopoly(EquationSystem):
    @property
    def variable_names(self) -> tuple[str, ...]:
        return ("q1", "q2")

    @property
    def param_names(self) -> tuple[str, ...]:
        return ("a", "b", "c")

    def equations(self, x: NDArrayFloat, params: Params) -> NDArrayFloat:
        q1, q2 = x[0], x[1]
        a, b, c = params["a"], params["b"], params["c"]
        return np.array([
            a - 2 * b * q1 - b * q2 - c,
            a - b * q1 - 2 * b * q2 - c,
        ])

    def metrics(self, x: NDArrayFloat, params: Params,
                intermediates: dict[str, float] | None = None) -> dict[str, float]:
        q1, q2 = float(x[0]), float(x[1])
        price = params["a"] - params["b"] * (q1 + q2)
        return {
            "q1": q1, "q2": q2, "price": price,
            "profit1": (price - params["c"]) * q1,
        }
```

### 第二步：求解

```python
from equilibrium.solvers import CompositeSolver, ScipyRootSolver

model = CournotDuopoly()
solver = CompositeSolver([
    ScipyRootSolver(method="hybr", require_constraints=True),
    ScipyRootSolver(method="lm", require_constraints=True),
])

params = {"a": 10.0, "b": 1.0, "c": 2.0}
result = solver.solve(model, params, initial_guess=np.array([1.0, 1.0]))

print(f"q1={result.variables['q1']:.4f}, q2={result.variables['q2']:.4f}")
print(f"残差: {result.residual_norm:.2e}")
```

### 第三步：参数扫描

```python
from equilibrium.plotting import ParameterSweep

sweep = ParameterSweep()
sweep_result = sweep.sweep_1d(
    system=model,
    solver=solver,
    base_params={"a": 10.0, "b": 1.0, "c": 2.0},
    sweep_param="c",
    sweep_values=np.linspace(0.5, 8.0, 16),
    metric_names=["q1", "price", "profit1"],
    initial_guess=np.array([3.0, 3.0]),
    mode="path",
)
```

### 第四步：画图

```python
from pathlib import Path
from equilibrium.plotting import FigurePlotter

plotter = FigurePlotter()
fig = plotter.plot_1d(
    sweep_result,
    metrics=["q1", "price", "profit1"],
    title="Cournot Duopoly: Effect of Marginal Cost",
    xlabel="Marginal Cost (c)",
)
plotter.save(fig, Path("output/cournot_example.png"))
```

## 下一步

- [定义方程组](define-model.md) — 深入了解 `EquationSystem` 的全部能力
- [求解方程组](solve.md) — 了解不同求解器的选择与配置
- [参数扫描](parameter-sweep.md) — 一维和二维扫描的完整用法
