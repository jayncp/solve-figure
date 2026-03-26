# 画图与导出

`FigurePlotter` 将扫描结果绘制为 matplotlib 图表。

## 一维折线图

```python
from pathlib import Path
from equilibrium.plotting import FigurePlotter

plotter = FigurePlotter()

fig = plotter.plot_1d(
    result,                                   # SweepResult1D
    metrics=["q1", "price", "profit1"],       # 要画的指标
    title="Effect of Marginal Cost",
    xlabel="Marginal Cost (c)",
    ylabel="Value",
)
plotter.save(fig, Path("output/my_plot.png"))
```

**`plot_1d` 参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `result` | `SweepResult1D` | — | 一维扫描结果 |
| `metrics` | `list[str]` | — | 要绑定的指标名称列表 |
| `title` | `str \| None` | `None` | 图表标题，默认为 `"{sweep_param} sweep"` |
| `xlabel` | `str \| None` | `None` | X 轴标签，默认为扫描参数名 |
| `ylabel` | `str` | `"value"` | Y 轴标签 |

每个指标画一条带圆点标记的折线，自动添加图例。

## 二维热力图

```python
fig = plotter.plot_2d_heatmap(
    result_2d,                # SweepResult2D
    metric="price",           # 单个指标名
    title="Price Heatmap",
    xlabel="c",
    ylabel="a",
)
plotter.save(fig, Path("output/heatmap.png"))
```

**`plot_2d_heatmap` 参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `result` | `SweepResult2D` | — | 二维扫描结果 |
| `metric` | `str` | — | 要绘制的指标名称 |
| `title` | `str \| None` | `None` | 图表标题 |
| `xlabel` | `str \| None` | `None` | X 轴标签，默认为 `sweep_param_2` |
| `ylabel` | `str \| None` | `None` | Y 轴标签，默认为 `sweep_param_1` |

## 保存图片

```python
path = plotter.save(fig, "output/figure.png")
```

- 自动创建父目录
- 以 150 DPI 保存
- 保存后自动关闭 figure 释放内存
- 返回保存路径的 `Path` 对象

## 自定义画图

如果内置的 `plot_1d` / `plot_2d_heatmap` 不满足需求，可以直接从 `SweepResult` 取数据，用 matplotlib 自行绑定：

```python
import matplotlib.pyplot as plt

fig, ax = plt.subplots()

# 从 SweepResult1D 取数据
x = result.sweep_values
y = result.metric_series("profit1")
mask = result.success_mask().astype(bool)

ax.plot(x[mask], y[mask], "o-", label="Profit")
ax.set_xlabel("c")
ax.set_ylabel("Profit")
ax.legend()

fig.savefig("output/custom.png", dpi=200)
plt.close(fig)
```

同样，`SweepResult2D.metric_grid("name")` 返回二维 numpy 数组，可以直接用 `imshow`、`contourf` 等绑定。
