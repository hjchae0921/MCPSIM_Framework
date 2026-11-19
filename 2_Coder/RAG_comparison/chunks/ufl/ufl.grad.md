# ufl.grad

```python
ufl.grad(f)
```

Take the gradient of f.

This operator follows the grad convention where
:   grad(s)[i] = s.dx(i)
    grad(v)[i,j] = v[i].dx(j)
    grad(T)[:,i] = T[:].dx(i)

for scalar expressions s, vector expressions v,
and arbitrary rank tensor expressions T.

See also: [`nabla_grad()`](https://docs.fenicsproject.org/ufl/2025.2.1/api-doc/ufl.html#ufl.nabla_grad "ufl.nabla_grad")
