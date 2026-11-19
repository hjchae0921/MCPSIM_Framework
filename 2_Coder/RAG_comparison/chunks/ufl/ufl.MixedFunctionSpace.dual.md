# ufl.MixedFunctionSpace.dual

```python
dual(*args)
```

Return the dual to this function space.

If no additional arguments are passed then a MixedFunctionSpace is
returned whose components are the duals of the originals.

If additional arguments are passed, these must be integers. In this
case, the MixedFunctionSpace which is returned will have dual
components in the positions corresponding to the arguments passed, and
the original components in the other positions.
