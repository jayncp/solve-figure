# 架构概述

本文档面向维护者，介绍框架的分层设计和核心设计决策。

## 分层结构

```
┌─────────────────────────────────────────────┐
│                  app                        │  CLI 入口 & demo pipeline
├─────────────────────────────────────────────┤
│                plotting                     │  ParameterSweep + FigurePlotter
├─────────────────────────────────────────────┤
│                solvers                      │  SolverStrategy 协议 & 实现
├─────────────────────────────────────────────┤
│                models                       │  EquationSystem ABC & 类型
├─────────────────────────────────────────────┤
│                utils                        │  校验工具
└─────────────────────────────────────────────┘
```

依赖方向严格**自上而下**：

- `models` 不依赖任何其他子包
- `utils` 仅依赖 `models`（引用 `NDArrayFloat` 类型）
- `solvers` 依赖 `models` 和 `utils`
- `plotting` 依赖 `models`、`solvers`、`utils`
- `app` 依赖所有子包

## 设计原则

### 模型接口无状态

`EquationSystem` 是纯函数式接口。所有方法接受 `(x, params)` 输入并返回结果，不在实例上存储状态。这使得同一个模型实例可以安全地被多个求解器和扫描过程共享。

### 求解器与模型解耦

求解器通过 `SolverStrategy` 协议接受任意 `EquationSystem`。求解器不知道模型的具体方程，只调用 `equations`、`intermediates`、`constraints`、`metrics` 等接口。新增模型不需要修改求解器，新增求解器不需要修改模型。

### 结果对象统一

所有求解器返回相同的 `SolveResult` 类型。`build_solve_result` 是唯一的结果构造路径，确保每个结果都经过参数校验、向量校验、有限性检查，并完整计算 intermediates → constraints → metrics 链。

### 扫描与绘图建立在 SolveResult 之上

`ParameterSweep` 在内部调用 `solver.solve`，收集 `SolveResult` 序列。`FigurePlotter` 从 `SweepResult` 中提取数据。整条链路不绕过 `SolveResult`，保证数据一致性。

## 类型约定

框架使用五个类型别名简化签名：

| 别名 | 定义 | 用途 |
|------|------|------|
| `Params` | `dict[str, float]` | 参数传递 |
| `NDArrayFloat` | `NDArray[np.float64]` | 解向量、残差向量 |
| `ConstraintMap` | `dict[str, float]` | 约束结果 |
| `MetricMap` | `dict[str, float]` | 后处理指标 |
| `IntermediateMap` | `dict[str, float]` | 中间值 |

所有这些别名定义在 `equilibrium.models.base` 中，由 `equilibrium.models` 统一导出。

## 扩展点

- **新增模型**：继承 `EquationSystem`，放入 `models/` 或独立目录
- **新增求解器**：实现 `SolverStrategy` 协议，注册到 `solvers/__init__.py`
- **新增绑图方式**：在 `FigurePlotter` 中添加方法，或直接从 `SweepResult` 取数据自行绑图
