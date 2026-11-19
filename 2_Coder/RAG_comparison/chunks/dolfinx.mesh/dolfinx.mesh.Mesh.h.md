# dolfinx.mesh.Mesh.h

```python
h(dim: int, entities: ndarray[tuple[int, ...], dtype[int32]]) → ndarray[tuple[int, ...], dtype[float64]]
```

Geometric size measure of cell entities.

**Parameters:**

- **dim** – Topological dimension of the entities to compute the
  size measure of.
- **entities** – Indices of entities of dimension `dim` to
  compute size measure of.

**Returns:**

Size measure for each requested entity.
