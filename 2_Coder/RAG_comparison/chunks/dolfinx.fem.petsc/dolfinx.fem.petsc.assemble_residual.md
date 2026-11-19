# dolfinx.fem.petsc.assemble_residual

```python
dolfinx.fem.petsc.assemble_residual(u: Function | Sequence[Function], residual: Form | Sequence[Form], jacobian: Form | Sequence[Sequence[Form]], bcs: Sequence[DirichletBC], _snes: SNES, x: Vec, b: Vec)
```

Assemble the residual at `x` into the vector `b`.

A function conforming to the interface expected by `SNES.setFunction`
can be created by fixing the first four arguments, e.g.:

Example:

```
snes = PETSc.SNES().create(mesh.comm)
assemble_residual = functools.partial(
    dolfinx.fem.petsc.assemble_residual,
    u, residual, jacobian, bcs)
snes.setFunction(assemble_residual, x, b)
```

**Parameters:**

- **u** – Function(s) tied to the solution vector within the residual and
  Jacobian.
- **residual** – Form of the residual. It can be a sequence of forms.
- **jacobian** – Form of the Jacobian. It can be a nested sequence of
  forms.
- **bcs** – List of Dirichlet boundary conditions to lift the residual.
- **\_snes** – The solver instance.
- **x** – The vector containing the point to evaluate the residual at.
- **b** – Vector to assemble the residual into.
