# dolfinx.mesh.Topology.get_facet_permutations

```python
get_facet_permutations() → ndarray[tuple[int, ...], dtype[uint8]]
```

Get the permutation integer to apply to facets.

The bits of each integer describes the number of reflections and
rotations that has to be applied to a facet to map between a
facet in the mesh (relative to a cell) and the corresponding
facet on the reference element. The data has the shape
`(num_cells, num_facets_per_cell)`, flattened row-wise. The
number of cells include potential ghost cells.

Note

The data can be unpacked with `numpy.unpack_bits`.
