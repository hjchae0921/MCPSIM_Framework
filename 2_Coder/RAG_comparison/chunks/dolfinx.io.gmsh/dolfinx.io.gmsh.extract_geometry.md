# dolfinx.io.gmsh.extract_geometry

```python
dolfinx.io.gmsh.extract_geometry(model, name: str | None = None) → ndarray[tuple[int, ...], dtype[float64]]
```

Extract the mesh geometry from a Gmsh model.

Returns an array of shape `(num_nodes, 3)`, where the i-th row
corresponds to the i-th node in the mesh.

**Parameters:**

- **model** – Gmsh model
- **name** – Name of the Gmsh model. If not set the current
  model will be used.

**Returns:**

The mesh geometry as an array of shape `(num_nodes, 3)`.
