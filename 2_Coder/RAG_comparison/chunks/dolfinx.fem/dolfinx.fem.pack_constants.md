# dolfinx.fem.pack_constants

```python
dolfinx.fem.pack_constants(form: Form | Sequence[Form]) → ndarray[tuple[int, ...], dtype[_ScalarType_co]] | Sequence[ndarray[tuple[int, ...], dtype[_ScalarType_co]]]
```

Pack form constants for use in assembly.

Pack the ‘constants’ that appear in forms. The packed constants can
then be passed to an assembler. This is a performance optimisation
for cases where a form is assembled multiple times and (some)
constants do not change.

If `form` is a sequence of forms, this function returns an array
of form constants with the same shape as `form`.

**Parameters:**

**form** – Single form or sequence of forms to pack the constants
for.

**Returns:**

A `constant` array for each form.
