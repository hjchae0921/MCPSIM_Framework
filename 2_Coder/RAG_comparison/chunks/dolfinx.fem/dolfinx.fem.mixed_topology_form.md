# dolfinx.fem.mixed_topology_form

```python
dolfinx.fem.mixed_topology_form(forms: Sequence[ufl.Form], dtype: npt.DTypeLike = <class 'numpy.float64'>, form_compiler_options: dict | None = None, jit_options: dict | None = None, entity_maps: Sequence[_EntityMap] | None = None)
```

Create a mixed-topology from from an array of Forms.

# FIXME: This function is a temporary hack for mixed-topology
meshes. # It is needed because UFL does not know about
mixed-topology meshes, # so we need to pass a list of forms for each
cell type.

**Parameters:**

- **form** – A list of UFL forms. Each form should be the same, just
  defined on different cell types.
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
