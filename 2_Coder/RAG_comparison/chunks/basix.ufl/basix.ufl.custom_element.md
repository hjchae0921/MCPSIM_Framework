# basix.ufl.custom_element

```python
basix.ufl.custom_element(cell_type: CellType, reference_value_shape: list[int] | tuple[int, ...], wcoeffs: ndarray[tuple[Any, ...], dtype[floating]], x: list[list[ndarray[tuple[Any, ...], dtype[floating]]]], M: list[list[ndarray[tuple[Any, ...], dtype[floating]]]], interpolation_nderivs: int, map_type: MapType, sobolev_space: SobolevSpace, discontinuous: bool, embedded_subdegree: int, embedded_superdegree: int, polyset_type: PolysetType = PolysetType.standard, dtype: type[Any] | dtype[Any] | _SupportsDType[dtype[Any]] | tuple[Any, Any] | list[Any] | _DTypeDict | str | None = None) → _ElementBase
```

Create a UFL compatible custom Basix element.

**Parameters:**

- **cell\_type** – The cell type
- **reference\_value\_shape** – The reference value shape of the element
- **wcoeffs** – Matrices for the kth value index containing the
  expansion coefficients defining a polynomial basis spanning
  the polynomial space for this element. Shape is
  `(dim(finite element polyset), dim(Legenre polynomials))`.
- **x** – Interpolation points. Indices are `(tdim, entity index,
  point index, dim)`.
- **M** – The interpolation matrices. Indices are `(tdim, entity
  index, dof, vs, point_index, derivative)`.
- **interpolation\_nderivs** – The number of derivatives that need to be
  used during interpolation.
- **map\_type** – The type of map to be used to map values from the
  reference to a cell.
- **sobolev\_space** – Underlying Sobolev space for the element.
- **discontinuous** – Indicates whether or not this is the
  discontinuous version of the element.
- **embedded\_subdegree** – The highest degree `n` such that a
  Lagrange (or vector Lagrange) element of degree `n` is a
  subspace of this element.
- **embedded\_superdegree** – The highest degree of a polynomial in this
  element’s polyset.
- **polyset\_type** – Polyset type for the element.
- **dtype** – Floating point data type.

**Returns:**

A custom finite element.
