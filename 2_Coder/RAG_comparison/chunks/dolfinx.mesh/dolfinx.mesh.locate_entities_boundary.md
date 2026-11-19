# dolfinx.mesh.locate_entities_boundary

```python
dolfinx.mesh.locate_entities_boundary(msh: Mesh, dim: int, marker: Callable) → ndarray
```

Compute mesh entities that are connected to an owned boundary
facet and satisfy a geometric marking function.

For vertices and edges, in parallel this function will not
necessarily mark all entities that are on the exterior boundary. For
example, it is possible for a process to have a vertex that lies on
the boundary without any of the attached facets being a boundary
facet. When used to find degrees-of-freedom, e.g. using
[`dolfinx.fem.locate_dofs_topological()`](https://docs.fenicsproject.org/dolfinx/v0.10.0/python/generated/dolfinx.fem.html#dolfinx.fem.locate_dofs_topological "dolfinx.fem.locate_dofs_topological"), the function that uses
the data returned by this function must typically perform some
parallel communication.

**Parameters:**

- **msh** – Mesh to locate boundary entities on.
- **dim** – Topological dimension of the mesh entities to consider
- **marker** – Function that takes an array of points `x` with shape
  `(gdim, num_points)` and returns an array of booleans of
  length `num_points`, evaluating to `True` for entities
  to be located.

**Returns:**

Indices (local to the process) of marked mesh entities.
