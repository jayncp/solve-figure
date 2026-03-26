# solvers — 求解器

`equilibrium.solvers` 提供求解器协议、三种求解器实现以及统一的结果类型。

```python
from equilibrium.solvers import (
    SolverStrategy,
    SolveResult, SolveAcceptance, SolverFailure,
    build_solve_result,
    ScipyRootSolver, ContinuationSolver, CompositeSolver,
)
```

## SolverStrategy

求解器协议（`Protocol`），所有求解器都满足此接口。

```python
class SolverStrategy(Protocol):
    name: str

    def solve(
        self,
        system: EquationSystem,
        params: Params,
        initial_guess: NDArrayFloat | None = None,
        *,
        options: dict[str, object] | None = None,
    ) -> SolveResult: ...
```

## SolveResult

求解结果的统一数据结构（`dataclass`）。

| 字段 | 类型 | 说明 |
|------|------|------|
| `success` | `bool` | 求解器是否报告收敛 |
| `method` | `str` | 使用的方法名称 |
| `x` | `NDArrayFloat` | 解向量 |
| `residual_norm` | `float` | 残差 L2 范数 |
| `variables` | `dict[str, float]` | 变量名到值的映射 |
| `constraints` | `ConstraintMap` | 约束检查结果 |
| `constraints_ok` | `bool` | 所有约束是否满足（全部 > 0） |
| `intermediates` | `IntermediateMap` | 中间值 |
| `metrics` | `MetricMap` | 后处理指标 |
| `message` | `str` | 求解器返回的消息 |
| `nfev` | `int \| None` | 函数评估次数 |
| `njev` | `int \| None` | 雅可比评估次数 |
| `failures` | `tuple[SolverFailure, ...]` | 失败记录列表 |

## SolveAcceptance

验收标准（`dataclass`，frozen）。用于 `ContinuationSolver` 判断每步是否接受。

```python
@dataclass(frozen=True, slots=True)
class SolveAcceptance:
    residual_tol: float = 1e-8
    require_success: bool = True
    require_constraints: bool = True

    def accepts(self, result: SolveResult) -> bool: ...
```

一个结果被接受需同时满足：
- `require_success=True` 时 `result.success == True`
- `require_constraints=True` 时 `result.constraints_ok == True`
- `result.residual_norm <= residual_tol`

## SolverFailure

失败记录（`dataclass`）。

| 字段 | 类型 | 说明 |
|------|------|------|
| `method` | `str` | 失败的方法名 |
| `message` | `str` | 错误消息 |
| `residual_norm` | `float \| None` | 残差范数（如有） |

## build_solve_result

```python
def build_solve_result(
    system: EquationSystem,
    params: Params,
    x: NDArrayFloat,
    *,
    success: bool,
    method: str,
    residual_norm: float,
    message: str,
    nfev: int | None = None,
    njev: int | None = None,
    failures: tuple[SolverFailure, ...] = (),
) -> SolveResult: ...
```

从 `system`、`params` 和解向量 `x` 构造完整的 `SolveResult`。自动按以下顺序计算：

1. `system.intermediates(x, params)`
2. `system.constraints(x, params, intermediates)`
3. `system.metrics(x, params, intermediates)`

同时调用 `validate_params`、`validate_x`、`ensure_finite` 进行校验。

## ScipyRootSolver

封装 `scipy.optimize.root` 的求解器。

```python
class ScipyRootSolver:
    def __init__(self, method: str = "hybr", *, require_constraints: bool = False) -> None: ...

    name: str  # "scipy.root[{method}]"

    def solve(self, system, params, initial_guess=None, *, options=None) -> SolveResult: ...
```

**构造参数：**

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `method` | `"hybr"` | scipy 方法名，常用 `"hybr"`、`"lm"` |
| `require_constraints` | `False` | 收敛但约束不满足时将 `success` 置为 `False` |

**`options` 支持的键：**

| 键 | 类型 | 说明 |
|----|------|------|
| `use_jacobian` | `bool` | 为 `True` 时使用 `system.jacobian` |
| 其余键 | — | 透传给 `scipy.optimize.root` 的 `options` |

`initial_guess` 为 `None` 时使用零向量。

## ContinuationSolver

参数延续求解器，沿路径逐步求解。

```python
class ContinuationSolver:
    def __init__(
        self,
        step_solver: SolverStrategy,
        *,
        acceptance: SolveAcceptance | None = None,
        path_builder: PathBuilder | None = None,
    ) -> None: ...

    name: str  # "continuation[{step_solver.name}]"

    def solve(self, system, params, initial_guess=None, *, options=None) -> SolveResult: ...
```

**构造参数：**

| 参数 | 说明 |
|------|------|
| `step_solver` | 每步使用的求解器 |
| `acceptance` | 验收标准，默认 `SolveAcceptance()` |
| `path_builder` | `Callable[[Params], tuple[Params, ...]]`，根据目标参数生成路径 |

**`options` 支持的键：**

| 键 | 类型 | 说明 |
|----|------|------|
| `continuation_path` | `Iterable[Mapping[str, float]]` | 显式路径（覆盖 `path_builder`） |
| `acceptance` | `SolveAcceptance` | 覆盖构造时设置的验收标准 |
| 其余键 | — | 透传给 `step_solver` |

路径解析优先级：`options["continuation_path"]` > 构造时的 `path_builder` > 单步直接求解。

## CompositeSolver

多策略组合求解器，按顺序尝试直到成功。

```python
class CompositeSolver:
    def __init__(self, strategies: list[SolverStrategy]) -> None: ...

    name: str  # "composite"

    def solve(self, system, params, initial_guess=None, *, options=None) -> SolveResult: ...
```

**构造参数：**

| 参数 | 说明 |
|------|------|
| `strategies` | 求解器列表，至少一个 |

**行为：**

- 按顺序尝试每个策略
- 第一个 `success == True` 且 `constraints_ok == True` 的结果立即返回
- 每个失败的策略记录到 `failures` 列表
- 全部失败时返回 `success=False` 的 `SolveResult`
- `options` 透传给每个子策略
