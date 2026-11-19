# dolfinx.fem.petsc.discrete_gradient

```python
dolfinx.fem.petsc.discrete_gradient(space0: FunctionSpace, space1: FunctionSpace) → Mat
```

Assemble a discrete gradient operator.

The discrete gradient operator interpolates the gradient of a H1
finite element function into a H(curl) space. It is assumed that the
H1 space uses an identity map and the H(curl) space uses a covariant
Piola map.

**Parameters:**

- **space0** – H1 space to interpolate the gradient from.
- **space1** – H(curl) space to interpolate into.

**Returns:**

Discrete gradient operator.
