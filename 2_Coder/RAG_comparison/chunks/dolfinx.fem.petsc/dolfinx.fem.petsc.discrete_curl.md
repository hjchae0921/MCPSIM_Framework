# dolfinx.fem.petsc.discrete_curl

```python
dolfinx.fem.petsc.discrete_curl(space0: FunctionSpace, space1: FunctionSpace) → Mat
```

Assemble a discrete curl operator.

**Parameters:**

- **space0** – H1 space to interpolate the gradient from.
- **space1** – H(curl) space to interpolate into.

**Returns:**

Discrete curl operator.
