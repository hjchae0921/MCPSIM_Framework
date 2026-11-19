# dolfinx.fem.petsc.assign

```python
dolfinx.fem.petsc.assign(u: Function | Sequence[Function], x: Vec)
dolfinx.fem.petsc.assign(x: Vec, u: Function | Sequence[Function])
```

Assign `Function` degrees-of-freedom to a vector.

Assigns degree-of-freedom values in `u`, which is possibly a
sequence of ``` Function``s, to ``x ```. When `u` is a sequence of
``` Function``s, degrees-of-freedom for the ``Function``s in ``u ``` are
‘stacked’ and assigned to `x`. See [`assign()`](https://docs.fenicsproject.org/dolfinx/v0.10.0/python/generated/dolfinx.fem.petsc.html#dolfinx.fem.petsc.assign "dolfinx.fem.petsc.assign") for
documentation on how stacked assignment is handled.

**Parameters:**

- **u** – `Function` (s) to assign degree-of-freedom value from.
- **x** – Vector to assign degree-of-freedom values in `u` to.
