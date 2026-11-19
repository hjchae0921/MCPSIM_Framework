# ufl.lhs

```python
ufl.lhs(form)
```

Get the left hand side.

Given a combined bilinear and linear form,
extract the left hand side (bilinear form part).

Example:
:   a = u\*v\*dx + f\*v\*dx
    a = lhs(a) -> u\*v\*dx
