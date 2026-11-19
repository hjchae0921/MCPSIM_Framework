# dolfinx.fem.Expression.eval

```python
eval(mesh: Mesh, entities: np.ndarray, values: np.ndarray | None = None) → np.ndarray
```

Evaluate Expression on entities.

**Parameters:**

- **mesh** – Mesh to evaluate Expression on.
- **entities** – Entities to evaluate the Expression over. For
  cells, it is a list of cell indices. For facets, it is a
  2D array of (cell index, local facet index).
- **values** – Array to fill with evaluated values. If `None`,
  storage will be allocated. Otherwise it must have shape
  `(entities.shape[0], num_points, *value_shape)` if
  there is not argument function and shape
  `(entities.shape[0], num_points, *value_shape,
  argument_space_dim)` if the Expression does have an
  argument function.

**Returns:**

Expression evaluated at points for `entities`. Shape is
`(entities.shape[0], num_points, *value_shape)` if there
is no argument function, or shape is `(entities.shape[0],
num_points, *value_shape, argument_space_dim)` if the
Expression does have an argument function.
