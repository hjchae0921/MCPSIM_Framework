# dolfinx.mesh.compute_incident_entities

```python
dolfinx.mesh.compute_incident_entities(topology: Topology, entities: ndarray[tuple[int, ...], dtype[int32]], d0: int, d1: int) → ndarray[tuple[int, ...], dtype[int32]]
```

Compute all entities of `d1` connected to `entities` of
dimension `d0`.

**Parameters:**

- **topology** – The topology.
- **entities** – List of entities of dimension `d0`.
- **d0** – Topological dimension.
- **d1** – Topological dimension to map to.

**Returns:**

Incident entity indices.
