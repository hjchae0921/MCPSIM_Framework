# ufl.domain.extract_domains

```python
ufl.domain.extract_domains(expr: Expr | Form, expand_mesh_sequence: bool = True)
```

Return all domains expression is defined on.

Args:
:   expr: Expr or Form.
    expand\_mesh\_sequence: If True, MeshSequence components are expanded.

Returns:
:   tuple of domains.
