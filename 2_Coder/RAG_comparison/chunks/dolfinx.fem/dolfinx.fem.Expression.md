# dolfinx.fem.Expression

```python
class dolfinx.fem.Expression(e: ufl.core.expr.Expr, X: np.ndarray, comm: _MPI.Comm | None = None, form_compiler_options: dict | None = None, jit_options: dict | None = None, dtype: npt.DTypeLike | None = None)
```

Bases: `object`

Create a DOLFINx Expression.

Represents a mathematical expression evaluated at a pre-defined
set of points on the reference cell. This class closely follows
the concept of a UFC Expression.

This functionality can be used to evaluate a gradient of a
Function at the quadrature points in all cells. This evaluated
gradient can then be used as input to a non-FEniCS function that
calculates a material constitutive model.

**Parameters:**

- **e** – UFL expression.
- **X** – Array of points of shape `(num_points, tdim)` on the
  reference element.
- **comm** – Communicator that the Expression is defined on.
- **form\_compiler\_options** – Options used in FFCx compilation of
  this Expression. Run `ffcx --help` in the commandline
  to see all available options.
- **jit\_options** – Options controlling JIT compilation of C code.

Note

This wrapper is responsible for the FFCx compilation of the
UFL Expr and attaching the correct data to the underlying
C++ Expression.
