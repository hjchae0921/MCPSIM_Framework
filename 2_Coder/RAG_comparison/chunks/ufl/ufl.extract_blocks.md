# ufl.extract_blocks

```python
ufl.extract_blocks(form: Form, i: int | None = None, j: int | None = None, replace_argument: bool = True)
```

Extract blocks.

Given a linear or bilinear form on a mixed space,
extract the block corresponding to the indices ix, iy.

Example:
:   a = inner(grad(u), grad(v))\*dx + div(u)\*q\*dx + div(v)\*p\*dx
    extract\_blocks(a, 0, 0) -> inner(grad(u), grad(v))\*dx
    extract\_blocks(a) -> [inner(grad(u), grad(v))\*dx, div(v)\*p\*dx, div(u)\*q\*dx, 0]
