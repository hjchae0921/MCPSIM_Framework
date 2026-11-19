# dolfinx.io.gmsh.extract_topology_and_markers

```python
dolfinx.io.gmsh.extract_topology_and_markers(model, name: str | None = None) → tuple[dict[int, TopologyDict], dict[str, PhysicalGroup]]
```

Extract all entities tagged with a physical marker in the gmsh
model.

Returns a nested dictionary where the first key is the gmsh MSH
element type integer. Each element type present in the model
contains the cell topology of the elements and corresponding
markers.

**Parameters:**

- **model** – Gmsh model.
- **name** – Name of the gmsh model. If not set the current
  model will be used.

**Returns:**

A tuple `(topologies, physical_groups)`, where `topologies` is
a nested dictionary where each key corresponds to a gmsh cell type.
Each cell type found in the mesh has a 2D array containing the
topology of the marked cell and a list with the corresponding
markers. `physical_groups` is a dictionary where the key is the
physical name and the value is a tuple with the dimension and tag.
