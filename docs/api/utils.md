# utils — 工具函数

`equilibrium.utils` 提供校验和类型转换工具，主要由框架内部使用，使用者在需要时也可直接调用。

```python
from equilibrium.utils import to_float_array, ensure_finite, constraints_ok
```

## to_float_array

```python
def to_float_array(values: Sequence[float] | NDArrayFloat) -> NDArrayFloat: ...
```

将一维输入序列转换为 `np.float64` 数组。

- 输入必须是一维的，否则抛出 `ValueError`
- 支持 list、tuple、numpy 数组等

## ensure_finite

```python
def ensure_finite(name: str, values: NDArrayFloat) -> None: ...
```

检查数组中是否包含 NaN 或 inf。如果包含，抛出 `ValueError`，消息中包含 `name` 参数用于定位。

## constraints_ok

```python
def constraints_ok(constraints: Mapping[str, float]) -> bool: ...
```

当所有约束值严格为正时返回 `True`。这是 `SolveResult.constraints_ok` 的底层判定逻辑。

```python
>>> constraints_ok({"x_positive": 1.5, "y_positive": 0.3})
True
>>> constraints_ok({"x_positive": 1.5, "y_positive": -0.1})
False
```
