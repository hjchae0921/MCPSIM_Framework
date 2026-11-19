# dolfinx.fem.petsc.assemble_matrix

```python
dolfinx.fem.petsc.assemble_matrix(a: Form | Sequence[Sequence[Form]], bcs: Sequence[DirichletBC] | None = None, diag: float = 1, constants: Sequence[ndarray[tuple[int, ...], dtype[_ScalarType_co]]] | Sequence[Sequence[ndarray[tuple[int, ...], dtype[_ScalarType_co]]]] | None = None, coeffs: dict[tuple[_IntegralType, int], ndarray[tuple[int, ...], dtype[_ScalarType_co]]] | Sequence[dict[tuple[_IntegralType, int], ndarray[tuple[int, ...], dtype[_ScalarType_co]]]] | None = None, kind=None)
dolfinx.fem.petsc.assemble_matrix(A: Mat, a: Form | Sequence[Sequence[Form]], bcs: Sequence[DirichletBC] | None = None, diag: float = 1, constants: ndarray[tuple[int, ...], dtype[_ScalarType_co]] | Sequence[Sequence[ndarray[tuple[int, ...], dtype[_ScalarType_co]]]] | None = None, coeffs: dict[tuple[_IntegralType, int], ndarray[tuple[int, ...], dtype[_ScalarType_co]]] | Sequence[Sequence[dict[tuple[_IntegralType, int], ndarray[tuple[int, ...], dtype[_ScalarType_co]]]]] | None = None) → Mat
```

Assemble a bilinear form into a matrix.

The following cases are supported:

1. If `a` is a single bilinear form, the form is assembled
   into PETSc matrix of type `kind`.
2. If `a` is a $m \times n$ rectangular array of forms the
   forms in `a` are assembled into a matrix such that:

   ```
   A = [A_00 ... A_0n]
       [A_10 ... A_1n]
       [     ...     ]
       [A_m0 ..  A_mn]
   ```

   where `A_ij` is the matrix associated with the form
   `a[i][j]`.

   1. If `kind` is a `PETSc.Mat.Type` (other than
      `PETSc.Mat.Type.NEST`) or is `None`, the matrix type is
      `kind` of the default type (if `kind` is `None`).
   2. If `kind` is `PETSc.Mat.Type.NEST` or a rectangular array
      of PETSc matrix types, the returned matrix has type
      `PETSc.Mat.Type.NEST`.

Rows/columns that are constrained by a Dirichlet boundary condition
are zeroed, with the diagonal to set to `diag`.

Constant and coefficient data that appear in the forms(s) can be
packed outside of this function to avoid re-packing by this
function. The functions [`dolfinx.fem.pack_constants()`](https://docs.fenicsproject.org/dolfinx/v0.10.0/python/generated/dolfinx.fem.html#dolfinx.fem.pack_constants "dolfinx.fem.pack_constants") and
[`dolfinx.fem.pack_coefficients()`](https://docs.fenicsproject.org/dolfinx/v0.10.0/python/generated/dolfinx.fem.html#dolfinx.fem.pack_coefficients "dolfinx.fem.pack_coefficients") can be used to ‘pre-pack’ the
data.

Note

The returned matrix is not ‘assembled’, i.e. ghost contributions
are not accumulated.

**Parameters:**

- **a** – Bilinear form(s) to assembled into a matrix.
- **bc** – Dirichlet boundary conditions applied to the system.
- **diag** – Value to set on the matrix diagonal for Dirichlet
  boundary condition constrained degrees-of-freedom belonging
  to the same trial and test space.
- **constants** – Constants appearing the in the form.
- **coeffs** – Coefficients appearing the in the form.

**Returns:**

Matrix representing the bilinear form.
