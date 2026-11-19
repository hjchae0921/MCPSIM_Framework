# dolfinx.mesh.Topology

```python
class dolfinx.mesh.Topology(topology: Topology)
```

Bases: `object`

Topology for a [`dolfinx.mesh.Mesh`](https://docs.fenicsproject.org/dolfinx/v0.10.0/python/generated/dolfinx.mesh.html#dolfinx.mesh.Mesh "dolfinx.mesh.Mesh")

Initialize a topology from a C++ topology.
:param topology: The C++ topology object

Note

Topology objects should usually be constructed with the
`dolfinx.cpp.mesh.create_topology()` and not this class
initializer.
