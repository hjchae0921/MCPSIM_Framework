# dolfinx.mesh.create_submesh

```python
dolfinx.mesh.create_submesh(msh: Mesh, dim: int, entities: ndarray[tuple[int, ...], dtype[int32]]) → tuple[Mesh, EntityMap, EntityMap, ndarray[tuple[int, ...], dtype[int32]]]
```

Create a mesh with specified entities from another mesh.

**Parameters:**

- **msh** – Mesh to create the sub-mesh from.
- **dim** – Topological dimension of the entities in `msh` to include
  in the sub-mesh.
- **entities** – Indices of entities in `msh` to include in the
  sub-mesh.

**Returns:**

The (1) sub mesh, (2) entity map, (3) vertex map, and (4) node
map (geometry). Each of the maps a local index of the sub mesh
to a local index of `msh`.
