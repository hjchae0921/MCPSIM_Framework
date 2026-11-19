# dolfinx.fem.assemble_scalar

```python
dolfinx.fem.assemble_scalar(M: Form, constants: ndarray[tuple[int, ...], dtype[_ScalarType_co]] | None = None, coeffs: dict[tuple[_IntegralType, int], ndarray[tuple[int, ...], dtype[_ScalarType_co]]] | None = None) → float | complex
```

Assemble functional. The returned value is local and not
accumulated across processes.

**Parameters:**

- **M** – The functional to compute.
- **constants** – Constants that appear in the form. If `None`, any
  required constants will be computed.
- **coeffs** – Coefficients that appear in the form. If not provided,
  any required coefficients will be computed.

**Returns:**

The computed scalar on the calling rank.

Note

Passing constants and coefficients is a performance
optimisation for when a form is assembled multiple times and
when (some) constants and coefficients are unchanged.

To compute the functional value on the whole domain, the output
of this function is typically summed across all MPI ranks.
