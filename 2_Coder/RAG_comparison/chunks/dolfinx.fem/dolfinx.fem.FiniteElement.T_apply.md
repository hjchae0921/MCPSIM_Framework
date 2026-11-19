# dolfinx.fem.FiniteElement.T_apply

```python
T_apply(x: ndarray[tuple[int, ...], dtype[floating]], cell_permutations: ndarray[tuple[int, ...], dtype[uint32]], dim: int) → None
```

Transform basis functions from the reference element ordering
and orientation to the globally consistent physical element
ordering and orientation.

**Parameters:**

- **x** – Data to transform (in place). The shape is
  `(num_cells, n, dim)`, where `n` is the number degrees-
  of-freedom and the data is flattened (row-major).
- **cell\_permutations** – Permutation data for the cell.
- **dim** – Number of columns in `data`.

Note

Exposed for testing. Function is not vectorised across multiple
cells. Please see basix.numba\_helpers for performant
versions.
