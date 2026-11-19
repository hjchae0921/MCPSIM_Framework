# dolfinx.fem.petsc.interpolation_matrix

```python
dolfinx.fem.petsc.interpolation_matrix(V0: FunctionSpace, V1: FunctionSpace) → Mat
```

Assemble an interpolation operator matrix for discreye
interpolation between finite element spaces.

Consider is the vector of degrees-of-freedom $u_{i}$
associated with a function in $V_{i}$. This function returns
the matrix $\Pi$ sucht that

$$
u_{1} = \Pi u_{0}.
$$

**Parameters:**

- **V0** – Space to interpolate from.
- **V1** – Space to interpolate into.

**Returns:**

The interpolation matrix $\Pi$.

Note

The returned matrix is not finalised, i.e. ghost values are not
accumulated.
