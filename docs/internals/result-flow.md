# 结果构造流程

`build_solve_result` 是所有求解器用于构造 `SolveResult` 的统一入口。理解这个函数的数据流有助于调试和扩展。

## 调用链

```
solver.solve()
  └── build_solve_result(system, params, x, ...)
        ├── system.validate_params(params)     # 校验参数完整性
        ├── to_float_array(x)                  # 转换为 float64 数组
        ├── system.validate_x(x)               # 校验维度
        ├── ensure_finite("solution vector", x) # 检查 NaN/inf
        ├── system.intermediates(x, params)     # 计算中间值
        ├── system.constraints(x, params, intermediates)  # 计算约束
        ├── system.metrics(x, params, intermediates)      # 计算指标
        ├── constraints_ok(constraints)         # 判定约束是否全部满足
        └── SolveResult(...)                    # 组装结果
```

## 为什么统一计算

`intermediates`、`constraints`、`metrics` 的计算被集中在 `build_solve_result` 中，而不是由模型自行组装，原因如下：

1. **避免重复计算**：`intermediates` 只计算一次，传递给 `constraints` 和 `metrics` 复用
2. **保证完整性**：任何求解器返回的结果都包含完整的约束和指标信息
3. **统一校验**：参数、解向量、有限性检查在一处完成

## 失败路径

当求解器在内部捕获异常时（如 `ContinuationSolver` 的某一步失败），也通过 `build_solve_result` 构造失败结果，传入 `success=False` 和 `failures` 记录。此时 `intermediates`、`constraints`、`metrics` 仍然会被计算（基于当前 `x`），这样即使失败的结果也包含诊断信息。

如果构造过程本身抛出异常（如 `x` 包含 NaN），`ContinuationSolver` 会回退到 `dataclasses.replace` 基于上一个有效结果构造失败记录，最终兜底使用零向量。

## 被调用的位置

当前代码中，`build_solve_result` 被以下位置调用：

- `ScipyRootSolver.solve` — 正常路径
- `CompositeSolver.solve` — 全部策略失败时的回退
- `ContinuationSolver._build_failure_result` — 步骤失败时的回退
- `ParameterSweep.sweep_1d` / `sweep_2d` — 扫描中求解器抛异常时的回退
