# dolfinx.fem.Function.interpolate_nonmatching

```python
interpolate_nonmatching(u0: Function, cells: ndarray[tuple[int, ...], dtype[int32]], interpolation_data: PointOwnershipData) → None
```

Interpolate a Function defined on one mesh to a function
defined on a different mesh.

**Parameters:**

- **u0** – The Function to interpolate.
- **cells** – The cells to interpolate over. If `None` then all
  cells are interpolated over.
- **interpolation\_data** – Data needed to interpolate functions
  defined on other meshes. Created by
  [`dolfinx.fem.create_interpolation_data()`](https://docs.fenicsproject.org/dolfinx/v0.10.0/python/generated/dolfinx.fem.html#dolfinx.fem.create_interpolation_data "dolfinx.fem.create_interpolation_data").
