# dolfinx.mesh.create_interval

```python
dolfinx.mesh.create_interval(comm: ~mpi4py.MPI.Comm, nx: int, points: ~collections.abc.Buffer | ~numpy._typing._array_like._SupportsArray[~numpy.dtype[~typing.Any]] | ~numpy._typing._nested_sequence._NestedSequence[~numpy._typing._array_like._SupportsArray[~numpy.dtype[~typing.Any]]] | bool | int | float | complex | str | bytes | ~numpy._typing._nested_sequence._NestedSequence[bool | int | float | complex | str | bytes], dtype: ~numpy.dtype[~typing.Any] | None | type[~typing.Any] | ~numpy._typing._dtype_like._SupportsDType[~numpy.dtype[~typing.Any]] | str | tuple[~typing.Any, int] | tuple[~typing.Any, ~typing.SupportsIndex | ~collections.abc.Sequence[~typing.SupportsIndex]] | list[~typing.Any] | ~numpy._typing._dtype_like._DTypeDict | tuple[~typing.Any, ~typing.Any] = <class 'numpy.float64'>, ghost_mode=GhostMode.shared_facet, partitioner=None) → Mesh
```

Create an interval mesh.

**Parameters:**

- **comm** – MPI communicator.
- **nx** – Number of cells.
- **points** – Coordinates of the end points.
- **dtype** – Float type for the mesh geometry(`numpy.float32`
  or `numpy.float64`).
- **ghost\_mode** – Ghost mode used in the mesh partitioning. Options
  are `GhostMode.none` and `GhostMode.shared_facet`.
- **partitioner** – Partitioning function to use for determining the
  parallel distribution of cells across MPI ranks.

**Returns:**

An interval mesh.
