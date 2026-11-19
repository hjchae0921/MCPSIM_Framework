# ufl.adjoint

```python
ufl.adjoint(form, reordered_arguments=None, derivatives_expanded=None)
```

Get the adjoint.

Given a combined bilinear form, compute the adjoint form by
changing the ordering (count) of the test and trial functions, and
taking the complex conjugate of the result.

By default, new `Argument` objects will be created with
opposite ordering. However, if the adjoint form is to
be added to other forms later, their arguments must match.
In that case, the user must provide a tuple [\*](https://docs.fenicsproject.org/ufl/2025.2.1/api-doc/ufl.html#id7)reordered\_arguments\*=(u2,v2).

If the form is a baseform instance instead of a Form object, we return an Adjoint
object instructing the adjoint to be computed at a later point.

When adjoint is being called multiple times on the same form, expanding derivatives
become expensive -> derivatives\_expanded enables to use caching mechanisms to avoid that.
