# dolfinx.mesh.create_mesh

```python
dolfinx.mesh.create_mesh(comm: Comm, cells: ndarray[tuple[int, ...], dtype[int64]], e: Mesh | FiniteElement | _BasixElement | CoordinateElement, x: ndarray[tuple[int, ...], dtype[floating]], partitioner: Callable | None = None, max_facet_to_cell_links: int = 2) → Mesh
```

Create a mesh from topology and geometry arrays.

**Parameters:**

- **comm** – MPI communicator to define the mesh on.
- **cells** – Cells of the mesh. `cells[i]` are the ‘nodes’ of
  cell `i`.
- **x** – Mesh geometry (‘node’ coordinates), with shape
  `(num_nodes, gdim)`.
- **e** – UFL mesh. The mesh scalar type is determined by the scalar
  type of `e`.
- **partitioner** – Function that determines the parallel distribution of
  cells across MPI ranks.
- **max\_facet\_to\_cell\_links** – Maximum number of cells a facet can
  be connected to.

Note

If required, the coordinates `x` will be cast to the same
scalar type as the domain/element `e`.

**Returns:**

A mesh.
