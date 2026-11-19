# dolfinx.mesh.Topology.get_cell_permutation_info

```python
get_cell_permutation_info() → ndarray[tuple[int, ...], dtype[uint32]]
```

Get permutation information.

The returned data is used for packing coefficients and
assembling of tensors. The bits of each integer encodes the
number of reflections and permutations for each sub-entity of
the cell to be able to map it to the reference element.
