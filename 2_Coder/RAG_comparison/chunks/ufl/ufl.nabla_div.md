# ufl.nabla_div

```python
ufl.nabla_div(f)
```

Take the divergence of f.

This operator follows the div convention where
:   nabla\_div(v) = v[i].dx(i)
    nabla\_div(T)[:] = T[i,:].dx(i)

for vector expressions v, and
arbitrary rank tensor expressions T.

See also: [`div()`](https://docs.fenicsproject.org/ufl/2025.2.1/api-doc/ufl.html#ufl.div "ufl.div")
