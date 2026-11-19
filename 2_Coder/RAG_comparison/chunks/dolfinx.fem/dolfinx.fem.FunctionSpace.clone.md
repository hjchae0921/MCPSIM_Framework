# dolfinx.fem.FunctionSpace.clone

```python
clone() → FunctionSpace
```

Create a new FunctionSpace $W$ which shares data with this
FunctionSpace $V$, but with a different unique integer ID.

This function is helpful for defining mixed problems and using
blocked linear algebra. For example, a matrix block defined on
the spaces $V \times W$ where, $V$ and $W$
are defined on the same finite element and mesh can be
identified as an off-diagonal block whereas the $V \times
V$ and $V \times V$ matrices can be identified as
diagonal blocks. This is relevant for the handling of boundary
conditions.

**Returns:**

A new function space that shares data
