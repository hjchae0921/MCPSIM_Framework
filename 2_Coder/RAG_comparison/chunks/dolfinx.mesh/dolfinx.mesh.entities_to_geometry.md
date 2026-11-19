# dolfinx.mesh.entities_to_geometry

```python
dolfinx.mesh.entities_to_geometry(msh: Mesh, dim: int, entities: ndarray[tuple[int, ...], dtype[int32]], permute=False) → ndarray[tuple[int, ...], dtype[int32]]
```

Compute the geometric DOFs associated with the closure of the
given mesh entities.

**Parameters:**

- **msh** – The mesh.
- **dim** – Topological dimension of the entities of interest.
- **entities** – Entity indices (local to the process).
- **permute** – Permute the DOFs such that they are consistent with the
  orientation of dim-dimensional mesh entities. This
  requires create\_entity\_permutations to be called first.

**Returns:**

The geometric DOFs associated with the closure of the entities
in entities.
