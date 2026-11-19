# dolfinx.fem.functionspace

```python
dolfinx.fem.functionspace(mesh: Mesh, element: ufl.finiteelement.AbstractFiniteElement | ElementMetaData | tuple[str, int] | tuple[str, int, tuple] | tuple[str, int, tuple, bool]) → FunctionSpace
```

Create a finite element function space.

**Parameters:**

- **mesh** – Mesh that space is defined on.
- **element** – Finite element description.

**Returns:**

A function space.
