# dolfinx.fem.pack_coefficients

```python
dolfinx.fem.pack_coefficients(form: Form | Sequence[Form]) → dict[tuple[_IntegralType, int], ndarray[tuple[int, ...], dtype[_ScalarType_co]]] | list[dict[tuple[_IntegralType, int], ndarray[tuple[int, ...], dtype[_ScalarType_co]]]]
```

Pack form coefficients for use in assembly.

Pack the `coefficients` that appear in forms. The packed
coefficients can be passed to an assembler. This is a performance
optimisation for cases where a form is assembled multiple times and
(some) coefficients do not change.

If `form` is an array of forms, this function returns an array of
form coefficients with the same shape as `form`.

**Parameters:**

- **form** – A form or a sequence of forms to pack the coefficients
- **for.**

**Returns:**

Coefficients for each form.
