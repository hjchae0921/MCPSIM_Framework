# dolfinx.fem.Function

```python
class dolfinx.fem.Function(*args, **kw)
```

Bases: [`Coefficient`](https://docs.fenicsproject.org/ufl/main/api-doc/ufl.html#ufl.coefficient.Coefficient "(in Unified Form Language (UFL) v2025.2.0.dev0)")

A finite element function that is represented by a function space
(domain, element and dofmap) and a vector holding the
degrees-of-freedom.

Initialize a finite element Function.

**Parameters:**

- **V** – The function space that the Function is defined on.
- **x** – Function degree-of-freedom vector. Typically required
  only when reading a saved Function from file.
- **name** – Function name.
- **dtype** – Scalar type. Is not set, the DOLFINx default scalar
  type is used.
