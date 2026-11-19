# dolfinx.fem.create_form

```python
dolfinx.fem.create_form(form: CompiledForm, function_spaces: list[FunctionSpace], msh: Mesh, subdomains: dict[IntegralType, list[tuple[int, np.ndarray]]], coefficient_map: dict[ufl.Coefficient, Function], constant_map: dict[ufl.Constant, Constant], entity_maps: Sequence[_EntityMap] | None = None) → Form
```

Create a Form object from a data-independent compiled form.

**Parameters:**

- **form** – Compiled ufl form function\_spaces: List of function spaces
- **the** (*associated with*) – form. Should match the number of arguments in the form.
- **msh** – Mesh to associate form with. subdomains: A map from
- **pairs** (*integral type to a list of*) – each pair corresponds to a subdomain id and the set of of
  integration entities to integrate over. Can be computed with
  {py:func}`dolfinx.fem.compute\_integration\_domains`.
- **where** – each pair corresponds to a subdomain id and the set of of
  integration entities to integrate over. Can be computed with
  {py:func}`dolfinx.fem.compute\_integration\_domains`.
- **coefficient\_map** – Map from UFL coefficient to function with data.
- **constant\_map** – Map from UFL constant to constant with data.
  to the integration domain `msh`. The value of the map is
  an array of integers, where the i-th entry is the entity in
  the key mesh.
- **entity\_maps** – Entity maps to support cases where forms involve
  sub-meshes.

**Returns:**

A Form object.
