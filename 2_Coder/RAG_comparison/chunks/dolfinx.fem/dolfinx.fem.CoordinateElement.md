# dolfinx.fem.CoordinateElement

```python
class dolfinx.fem.CoordinateElement(cmap: CoordinateElement_float32 | CoordinateElement_float64)
```

Bases: `object`

Coordinate element describing the geometry map for mesh cells.

Create a coordinate map element.

Note

This initialiser is for internal use and not normally called
in user code. Use [`coordinate_element()`](https://docs.fenicsproject.org/dolfinx/v0.10.0/python/generated/dolfinx.fem.html#dolfinx.fem.coordinate_element "dolfinx.fem.coordinate_element") to create a
CoordinateElement.

**Parameters:**

**cmap** – A C++ CoordinateElement.
