# dolfinx.mesh.refine

```python
dolfinx.mesh.refine(msh: ~dolfinx.mesh.Mesh, edges: ~numpy.ndarray | None = None, partitioner: ~collections.abc.Callable | ~dolfinx.cpp.refinement.IdentityPartitionerPlaceholder = <dolfinx.cpp.refinement.IdentityPartitionerPlaceholder object>, option: ~dolfinx.cpp.refinement.RefinementOption = RefinementOption.parent_cell) → tuple[Mesh, ndarray[tuple[int, ...], dtype[int32]], ndarray[tuple[int, ...], dtype[int8]]]
```

Refine a mesh.

Note

Using the None partitioner for the refined mesh, the refined mesh
will **not** include ghosts cells (cells connected by facet to an
owned cells) even if the parent mesh is ghosted. The refined cells
will be on the same process as the parent cell.

**Parameters:**

- **msh** – Mesh from which to create the refined mesh.
- **edges** – Indices of edges to split during refinement. If `None`,
  mesh refinement is uniform.
- **partitioner** – Partitioner to distribute the refined mesh. If a
  [`IdentityPartitionerPlaceholder`](https://docs.fenicsproject.org/dolfinx/v0.10.0/python/generated/dolfinx.mesh.html#dolfinx.mesh.IdentityPartitionerPlaceholder "dolfinx.mesh.IdentityPartitionerPlaceholder") is passed (default)
  no redistribution is performed, i.e. refined cells remain on
  the same process as the parent cell, but the ghost layer is
  updated. If a custom partitioner is passed, it will be used for
  distributing the refined mesh. If `None` is passed no
  redistribution will happen.
- **option** – Controls whether parent cells and/or parent facets are
  computed.

**Returns:**

Refined mesh, (optional) parent cells, (optional) parent facets
