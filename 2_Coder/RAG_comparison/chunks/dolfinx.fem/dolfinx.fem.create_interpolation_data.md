# dolfinx.fem.create_interpolation_data

```python
dolfinx.fem.create_interpolation_data(V_to: FunctionSpace, V_from: FunctionSpace, cells: ndarray[tuple[int, ...], dtype[int32]], padding: float = 1e-14) → PointOwnershipData
```

Generate data needed to interpolate discrete functions across
different meshes.

**Parameters:**

- **V\_to** – Function space to interpolate into
- **V\_from** – Function space to interpolate from
- **cells** – Indices of the cells associated with V\_to on which to
  interpolate into.
- **padding** – Absolute padding of bounding boxes of all entities on
  mesh\_to

**Returns:**

Data needed to interpolation functions defined on function
spaces on the meshes.
