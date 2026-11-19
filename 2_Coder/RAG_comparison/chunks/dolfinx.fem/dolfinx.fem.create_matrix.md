# dolfinx.fem.create_matrix

```python
dolfinx.fem.create_matrix(a: Form, block_mode: BlockMode | None = None) → MatrixCSR
```

Create a sparse matrix that is compatible with a given bilinear
form.

**Parameters:**

- **a** – Bilinear form.
- **block\_mode** – Block mode of the CSR matrix. If `None`, default
  is used.

**Returns:**

A sparse matrix that the form can be assembled into.
