# dolfinx.fem.Form

```python
class dolfinx.fem.Form(form: Form_complex64 | Form_complex128 | Form_float32 | Form_float64, ufcx_form=None, code: str | list[str] | None = None, module: ModuleType | list[ModuleType] | None = None)
```

Bases: `object`

A finite element form.

Note

Forms should normally be constructed using [`form()`](https://docs.fenicsproject.org/dolfinx/v0.10.0/python/generated/dolfinx.fem.html#dolfinx.fem.form "dolfinx.fem.form") and
not using this class initialiser. This class is combined
with different base classes that depend on the scalar type
used in the Form.

**Parameters:**

- **form** – Compiled form object.
- **ufcx\_form** – UFCx form.
- **code** – Form C++ code.
- **module** – CFFI module.
