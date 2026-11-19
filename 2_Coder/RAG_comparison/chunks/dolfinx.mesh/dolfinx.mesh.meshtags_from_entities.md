# dolfinx.mesh.meshtags_from_entities

```python
dolfinx.mesh.meshtags_from_entities(msh: Mesh, dim: int, entities: AdjacencyList, values: ndarray[tuple[int, ...], dtype[Any]])
```

Create a :class:dolfinx.mesh.MeshTags` object that associates
data with a subset of mesh entities, where the entities are defined
by their vertices.

**Parameters:**

- **msh** – The mesh.
- **dim** – Topological dimension of the mesh entity.
- **entities** – Entities to associated values with, with entities
  defined by their vertices.
- **values** – The corresponding value for each entity.

**Returns:**

A mesh tags object.

Note

The type of the returned MeshTags is inferred from the type of
`values`.
