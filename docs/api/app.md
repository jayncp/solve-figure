# app — Demo 入口

`equilibrium.app` 包含 Demo pipeline 的入口函数。这些函数目前只服务于内置的演示流程，不构成通用 CLI 框架。

```python
from equilibrium.app import run_demo_pipeline, build_status_message, main
```

## run_demo_pipeline

```python
def run_demo_pipeline(output_dir: str | Path = "output") -> Path: ...
```

运行内置的 Demo 流程：

1. 创建 `DemoEquilibriumModel` 实例
2. 用 `CompositeSolver`（hybr + lm，均开启约束检查）求解
3. 用 `ParameterSweep.sweep_1d` 沿 `curvature` 参数扫描 8 个点
4. 用 `FigurePlotter.plot_1d` 绑图并保存

**参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `output_dir` | `str \| Path` | `"output"` | 输出目录 |

**返回：** 保存的图片路径（`Path`），默认为 `output/demo_equilibrium_sweep.png`。

## build_status_message

```python
def build_status_message(figure_path: str | Path) -> str: ...
```

生成一行状态摘要。

**返回：** `"demo pipeline complete: figure saved to {path}"`

## main

```python
def main() -> None: ...
```

CLI 入口函数。调用 `run_demo_pipeline` 并打印状态消息。

注册在 `pyproject.toml` 的 `[project.scripts]` 中：

```toml
[project.scripts]
solve-figure0326 = "equilibrium.app:main"
```

通过 `uv run solve-figure0326` 调用。
