# ufl.div

```python
ufl.div(f)
```

Take the divergence of f.

This operator follows the div convention where
:   div(v) = v[i].dx(i)
    div(T)[:] = T[:,i].dx(i)

for vector expressions v, and
arbitrary rank tensor expressions T.

See also: [`nabla_div()`](https://docs.fenicsproject.org/ufl/2025.2.1/api-doc/ufl.html#ufl.nabla_div "ufl.nabla_div")
