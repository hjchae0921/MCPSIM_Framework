# ufl.derivative

```python
ufl.derivative(form, coefficient, argument=None, coefficient_derivatives=None)
```

Compute the Gateaux derivative of *form* w.r.t. *coefficient* in direction of *argument*.

If the argument is omitted, a new `Argument` is created
in the same space as the coefficient, with argument number
one higher than the highest one in the form.

The resulting form has one additional `Argument`
in the same finite element space as the coefficient.

A tuple of `Coefficient` s may be provided in place of
a single `Coefficient`, in which case the new `Argument`
argument is based on a `MixedElement` created from this tuple.

An indexed `Coefficient` from a mixed space may be provided,
in which case the argument should be in the corresponding
subspace of the coefficient space.

If provided, *coefficient\_derivatives* should be a mapping from
`Coefficient` instances to their derivatives w.r.t. *coefficient*.
