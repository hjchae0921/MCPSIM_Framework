# dolfinx.io.gmsh.MeshData

```python
class dolfinx.io.gmsh.MeshData(mesh: Mesh, cell_tags: MeshTags | None, facet_tags: MeshTags | None, ridge_tags: MeshTags | None, peak_tags: MeshTags | None, physical_groups: dict[str, PhysicalGroup])
```

Bases: `NamedTuple`

Data for representing a mesh and associated tags.

**Parameters:**

- **mesh** – Mesh.
- **cell\_tags** – MeshTags for cells.
- **facet\_tags** – MeshTags for facets (codim 1).
- **ridge\_tags** – MeshTags for ridges (codim 2).
- **peak\_tags** – MeshTags for peaks (codim 3).
- **physical\_groups** – Physical groups in the mesh, where the key
  is the physical name and the value is a tuple with the
  dimension and tag.

Create new instance of MeshData(mesh, cell\_tags, facet\_tags, ridge\_tags, peak\_tags, physical\_groups)
