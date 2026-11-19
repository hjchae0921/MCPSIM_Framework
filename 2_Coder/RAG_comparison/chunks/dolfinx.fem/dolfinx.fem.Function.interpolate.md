# dolfinx.fem.Function.interpolate

```python
interpolate(u0: Callable | Expression | Function, cells0: ndarray | None = None, cells1: ndarray | None = None) → None
```

Interpolate an expression.

**Parameters:**

- **u0** – Callable function, Expression or Function to
  interpolate.
- **cells0** – Cells in mesh associated with `u0` to interpolate
  over. If `None` then all cells are interpolated over.
- **cells1** – Cells in the mesh associated with `self` to
  interpolate over. If `None`, then taken to be the same
  cells as `cells0`. If `cells1` is not `None`, then
  it must have the same length as `cells0`.
