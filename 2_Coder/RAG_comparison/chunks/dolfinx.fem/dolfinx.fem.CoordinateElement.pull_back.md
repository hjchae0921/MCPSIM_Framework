# dolfinx.fem.CoordinateElement.pull_back

```python
pull_back(x: ndarray[tuple[int, ...], dtype[float32]] | ndarray[tuple[int, ...], dtype[float64]], cell_geometry: ndarray[tuple[int, ...], dtype[float32]] | ndarray[tuple[int, ...], dtype[float64]]) → ndarray[tuple[int, ...], dtype[float32]] | ndarray[tuple[int, ...], dtype[float64]]
```

Pull points on the physical cell back to the reference cell.

For non-affine cells, the pull-back is a nonlinear operation.

**Parameters:**

- **x** – Physical coordinates to pull back to the reference cells,
  `shape=(num_points, geometrical_dimension)`.
- **cell\_geometry** – Physical coordinates describing the cell,
  shape `(num_of_geometry_basis_functions,
  geometrical_dimension)`. They can be created by accessing
  `geometry.x[geometry.dofmap.cell_dofs(i)]`,

**Returns:**

Reference coordinates of the physical points `x`.
