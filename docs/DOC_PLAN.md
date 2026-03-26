# 文档建设计划

## 一、目标

基于当前仓库实际状态，建设一套**先可维护、再扩展**的中文文档。

文档目标分为两部分：

1. **主框架文档**：说明 `src/equilibrium/` 下通用求解框架的公开能力与使用方式。
2. **LYC 专项文档**：说明 `LYC-0327/` 下两期模型脚本的运行、修改和输出，不将其包装成主框架公共 API。

本计划以**当前代码组织为准**，不假设未来会把 `LYC-0327` 完整并入 `equilibrium` 包。

---

## 二、文档策略

当前阶段不引入 `mdbook`、`MkDocs` 或其他额外站点生成工具，先采用**仓库内 Markdown 文档**方案：

- 优点：
  - 与当前 Python 工具链一致，不额外引入 Rust 或前端构建依赖
  - 修改成本低，便于先把内容写准确
  - 适合当前项目规模
- 原则：
  - 只写**已经存在且可运行**的能力
  - 只把 `equilibrium` 包内的稳定接口当作主文档对象
  - `LYC-0327` 单独成文，不混入主框架 API 参考

等主框架 API 稳定、文档页数明显增加后，再评估是否迁移到站点生成方案。

---

## 三、文档边界

### 3.1 主框架文档覆盖范围

主文档只覆盖以下内容：

- `equilibrium.models`
- `equilibrium.solvers`
- `equilibrium.plotting`
- `equilibrium.utils`
- `equilibrium.app` 中当前已存在的 demo 入口
- `examples/cournot_duopoly.py`

### 3.2 不放入主框架文档的内容

以下内容不写入主文档 API 参考：

- `LYC-0327/two_period.py`
- `LYC-0327/run_figures.py`
- `LYC-0327/two_period_benchmark.py`
- 任何仅服务于 LYC 子目录的脚本和试验性逻辑

这些内容单独放在 `LYC-0327/LYC-README.md` 中描述。

---

## 四、目录规划

采用纯 Markdown 目录结构：

```text
docs/
├── DOC_PLAN.md
├── index.md
├── guide/
│   ├── quickstart.md
│   ├── define-model.md
│   ├── solve.md
│   ├── parameter-sweep.md
│   └── plotting.md
├── api/
│   ├── overview.md
│   ├── models.md
│   ├── solvers.md
│   ├── plotting.md
│   ├── utils.md
│   └── app.md
└── internals/
    ├── architecture.md
    ├── result-flow.md
    ├── scipy-root.md
    ├── continuation.md
    └── composite.md
```

补充说明：

- `docs/index.md` 作为总入口，承担导航作用。
- `docs/api/app.md` 只描述当前已有 demo 入口，不提前设计未来接口。
- `LYC-0327/LYC-README.md` 独立维护，不放在 `docs/` 下。

---

## 五、各页面内容规划

### 5.1 `docs/index.md`

定位：项目总入口。

内容：

- 项目一句话介绍
- 当前仓库包含两条线：
  - 通用均衡求解框架
  - LYC 两期模型专项脚本
- 建议阅读顺序：
  - 新用户先看 `guide/quickstart.md`
  - 查接口看 `api/`
  - 看实现思路看 `internals/`
  - 使用 LYC 脚本看 `LYC-0327/LYC-README.md`

### 5.2 用户指南

#### `docs/guide/quickstart.md`

定位：最短可跑通路径。

内容：

- 环境要求：Python 3.13
- 安装与同步依赖：
  - `uv sync --all-groups`
- 运行 demo：
  - `uv run solve-figure0326`
- 可补充说明备用入口：
  - `uv run python main.py`
- 输出位置：`output/demo_equilibrium_sweep.png`
- 说明 demo 的完整链路：
  - 模型
  - 求解
  - 扫描
  - 画图

#### `docs/guide/define-model.md`

定位：如何定义自己的方程系统。

内容：

- `EquationSystem` 的职责
- 必须实现的方法：
  - `variable_names`
  - `param_names`
  - `equations`
- 可选实现的方法：
  - `intermediates`
  - `constraints`
  - `metrics`
  - `jacobian`
  - `validate_params`
- `validate_x` 和 `variable_dict` 的作用
- 使用 `examples/cournot_duopoly.py` 作为讲解样例

#### `docs/guide/solve.md`

定位：如何调用求解器。

内容：

- `ScipyRootSolver` 的最小用法
- `CompositeSolver` 的回退策略
- `ContinuationSolver` 的适用场景
- `SolveResult` 中最常用字段说明：
  - `success`
  - `method`
  - `x`
  - `variables`
  - `constraints_ok`
  - `metrics`
  - `failures`
- `options` 的传递规则
- 初始值与约束判定的基本建议

#### `docs/guide/parameter-sweep.md`

定位：参数扫描工作流。

内容：

- `ParameterSweep.sweep_1d`
- `ParameterSweep.sweep_2d`
- `mode="path"` 与 `mode="independent"` 的区别
- `metric_names` 的作用
- `SweepResult1D` / `SweepResult2D` 如何取值
- `save_json` 的输出格式和适用场景

#### `docs/guide/plotting.md`

定位：结果可视化。

内容：

- `FigurePlotter.plot_1d`
- `FigurePlotter.plot_2d_heatmap`
- `FigurePlotter.save`
- 如何从 `SweepResult` 中自行取数据，用 `matplotlib` 自定义作图

### 5.3 API 参考

API 参考坚持一个规则：

- **优先记录公开导入路径**
- 如果某个能力没有在包层级公开导出，就只在实现说明里提及，不在“稳定 API”里承诺

#### `docs/api/overview.md`

内容：

- 当前包结构总览
- 推荐导入路径
- 哪些模块是面向使用者的，哪些更偏内部实现

#### `docs/api/models.md`

内容：

- `Params`
- `NDArrayFloat`
- `ConstraintMap`
- `MetricMap`
- `IntermediateMap`
- `EquationSystem`
- `DemoEquilibriumModel`

说明重点：

- 抽象基类的方法契约
- 类型别名约定
- 哪些是演示模型，哪些不是业务模型模板

#### `docs/api/solvers.md`

内容：

- `SolverStrategy`
- `SolveResult`
- `SolveAcceptance`
- `SolverFailure`
- `build_solve_result`
- `ScipyRootSolver`
- `ContinuationSolver`
- `CompositeSolver`

说明重点：

- `SolveResult` 字段含义
- 各求解器的构造参数
- `options` 中哪些键由哪个求解器解释

#### `docs/api/plotting.md`

内容：

- `ParameterSweep`
- `SweepMode`
- `SweepPoint`
- `SweepFailurePoint`
- `SweepResult1D`
- `SweepPoint2D`
- `SweepFailurePoint2D`
- `SweepResult2D`
- `FigurePlotter`

#### `docs/api/utils.md`

内容：

- `to_float_array`
- `ensure_finite`
- `constraints_ok`

#### `docs/api/app.md`

内容：

- `run_demo_pipeline`
- `build_status_message`
- `main`

说明重点：

- 这些函数目前只服务 demo pipeline
- 不把 `app.py` 写成“完整 CLI 框架”，避免文档超前

### 5.4 内部设计文档

#### `docs/internals/architecture.md`

内容：

- 分层关系：
  - Models
  - Solvers
  - Plotting
  - Utils
- 设计原则：
  - 模型接口无状态
  - 求解器与模型解耦
  - 结果对象统一
  - 扫描与绘图建立在 `SolveResult` 之上

#### `docs/internals/result-flow.md`

内容：

- 数据流：
  - `EquationSystem`
  - `solver.solve()`
  - `build_solve_result`
  - `ParameterSweep`
  - `SweepResult`
  - `FigurePlotter`
- 为什么 `intermediates -> constraints -> metrics` 要统一计算

#### `docs/internals/scipy-root.md`

内容：

- 对 `scipy.optimize.root` 的包装方式
- `require_constraints` 的后处理逻辑
- `use_jacobian` 的参数传递方式
- 初始值默认零向量的行为

#### `docs/internals/continuation.md`

内容：

- `ContinuationSolver` 的适用场景
- continuation path 的来源
- `SolveAcceptance` 的角色
- 失败后如何返回结构化信息

#### `docs/internals/composite.md`

内容：

- 顺序尝试策略
- 失败累积机制
- 全部失败时的回退结果构造

---

## 六、`LYC-0327/LYC-README.md` 规划

该文档是**专项使用说明**，不是主框架 API 参考。

建议内容如下：

### 6.1 项目概述

- 两期模型的背景说明
- 子目录内关键文件说明：
  - `two_period.py`
  - `run_figures.py`
  - `two_period_benchmark.py`
  - 测试文件

### 6.2 环境准备

- 在仓库根目录执行：
  - `uv sync --all-groups`
- 说明 `LYC-0327` 当前采用**独立脚本 + 本地模块导入**方式维护
- 说明 `run_figures.py` 当前通过向 `sys.path` 注入脚本目录并使用 `from two_period import TwoPeriodModel` 加载本地模型文件
- 不承诺其为 `equilibrium` 包公开 API 的一部分

### 6.3 运行方式

- 从仓库根目录运行：
  - `uv run python LYC-0327/run_figures.py`
- 文档中不要写成 `equilibrium.models.two_period` 形式的主包导入路径，避免与当前实现不一致
- 输出位置：
  - `LYC-0327/figures/`

### 6.4 五张图说明

- 图 1：`J_I` 扫描，且 `J_I + J_U = 30`
- 图 2：`sigma_epsilon2` 扫描
- 图 3：`sigma_eta2` 扫描
- 图 4：`sigma_u2` 扫描
- 图 5：`rho` 扫描

### 6.5 如何修改模型

- 修改参数：编辑 `BASE_PARAMS`
- 修改方程：编辑 `TwoPeriodModel.equations`
- 修改指标：编辑 `metrics()`
- 修改约束：编辑 `constraints()`

### 6.6 如何修改画图脚本

- 修改扫描区间：调整 `np.linspace` / `np.arange`
- 修改联动参数：调整 `extra_param` / `extra_fn`
- 修改图表样式：调整 `plot_profit_curves`

### 6.7 验证建议

- 主框架检查：
  - `uv run ty check`
  - `uv run pytest tests`
  - `uv run ruff check .`
- 如果需要单独验证 LYC 子目录，再补充专项命令

---

## 七、编写顺序

建议按以下顺序落地：

1. 写 `docs/index.md`
2. 写 `docs/guide/quickstart.md`
3. 写 `docs/api/models.md` 与 `docs/api/solvers.md`
4. 写 `docs/guide/solve.md`、`docs/guide/parameter-sweep.md`
5. 写 `docs/api/plotting.md`、`docs/api/utils.md`、`docs/api/app.md`
6. 写 `docs/internals/` 下的实现说明
7. 写 `LYC-0327/LYC-README.md`

原因：

- 先把用户最容易走通的路径写出来
- 再补 API 参考
- 最后再写内部设计和专项说明

---

## 八、编写规范

- 全部使用中文简体
- 代码示例统一使用 `uv` 工作流，不写 `pip install -e .`
- 示例代码只展示当前仓库中**实际存在**的能力
- Quickstart 只写当前已验证可用的入口命令，不写 `python -m equilibrium.app`
- 对公共 API 的描述以源码为准，不对未来接口做承诺
- 对 `LYC-0327` 的描述明确标注为“专项脚本”，不混淆为主框架稳定接口
- `LYC-0327` 的运行说明必须与脚本中的真实导入方式一致
- 不文档化未实现功能，不预留空接口说明

---

## 九、后续升级条件

只有在同时满足以下条件时，才建议把文档迁移到站点工具：

1. `docs/` 页面数明显增加
2. API 变化趋于稳定
3. 需要搜索、导航、目录树、主题等站点能力
4. 团队接受新增文档构建工具链

在那之前，优先保证内容准确、命令可运行、路径真实存在。
