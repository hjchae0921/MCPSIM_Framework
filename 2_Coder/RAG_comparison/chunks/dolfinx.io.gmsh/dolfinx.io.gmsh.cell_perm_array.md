# dolfinx.io.gmsh.cell_perm_array

```python
dolfinx.io.gmsh.cell_perm_array(cell_type: CellType, num_nodes: int) → list[int]
```

The permutation array for permuting Gmsh ordering to DOLFINx
ordering.

**Parameters:**

- **cell\_type** – DOLFINx cell type.
- **num\_nodes** – Number of nodes in the cell.

**Returns:**

An array `p` such that `a_dolfinx[i] = a_gmsh[p[i]]`.
