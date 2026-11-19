# basix.ufl.quadrature_element

```python
basix.ufl.quadrature_element(cell: str | CellType, value_shape: tuple[int, ...] = (), scheme: str | None = None, degree: int | None = None, points: ndarray[tuple[Any, ...], dtype[floating]] | None = None, weights: ndarray[tuple[Any, ...], dtype[floating]] | None = None, pullback: AbstractPullback = IdentityPullback(), symmetry: bool | None = None, dtype: type[Any] | dtype[Any] | _SupportsDType[dtype[Any]] | tuple[Any, Any] | list[Any] | _DTypeDict | str | None = None) → _ElementBase
```

Create a quadrature element.

When creating this element, either the quadrature scheme and degree
must be input or the quadrature points and weights must be.

**Parameters:**

- **cell** – Cell to create the element on.
- **value\_shape** – Value shape of the element.
- **scheme** – Quadrature scheme.
- **degree** – Quadrature degree.
- **points** – Quadrature points.
- **weights** – Quadrature weights.
- **pullback** – Map name.
- **symmetry** – Set to `True` if the tensor is symmetric. Valid for
  rank 2 elements only.
- **dtype** – Data type of quadrature points and weights

**Returns:**

A ‘quadrature’ finite element.
