# dolfinx.fem.dirichletbc

```python
dolfinx.fem.dirichletbc(value: Function | Constant | ndarray, dofs: ndarray[tuple[int, ...], dtype[int32]], V: FunctionSpace | None = None) → DirichletBC
```

Create a representation of Dirichlet boundary condition which
is imposed on a linear system.

**Parameters:**

- **value** – Lifted boundary values function. It must have a `dtype`
  property.
- **dofs** – Local indices of degrees of freedom in function space to
  which boundary condition applies. Expects array of size
  (number of dofs, 2) if function space of the problem, `V`,
  is passed. Otherwise assumes function space of the problem
  is the same of function space of boundary values function.
- **V** – Function space of a problem to which boundary conditions are
  applied.

**Returns:**

A representation of the boundary condition for modifying linear
systems.
