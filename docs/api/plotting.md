# plotting — 扫描与画图

`equilibrium.plotting` 提供参数扫描执行器、结果数据类和绑图工具。

```python
from equilibrium.plotting import (
    ParameterSweep,
    SweepMode, SweepPoint, SweepPoint2D,
    SweepFailurePoint, SweepFailurePoint2D,
    SweepResult1D, SweepResult2D,
    FigurePlotter,
)
```

## ParameterSweep

执行参数扫描，沿一个或两个参数的值域批量求解。

### sweep_1d

```python
def sweep_1d(
    self,
    system: EquationSystem,
    solver: SolverStrategy,
    base_params: Params,
    sweep_param: str,
    sweep_values: NDArrayFloat,
    metric_names: list[str],
    *,
    initial_guess: NDArrayFloat | None = None,
    options: dict[str, object] | None = None,
    mode: SweepMode = "path",
) -> SweepResult1D: ...
```

沿一个参数扫描。`sweep_param` 必须是 `base_params` 中已有的键。

### sweep_2d

```python
def sweep_2d(
    self,
    system: EquationSystem,
    solver: SolverStrategy,
    base_params: Params,
    sweep_param_1: str,
    sweep_values_1: NDArrayFloat,
    sweep_param_2: str,
    sweep_values_2: NDArrayFloat,
    metric_names: list[str],
    *,
    initial_guess: NDArrayFloat | None = None,
    options: dict[str, object] | None = None,
    mode: SweepMode = "path",
) -> SweepResult2D: ...
```

沿两个参数构成的网格扫描。

### save_json

```python
def save_json(
    self,
    result: SweepResult1D | SweepResult2D,
    path: str | Path,
) -> Path: ...
```

将扫描结果序列化为 JSON 文件。自动创建父目录。

## SweepMode

```python
SweepMode = Literal["independent", "path"]
```

- `"path"`：每步成功后将解作为下一步的初始值（warm start）
- `"independent"`：每步都使用相同的初始值

## SweepPoint

一维扫描中的单个点（`dataclass`）。

| 字段 | 类型 | 说明 |
|------|------|------|
| `index` | `int` | 在扫描序列中的索引 |
| `sweep_value` | `float` | 当前扫描值 |
| `params` | `Params` | 当前参数字典 |
| `initial_guess` | `NDArrayFloat \| None` | 使用的初始值 |
| `result` | `SolveResult` | 求解结果 |

## SweepResult1D

一维扫描的完整结果（`dataclass`）。

| 字段 | 类型 |
|------|------|
| `mode` | `SweepMode` |
| `sweep_param` | `str` |
| `sweep_values` | `NDArrayFloat` |
| `metric_names` | `tuple[str, ...]` |
| `points` | `tuple[SweepPoint, ...]` |

**方法：**

| 方法 | 返回 | 说明 |
|------|------|------|
| `metric_series(name)` | `NDArrayFloat` | 某指标的值序列，失败点填 NaN |
| `success_mask()` | `NDArrayFloat` | 1.0 = 成功，0.0 = 失败 |
| `constraints_mask()` | `NDArrayFloat` | 1.0 = 约束满足 |
| `failure_points()` | `tuple[SweepFailurePoint, ...]` | 失败点摘要 |
| `to_dict()` | `dict[str, object]` | JSON 序列化 |

## SweepFailurePoint

一维扫描失败点摘要（`dataclass`）。

| 字段 | 类型 |
|------|------|
| `index` | `int` |
| `sweep_value` | `float` |
| `method` | `str` |
| `message` | `str` |
| `residual_norm` | `float` |

## SweepPoint2D

二维扫描中的单个点（`dataclass`）。

| 字段 | 类型 | 说明 |
|------|------|------|
| `row_index` | `int` | 第一参数的索引 |
| `col_index` | `int` | 第二参数的索引 |
| `sweep_value_1` | `float` | 第一参数值 |
| `sweep_value_2` | `float` | 第二参数值 |
| `params` | `Params` | 当前参数字典 |
| `initial_guess` | `NDArrayFloat \| None` | 使用的初始值 |
| `result` | `SolveResult` | 求解结果 |

## SweepResult2D

二维扫描的完整结果（`dataclass`）。

| 字段 | 类型 |
|------|------|
| `mode` | `SweepMode` |
| `sweep_param_1` | `str` |
| `sweep_values_1` | `NDArrayFloat` |
| `sweep_param_2` | `str` |
| `sweep_values_2` | `NDArrayFloat` |
| `metric_names` | `tuple[str, ...]` |
| `points` | `tuple[SweepPoint2D, ...]` |

**方法：**

| 方法 | 返回 | 说明 |
|------|------|------|
| `metric_grid(name)` | `NDArrayFloat` | 二维数组 `(len(values_1), len(values_2))` |
| `success_mask()` | `NDArrayFloat` | 二维掩码 |
| `constraints_mask()` | `NDArrayFloat` | 二维掩码 |
| `failure_points()` | `tuple[SweepFailurePoint2D, ...]` | 失败点摘要 |
| `to_dict()` | `dict[str, object]` | JSON 序列化 |

## SweepFailurePoint2D

二维扫描失败点摘要（`dataclass`）。

| 字段 | 类型 |
|------|------|
| `row_index` | `int` |
| `col_index` | `int` |
| `sweep_value_1` | `float` |
| `sweep_value_2` | `float` |
| `method` | `str` |
| `message` | `str` |
| `residual_norm` | `float` |

## FigurePlotter

将扫描结果绘制为 matplotlib 图表。使用 `Agg` 后端，不弹出窗口。

### plot_1d

```python
def plot_1d(
    self,
    result: SweepResult1D,
    metrics: list[str],
    *,
    title: str | None = None,
    xlabel: str | None = None,
    ylabel: str = "value",
) -> Figure: ...
```

绘制一维扫描的折线图。每个指标一条线，带圆点标记和图例。

### plot_2d_heatmap

```python
def plot_2d_heatmap(
    self,
    result: SweepResult2D,
    metric: str,
    *,
    title: str | None = None,
    xlabel: str | None = None,
    ylabel: str | None = None,
) -> Figure: ...
```

绘制二维扫描的热力图。

### save

```python
def save(self, figure: Figure, path: str | Path) -> Path: ...
```

保存图片（150 DPI），自动创建父目录，保存后关闭 figure。返回路径。
