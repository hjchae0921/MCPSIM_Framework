# ufl.domain.join_domains

```python
ufl.domain.join_domains(domains: Sequence[AbstractDomain], expand_mesh_sequence: bool = True)
```

Take a list of domains and return a set with only unique domain objects.

Args:
:   domains: Sequence of domains.
    expand\_mesh\_sequence: If True, MeshSequence components are expanded.

Returns:
:   set of domains.
