# ufl.exterior_derivative

```python
ufl.exterior_derivative(f)
```

Take the exterior derivative of f.

The exterior derivative uses the element Sobolev space to
determine whether id, grad, curl or div should be used.

Note that this uses the grad and div operators,
as opposed to nabla\_grad and nabla\_div.
