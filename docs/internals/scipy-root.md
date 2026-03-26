# ScipyRootSolver 实现细节

`ScipyRootSolver` 是对 `scipy.optimize.root` 的薄封装，是框架中最常用的底层求解器。

## 底层调用

```python
raw = optimize.root(
    lambda vector: system.equations(to_float_array(vector), params),
    guess,
    method=self.method,
    jac=system.jacobian if use_jacobian else None,
    options=root_options,
)
```

- `fun` 是一个 lambda，将 scipy 传入的向量转换为 `NDArrayFloat` 后调用 `system.equations`
- `method` 由构造参数指定，常用 `"hybr"`（Powell 混合法）和 `"lm"`（Levenberg-Marquardt）
- `jac` 仅在 `options["use_jacobian"]` 为 `True` 时传入 `system.jacobian`

## options 处理

`options` 字典在传递给 scipy 之前，框架会先提取 `use_jacobian` 键：

```python
root_options = dict(options or {})
use_jacobian = bool(root_options.pop("use_jacobian", False))
```

提取后的剩余键直接透传给 `scipy.optimize.root` 的 `options` 参数。

## 初始值处理

- `initial_guess=None` 时，生成长度为 `n_vars` 的零向量
- 非 `None` 时，经过 `to_float_array` 和 `system.validate_x` 校验

## 残差计算

```python
residual_norm = float(np.linalg.norm(raw.fun))
```

使用 `raw.fun`（scipy 返回的最终残差向量）的 L2 范数。

## require_constraints 后处理

当 `require_constraints=True` 时，即使 scipy 报告收敛（`raw.success=True`），如果模型的约束检查不通过，结果会被修改：

```python
if self.require_constraints and result.success and not result.constraints_ok:
    return replace(result, success=False,
                   message=f"{result.message}; constraints not satisfied")
```

这确保 `CompositeSolver` 在遇到约束不满足的解时，会继续尝试下一个策略。

## 常见 method 选择

| method | 特点 | 适用场景 |
|--------|------|---------|
| `"hybr"` | Powell 混合法，默认方法 | 通用，适合大多数问题 |
| `"lm"` | Levenberg-Marquardt | 适合病态或近奇异问题，超定系统 |

更多方法参见 [scipy 文档](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.root.html)。
