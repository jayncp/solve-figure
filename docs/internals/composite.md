# CompositeSolver 实现细节

`CompositeSolver` 按顺序尝试多个求解策略，第一个成功的结果即返回。

## 策略执行逻辑

```
for strategy in strategies:
    result = strategy.solve(system, params, initial_guess, options)
    if result.success and result.constraints_ok:
        return result    # 第一个同时成功且约束满足的结果
    else:
        failures.append(...)  # 记录失败
```

判定一个策略"成功"需要同时满足两个条件：

- `result.success == True`（求解器报告收敛）
- `result.constraints_ok == True`（所有约束满足）

如果某个策略求解过程抛出异常，异常被捕获并记录为 `SolverFailure`，然后继续尝试下一个策略。

## 失败累积

每个未通过的策略（包括异常和非成功结果）都被记录到 `failures` 列表中。成功返回的结果中，`failures` 字段包含之前所有策略的失败记录，便于诊断。

## 全部失败时的回退

当所有策略都未通过时：

1. 如果提供了 `initial_guess`，使用它作为回退解向量
2. 如果 `initial_guess=None`，使用零向量
3. 通过 `build_solve_result` 构造 `success=False` 的结果
4. `method` 为 `"composite"`，`message` 为 `"All solver strategies failed"`

## 典型用法

```python
solver = CompositeSolver([
    ScipyRootSolver(method="hybr", require_constraints=True),
    ScipyRootSolver(method="lm", require_constraints=True),
    ScipyRootSolver(method="hybr", require_constraints=False),
])
```

上述配置的含义：

1. 先尝试 hybr 方法，要求约束满足
2. 失败则尝试 lm 方法，要求约束满足
3. 再失败则放宽约束要求，用 hybr 再试一次

`options` 参数会透传给每个子策略，不做过滤。
