# dolfinx.io.gmsh.read_from_msh

```python
dolfinx.io.gmsh.read_from_msh(filename: str | Path, comm: Comm, rank: int = 0, gdim: int = 3, partitioner: Callable[[Comm, int, int, AdjacencyList], AdjacencyList_int32] | None = None) → MeshData
```

Read a Gmsh .msh file and return a [`dolfinx.mesh.Mesh`](https://docs.fenicsproject.org/dolfinx/v0.10.0/python/generated/dolfinx.mesh.html#dolfinx.mesh.Mesh "dolfinx.mesh.Mesh") and
cell facet markers.

Note

This function requires the Gmsh Python module.

**Parameters:**

- **filename** – Name of `.msh` file.
- **comm** – MPI communicator to create the mesh on.
- **rank** – Rank of `comm` responsible for reading the `.msh`
  file.
- **gdim** – Geometric dimension of the mesh

**Returns:**

Meshdata with mesh, cell tags, facet tags, edge tags,
vertex tags and physical groups.
