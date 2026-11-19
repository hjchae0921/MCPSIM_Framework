# dolfinx.mesh.uniform_refine

```python
dolfinx.mesh.uniform_refine(msh: Mesh, partitioner: Callable | None = None) → Mesh
```

Uniformly refine a mesh.

Note

Using the default partitioner for the refined mesh, the refined
mesh will **not** include ghosts cells (cells connected by facet
to an owned cells) even if the parent mesh is ghosted. The
refined cells will be on the same process as the parent cell.

**Parameters:**

- **msh** – Mesh from which to create the refined mesh.
- **partitioner** – Partitioner to distribute the refined mesh.
  If `None` is passed (default) no redistribution will happen.

**Returns:**

The refined mesh.
