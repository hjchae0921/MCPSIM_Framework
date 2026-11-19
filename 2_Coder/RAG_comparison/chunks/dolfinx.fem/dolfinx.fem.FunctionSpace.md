# dolfinx.fem.FunctionSpace

```python
class dolfinx.fem.FunctionSpace(mesh: Mesh, element: ufl.finiteelement.AbstractFiniteElement, cppV: _cpp.fem.FunctionSpace_float32 | _cpp.fem.FunctionSpace_float64)
```

Bases: [`FunctionSpace`](https://docs.fenicsproject.org/ufl/main/api-doc/ufl.html#ufl.functionspace.FunctionSpace "(in Unified Form Language (UFL) v2025.2.0.dev0)")

A space on which Functions (fields) can be defined.

Create a finite element function space.

Note

This initialiser is for internal use and not normally called
in user code. Use [`functionspace()`](https://docs.fenicsproject.org/dolfinx/v0.10.0/python/generated/dolfinx.fem.html#dolfinx.fem.functionspace "dolfinx.fem.functionspace") to create a function
space.

**Parameters:**

- **mesh** – Mesh that space is defined on.
- **element** – UFL finite element.
- **cppV** – Compiled C++ function space.
