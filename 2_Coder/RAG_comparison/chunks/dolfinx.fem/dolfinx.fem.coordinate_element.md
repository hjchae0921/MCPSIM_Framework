# dolfinx.fem.coordinate_element

```python
dolfinx.fem.coordinate_element(celltype: ~dolfinx.cpp.mesh.CellType, degree: int, variant=0, dtype: ~numpy.dtype[~typing.Any] | None | type[~typing.Any] | ~numpy._typing._dtype_like._SupportsDType[~numpy.dtype[~typing.Any]] | str | tuple[~typing.Any, int] | tuple[~typing.Any, ~typing.SupportsIndex | ~collections.abc.Sequence[~typing.SupportsIndex]] | list[~typing.Any] | ~numpy._typing._dtype_like._DTypeDict | tuple[~typing.Any, ~typing.Any] = <class 'numpy.float64'>)
dolfinx.fem.coordinate_element(e: FiniteElement)
```

Create a Lagrange CoordinateElement from element metadata.

Coordinate elements are typically used to create meshes.

**Parameters:**

- **celltype** – Cell shape
- **degree** – Polynomial degree of the coordinate element map.
- **variant** – Basix Lagrange variant (affects node placement).
- **dtype** – Scalar type for the coordinate element.

**Returns:**

A coordinate element.
