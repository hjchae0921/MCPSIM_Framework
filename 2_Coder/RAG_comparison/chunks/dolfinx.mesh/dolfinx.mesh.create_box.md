# dolfinx.mesh.create_box

```python
dolfinx.mesh.create_box(comm: ~mpi4py.MPI.Comm, points: list[~collections.abc.Buffer | ~numpy._typing._array_like._SupportsArray[~numpy.dtype[~typing.Any]] | ~numpy._typing._nested_sequence._NestedSequence[~numpy._typing._array_like._SupportsArray[~numpy.dtype[~typing.Any]]] | bool | int | float | complex | str | bytes | ~numpy._typing._nested_sequence._NestedSequence[bool | int | float | complex | str | bytes]], n: ~collections.abc.Sequence[int], cell_type=CellType.tetrahedron, dtype: ~numpy.dtype[~typing.Any] | None | type[~typing.Any] | ~numpy._typing._dtype_like._SupportsDType[~numpy.dtype[~typing.Any]] | str | tuple[~typing.Any, int] | tuple[~typing.Any, ~typing.SupportsIndex | ~collections.abc.Sequence[~typing.SupportsIndex]] | list[~typing.Any] | ~numpy._typing._dtype_like._DTypeDict | tuple[~typing.Any, ~typing.Any] = <class 'numpy.float64'>, ghost_mode=GhostMode.shared_facet, partitioner=None) → Mesh
```

Create a box mesh.

**Parameters:**

- **comm** – MPI communicator.
- **points** – Coordinates of the ‘lower-left’ and ‘upper-right’
  corners of the box.
- **n** – List of cells in each direction
- **cell\_type** – The cell type.
- **dtype** – Float type for the mesh geometry(`numpy.float32`
  or `numpy.float64`).
- **ghost\_mode** – The ghost mode used in the mesh partitioning.
- **partitioner** – Function that computes the parallel distribution of
  cells across MPI ranks.

**Returns:**

A mesh of a box domain.
