# dolfinx.fem.FunctionSpace.sub

```python
sub(i: int) → FunctionSpace
```

Return the i-th sub space.

**Parameters:**

**i** – Index of the subspace to extract.

**Returns:**

A subspace.

Note

If the subspace is re-used, for performance reasons the
returned subspace should be stored by the caller to avoid
repeated re-computation of the subspace.
