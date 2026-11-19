# dolfinx.fem.FiniteElement.Tt_apply

```python
Tt_apply(x: ndarray[tuple[int, ...], dtype[floating]], cell_permutations: ndarray[tuple[int, ...], dtype[uint32]], dim: int) → None
```

Apply the transpose of the operator applied by T\_apply().

**Parameters:**

- **x** – Data to transform (in place). The shape is
  `(num_cells, n, dim)`, where `n` is the number degrees-
  of-freedom and the data is flattened (row-major).
- **cell\_permutations** – Permutation data for the cells
- **dim** – Number of columns in `data`.
