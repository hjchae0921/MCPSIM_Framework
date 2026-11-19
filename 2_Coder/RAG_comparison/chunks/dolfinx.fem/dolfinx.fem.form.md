# dolfinx.fem.form

```python
dolfinx.fem.form(form: ufl.Form | Sequence[ufl.Form] | Sequence[Sequence[ufl.Form]], dtype: npt.DTypeLike = <class 'numpy.float64'>, form_compiler_options: dict | None = None, jit_options: dict | None = None, entity_maps: Sequence[_EntityMap] | None = None)
```

Create a Form or list of Forms.

**Parameters:**

- **form** – A UFL form or iterable of UFL forms.
- **dtype** – Scalar type to use for the compiled form.
- **form\_compiler\_options** – See [`ffcx_jit`](https://docs.fenicsproject.org/dolfinx/v0.10.0/python/generated/dolfinx.jit.html#dolfinx.jit.ffcx_jit "dolfinx.jit.ffcx_jit")
- **jit\_options** – See [`ffcx_jit`](https://docs.fenicsproject.org/dolfinx/v0.10.0/python/generated/dolfinx.jit.html#dolfinx.jit.ffcx_jit "dolfinx.jit.ffcx_jit").
- **entity\_maps** – If any trial functions, test functions, or
  coefficients in the form are not defined over the same mesh
  as the integration domain (the domain associated with the
  measure), entity\_maps must be supplied. For each mesh in
  the form, there should be an entity map relating entities in
  that mesh to the integration domain mesh.

**Returns:**

Compiled finite element Form.

Note

This function is responsible for the compilation of a UFL form
(using FFCx) and attaching coefficients and domains specific
data to the underlying C++ form. It dynamically create a
[`Form`](https://docs.fenicsproject.org/dolfinx/v0.10.0/python/generated/dolfinx.fem.html#dolfinx.fem.Form "dolfinx.fem.Form") instance with an appropriate base class for the
scalar type, e.g. `_cpp.fem.Form_float64()`.
