# dolfinx.mesh.meshtags

```python
dolfinx.mesh.meshtags(msh: Mesh, dim: int, entities: ndarray[tuple[int, ...], dtype[int32]], values: ndarray | int | float) → MeshTags
```

Create a MeshTags object that associates data with a subset of
mesh entities.

**Parameters:**

- **msh** – The mesh.
- **dim** – Topological dimension of the mesh entity.
- **entities** – Indices(local to process) of entities to associate
  values with . The array must be sorted and must not contain
  duplicates.
- **values** – The corresponding value for each entity.

**Returns:**

A mesh tags object.

Note

The type of the returned MeshTags is inferred from the type of
`values`.
