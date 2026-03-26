# ContinuationSolver 实现细节

`ContinuationSolver` 实现参数延续法：从容易求解的参数点出发，沿一条参数路径逐步推进到目标参数。

## 适用场景

- 目标参数下直接求解不收敛（初始值敏感）
- 存在一组"容易"的参数（如简化参数），从那里出发可以逐步走到目标
- 参数空间中解是连续变化的

## 路径解析

路径的来源按优先级：

1. **`options["continuation_path"]`**：显式传入的参数路径（`Iterable[Mapping[str, float]]`），最高优先级
2. **构造时的 `path_builder`**：`Callable[[Params], tuple[Params, ...]]`，根据目标参数自动生成路径
3. **单步直接求解**：两者都没有时，退化为单步直接求解（`(dict(params),)`）

路径中的每一步都是一个完整的参数字典。框架不做参数插值，路径的设计由使用者负责。

## 逐步求解

```
for step_params in path:
    result = step_solver.solve(system, step_params, initial_guess=current_guess)
    if acceptance.accepts(result):
        current_guess = result.x   # warm start: 传递给下一步
    else:
        return failure_result      # 立即中止
```

每步的逻辑：

1. 调用 `step_solver.solve` 求解当前步的参数
2. 用 `SolveAcceptance.accepts` 检查结果是否可接受
3. 接受则将 `result.x` 作为下一步的初始值
4. 不接受则立即返回失败结果，附带 `failures` 记录

## SolveAcceptance 的角色

`SolveAcceptance` 决定每步的结果是否可以作为基础继续推进：

```python
def accepts(self, result: SolveResult) -> bool:
    if self.require_success and not result.success:
        return False
    if self.require_constraints and not result.constraints_ok:
        return False
    return result.residual_norm <= self.residual_tol
```

默认配置（`residual_tol=1e-8`，`require_success=True`，`require_constraints=True`）要求每步都严格收敛且约束满足。可以在构造时或通过 `options["acceptance"]` 覆盖。

## 失败处理

失败时的结果构造有三层回退：

1. 尝试用当前 `current_guess` 调用 `build_solve_result`
2. 如果上一步失败，使用 `dataclasses.replace` 基于上一个有效结果修改
3. 最终兜底：使用零向量构造

每个失败步骤都记录为 `SolverFailure`，method 字段标注步骤索引（如 `"scipy.root[hybr]@step3"`）。

## 最终结果

路径全部通过后，返回最后一步的 `SolveResult`，method 改为 `"continuation[{step_solver.name}]"`。`failures` 列表为空（如果中途没有异常）。
