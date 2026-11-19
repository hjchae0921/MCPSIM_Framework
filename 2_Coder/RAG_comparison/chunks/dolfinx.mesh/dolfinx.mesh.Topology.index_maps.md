# dolfinx.mesh.Topology.index_maps

```python
index_maps(dim: int) → list[IndexMap]
```

Get the IndexMaps that describes the parallel distribution of
:   the mesh entities, for each entity type of the dimension.

**Parameters:**

**dim** – Topological dimension.

**Returns:**

List of IndexMaps for the entities of dimension `dim`.
May be empty if not yet computed.
