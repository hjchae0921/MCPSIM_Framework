# basix.ufl.element

```python
basix.ufl.element(family: ElementFamily | str, cell: CellType | str, degree: int, lagrange_variant: LagrangeVariant = LagrangeVariant.unset, dpc_variant: DPCVariant = DPCVariant.unset, discontinuous: bool = False, shape: tuple[int, ...] | None = None, symmetry: bool | None = None, dof_ordering: list[int] | None = None, dtype: type[Any] | dtype[Any] | _SupportsDType[dtype[Any]] | tuple[Any, Any] | list[Any] | _DTypeDict | str | None = None) → _ElementBase
```

Create a UFL compatible element using Basix.

**Parameters:**

- **family** – Element family/type.
- **cell** – Element cell type.
- **degree** – Degree of the finite element.
- **lagrange\_variant** – Variant of Lagrange to be used.
- **dpc\_variant** – Variant of DPC to be used.
- **discontinuous** – If `True`, the discontinuous version of the
  element is created.
- **shape** – Value shape of the element. For scalar-valued families,
  this can be used to create vector and tensor elements.
- **symmetry** – Set to `True` if the tensor is symmetric. Valid for
  rank 2 elements only.
- **dof\_ordering** – Ordering of dofs for `ElementDofLayout`.
- **dtype** – Floating point data type.

**Returns:**

A finite element.
