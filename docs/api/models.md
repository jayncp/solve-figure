# models — 模型定义

`equilibrium.models` 提供方程组的抽象基类和类型别名。

```python
from equilibrium.models import (
    EquationSystem,
    Params, NDArrayFloat,
    ConstraintMap, MetricMap, IntermediateMap,
    DemoEquilibriumModel,
)
```

## 类型别名

| 名称 | 定义 | 说明 |
|------|------|------|
| `Params` | `dict[str, float]` | 参数字典 |
| `NDArrayFloat` | `NDArray[np.float64]` | 一维浮点数组 |
| `ConstraintMap` | `dict[str, float]` | 约束名称到值的映射，值 > 0 表示满足 |
| `MetricMap` | `dict[str, float]` | 指标名称到值的映射 |
| `IntermediateMap` | `dict[str, float]` | 中间变量名称到值的映射 |

## EquationSystem

抽象基类，所有模型必须继承。

### 抽象方法（必须实现）

#### `variable_names -> tuple[str, ...]`

```python
@property
@abstractmethod
def variable_names(self) -> tuple[str, ...]: ...
```

未知量名称元组，顺序与解向量 `x` 一一对应。

#### `param_names -> tuple[str, ...]`

```python
@property
@abstractmethod
def param_names(self) -> tuple[str, ...]: ...
```

必需参数名称元组，用于 `validate_params` 自动校验。

#### `equations(x, params) -> NDArrayFloat`

```python
@abstractmethod
def equations(self, x: NDArrayFloat, params: Params) -> NDArrayFloat: ...
```

计算残差向量 F(x)。求解器的目标是找到 F(x) = 0 的解。

- `x`：形状为 `(n_vars,)` 的解向量
- `params`：参数字典
- 返回：形状为 `(n_vars,)` 的残差向量

### 可选方法（有默认实现）

#### `intermediates(x, params) -> IntermediateMap`

```python
def intermediates(self, x: NDArrayFloat, params: Params) -> IntermediateMap: ...
```

计算共享中间值。默认返回 `{}`。

#### `constraints(x, params, intermediates) -> ConstraintMap`

```python
def constraints(self, x: NDArrayFloat, params: Params,
                intermediates: IntermediateMap | None = None) -> ConstraintMap: ...
```

定义不等式约束。默认返回 `{}`。值 > 0 表示约束满足。

#### `metrics(x, params, intermediates) -> MetricMap`

```python
def metrics(self, x: NDArrayFloat, params: Params,
            intermediates: IntermediateMap | None = None) -> MetricMap: ...
```

计算后处理指标。默认返回 `{}`。

#### `jacobian(x, params) -> NDArrayFloat | None`

```python
def jacobian(self, x: NDArrayFloat, params: Params) -> NDArrayFloat | None: ...
```

返回解析雅可比矩阵。默认返回 `None`（使用数值差分）。

#### `validate_params(params) -> None`

```python
def validate_params(self, params: Mapping[str, float]) -> None: ...
```

校验参数名称完整性。多余或缺失的参数名会抛出 `ValueError`。可覆写以添加值域校验。

### 自动提供的方法

#### `n_vars -> int`

```python
@property
def n_vars(self) -> int: ...
```

未知量个数，等于 `len(variable_names)`。

#### `validate_x(x) -> NDArrayFloat`

```python
def validate_x(self, x: NDArrayFloat) -> NDArrayFloat: ...
```

校验解向量：必须是一维数组，长度等于 `n_vars`。返回归一化的 float 数组。

#### `variable_dict(x) -> dict[str, float]`

```python
def variable_dict(self, x: NDArrayFloat) -> dict[str, float]: ...
```

将解向量映射为 `{变量名: 值}` 字典。

## DemoEquilibriumModel

内置的 2 变量演示模型，用于框架验证。

- 变量：`x`, `y`
- 参数：`curvature`（必须 > 0）, `slope`（必须 ≥ 0）
- 方程：`x² - curvature = 0`，`y - slope·x = 0`
- 约束：`x > 0`，`y ≥ 0`
- 指标：`x`、`y`、`total`（x+y）、`product`（x·y）

此模型仅用于 `run_demo_pipeline` 和测试，不是业务模型模板。
