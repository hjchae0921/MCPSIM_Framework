# dolfinx.mesh.transfer_meshtag

```python
dolfinx.mesh.transfer_meshtag(meshtag: MeshTags, msh1: Mesh, parent_cell: ndarray[tuple[int, ...], dtype[int32]], parent_facet: ndarray[tuple[int, ...], dtype[int8]] | None = None) → MeshTags
```

Generate cell mesh tags on a refined mesh from the mesh tags on the
coarse parent mesh.

**Parameters:**

- **meshtag** – Mesh tags on the coarse, parent mesh.
- **msh1** – The refined mesh.
- **parent\_cell** – Index of the parent cell for each cell in the
  refined mesh.
- **parent\_facet** – Index of the local parent facet for each cell
  in the refined mesh. Only required for transfer tags on
  facets.

**Returns:**

Mesh tags on the refined mesh.
