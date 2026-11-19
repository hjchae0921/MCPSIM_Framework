# dolfinx.fem.CoordinateElement.push_forward

```python
push_forward(X: ndarray[tuple[int, ...], dtype[float32]] | ndarray[tuple[int, ...], dtype[float64]], cell_geometry: ndarray[tuple[int, ...], dtype[float32]] | ndarray[tuple[int, ...], dtype[float64]]) → ndarray[tuple[int, ...], dtype[float32]] | ndarray[tuple[int, ...], dtype[float64]]
```

Push points on the reference cell forward to the physical cell.

**Parameters:**

- **X** – Coordinates of points on the reference cell,
  `shape=(num_points, topological_dimension)`.
- **cell\_geometry** – Coordinate ‘degrees-of-freedom’ (nodes) of
  the cell, `shape=(num_geometry_basis_functions,
  geometrical_dimension)`. Can be created by accessing
  `geometry.x[geometry.dofmap.cell_dofs(i)]`,

**Returns:**

Physical coordinates of the points reference points `X`.
