# 方程求解与画图框架计划

## 1. 目标与边界

### 1.1 目标

构建一个可复用的 Python 框架，用于：

1. 定义一组非线性方程和约束。
2. 用统一接口调用不同求解策略。
3. 对参数做 1D/2D 扫描。
4. 输出用于分析的指标和图像。
5. 最终落到 `reference/tex_code.tex` 中的 11 变量两期模型。

### 1.2 非目标

本项目**不**以 MATLAB 代码迁移为目标。

- MATLAB 只作为背景参考，用来说明旧实现的问题。
- 框架验证阶段使用更简单、常见、已知可求解的测试模型。
- 只有最终的两期 11 变量模型需要严格对照 `reference/tex_code.tex`。

### 1.3 当前仓库现状

当前仓库还处于起步阶段：

- 已有 `src/`、`docs/`、`output/` 目录骨架。
- `main.py` 还是占位入口。
- `pyproject.toml` 已加入 `ruff`、`ty` 开发工具，但求解、测试、绘图依赖还未补齐。
- 已有 `justfile` 提供基础 lint 命令，但测试入口和运行依赖仍未补全。
- 还没有实际业务代码、测试文件和可运行 pipeline。

因此计划必须先解决“最小可运行项目”问题，再谈 11 变量模型。

---

## 2. 问题分析

### 2.1 旧实现暴露出的核心问题

旧 MATLAB 思路的主要问题不是语法，而是工作方式：

1. 配置、求解、筛选、画图耦合在单文件中。
2. 方程和辅助变量写死，无法复用。
3. 参数缺少结构化校验。
4. 同一中间量在多个地方重复计算。
5. 依赖随机初值重试；维度升高后效率和稳定性都会快速恶化。

### 2.2 11 变量模型的结构

来自 `reference/tex_code.tex` 的未知量为：

- `(β₁, β₂, δ_T, α_{I,1}, γ₁, α_{I,2}, γ₂, δ_I, α_{U,1}, α_{U,2}, δ_U)`

显式外生参数至少包括：

- `J_I`, `J_U`
- `σ²_v`, `σ²_u`, `σ²_ε`, `σ²_η`
- `ρ`

派生量至少包括：

- `varphi_1`, `varphi_2`, `psi_1`, `psi_2`
- `phi_1`, `phi_2`, `phi_3`
- `kappa_1`, `kappa_2`
- `xi_1`, `xi_2`
- `A`, `B`, `C`, `D`, `F`, `G`
- 利润相关量 `H`, `J`, `K`, `L`, `M`, `N`, `Q`
- `nu = σ²_u / (σ²_u + σ²_ε)`

需要注意：

- `nu` 是派生量，不应作为外生参数暴露。
- 文中同时存在 `varphi_*` 和 `phi_*` 两套符号，代码里必须明确区分。
- 公式文本存在疑似排版或记号错误，不能直接“照抄即实现”。

### 2.3 11 变量模型的真正难点

1. 高维非线性系统可能有多解或局部伪解。
2. 方程含多个分母，数值稳定性脆弱。
3. 二阶条件是硬约束，不是求出根后再随意参考的软指标。
4. continuation 路径如果定义不清，所谓“同伦延拓”无法落地。
5. 参数扫描和 warm start 之间存在冲突，不能一概并行。

---

## 3. 总体方案

### 3.1 分成三个层次

#### 层次 A: 框架层

目标是先把以下能力做扎实：

- 方程系统抽象
- 求解器抽象
- 结果对象
- 参数扫描
- 绘图输出
- 校验与错误报告

#### 层次 B: 验证层

使用简单测试模型验证框架，而不是直接上 11 变量系统。

测试模型要求：

- 变量数低于 11
- 有已知解或稳定数值解
- 足以覆盖多求解器、约束、扫描、作图流程

#### 层次 C: 目标模型层

最后实现 `tex_code.tex` 的两期 11 变量系统，并在框架上接入：

- 方程
- 中间变量
- 二阶条件
- 指标计算
- continuation / fallback 求解流程

---

## 4. 架构设计

### 4.1 文件结构

```text
solve-figure0326/
├── main.py
├── pyproject.toml
├── docs/
│   ├── PLAN.md
│   └── formula_audit.md
├── output/
├── reference/
├── src/
│   └── equilibrium/
│       ├── __init__.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── demo_model.py
│       │   └── two_period.py
│       ├── solvers/
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── scipy_root.py
│       │   ├── constrained_opt.py
│       │   ├── continuation.py
│       │   └── composite.py
│       ├── plotting/
│       │   ├── __init__.py
│       │   ├── sweep.py
│       │   └── figures.py
│       └── utils/
│           ├── __init__.py
│           └── validation.py
└── tests/
    ├── test_demo_model.py
    ├── test_solvers.py
    └── test_two_period_formulae.py
```

说明：

- `demo_model.py` 用于框架验证，避免和最终模型混淆。
- `docs/formula_audit.md` (手工维护) 用于整理 TeX 到代码的符号映射和勘误。
  - SymPy `parse_latex()` 无法可靠解析本文档（自定义宏 `\splitfrac`、`\C`、`\V`，复杂嵌套下标），不做自动化校验。
- `tests/` 必须从一开始纳入，而不是最后补。

### 4.2 核心接口

#### 类型别名

```python
Params = dict[str, float]
NDArrayFloat = np.ndarray  # dtype=float64
```

#### 方程系统

```python
class EquationSystem(ABC):
    @property
    @abstractmethod
    def variable_names(self) -> tuple[str, ...]: ...

    @property
    @abstractmethod
    def param_names(self) -> tuple[str, ...]: ...

    @abstractmethod
    def equations(self, x: NDArrayFloat, params: Params) -> NDArrayFloat: ...

    def intermediates(self, x: NDArrayFloat, params: Params) -> dict[str, float]:
        return {}

    def constraints(
        self, x: NDArrayFloat, params: Params,
        intermediates: dict[str, float] | None = None,
    ) -> dict[str, float]:
        if intermediates is None:
            intermediates = self.intermediates(x, params)
        return {}

    def metrics(
        self, x: NDArrayFloat, params: Params,
        intermediates: dict[str, float] | None = None,
    ) -> dict[str, float]:
        if intermediates is None:
            intermediates = self.intermediates(x, params)
        return {}

    def jacobian(self, x: NDArrayFloat, params: Params) -> NDArrayFloat | None:
        return None

    def validate_params(self, params: Params) -> None:
        """校验参数完整性。缺失或多余参数时抛出 ValueError。"""
        expected = set(self.param_names)
        got = set(params.keys())
        missing = expected - got
        extra = got - expected
        if missing or extra:
            raise ValueError(
                f"Param mismatch: missing={missing}, extra={extra}"
            )
```

约定：

- **EquationSystem 完全无状态**。所有方法都是 `(x, params)` 的纯函数，不缓存任何内部状态。
- `intermediates()` 负责所有共享中间量的一次性计算。
- `constraints()` 和 `metrics()` 接受可选的 `intermediates` 参数。
  - 如果传入，直接使用，避免重复计算。
  - 如果不传，自行调用 `intermediates()` 计算。
  - **solver 在求解完成后统一调用一次 `intermediates()`，然后传递给 `constraints()` 和 `metrics()`**。
- `constraints()` 返回“约束名 -> 值”映射，统一约定“值 > 0 为满足”。
- `metrics()` 只负责结果分析，不参与求解核心逻辑。
- `validate_params()` 在 solver 调用前校验参数完整性。

#### 求解结果

```python
@dataclass(slots=True)
class SolveResult:
    success: bool
    method: str
    x: NDArrayFloat
    residual_norm: float
    variables: dict[str, float]
    constraints: dict[str, float]
    constraints_ok: bool           # solver 负责计算: all(v > 0 for v in constraints.values())
    intermediates: dict[str, float]
    metrics: dict[str, float]
    message: str
    nfev: int | None = None
    njev: int | None = None
```

`constraints_ok` 由 solver 在求解后统一计算：
```python
imed = system.intermediates(x, params)
cons = system.constraints(x, params, intermediates=imed)
mets = system.metrics(x, params, intermediates=imed)
constraints_ok = all(v > 0 for v in cons.values()) if cons else True
```

#### 求解器

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

`CompositeSolver` 负责按顺序尝试多个策略，并保留失败信息，便于调试。

### 4.4 日志设计

使用 Python 标准 `logging` 模块，贯穿求解器和扫描层，方便调试。

```python
import logging
logger = logging.getLogger("equilibrium")
```

日志级别约定：
- **DEBUG**: 每次 scipy 调用的入参、退出码、残差、约束值
- **INFO**: 求解成功/失败摘要、扫描进度
- **WARNING**: 约束不满足、fallback 触发、数值异常
- **ERROR**: 所有策略失败、参数校验失败

每条 solver 日志至少包含：`method`、`residual`、`nfev`、`constraints_ok`。
CompositeSolver 额外记录每个策略的尝试结果和最终选择。
扫描层记录进度 `[i/n]` 和失败点。

### 4.3 扫描策略设计

参数扫描不能只有一种模式，至少区分两类：

#### 模式 1: 独立点评估

适用于简单模型或 cheap solver：

- 每个参数点彼此独立。
- 可以并行。
- 不依赖前一点的解。

#### 模式 2: 路径延续评估

适用于 11 变量目标模型：

- 按路径顺序逐点求解。
- 默认用前一点解作为下一点初值。
- 失败时允许局部回退、减小步长或切换 fallback solver。
- 不应默认全并行。

因此 `ParameterSweep` 需要体现这种差异，而不是只暴露一个“多进程开关”。

---

## 5. 关键设计决策

### 5.1 不把 MATLAB 4 变量模型作为正式里程碑

原因：

- 你已经明确说明最终目标不是复刻 MATLAB。
- 如果把 MATLAB 方程纳入正式路线，会分散精力并制造兼容负担。
- 更合理的是引入一个更小、更标准、可控的演示模型来验证框架。

### 5.2 continuation 是 11 变量模型的核心，但不能先拍脑袋指定路径

此前“从 `J_U = 0` 开始”的表述过早下结论，暂时不作为固定方案。

在正式实现 continuation 前，必须先完成：

1. 公式勘误和边界情形分析。
2. 哪些变量在边界会退化的确认。
3. continuation 路径定义。
4. benchmark 参数组选择。

在这些条件没完成前，只能把 continuation 视为候选主策略，而不是已确定实现细节。

### 5.3 指标计算与求解解耦

利润、价格协方差等指标只依赖解和中间量，因此应放在 `metrics()` 层。

这样做的好处：

- 求解流程更干净。
- 更容易单独测试公式。
- 扫描和画图逻辑不用关心模型内部细节。

### 5.4 参数容器先用 `dict`

暂时继续用 `Params = dict[str, float]`（类型别名定义在 `models/base.py`），原因是不同模型的参数集合不同。

校验分两层：

- **结构校验**: `EquationSystem.validate_params()` 基类方法，检查缺失和多余参数。solver 在调用 `equations()` 前自动调用。
- **语义校验**: 各模型可在 `validate_params()` 中追加数值范围检查（如方差 > 0）。

### 5.5 EquationSystem 无状态设计

**已确认决策**：EquationSystem 完全无状态，所有方法都是 `(x, params)` 的纯函数。

- 不缓存任何内部状态，不存在缓存失效问题。
- 参数变化、变量变化都不影响正确性。
- 不需要为不同参数组创建多个实例。
- 求解器在求解后统一调一次 `intermediates()`，传给 `constraints()` 和 `metrics()`。
- 带约束优化时 `constraints()` 每步会重算中间量，对纯算术运算开销可忽略。

### 5.6 详细日志

使用 Python `logging` 模块，命名空间 `equilibrium`。

覆盖范围：
- solver 层：每次尝试的方法、残差、函数调用次数、约束满足情况
- composite solver 层：每个策略的尝试结果、最终选择、失败原因
- sweep 层：扫描进度 `[i/n]`、失败点位置、warm start 使用情况
- 参数校验层：校验失败的具体字段

日志级别：DEBUG 记录细节，INFO 记录摘要，WARNING 记录 fallback/异常，ERROR 记录致命失败。

---

## 6. 分步实施计划

### Step 0: 项目最小可运行骨架

目标：让仓库具备“可导入、可检查、可测试”的最低条件。

需要完成：

- 补全 `pyproject.toml` 中运行依赖：`numpy`、`scipy`、`matplotlib`
- 补全测试依赖：`pytest`
- 明确 `src` layout 的包配置
- 统一 `ruff`、`ty`、`pytest` 的运行入口
- 让 `main.py` 至少能调用包内代码，而不是纯占位输出

验收标准：

- `uv run ruff check .`
- `uv run ty check .`
- `uv run pytest`

### Step 1: 基础抽象与校验层

目标：建立后续所有模型共用的稳定接口。

需要完成：

- `EquationSystem`
- `SolveResult`
- 参数校验与约束校验工具
- 求解失败信息结构
- 基础数值辅助函数

验收标准：

- 基础单元测试齐全
- `EquationSystem`、参数校验和结果结构可被最小 mock system 单独测试

### Step 2: 通用求解器

目标：先实现不依赖具体模型的求解层。

需要完成：

- `ScipyRootSolver`
- `CompositeSolver`
- 可选的 `ConstrainedOptimizationSolver`

设计要求：

- 支持多种 `scipy.optimize.root` 方法
- 支持传入初值
- 统一残差、约束和异常信息

验收标准：

- 对简单系统可稳定收敛
- 失败时能返回可诊断信息，而不是只抛裸异常
- 一个最小 mock system 可以走完整个 solve 流程

### Step 3: 演示模型与完整 pipeline

目标：用简单模型验证框架不是空架子。

建议演示模型特征：

- 2 到 3 个变量
- 至少 1 个约束
- 至少 1 个可画图指标

需要完成：

- `demo_model.py`
- 1D 参数扫描
- 1D 画图
- `main.py` 演示入口

验收标准：

- 能稳定输出数值解
- 能输出一张示例图
- 测试覆盖 solve + sweep + plot 主链路

### Step 4: 扫描策略升级

目标：补齐扫描层，而不是提前把多进程硬塞进 Step 3。

需要完成：

- 独立点评估模式
- 路径延续评估模式
- 可选多进程，仅用于适合独立计算的场景
- 失败点记录与结果掩码

验收标准：

- 简单模型可并行扫描
- continuation 模式支持顺序 warm start

### Step 5: TeX 公式审计与符号映射（手工）

目标：在写 11 变量模型前，先把公式源整理成可编码版本。

**为什么不做自动化校验**：SymPy `parse_latex()` 无法可靠解析本文档的 LaTeX，原因：
- 自定义宏 `\splitfrac`、`\C`、`\V` 不被识别
- 双下标 `α_{I,1}` 和复合上下标解析不稳定
- 多行 `align` 环境中的表达式需要手工拆分

因此本步骤为**纯手工审计**，产出 `docs/formula_audit.md`。

需要完成：

- 提取 `tex_code.tex` 中所有变量、参数、中间量、约束、指标
- 建立”TeX 符号 -> Python 字段名”映射表
- 记录疑似笔误、排版错误和边界情况
- 明确哪些量是外生参数，哪些量是派生量

验收标准：

- 形成一份可直接照着编码的符号/公式清单
- 对疑似错误公式有备注，不在实现时临场猜测

### Step 6: 11 变量模型实现

目标：实现 `TwoPeriodModel`，但此时只做“方程与指标的正确表达”。

需要完成：

- 11 个方程
- 全部共享中间量
- 6 个二阶条件
- 利润与价格协方差指标
- 单元测试覆盖关键公式块

验收标准：

- 维度正确
- 所有中间量在给定测试输入下返回有限值或明确报错
- 单元测试能覆盖主要分母和边界条件

### Step 7: 11 变量求解策略与 benchmark

目标：给目标模型定义“可判断成功与失败”的求解协议。

需要完成：

- 选定至少一组 benchmark 参数
- 定义收敛阈值、残差阈值、约束阈值
- 设计 continuation 路径
- 实现 continuation solver 或 continuation runner
- 将 root / constrained / continuation 组合成分层 fallback

验收标准：

- 至少一组 benchmark 参数可重复得到满足约束的有限解
- 同一 benchmark 重复运行时结果稳定

### Step 8: 2D 扫描与最终集成

目标：完成用户真正要用的分析入口。

需要完成：

- 2D 扫描
- 结果持久化
- 图像输出
- `main.py` 或 CLI 中的最终演示入口

验收标准：

- 能对目标模型跑一组 1D 或 2D 示例
- 输出图像和关键指标
- 全项目通过 lint、typecheck、tests

---

## 7. 风险与应对

### 风险 1: TeX 公式本身有错误

应对：

- 先做公式审计。
- 对可疑公式单独标记，不把实现和勘误混在一起。

### 风险 2: 11 变量系统无法靠单一 root 方法稳定求解

应对：

- 不把 `scipy.optimize.root` 当成唯一方案。
- 保留 constrained optimization 和 continuation fallback。

### 风险 3: 扫描计算量过大

应对：

- 对简单模型用并行。
- 对目标模型优先用路径延续和 warm start。
- 不默认对 11 变量模型做“全点独立并行”。

### 风险 4: 成功标准不明确导致开发反复

应对：

- 先定义 benchmark 参数和阈值。
- 用固定 benchmark 驱动调试。

---

## 8. 当前结论

当前最合理的路线不是“直接上 11 变量 + 同伦 + 多进程”，而是：

1. 先把项目骨架、检查链路和基础抽象补完整。
2. 用简单模型验证框架可行。
3. 单独做 `tex_code.tex` 公式审计。
4. 再实现 11 变量模型。
5. 最后定义并实现适合该模型的 continuation 与扫描策略。

这条路线更慢一点，但逻辑闭环完整，且更接近真正可交付的实现。
