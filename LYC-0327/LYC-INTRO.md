# LYC 项目环境搭建与运行指南

本文档将指导你在 Mac 上从零开始搭建开发环境，克隆项目并运行代码。

> 仓库地址：<https://github.com/jayncp/solve-figure.git>

---

## 1. 安装 Homebrew

打开 **终端**（Terminal.app），粘贴以下命令：

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

安装完成后，终端会提示你执行两条命令将 brew 加入 PATH。根据你的芯片类型：

**Apple Silicon（M1/M2/M3/M4）：**

```bash
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

**Intel Mac：**

```bash
echo 'eval "$(/usr/local/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/usr/local/bin/brew shellenv)"
```

验证安装：

```bash
brew --version
```

能看到版本号即成功。

---

## 2. 安装 Fish Shell 并设为默认终端

```bash
brew install fish
```

将 fish 添加到系统合法 shell 列表：

```bash
echo $(which fish) | sudo tee -a /etc/shells
```

设为默认 shell：

```bash
chsh -s $(which fish)
```

**重新打开终端**，确认已经进入 fish：

```fish
echo $SHELL
# 应显示 /opt/homebrew/bin/fish 或 /usr/local/bin/fish
```

### 2.1 在 Fish 中配置 Homebrew

```fish
echo 'eval (/opt/homebrew/bin/brew shellenv)' >> ~/.config/fish/config.fish
```

> Intel Mac 将路径改为 `/usr/local/bin/brew`。

重新打开终端，验证：

```fish
brew --version
```

---

## 3. 安装 uv（Python 包管理器）

```fish
brew install uv
```

验证：

```fish
uv --version
```

---

## 4. 安装通义灵码（Tongyi Lingma）编辑器

从官网下载安装：

> <https://tongyi.aliyun.com/lingma/download>

下载 macOS 版本的 `.dmg` 文件，双击安装，拖入 Applications 文件夹。

### 4.1 配置 Fish 为默认终端

1. 打开通义灵码
2. 使用快捷键 `Cmd + ,` 打开设置
3. 在搜索栏输入 `terminal default profile`
4. 找到 **Terminal > Integrated > Default Profile: Osx**
5. 在下拉菜单中选择 **fish**

如果下拉菜单中没有 fish 选项，手动配置：

1. 在设置搜索栏输入 `terminal profiles`
2. 点击 **在 settings.json 中编辑**
3. 添加以下内容：

```json
{
  "terminal.integrated.profiles.osx": {
    "fish": {
      "path": "/opt/homebrew/bin/fish"
    }
  },
  "terminal.integrated.defaultProfile.osx": "fish"
}
```

> Intel Mac 将路径改为 `/usr/local/bin/fish`。

---

## 5. 注册 GitHub 账号并配置 Git

### 5.1 注册 GitHub

访问 <https://github.com/signup>，按提示注册。

### 5.2 配置 Git 用户信息

```fish
git config --global user.name "你的名字"
git config --global user.email "你的邮箱@example.com"
```

---

## 6. 克隆项目

选择一个你喜欢的工作目录，例如桌面：

```fish
cd ~/Desktop
git clone https://github.com/jayncp/solve-figure.git
cd solve-figure
```

---

## 7. 安装项目依赖

在项目根目录下执行：

```fish
uv sync
```

这会自动创建虚拟环境并安装所有依赖（numpy, scipy, matplotlib 等）。

---

## 8. 运行代码

### 8.1 生成利润对比图（run_figures.py）

```fish
uv run python LYC-0327/run_figures.py
```

运行完成后，图片输出到 `LYC-0327/figures/` 目录下，包括：

| 文件 | 内容 |
|------|------|
| `fig1_J_I_sweep.png` | J_I 变化下的利润曲线 |
| `fig1_J_I_sweep_rescaled.png` | 同上（分段线性缩放） |
| `fig2_sigma_epsilon2_sweep.png` | sigma_epsilon2 变化 |
| `fig3_sigma_eta2_sweep.png` | sigma_eta2 变化 |
| `fig4_sigma_u2_sweep.png` | sigma_u2 变化 |
| `fig5_rho_sweep.png` | rho 变化 |

### 8.2 rho 参数扫描分析（sweep_rho.py）

```fish
uv run python LYC-0327/change_rho/sweep_rho.py
```

运行完成后，输出到 `LYC-0327/change_rho/output/` 目录下，包括：

- 各参数组合的利润图（`.png`）
- 非单调性分析报告 `non_monotonic_report.md`

---

## 9. 使用通义灵码 AI 辅助修改脚本

通义灵码内置了 AI 编程助手，可以帮你理解代码、按需求微调脚本，而不需要你完全掌握 Python 语法。

### 9.1 打开项目

在通义灵码中：**文件 > 打开文件夹**，选择克隆下来的 `solve-figure` 目录。

左侧文件树会显示项目结构，关注以下文件：

```
LYC-0327/
├── run_figures.py          ← 生成利润对比图的主脚本
├── two_period.py           ← 模型定义（利润公式、均衡方程）
├── change_rho/
│   └── sweep_rho.py        ← rho 参数扫描脚本
└── figures/                ← 输出图片目录
```

### 9.2 理解代码：选中 → 问 AI

当你想理解某段代码的含义时：

1. 在编辑器中 **选中** 你感兴趣的代码段
2. 右键 → **通义灵码 > 解释代码**（或使用快捷键）
3. AI 会在侧边栏用中文解释这段代码的作用

**示例：** 选中 `run_figures.py` 里的 `METRICS` 和 `LABELS` 部分，问 AI「这里定义了哪些指标？每个指标是什么意思？」

### 9.3 修改需求：用自然语言描述你想要的改动

在侧边栏的 AI 对话框中，直接用中文描述你的需求。以下是常见场景的提问模板：

#### 场景 A：修改参数范围

> 我想把 `run_figures.py` 中 rho 的扫描范围从 0.01~0.99 改成 0.1~0.9，步数改为 50

#### 场景 B：增加新指标

> 我想在 `run_figures.py` 的图中增加一条新曲线，表示 informed MM 利润与 uninformed MM 利润之差

#### 场景 C：修改图表样式

> 我想把 `run_figures.py` 生成的图的标题字体改大，线条改粗，并且给每条曲线用不同的线型（实线、虚线、点划线）

#### 场景 D：修改模型参数基准值

> 我想把 `run_figures.py` 中 `BASE_PARAMS` 的 `J_I` 从 15 改成 20，`sigma_v2` 从 1 改成 2

### 9.4 应用 AI 建议的改动

AI 给出代码修改建议后，有两种方式应用：

**方式一：使用内联编辑（推荐）**

1. 在编辑器中打开要修改的文件
2. 选中需要修改的代码区域
3. 按 `Cmd + I` 调出内联编辑框
4. 输入你的修改需求，例如：「把这个列表里增加 profit_mm_diff 指标」
5. AI 会直接在编辑器中显示修改前后的对比（绿色为新增，红色为删除）
6. 点击 **接受** 或 **拒绝**

**方式二：手动复制**

1. 从 AI 侧边栏的回答中复制代码块
2. 替换编辑器中对应的代码段
3. `Cmd + S` 保存

### 9.5 修改后验证

每次修改后，**必须在终端中重新运行脚本**，确认改动生效且没有报错：

```fish
# 在通义灵码的内置终端中执行（Ctrl + ` 打开终端）
uv run python LYC-0327/run_figures.py
```

如果报错，将错误信息复制粘贴到 AI 对话框中，AI 会帮你分析原因并给出修复建议。

### 9.6 实战示例：增加利润差指标

以下演示一个完整的修改流程——在图中增加 informed MM 和 uninformed MM 的利润差。

**第一步：** 打开 `LYC-0327/two_period.py`，找到 `intermediates` 方法末尾的 `return` 字典（约第 419 行）。按 `Cmd + I`，输入：

> 在 intermediates 字典中增加 profit_mm_diff，值为 profit_informed_mm 减去 profit_uninformed_mm

**第二步：** 在同一文件中找到 `metrics` 方法（约第 457 行）。按 `Cmd + I`，输入：

> 在 metrics 返回值中增加 profit_mm_diff

**第三步：** 打开 `LYC-0327/run_figures.py`，找到 `METRICS` 和 `LABELS`（约第 25 行）。按 `Cmd + I`，输入：

> 在 METRICS 元组中增加 "profit_mm_diff"，在 LABELS 中增加对应标签 "Informed MM − Uninformed MM"

**第四步：** 保存所有文件，在终端运行：

```fish
uv run python LYC-0327/run_figures.py
```

检查 `LYC-0327/figures/` 下新生成的图片中是否多了一条利润差曲线。

### 9.7 提问技巧

| 做法 | 效果 |
|------|------|
| 指明文件名和大致位置 | AI 定位更准确 |
| 说清楚「在哪里改」和「改成什么」 | 避免 AI 改错位置 |
| 贴上报错信息 | AI 能直接定位 bug |
| 一次只改一个小功能 | 容易验证，出错好排查 |
| 改完立刻运行验证 | 问题趁热修比积攒起来改更轻松 |

---

## 常见问题

### Q: `brew` 命令找不到？

确保已将 brew 加入 fish 的 PATH（见第 2.1 节）。重新打开终端后再试。

### Q: `uv sync` 报错 Python 版本不满足？

本项目要求 Python >= 3.13。执行：

```fish
uv python install 3.13
uv sync
```

### Q: 运行脚本报 `ModuleNotFoundError`？

确保使用 `uv run python ...` 而不是直接 `python ...`，前者会自动激活项目虚拟环境。

### Q: matplotlib 报错 `no display`？

脚本已使用 `matplotlib.use("Agg")` 后端，不需要图形界面。如果仍有问题，确认依赖安装完整：

```fish
uv sync
```
