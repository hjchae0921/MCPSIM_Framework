# dolfinx.fem.Function.split

```python
split() → tuple[Function, ...]
```

Extract (any) sub-functions.

A sub-function can be extracted from a discrete function that is
in a mixed, vector, or tensor FunctionSpace. The sub-function
resides in the subspace of the mixed space.

**Returns:**

First level of subspaces of the function space.
