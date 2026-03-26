# 求解方程组

模型定义完成后，用求解器求解 F(x) = 0。框架提供三种求解器，满足不同场景。

## ScipyRootSolver：基础求解

最常用的求解器，封装了 `scipy.optimize.root`。

```python
from equilibrium.solvers import ScipyRootSolver

solver = ScipyRootSolver(method="hybr", require_constraints=True)
result = solver.solve(model, params, initial_guess=np.array([1.0, 1.0]))
```

**构造参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `method` | `str` | `"hybr"` | scipy 求解方法，常用 `"hybr"`、`"lm"` |
| `require_constraints` | `bool` | `False` | 为 `True` 时，收敛但约束不满足的解标记为失败 |

**solve 参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `system` | `EquationSystem` | 模型实例 |
| `params` | `Params` | 参数字典 |
| `initial_guess` | `NDArrayFloat \| None` | 初始值，`None` 时使用零向量 |
| `options` | `dict \| None` | 可选配置，支持 `use_jacobian: True` |

## CompositeSolver：多策略回退

按顺序尝试多个求解器，第一个**成功且约束满足**的结果即返回。

```python
from equilibrium.solvers import CompositeSolver, ScipyRootSolver

solver = CompositeSolver([
    ScipyRootSolver(method="hybr", require_constraints=True),
    ScipyRootSolver(method="lm", require_constraints=True),
])
result = solver.solve(model, params, initial_guess=np.array([1.0, 1.0]))
```

适用场景：不确定哪种方法对当前问题最优时，让框架自动回退。

## ContinuationSolver：参数延续

从容易求解的参数点出发，沿一条参数路径逐步推进到目标参数。每步的解作为下一步的初始值。

```python
from equilibrium.solvers import ContinuationSolver, ScipyRootSolver, SolveAcceptance

step_solver = ScipyRootSolver(method="hybr", require_constraints=True)
solver = ContinuationSolver(step_solver)

# 通过 options 传入 continuation path
path = [
    {"a": 10.0, "b": 1.0, "c": 0.5},
    {"a": 10.0, "b": 1.0, "c": 1.5},
    {"a": 10.0, "b": 1.0, "c": 2.0},  # 目标参数
]
result = solver.solve(model, params, initial_guess=x0,
                      options={"continuation_path": path})
```

也可以在构造时传入 `path_builder` 函数，自动根据目标参数生成路径：

```python
def my_path_builder(target: Params) -> tuple[Params, ...]:
    steps = []
    for c in np.linspace(0.0, target["c"], 5):
        step = dict(target)
        step["c"] = float(c)
        steps.append(step)
    return tuple(steps)

solver = ContinuationSolver(step_solver, path_builder=my_path_builder)
```

## SolveResult：求解结果

所有求解器返回统一的 `SolveResult` 对象。

```python
result = solver.solve(model, params)

# 常用字段
result.success          # bool: 是否收敛
result.variables        # dict[str, float]: {"q1": 2.67, "q2": 2.67}
result.x                # NDArrayFloat: 解向量
result.residual_norm    # float: 残差 L2 范数
result.constraints_ok   # bool: 所有约束是否满足
result.metrics          # dict[str, float]: 后处理指标
result.method           # str: 实际使用的方法名
result.message          # str: 求解器消息
result.failures         # tuple[SolverFailure, ...]: 失败记录
```

## 初始值建议

- 初始值的选择对收敛性影响很大。尽量给出接近真实解的估计。
- `initial_guess=None` 时使用零向量，适合简单问题。
- 对于困难问题，可以先在容易的参数下求解，再用 `ContinuationSolver` 或 `ParameterSweep` 的 `mode="path"` 逐步推进。

## options 传递规则

`options` 字典会直接传递给底层求解器：

- `ScipyRootSolver`：`use_jacobian` 由框架处理，其余键透传给 `scipy.optimize.root` 的 `options`。
- `ContinuationSolver`：`continuation_path` 和 `acceptance` 由框架处理，其余键透传给内部的 `step_solver`。
- `CompositeSolver`：`options` 透传给每个子策略。

## 下一步

- [参数扫描](parameter-sweep.md) — 沿参数路径批量求解并收集指标
- [画图与导出](plotting.md) — 将扫描结果可视化
