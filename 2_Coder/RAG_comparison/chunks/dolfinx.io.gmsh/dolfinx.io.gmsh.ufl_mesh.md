# dolfinx.io.gmsh.ufl_mesh

```python
dolfinx.io.gmsh.ufl_mesh(gmsh_cell: int, gdim: int, dtype: dtype[Any] | None | type[Any] | _SupportsDType[dtype[Any]] | str | tuple[Any, int] | tuple[Any, SupportsIndex | Sequence[SupportsIndex]] | list[Any] | _DTypeDict | tuple[Any, Any]) → Mesh
```

Create a UFL mesh from a Gmsh cell identifier and geometric
dimension.

See <https://gmsh.info//doc/texinfo/gmsh.html#MSH-file-format>.

**Parameters:**

- **gmsh\_cell** – Gmsh cell identifier.
- **gdim** – Geometric dimension of the mesh.

**Returns:**

UFL Mesh using Lagrange elements (equispaced) of the
corresponding DOLFINx cell.
