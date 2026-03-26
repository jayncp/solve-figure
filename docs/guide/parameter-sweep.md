# 参数扫描

`ParameterSweep` 自动沿参数空间批量求解，收集每个点的指标数据。

## 一维扫描

```python
import numpy as np
from equilibrium.plotting import ParameterSweep

sweep = ParameterSweep()

result = sweep.sweep_1d(
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

**参数说明：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `system` | `EquationSystem` | 模型实例 |
| `solver` | `SolverStrategy` | 求解器实例 |
| `base_params` | `Params` | 基准参数，扫描时替换其中一个 |
| `sweep_param` | `str` | 要扫描的参数名 |
| `sweep_values` | `NDArrayFloat` | 扫描值序列 |
| `metric_names` | `list[str]` | 要收集的指标名称，对应 `metrics()` 返回的键 |
| `initial_guess` | `NDArrayFloat \| None` | 初始猜测值 |
| `options` | `dict \| None` | 传递给求解器的选项 |
| `mode` | `"path" \| "independent"` | 扫描模式（见下文） |

### 扫描模式

- **`mode="path"`**（默认）：每步成功后，将解作为下一步的初始值（warm start）。适合参数连续变化、解也连续变化的场景。
- **`mode="independent"`**：每步都使用相同的 `initial_guess`，各步互不影响。适合参数跳跃较大、或需要并行验证的场景。

## 二维扫描

```python
result_2d = sweep.sweep_2d(
    system=model,
    solver=solver,
    base_params={"a": 10.0, "b": 1.0, "c": 2.0},
    sweep_param_1="a",
    sweep_values_1=np.linspace(5.0, 15.0, 10),
    sweep_param_2="c",
    sweep_values_2=np.linspace(0.5, 8.0, 10),
    metric_names=["price", "profit1"],
    initial_guess=np.array([3.0, 3.0]),
    mode="path",
)
```

二维扫描逐行遍历，`mode="path"` 时每行内 warm start，行间也传递上一行最后成功的解。

## 使用扫描结果

### SweepResult1D

```python
# 取某个指标的序列（与 sweep_values 对齐，失败点填 NaN）
q1_series = result.metric_series("q1")

# 布尔掩码
success = result.success_mask()       # 1.0 = 成功, 0.0 = 失败
feasible = result.constraints_mask()   # 1.0 = 约束满足

# 失败诊断
for fp in result.failure_points():
    print(f"index={fp.index}, value={fp.sweep_value}, msg={fp.message}")
```

### SweepResult2D

```python
# 取指标的二维网格 (len(values_1) x len(values_2))
grid = result_2d.metric_grid("price")

# 同样支持 success_mask()、constraints_mask()、failure_points()
```

## 导出 JSON

```python
sweep.save_json(result, "output/sweep_result.json")
```

输出为 JSON 格式，包含每个扫描点的参数、求解状态、指标和约束信息。结构参见 `SweepResult1D.to_dict()` / `SweepResult2D.to_dict()` 方法。

## 下一步

- [画图与导出](plotting.md) — 将扫描结果绘制为折线图或热力图
