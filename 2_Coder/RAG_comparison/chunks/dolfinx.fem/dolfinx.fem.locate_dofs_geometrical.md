# dolfinx.fem.locate_dofs_geometrical

```python
dolfinx.fem.locate_dofs_geometrical(V: FunctionSpace | Iterable[FunctionSpace], marker: Callable) → ndarray
```

Locate degrees-of-freedom geometrically using a marker function.

**Parameters:**

- **V** – Function space(s) in which to search for degree-of-freedom
  indices.
- **marker** – A function that takes an array of points `x` with
  shape `(gdim, num_points)` and returns an array of
  booleans of length `num_points`, evaluating to `True`
  for entities whose degree-of-freedom should be returned.

**Returns:**

An array of degree-of-freedom indices (local to the process) for
degrees-of-freedom whose coordinate evaluates to True for the
marker function.

If `V` is a list of two function spaces, then a 2-D array of
shape (number of dofs, 2) is returned.

Returned degree-of-freedom indices are unique and ordered by the
first column.
