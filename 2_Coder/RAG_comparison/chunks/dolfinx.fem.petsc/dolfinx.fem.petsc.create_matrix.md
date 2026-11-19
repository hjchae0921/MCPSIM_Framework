# dolfinx.fem.petsc.create_matrix

```python
dolfinx.fem.petsc.create_matrix(a: Form | Sequence[Sequence[Form]], kind: str | Sequence[Sequence[str]] | None = None) → Mat
```

Create a PETSc matrix that is compatible with the (sequence) of
bilinear form(s).

Three cases are supported:

1. For a single bilinear form, it creates a compatible PETSc matrix
   of type `kind`.
2. For a rectangular array of bilinear forms, if `kind` is
   `PETSc.Mat.Type.NEST` or `kind` is an array of PETSc `Mat`
   types (with the same shape as `a`), a matrix of type
   `PETSc.Mat.Type.NEST` is created. The matrix is compatible
   with the forms `a`.
3. For a rectangular array of bilinear forms, it create a single
   (non-nested) matrix of type `kind` that is compatible with the
   array of for forms `a`. If `kind` is `None`, then the
   matrix is the default type.

   In this case, the matrix is arranged:

   ```
   A = [a_00 ... a_0n]
       [a_10 ... a_1n]
       [     ...     ]
       [a_m0 ..  a_mn]
   ```

**Parameters:**

- **a** – A bilinear form or a nested sequence of bilinear forms.
- **kind** – The PETSc matrix type (`MatType`).

**Returns:**

A PETSc matrix.
