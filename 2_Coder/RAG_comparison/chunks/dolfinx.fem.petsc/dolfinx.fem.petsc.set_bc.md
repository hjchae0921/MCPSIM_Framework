# dolfinx.fem.petsc.set_bc

```python
dolfinx.fem.petsc.set_bc(b: Vec, bcs: Sequence[DirichletBC] | Sequence[Sequence[DirichletBC]], x0: Vec | None = None, alpha: float = 1) → None
```

Set constraint (Dirchlet boundary condition) values in an vector.

For degrees-of-freedoms that are constrained by a Dirichlet boundary
condition, this function sets that degrees-of-freedom to `alpha *
(g - x0)`, where `g` is the boundary condition value.

Only owned entries in `b` (owned by the MPI process) are modified
by this function.

**Parameters:**

- **b** – Vector to modify by setting boundary condition values.
- **bcs** – Boundary conditions to apply. If `b` is nested or
  blocked, `bcs` is a 2D array and `bcs[i]` are the
  boundary conditions to apply to block/nest `i`. Otherwise
  `bcs` should be a sequence of `DirichletBC`s. For
  block/nest problems, [`dolfinx.fem.bcs_by_block()`](https://docs.fenicsproject.org/dolfinx/v0.10.0/python/generated/dolfinx.fem.html#dolfinx.fem.bcs_by_block "dolfinx.fem.bcs_by_block") can be
  used to prepare the 2D array of `DirichletBC` objects.
- **x0** – Vector used in the value that constrained entries are set
  to. If `None`, `x0` is treated as zero.
- **alpha** – Scalar value used in the value that constrained entries
  are set to.
