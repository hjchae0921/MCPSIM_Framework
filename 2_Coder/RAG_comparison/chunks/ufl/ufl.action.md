# ufl.action

```python
ufl.action(form, coefficient=None, derivatives_expanded=None)
```

Get the action.

Given a bilinear form, return a linear form
with an additional coefficient, representing the
action of the form on the coefficient. This can be
used for matrix-free methods.
For formbase objects,coefficient can be any object of the correct type,
and this function returns an Action object.

When action is being called multiple times on the same form, expanding derivatives
become expensive -> derivatives\_expanded enables to use caching mechanisms to avoid that.
