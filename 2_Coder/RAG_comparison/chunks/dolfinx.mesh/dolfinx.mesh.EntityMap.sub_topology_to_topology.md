# dolfinx.mesh.EntityMap.sub_topology_to_topology

```python
sub_topology_to_topology(entities, inverse)
```

Map entities between the sub-topology and the parent topology.

If inverse is False, this function maps a list of
self.dim()-dimensional entities from self.sub\_topology() to
the corresponding entities in self.topology(). If inverse is
True, it performs the inverse mapping from self.topology() to
self.sub\_topology(). Entities that do not exist in the
sub-topology are marked as -1.

Note

If inverse is True, this function recomputes the inverse
map on every call (it is not cached), which may be expensive
if called repeatedly.

**Parameters:**

- **entities** – A list of entity indices in the source topology.
- **inverse** – If False, maps from self.sub\_topology() to
  self.topology(). If True, maps from this.topology()
  to this.sub\_topology().

**Returns:**

A list of mapped entity indices. Entities that don’t exist
in the target topology are marked as -1.
