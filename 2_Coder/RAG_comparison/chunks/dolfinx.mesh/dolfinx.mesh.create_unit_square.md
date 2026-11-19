# dolfinx.mesh.create_unit_square

```python
dolfinx.mesh.create_unit_square(comm: ~mpi4py.MPI.Comm, nx: int, ny: int, cell_type=CellType.triangle, dtype: ~numpy.dtype[~typing.Any] | None | type[~typing.Any] | ~numpy._typing._dtype_like._SupportsDType[~numpy.dtype[~typing.Any]] | str | tuple[~typing.Any, int] | tuple[~typing.Any, ~typing.SupportsIndex | ~collections.abc.Sequence[~typing.SupportsIndex]] | list[~typing.Any] | ~numpy._typing._dtype_like._DTypeDict | tuple[~typing.Any, ~typing.Any] = <class 'numpy.float64'>, ghost_mode=GhostMode.shared_facet, partitioner=None, diagonal: ~dolfinx.cpp.mesh.DiagonalType = DiagonalType.right) → Mesh
```

Create a mesh of a unit square.

**Parameters:**

- **comm** – MPI communicator.
- **nx** – Number of cells in the “x” direction.
- **ny** – Number of cells in the “y” direction.
- **cell\_type** – Mesh cell type.
- **dtype** – Float type for the mesh geometry(`numpy.float32`
  or `numpy.float64`).
- **ghost\_mode** – Ghost mode used in the mesh partitioning.
- **partitioner** – Function that computes the parallel distribution of
  cells across MPI ranks.
- **diagonal** – Direction of diagonal. See [`DiagonalType`](https://docs.fenicsproject.org/dolfinx/v0.10.0/python/generated/dolfinx.mesh.html#dolfinx.mesh.DiagonalType "dolfinx.mesh.DiagonalType") for
  available options.

**Returns:**

A mesh of a square with corners at `(0, 0)` and `(1, 1)`.
