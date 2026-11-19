# dolfinx.mesh.create_geometry

```python
dolfinx.mesh.create_geometry(index_map: IndexMap, dofmap: ndarray[tuple[int, ...], dtype[int32]], element: CoordinateElement, x: ndarray, input_global_indices: ndarray[tuple[int, ...], dtype[int64]]) → Geometry
```

Create a Geometry object.

**Parameters:**

- **index\_map** – Index map describing the layout of the geometry
  points (nodes).
- **dofmap** – The geometry (point) dofmap. For a cell, it gives the
  row in the point coordinates `x` of each local geometry
  node. `shape=(num_cells, num_dofs_per_cell)`.
- **element** – Element that describes the cell geometry map.
- **x** – The point coordinates. The shape is
  `(num_points, geometric_dimension).`
- **input\_global\_indices** – The ‘global’ input index of each point,
  commonly from a mesh input file.
