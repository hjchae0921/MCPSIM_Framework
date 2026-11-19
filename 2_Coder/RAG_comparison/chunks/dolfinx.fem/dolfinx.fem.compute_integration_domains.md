# dolfinx.fem.compute_integration_domains

```python
dolfinx.fem.compute_integration_domains(integral_type: _IntegralType, topology: dolfinx.mesh.Topology, entities: ndarray)
```

Given an integral type and a set of entities compute integration
entities.

This function returns a list `[(id, entities)]`. For cell
integrals `entities` are the cell indices. For exterior facet
integrals, `entities` is a list of `(cell_index,
local_facet_index)` pairs. For interior facet integrals,
`entities` is a list of `(cell_index0, local_facet_index0,
cell_index1, local_facet_index1)`. `id` refers to the subdomain
id used in the definition of the integration measures of the
variational form.

Note

Owned mesh entities only are returned. Ghost entities are not
included.

Note

For facet integrals, the topology facet-to-cell and
cell-to-facet connectivity must be computed before calling this
function.

**Parameters:**

- **integral\_type** – Integral type.
- **topology** – Mesh topology.
- **entities** – List of mesh entities. For
  `integral_type==IntegralType.cell`, `entities` should be
  cell indices. For other ``` IntegralType``s, ``entities ```
  should be facet indices.

**Returns:**

List of integration entities.
