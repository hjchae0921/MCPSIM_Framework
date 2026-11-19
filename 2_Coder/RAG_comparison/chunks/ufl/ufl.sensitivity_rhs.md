# ufl.sensitivity_rhs

```python
ufl.sensitivity_rhs(a, u, L, v)
```

Compute the right hand side for a sensitivity calculation system.

The derivation behind this computation is as follows.
Assume *a*, *L* to be bilinear and linear forms
corresponding to the assembled linear system

$$
Ax = b.
$$

Where *x* is the vector of the discrete function corresponding to *u*.
Let *v* be some scalar variable this equation depends on.
Then we can write

$$
\begin{align}\begin{aligned}\begin{split}0 = \\frac{d}{dv}(Ax-b) = \\frac{dA}{dv} x + A \\frac{dx}{dv} -
\\frac{db}{dv},\end{split}\\\begin{split}A \\frac{dx}{dv} = \\frac{db}{dv} - \\frac{dA}{dv} x,\end{split}\end{aligned}\end{align}
$$

and solve this system for $\\frac{dx}{dv}$, using the same bilinear
form *a* and matrix *A* from the original system.
Assume the forms are written

```
v = variable(v_expression)
L = IL(v) * dx
a = Ia(v) * dx
```

where `IL` and `Ia` are integrand expressions.
Define a `Coefficient u` representing the solution
to the equations. Then we can compute $\\frac{db}{dv}$
and $\\frac{dA}{dv}$ from the forms

```
da = diff(a, v)
dL = diff(L, v)
```

and the action of `da` on `u` by

```
dau = action(da, u)
```

In total, we can build the right hand side of the system
to compute $\\frac{du}{dv}$ with the single line

```
dL = diff(L, v) - action(diff(a, v), u)
```

or, using this function,

```
dL = sensitivity_rhs(a, u, L, v)
```
