# dolfinx.fem.DirichletBC.set

```python
set(x: ndarray[tuple[int, ...], dtype[_ScalarType_co]], x0: ndarray[tuple[int, ...], dtype[int32]] | None = None, alpha: float = 1) → None
```

Set entries in an array that are constrained by Dirichlet
boundary conditions.

Entries in `x` that are constrained by a Dirichlet boundary
conditions are set to `alpha * (x_bc - x0)`, where `x_bc` is
the (interpolated) boundary condition value.

For elements with point-wise evaluated degrees-of-freedom, e.g.
Lagrange elements, `x_bc` is the value of the boundary condition
at the degree-of-freedom. For elements with moment
degrees-of-freedom, `x_bc` is the value of the boundary condition
interpolated into the finite element space.

If x includes ghosted entries (entries available on the calling
rank but owned by another rank), ghosted entries constrained by a
Dirichlet condition will also be set.

**Parameters:**

- **x** – Array to modify for Dirichlet boundary conditions.
- **x0** – Optional array used in computing the value to set. If
  not provided it is treated as zero.
- **alpha** – Scaling factor.
