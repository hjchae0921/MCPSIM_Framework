# dolfinx.fem.locate_dofs_topological

```python
dolfinx.fem.locate_dofs_topological(V: FunctionSpace | Iterable[FunctionSpace], entity_dim: int, entities: ndarray[tuple[int, ...], dtype[int32]], remote: bool = True) → ndarray
```

Locate degrees-of-freedom belonging to mesh entities topologically.

**Parameters:**

- **V** – Function space(s) in which to search for degree-of-freedom
  indices.
- **entity\_dim** – Topological dimension of entities where
  degrees-of-freedom are located.
- **entities** – Indices of mesh entities of dimension `entity_dim`
  where degrees-of-freedom are located.
- **remote** – True to return also “remotely located” degree-of-freedom
  indices.

**Returns:**

An array of degree-of-freedom indices (local to the process) for
degrees-of-freedom topologically belonging to mesh entities.

If `V` is a list of two function spaces, then a 2-D array of
shape (number of dofs, 2) is returned.

Returned degree-of-freedom indices are unique and ordered by the
first column.
