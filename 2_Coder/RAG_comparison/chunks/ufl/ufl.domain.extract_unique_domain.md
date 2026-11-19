# ufl.domain.extract_unique_domain

```python
ufl.domain.extract_unique_domain(expr, expand_mesh_sequence: bool = True)
```

Return the single unique domain expression is defined on or throw an error.

Args:
:   expr: Expr or Form.
    expand\_mesh\_sequence: If True, MeshSequence components are expanded.

Returns:
:   domain.
