# dolfinx.fem.assemble_matrix

```python
dolfinx.fem.assemble_matrix(a: Any, bcs: Sequence[DirichletBC] | None = None, diag: float = 1.0, constants: ndarray[tuple[int, ...], dtype[_ScalarType_co]] | None = None, coeffs: dict[tuple[_IntegralType, int], ndarray[tuple[int, ...], dtype[_ScalarType_co]]] | None = None, block_mode: BlockMode | None = None) → MatrixCSR
dolfinx.fem.assemble_matrix(A: MatrixCSR, a: Form, bcs: Sequence[DirichletBC] | None = None, diag: float = 1.0, constants: ndarray[tuple[int, ...], dtype[_ScalarType_co]] | None = None, coeffs: dict[tuple[_IntegralType, int], ndarray[tuple[int, ...], dtype[_ScalarType_co]]] | None = None) → MatrixCSR
```

Assemble bilinear form into a matrix.

**Parameters:**

- **a** – The bilinear form assemble.
- **bcs** – Boundary conditions that affect the assembled matrix.
  Degrees-of-freedom constrained by a boundary condition will
  have their rows/columns zeroed and the value `diagonal`
  set on on the matrix diagonal.
- **diagonal** – Value to set on the matrix diagonal for Dirichlet
  boundary condition constrained degrees-of-freedom belonging
  to the same trial and test space.
- **constants** – Constants that appear in the form. If `None`,
  any required constants will be computed.
- **coeffs** –

  Coefficients that appear in the form. If not provided,
  :   any required coefficients will be computed.

  block\_mode: Block size mode for the returned space matrix. If
  :   `None`, default is used.

**Returns:**

Matrix representation of the bilinear form `a`.

Note

The returned matrix is not finalised, i.e. ghost values are not
accumulated.
