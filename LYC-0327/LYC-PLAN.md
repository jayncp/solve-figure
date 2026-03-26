# LYC-0327 画图计划

## 目标

生成 5 张图，每张图横轴为一个变化参数，纵轴为 `profit_informed_mm` 和 `profit_uninformed_mm` 两条曲线。

## 5 张图的参数配置

### 公共默认参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| J_I | 15 | informed 做市商数量 |
| J_U | 15 | uninformed 做市商数量 |
| sigma_v2 | 1.0 | 基本面方差 |
| sigma_u2 | 1.0 | 成本冲击方差 |
| sigma_epsilon2 | 1.0 | 信息噪声方差 |
| sigma_eta2 | 1.0 | 第二期噪声方差 |
| rho | 0.5 | 相关系数 |

### 图 1: J_I 变化 (J_I + J_U = 30)

- 横轴: J_I = 1, 2, ..., 29 (整数，29个点)
- 对应: J_U = 30 - J_I
- 其余参数: sigma_v2=1, sigma_u2=1, sigma_epsilon2=1, sigma_eta2=1, rho=0.5
- 特殊: 需要每个点单独设置 J_I 和 J_U，不能用标准单参数 sweep
- 方案: 手动循环 + warm start

### 图 2: sigma_epsilon2 变化

- 横轴: sigma_epsilon2 = linspace(0.1, 30, 100)
- 固定: J_I=15, J_U=15, sigma_v2=1, sigma_u2=1, sigma_eta2=1, rho=0.5

### 图 3: sigma_eta2 变化

- 横轴: sigma_eta2 = linspace(0.1, 30, 100)
- 固定: J_I=15, J_U=15, sigma_v2=1, sigma_u2=1, sigma_epsilon2=1, rho=0.5

### 图 4: sigma_u2 变化

- 横轴: sigma_u2 = linspace(0.1, 30, 100)
- 固定: J_I=15, J_U=15, sigma_v2=1, sigma_epsilon2=1, sigma_eta2=1, rho=0.5

### 图 5: rho 变化

- 横轴: rho = linspace(0.01, 0.99, 100)
- 固定: J_I=15, J_U=15, sigma_v2=1, sigma_u2=1, sigma_epsilon2=1, sigma_eta2=1

## 求解策略

- CompositeSolver(hybr, lm) + require_constraints
- sweep 模式 `path`，利用 warm start
- 图 1 手动循环（J_I 和 J_U 联动），其余 4 张用 ParameterSweep.sweep_1d

## 输出

- `LYC-0327/fig1_J_I_sweep.png`
- `LYC-0327/fig2_sigma_epsilon2_sweep.png`
- `LYC-0327/fig3_sigma_eta2_sweep.png`
- `LYC-0327/fig4_sigma_u2_sweep.png`
- `LYC-0327/fig5_rho_sweep.png`

## 实现

单个脚本 `LYC-0327/run_figures.py`。
