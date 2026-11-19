# dolfinx.fem.create_dofmaps

```python
dolfinx.fem.create_dofmaps(comm: Comm, topology: dolfinx.mesh.Topology, elements: Sequence[FiniteElement]) → list[DofMap]
```

Create degree-of-freedom maps on a given topology.

**Parameters:**

- **comm** – MPI communicator
- **topology** – Mesh topology
- **elements** – Sequence of elements

**Returns:**

List of degree-of-freedom maps where the `i`-th map is the map
for `elements[i]`.
