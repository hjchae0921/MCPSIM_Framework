# dolfinx.mesh.exterior_facet_indices

```python
dolfinx.mesh.exterior_facet_indices(topology: Topology) → ndarray[tuple[int, ...], dtype[int32]]
```

Compute the indices of all exterior facets that are owned by the
caller.

An exterior facet (co-dimension 1) is one that is connected globally
to only one cell of co-dimension 0).

Note

This is a collective operation that should be called on all
processes.

**Parameters:**

**topology** – The topology

**Returns:**

Sorted list of owned facet indices that are exterior facets of
the mesh.
