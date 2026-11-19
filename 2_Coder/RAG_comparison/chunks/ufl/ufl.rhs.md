# ufl.rhs

```python
ufl.rhs(form)
```

Get the right hand side.

Given a combined bilinear and linear form,
extract the right hand side (negated linear form part).

Example:
:   a = u\*v\*dx + f\*v\*dx
    L = rhs(a) -> -f\*v\*dx
