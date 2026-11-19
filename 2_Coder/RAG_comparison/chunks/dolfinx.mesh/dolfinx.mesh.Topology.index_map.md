# dolfinx.mesh.Topology.index_map

```python
index_map(dim: int) → IndexMap
```

Get the IndexMap that describes the parallel distribution of the
mesh entities.

**Parameters:**

**dim** – Topological dimension.

**Returns:**

Index map for the entities of dimension `dim`.
