# dolfinx.fem.petsc.assemble_vector

```python
dolfinx.fem.petsc.assemble_vector(L: Form | Sequence[Form], constants: ndarray[tuple[int, ...], dtype[_ScalarType_co]] | Sequence[ndarray[tuple[int, ...], dtype[_ScalarType_co]]] | None = None, coeffs: dict[tuple[_IntegralType, int], ndarray[tuple[int, ...], dtype[_ScalarType_co]]] | Sequence[dict[tuple[_IntegralType, int], ndarray[tuple[int, ...], dtype[_ScalarType_co]]]] | None = None, kind: str | None = None) → Vec
dolfinx.fem.petsc.assemble_vector(b: Vec, L: Form | Sequence[Form], constants: ndarray[tuple[int, ...], dtype[_ScalarType_co]] | Sequence[ndarray[tuple[int, ...], dtype[_ScalarType_co]]] | None = None, coeffs: dict[tuple[_IntegralType, int], ndarray[tuple[int, ...], dtype[_ScalarType_co]]] | Sequence[dict[tuple[_IntegralType, int], ndarray[tuple[int, ...], dtype[_ScalarType_co]]]] | None = None) → Vec
```

Assemble linear form(s) into a new PETSc vector.

Three cases are supported:

1. If `L` is a single linear form, the form is assembled into a
   ghosted PETSc vector.
2. If `L` is a sequence of linear forms and `kind` is `None`
   or is `PETSc.Vec.Type.MPI`, the forms are assembled into a
   vector `b` such that `b = [b_0, b_1, ..., b_n, b_0g, b_1g,
   ..., b_ng]` where `b_i` are the entries associated with the
   ‘owned’ degrees-of-freedom for `L[i]` and `b_ig` are the
   ‘unowned’ (ghost) entries for `L[i]`.

   For this case, the returned vector has an attribute `_blocks`
   that holds the local offsets into `b` for the (i) owned and
   (ii) ghost entries for each `L[i]`. See [`create_vector()`](https://docs.fenicsproject.org/dolfinx/v0.10.0/python/generated/dolfinx.fem.petsc.html#dolfinx.fem.petsc.create_vector "dolfinx.fem.petsc.create_vector")
   for a description of the offset blocks.
3. If `L` is a sequence of linear forms and `kind` is
   `PETSc.Vec.Type.NEST`, the forms are assembled into a PETSc
   nested vector `b` (a nest of ghosted PETSc vectors) such that
   `L[i]` is assembled into into the ith nested matrix in `b`.

Constant and coefficient data that appear in the forms(s) can be
packed outside of this function to avoid re-packing by this
function. The functions [`dolfinx.fem.pack_constants()`](https://docs.fenicsproject.org/dolfinx/v0.10.0/python/generated/dolfinx.fem.html#dolfinx.fem.pack_constants "dolfinx.fem.pack_constants") and
[`dolfinx.fem.pack_coefficients()`](https://docs.fenicsproject.org/dolfinx/v0.10.0/python/generated/dolfinx.fem.html#dolfinx.fem.pack_coefficients "dolfinx.fem.pack_coefficients") can be used to ‘pre-pack’ the
data.

Note

The returned vector is not finalised, i.e. ghost values are not
accumulated on the owning processes.

**Parameters:**

- **L** – A linear form or sequence of linear forms.
- **constants** – Constants appearing in the form. For a single form,
  `constants.ndim==1`. For multiple forms, the constants for
  form `L[i]` are `constants[i]`.
- **coeffs** – Coefficients appearing in the form. For a single form,
  `coeffs.shape=(num_cells, n)`. For multiple forms, the
  coefficients for form `L[i]` are `coeffs[i]`.
- **kind** – PETSc vector type.

**Returns:**

An assembled vector.
