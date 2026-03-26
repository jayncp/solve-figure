# 模块总览

## 包结构

```
equilibrium
├── models       # 模型抽象与类型定义
├── solvers      # 求解器协议、实现与结果类型
├── plotting     # 参数扫描与绑图工具
├── utils        # 通用校验函数
└── app          # Demo pipeline 入口
```

## 推荐导入路径

日常使用通过子包导入即可，不需要深入到具体文件：

```python
# 模型定义
from equilibrium.models import EquationSystem, Params, NDArrayFloat

# 求解器
from equilibrium.solvers import (
    ScipyRootSolver, CompositeSolver, ContinuationSolver,
    SolveResult, SolveAcceptance,
)

# 扫描与画图
from equilibrium.plotting import ParameterSweep, FigurePlotter, SweepResult1D

# 工具函数
from equilibrium.utils import to_float_array, constraints_ok
```

## 面向使用者 vs 内部实现

| 模块 | 面向 | 说明 |
|------|------|------|
| `equilibrium.models` | 使用者 | 定义模型时需要继承和使用的类型 |
| `equilibrium.solvers` | 使用者 | 选择求解器、检查结果 |
| `equilibrium.plotting` | 使用者 | 执行扫描、绑制图表 |
| `equilibrium.utils` | 使用者/内部 | 通用校验，使用者偶尔用到 |
| `equilibrium.app` | 内部 | Demo pipeline，通常不直接调用 |

## 顶层包导出

`equilibrium` 顶层包仅导出 demo 相关的两个函数：

```python
from equilibrium import run_demo_pipeline, build_status_message
```

这两个函数来自 `equilibrium.app`，主要用于 `uv run solve-figure0326` 的 CLI 入口。
