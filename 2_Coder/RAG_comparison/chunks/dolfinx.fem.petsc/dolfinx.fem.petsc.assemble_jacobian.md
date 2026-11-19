# dolfinx.fem.petsc.assemble_jacobian

```python
dolfinx.fem.petsc.assemble_jacobian(u: Sequence[Function] | Function, jacobian: Form | Sequence[Sequence[Form]], preconditioner: Form | Sequence[Sequence[Form]] | None, bcs: Sequence[DirichletBC], _snes: SNES, x: Vec, J: Mat, P_mat: Mat)
```

Assemble the Jacobian and preconditioner matrices at `x`
into `J` and `P_mat`.

A function conforming to the interface expected by `SNES.setJacobian`
can be created by fixing the first four arguments e.g.:

Example:

```
snes = PETSc.SNES().create(mesh.comm)
assemble_jacobian = functools.partial(
    dolfinx.fem.petsc.assemble_jacobian,
    u, jacobian, preconditioner, bcs)
snes.setJacobian(assemble_jacobian, A, P_mat)
```

**Parameters:**

- **u** – Function tied to the solution vector within the residual and
  jacobian.
- **jacobian** – Compiled form of the Jacobian.
- **preconditioner** – Compiled form of the preconditioner.
- **bcs** – List of Dirichlet boundary conditions to apply to the Jacobian
  and preconditioner matrices.
- **\_snes** – The solver instance.
- **x** – The vector containing the point to evaluate at.
- **J** – Matrix to assemble the Jacobian into.
- **P\_mat** – Matrix to assemble the preconditioner into.
