# dolfinx.fem.discrete_curl

```python
dolfinx.fem.discrete_curl(V0: FunctionSpace, V1: FunctionSpace) → MatrixCSR
```

Assemble a discrete curl operator.

The discrete curl operator interpolates the curl of H(curl) finite
element function into a H(div) space.

**Parameters:**

- **V0** – H1(curl) space to interpolate the curl from.
- **V1** – H(div) space to interpolate into.

**Returns:**

Discrete curl operator.
