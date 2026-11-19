# ufl.nabla_grad

```python
ufl.nabla_grad(f)
```

Take the gradient of f.

This operator follows the grad convention where
:   nabla\_grad(s)[i] = s.dx(i)
    nabla\_grad(v)[i,j] = v[j].dx(i)
    nabla\_grad(T)[i,:] = T[:].dx(i)

for scalar expressions s, vector expressions v,
and arbitrary rank tensor expressions T.

See also: [`grad()`](https://docs.fenicsproject.org/ufl/2025.2.1/api-doc/ufl.html#ufl.grad "ufl.grad")
