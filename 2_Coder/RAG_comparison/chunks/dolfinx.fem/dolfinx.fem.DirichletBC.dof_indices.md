# dolfinx.fem.DirichletBC.dof_indices

```python
dof_indices() → tuple[ndarray[tuple[int, ...], dtype[int32]], int]
```

Access dof indices (local indices, unrolled), including
ghosts, to which a Dirichlet condition is applied, and the index to
the first non-owned (ghost) index. The array of indices is sorted.

Note

The returned array is read-only.

**Returns:**

Sorted array of dof indices (unrolled) and index to the
first entry in the dof index array that is not owned. Entries
dofs[:pos] are owned and entries dofs[pos:] are ghosts.
