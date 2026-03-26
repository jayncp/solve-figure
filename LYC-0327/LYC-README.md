# LYC 两期模型 — 使用说明

本目录包含两期均衡模型的求解脚本和出图工具。这些脚本使用主框架 `equilibrium` 的求解器和绘图能力，但模型本身（`TwoPeriodModel`）作为独立文件维护，不属于主框架的公开 API。

## 文件清单

| 文件 | 用途 |
|------|------|
| `two_period.py` | `TwoPeriodModel` — 11 变量、7 参数的两期均衡方程组 |
| `run_figures.py` | 出图脚本 — 生成 5 张利润对比图 |
| `reference/` | 参考资料 — TeX 规格和 MATLAB 参考代码 |

## 环境准备

在仓库根目录执行：

```bash
uv sync --all-groups
```

> 本目录采用**独立脚本 + 本地模块导入**方式维护。`run_figures.py` 通过向 `sys.path` 注入脚本所在目录，使用 `from two_period import TwoPeriodModel` 加载本地模型文件。模型不通过 `equilibrium.models` 包路径导入。

## 运行出图

从仓库根目录执行：

```bash
uv run python LYC-0327/run_figures.py
```

输出位置：`LYC-0327/figures/`，共 5 张 PNG 图片。

运行过程中会打印每个扫描方向的进度和成功率。

## 五张图说明

| 图片 | 扫描参数 | 说明 |
|------|---------|------|
| `fig1_J_I_sweep.png` | J_I（1→29） | J_I 变化，固定 J_I + J_U = 30 |
| `fig2_sigma_epsilon2_sweep.png` | σ_ε²（0.1→30） | 私有信号噪声方差 |
| `fig3_sigma_eta2_sweep.png` | σ_η²（0.1→30） | 第二期公开信号噪声方差 |
| `fig4_sigma_u2_sweep.png` | σ_u²（0.1→30） | 噪声交易方差 |
| `fig5_rho_sweep.png` | ρ（0.01→0.99） | 噪声交易跨期相关系数 |

每张图展示两条曲线：**Informed MM** 和 **Uninformed MM** 的预期利润随参数变化的对比。

## 如何修改模型

### 修改参数默认值

编辑 `run_figures.py` 中的 `BASE_PARAMS`：

```python
BASE_PARAMS = {
    "J_I": 15.0,
    "J_U": 15.0,
    "sigma_v2": 1.0,
    "sigma_u2": 1.0,
    "sigma_epsilon2": 1.0,
    "sigma_eta2": 1.0,
    "rho": 0.5,
}
```

### 修改方程

编辑 `two_period.py` 中 `TwoPeriodModel.equations` 方法。方程的推导对照 `reference/tex_code.tex`。

### 添加新指标

在 `two_period.py` 的 `TwoPeriodModel.metrics` 方法中添加返回键。新指标可以引用 `intermediates` 中的任何中间值。

### 添加或修改约束

编辑 `two_period.py` 的 `TwoPeriodModel.constraints` 方法。约束值 > 0 表示满足。

## 如何修改画图方案

### 修改扫描范围

编辑 `run_figures.py` 中 `run_all` 函数里的 `np.linspace` / `np.arange` 参数：

```python
# 例：将 sigma_epsilon2 扫描范围改为 0.5 到 10
x, res = solve_sweep("sigma_epsilon2", np.linspace(0.5, 10, 50))
```

### 修改联动参数

使用 `extra_param` 和 `extra_fn` 参数实现两个参数同时变化：

```python
# 例：J_I 扫描时 J_U = 40 - J_I
x, res = solve_sweep(
    "J_I", j_values,
    extra_param="J_U",
    extra_fn=lambda j: 40 - j,
)
```

### 添加新图

在 `run_all` 函数中按现有模式添加：

```python
# 例：添加 sigma_v2 扫描
print("Fig 6: sigma_v2 sweep")
x, res = solve_sweep("sigma_v2", np.linspace(0.1, 10, 60))
plot_profit_curves(x, res, r"$\sigma_v^2$",
                   r"Profits vs $\sigma_v^2$",
                   "fig6_sigma_v2_sweep.png")
```

### 修改图表样式

编辑 `plot_profit_curves` 函数中的 matplotlib 配置：

- `figsize=(9, 5)` — 图片尺寸
- `marker="."`, `markersize=3` — 数据点样式
- `fontsize` — 字号
- `dpi=200` — 输出分辨率

### 添加新的指标到图中

修改 `METRICS` 和 `LABELS` 全局变量：

```python
METRICS = ("profit_informed_mm", "profit_uninformed_mm", "profit_insider")
LABELS = {
    "profit_informed_mm": "Informed MM",
    "profit_uninformed_mm": "Uninformed MM",
    "profit_insider": "Insider",
}
```

## 验证

主框架检查：

```bash
uv run ty check
uv run pytest tests
uv run ruff check .
```
