# dolfinx.fem.Function.sub

```python
sub(i: int) → Function
```

Return a sub-function (a view into the `Function`).

Sub-functions are indexed `i = 0, ..., N-1`, where `N` is
the number of sub-spaces.

**Parameters:**

**i** – Index of the sub-function to extract.

**Returns:**

A view into the parent `Function`.

Note

If the sub-Function is re-used, for performance reasons the
returned `Function` should be stored by the caller to
avoid repeated re-computation of the subspace.
