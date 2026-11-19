# dolfinx.fem.create_vector

```python
dolfinx.fem.create_vector(V: ~dolfinx.fem.function.FunctionSpace, dtype: ~numpy.dtype[~typing.Any] | None | type[~typing.Any] | ~numpy._typing._dtype_like._SupportsDType[~numpy.dtype[~typing.Any]] | str | tuple[~typing.Any, int] | tuple[~typing.Any, ~typing.SupportsIndex | ~collections.abc.Sequence[~typing.SupportsIndex]] | list[~typing.Any] | ~numpy._typing._dtype_like._DTypeDict | tuple[~typing.Any, ~typing.Any] = <class 'numpy.float64'>) → Vector
```

Create a Vector that is compatible with the given function space.

**Parameters:**

**V** – A function space.

**Returns:**

A vector compatible with the function space.
