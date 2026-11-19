# dolfinx.fem.petsc.apply_lifting

```python
dolfinx.fem.petsc.apply_lifting(b: Vec, a: Sequence[Form] | Sequence[Sequence[Form]], bcs: Sequence[DirichletBC] | Sequence[Sequence[DirichletBC]] | None, x0: Sequence[Vec] | None = None, alpha: float = 1, constants: Sequence[ndarray[tuple[int, ...], dtype[_ScalarType_co]]] | Sequence[Sequence[ndarray[tuple[int, ...], dtype[_ScalarType_co]]]] | None = None, coeffs: dict[tuple[_IntegralType, int], ndarray[tuple[int, ...], dtype[_ScalarType_co]]] | Sequence[Sequence[dict[tuple[_IntegralType, int], ndarray[tuple[int, ...], dtype[_ScalarType_co]]]]] | None = None) → None
```

Modify the right-hand side PETSc vector `b` to account for
constraints (Dirichlet boundary conitions).

See [`dolfinx.fem.apply_lifting()`](https://docs.fenicsproject.org/dolfinx/v0.10.0/python/generated/dolfinx.fem.html#dolfinx.fem.apply_lifting "dolfinx.fem.apply_lifting") for a mathematical
descriptions of the lifting operation.

**Parameters:**

- **b** – Vector to modify in-place.
- **a** – List of bilinear forms. If `b` is not blocked or a nest,
  then `a` is a 1D sequence. If `b` is blocked or a nest,
  then `a` is a 2D array of forms, with the `a[i]` forms
  used to modify the block/nest vector `b[i]`.
- **bcs** –

  Boundary conditions to apply, which form a 2D array.
  If `b` is nested or blocked then `bcs[i]` are the
  boundary conditions to apply to block/nest `i`.
  The function [`dolfinx.fem.bcs_by_block()`](https://docs.fenicsproject.org/dolfinx/v0.10.0/python/generated/dolfinx.fem.html#dolfinx.fem.bcs_by_block "dolfinx.fem.bcs_by_block") can be
  used to prepare the 2D array of `DirichletBC` objects
  from the 2D sequence `a`:

  ```
  bcs1 = fem.bcs_by_block(
      fem.extract_function_spaces(a, 1),
      bcs
  )
  ```

  If `b` is not blocked or nest, then `len(bcs)` must be
  equal to 1. The function [`dolfinx.fem.bcs_by_block()`](https://docs.fenicsproject.org/dolfinx/v0.10.0/python/generated/dolfinx.fem.html#dolfinx.fem.bcs_by_block "dolfinx.fem.bcs_by_block")
  can be used to prepare the 2D array of `DirichletBC`
  from the 1D sequence `a`:

  ```
  bcs1 = fem.bcs_by_block(
      fem.extract_function_spaces([a], 1),
      bcs
  )
  ```
- **x0** – Vector to use in modify `b` (see
  [`dolfinx.fem.apply_lifting()`](https://docs.fenicsproject.org/dolfinx/v0.10.0/python/generated/dolfinx.fem.html#dolfinx.fem.apply_lifting "dolfinx.fem.apply_lifting")). Treated as zero if
  `None`.
- **alpha** – Scalar parameter in lifting (see
  [`dolfinx.fem.apply_lifting()`](https://docs.fenicsproject.org/dolfinx/v0.10.0/python/generated/dolfinx.fem.html#dolfinx.fem.apply_lifting "dolfinx.fem.apply_lifting")).
- **constants** – Packed constant data appearing in the forms `a`. If
  `None`, the constant data will be packed by the function.
- **coeffs** – Packed coefficient data appearing in the forms `a`. If
  `None`, the coefficient data will be packed by the
  function.

Note

Ghost contributions are not accumulated (not sent to owner).
Caller is responsible for reverse-scatter to update the ghosts.

Note

Boundary condition values are *not* set in `b` by this
function. Use [`dolfinx.fem.DirichletBC.set()`](https://docs.fenicsproject.org/dolfinx/v0.10.0/python/generated/dolfinx.fem.html#dolfinx.fem.DirichletBC.set "dolfinx.fem.DirichletBC.set") to set values
in `b`.
