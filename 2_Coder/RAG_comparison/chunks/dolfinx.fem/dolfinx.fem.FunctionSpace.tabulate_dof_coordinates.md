# dolfinx.fem.FunctionSpace.tabulate_dof_coordinates

```python
tabulate_dof_coordinates() → ndarray[tuple[int, ...], dtype[float64]]
```

Tabulate the coordinates of the degrees-of-freedom in the
function space.

**Returns:**

Coordinates of the degrees-of-freedom.

Note

This method is only for elements with point evaluation
degrees-of-freedom.
