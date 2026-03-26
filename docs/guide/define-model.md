# 定义方程组

所有模型都通过继承 `EquationSystem` 抽象基类来定义。框架对模型的唯一要求是：**给定参数和未知量向量，能计算出残差向量**。

## 最小可用模型

一个模型至少需要实现三个成员：

```python
from equilibrium.models.base import EquationSystem, NDArrayFloat, Params
import numpy as np

class MyModel(EquationSystem):
    @property
    def variable_names(self) -> tuple[str, ...]:
        return ("x", "y")

    @property
    def param_names(self) -> tuple[str, ...]:
        return ("a",)

    def equations(self, x: NDArrayFloat, params: Params) -> NDArrayFloat:
        return np.array([
            x[0] ** 2 - params["a"],
            x[1] - x[0],
        ])
```

| 成员 | 类型 | 作用 |
|------|------|------|
| `variable_names` | `property -> tuple[str, ...]` | 未知量名称，顺序与解向量 `x` 一一对应 |
| `param_names` | `property -> tuple[str, ...]` | 必需参数名称，用于 `validate_params` 自动校验 |
| `equations(x, params)` | `method -> NDArrayFloat` | 残差向量 F(x)，求解目标是 F(x) = 0 |

## 可选方法

以下方法有默认实现（返回空字典或 `None`），按需覆写即可。

### `intermediates(x, params) -> IntermediateMap`

计算方程组中的**共享中间值**。返回 `dict[str, float]`。

中间值会被 `build_solve_result` 自动计算并传递给 `constraints` 和 `metrics`，避免重复计算。

```python
def intermediates(self, x: NDArrayFloat, params: Params) -> dict[str, float]:
    q1, q2 = float(x[0]), float(x[1])
    price = params["a"] - params["b"] * (q1 + q2)
    return {"price": price, "total_quantity": q1 + q2}
```

### `constraints(x, params, intermediates) -> ConstraintMap`

定义不等式约束。返回 `dict[str, float]`，**值 > 0 表示约束满足**。

```python
def constraints(self, x: NDArrayFloat, params: Params,
                intermediates: dict[str, float] | None = None) -> dict[str, float]:
    if intermediates is None:
        intermediates = self.intermediates(x, params)
    return {
        "q1_positive": float(x[0]),
        "price_positive": intermediates["price"],
    }
```

约束结果会被记录在 `SolveResult.constraints` 中，`constraints_ok` 字段表示所有约束是否全部满足。`ScipyRootSolver` 开启 `require_constraints=True` 后，约束不满足的解会被标记为失败。

### `metrics(x, params, intermediates) -> MetricMap`

定义后处理指标。返回 `dict[str, float]`，在求解完成后计算，用于参数扫描时收集数据。

```python
def metrics(self, x: NDArrayFloat, params: Params,
            intermediates: dict[str, float] | None = None) -> dict[str, float]:
    if intermediates is None:
        intermediates = self.intermediates(x, params)
    return {
        "q1": float(x[0]),
        "price": intermediates["price"],
        "profit1": (intermediates["price"] - params["c"]) * float(x[0]),
    }
```

`ParameterSweep` 的 `metric_names` 参数指定要从每个求解点收集哪些指标。

### `jacobian(x, params) -> NDArrayFloat | None`

返回解析雅可比矩阵。默认返回 `None`，此时 scipy 使用数值差分。

如果方程组的雅可比容易手写，提供解析雅可比可以加速收敛：

```python
def jacobian(self, x: NDArrayFloat, params: Params) -> NDArrayFloat:
    return np.array([
        [2 * x[0], 0],
        [-1, 1],
    ])
```

使用时需在 `options` 中开启：

```python
result = solver.solve(model, params, options={"use_jacobian": True})
```

### `validate_params(params) -> None`

默认实现会检查参数名称是否与 `param_names` 完全匹配（多余或缺失均报错）。可以覆写以添加值域校验：

```python
def validate_params(self, params: Mapping[str, float]) -> None:
    super().validate_params(params)
    if params["a"] <= 0:
        raise ValueError("a must be positive")
```

## 自动提供的方法

以下方法由基类实现，通常不需要覆写：

| 方法 | 作用 |
|------|------|
| `n_vars` | 未知量个数，等于 `len(variable_names)` |
| `validate_x(x)` | 校验解向量维度，返回归一化的 1D float 数组 |
| `variable_dict(x)` | 将解向量映射为 `{变量名: 值}` 字典 |

## 完整示例

参见 `examples/cournot_duopoly.py`，其中 `CournotDuopoly` 实现了全部可选方法（`intermediates`、`constraints`、`metrics`），展示了一个完整的模型定义。

## 下一步

模型定义完成后，进入 [求解方程组](solve.md) 了解如何选择和调用求解器。
