# dolfinx.mesh.create_unit_cube

```python
dolfinx.mesh.create_unit_cube(comm: ~mpi4py.MPI.Comm, nx: int, ny: int, nz: int, cell_type=CellType.tetrahedron, dtype: ~numpy.dtype[~typing.Any] | None | type[~typing.Any] | ~numpy._typing._dtype_like._SupportsDType[~numpy.dtype[~typing.Any]] | str | tuple[~typing.Any, int] | tuple[~typing.Any, ~typing.SupportsIndex | ~collections.abc.Sequence[~typing.SupportsIndex]] | list[~typing.Any] | ~numpy._typing._dtype_like._DTypeDict | tuple[~typing.Any, ~typing.Any] = <class 'numpy.float64'>, ghost_mode=GhostMode.shared_facet, partitioner=None) → Mesh
```

Create a mesh of a unit cube.

**Parameters:**

- **comm** – MPI communicator.
- **nx** – Number of cells in “x” direction.
- **ny** – Number of cells in “y” direction.
- **nz** – Number of cells in “z” direction.
- **cell\_type** – Mesh cell type
- **dtype** – Float type for the mesh geometry(`numpy.float32`
  or `numpy.float64`).
- **ghost\_mode** – Ghost mode used in the mesh partitioning.
- **partitioner** – Function that computes the parallel distribution of
  cells across MPI ranks.

**Returns:**

A mesh of an axis-aligned unit cube with corners at `(0, 0, 0)`
and `(1, 1, 1)`.
