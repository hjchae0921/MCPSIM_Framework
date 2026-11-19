# dolfinx.mesh.compute_midpoints

```python
dolfinx.mesh.compute_midpoints(msh: Mesh, dim: int, entities: ndarray[tuple[int, ...], dtype[int32]])
```

Compute the midpoints of a set of mesh entities.

**Parameters:**

- **msh** – The mesh.
- **dim** – Topological dimension of the mesh entities to consider.
- **entities** – Indices of entities in `mesh` to consider.

**Returns:**

Midpoints of the entities, shape `(num_entities, 3)`.
