# dolfinx.mesh.locate_entities

```python
dolfinx.mesh.locate_entities(msh: Mesh, dim: int, marker: Callable) → ndarray
```

Compute mesh entities satisfying a geometric marking function.

**Parameters:**

- **msh** – Mesh to locate entities on.
- **dim** – Topological dimension of the mesh entities to consider.
- **marker** – A function that takes an array of points `x` with
  shape `(gdim, num_points)` and returns an array of
  booleans of length `num_points`, evaluating to True for
  entities to be located.

**Returns:**

Indices (local to the process) of marked mesh entities.
