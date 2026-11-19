# dolfinx.fem.petsc.NonlinearProblem.solve

```python
solve() → Function | Sequence[Function]
```

Solve the problem.

This method updates the solution `u` function(s) stored in the
problem instance.

Note

The user is responsible for asserting convergence of the SNES
solver e.g. `assert problem.solver.getConvergedReason() > 0`.
Alternatively, pass `"snes_error_if_not_converged": True` and
`"ksp_error_if_not_converged" : True` in `petsc_options` to
raise a `PETScError` on failure.

**Returns:**

The solution function(s).
