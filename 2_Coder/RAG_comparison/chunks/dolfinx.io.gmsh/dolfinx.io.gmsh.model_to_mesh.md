# dolfinx.io.gmsh.model_to_mesh

```python
dolfinx.io.gmsh.model_to_mesh(model, comm: ~mpi4py.MPI.Comm, rank: int, gdim: int = 3, partitioner: ~collections.abc.Callable[[~mpi4py.MPI.Comm, int, int, ~dolfinx.cpp.graph.AdjacencyList_int32], ~dolfinx.cpp.graph.AdjacencyList_int32] | None = None, dtype=<class 'numpy.float64'>) → MeshData
```

Create a Mesh from a Gmsh model.

Creates a [`dolfinx.mesh.Mesh`](https://docs.fenicsproject.org/dolfinx/v0.10.0/python/generated/dolfinx.mesh.html#dolfinx.mesh.Mesh "dolfinx.mesh.Mesh") from the physical entities of
the highest topological dimension in the Gmsh model. In parallel,
the gmsh model is processed on one MPI rank, and the
[`dolfinx.mesh.Mesh`](https://docs.fenicsproject.org/dolfinx/v0.10.0/python/generated/dolfinx.mesh.html#dolfinx.mesh.Mesh "dolfinx.mesh.Mesh") is distributed across ranks.

**Parameters:**

- **model** – Gmsh model.
- **comm** – MPI communicator to use for mesh creation.
- **rank** – MPI rank that the Gmsh model is initialized on.
- **gdim** – Geometrical dimension of the mesh.
- **partitioner** – Function that computes the parallel
  distribution of cells across MPI ranks.

**Returns:**

MeshData with mesh and tags of corresponding entities by
codimension. Codimension 0 is the cell tags, codimension 1 is the
facet tags, codimension 2 is the ridge tags and codimension 3 is
the peak tags as well as a lookup table from the physical groups by
name to integer.

Note

For performance, this function should only be called once for
large problems. For reuse, it is recommended to save the mesh
and corresponding tags using [`dolfinx.io.XDMFFile`](https://docs.fenicsproject.org/dolfinx/v0.10.0/python/generated/dolfinx.io.html#dolfinx.io.XDMFFile "dolfinx.io.XDMFFile") after
creation for efficient access.
