# dolfinx.fem.DirichletBC

```python
class dolfinx.fem.DirichletBC(bc)
```

Bases: `object`

Representation of Dirichlet boundary condition which is imposed
on a linear system.

Note

Dirichlet boundary conditions should normally be
constructed using `fem.dirichletbc()` and not using this
class initialiser. This class is combined with different
base classes that depend on the scalar type of the boundary
condition.

**Parameters:**

- **value** – Lifted boundary values function.
- **dofs** – Local indices of degrees of freedom in function space
  to which boundary condition applies. Expects array of
  size (number of dofs, 2) if function space of the
  problem, `V` is passed. Otherwise assumes function
  space of the problem is the same of function space of
  boundary values function.
- **V** – Function space of a problem to which boundary conditions
  are applied.
