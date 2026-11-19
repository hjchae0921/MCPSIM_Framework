# ufl.Form.ufl_domains

```python
ufl_domains()
```

Return the geometric integration domains occuring in the form.

NB! This does not include domains of coefficients defined on
other meshes.

The return type is a tuple even if only a single domain exists.
