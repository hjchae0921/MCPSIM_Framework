# dolfinx.mesh.Mesh.ufl_domain

```python
ufl_domain() → Mesh | None
```

Return the ufl domain corresponding to the mesh.

**Returns:**

The UFL domain. Is `None` if the domain has not been set.

Note

This method is required for UFL compatibility.
