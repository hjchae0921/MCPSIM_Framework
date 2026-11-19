# dolfinx.fem.form_cpp_class

```python
dolfinx.fem.form_cpp_class(dtype: dtype[Any] | None | type[Any] | _SupportsDType[dtype[Any]] | str | tuple[Any, int] | tuple[Any, SupportsIndex | Sequence[SupportsIndex]] | list[Any] | _DTypeDict | tuple[Any, Any]) → Form_float32 | Form_float64 | Form_complex64 | Form_complex128
```

Return the wrapped C++ class of a variational form of a specific
scalar type.

**Parameters:**

**dtype** – Scalar type of the required form class.

**Returns:**

Wrapped C++ form class of the requested type.

Note

This function is for advanced usage, typically when writing
custom kernels using Numba or C.
