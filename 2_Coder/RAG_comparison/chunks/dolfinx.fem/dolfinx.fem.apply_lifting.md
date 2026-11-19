# dolfinx.fem.apply_lifting

```python
dolfinx.fem.apply_lifting(b: ndarray[tuple[int, ...], dtype[_ScalarType_co]], a: Sequence[Form], bcs: Sequence[Sequence[DirichletBC]], x0: Sequence[ndarray[tuple[int, ...], dtype[_ScalarType_co]]] | None = None, alpha: float = 1, constants: ndarray[tuple[int, ...], dtype[_ScalarType_co]] | None = None, coeffs: dict[tuple[_IntegralType, int], ndarray[tuple[int, ...], dtype[_ScalarType_co]]] | None = None) → None
```

Modify right-hand side vector `b` for lifting of Dirichlet
boundary conditions.

Consider the discrete algebraic system:

$$
\begin{split}\begin{bmatrix} A_{0} & A_{1} \end{bmatrix}
\begin{bmatrix}u_{0} \\ u_{1}\end{bmatrix}
= b,\end{split}
$$

where $A_{i}$ is a matrix. Partitioning each vector
$u_{i}$ into ‘unknown’ ($u_{i}^{(0)}$) and prescribed
($u_{i}^{(1)}$) groups,

$$
\begin{split}\begin{bmatrix}
    A_{0}^{(0)} & A_{0}^{(1)} & A_{1}^{(0)} & A_{1}^{(1)}
\end{bmatrix}
\begin{bmatrix}
    u_{0}^{(0)} \\ u_{0}^{(1)} \\ u_{1}^{(0)} \\ u_{1}^{(1)}
\end{bmatrix}
= b.\end{split}
$$

If $u_{i}^{(1)} = \alpha(g_{i} - x_{i})$, where $g_{i}$
is the Dirichlet boundary condition value, $x_{i}$ is provided
and $\alpha$ is a constant, then

$$
\begin{split}\begin{bmatrix}
    A_{0}^{(0)} & A_{0}^{(1)} & A_{1}^{(0)} & A_{1}^{(1)}
\end{bmatrix}
\begin{bmatrix}u_{0}^{(0)} \\ \alpha(g_{0} - x_{0})
\\ u_{1}^{(0)} \\ \alpha(g_{1} - x_{1})\end{bmatrix}
= b.\end{split}
$$

Rearranging,

$$
\begin{split}\begin{bmatrix}A_{0}^{(0)} & A_{1}^{(0)}\end{bmatrix}
\begin{bmatrix}u_{0}^{(0)} \\ u_{1}^{(0)}\end{bmatrix}
= b - \alpha A_{0}^{(1)} (g_{0} - x_{0})
- \alpha A_{1}^{(1)} (g_{1} - x_{1}).\end{split}
$$

The modified $b$ vector is

$$
b \leftarrow b - \alpha A_{0}^{(1)} (g_{0} - x_{0})
- \alpha A_{1}^{(1)} (g_{1} - x_{1})
$$

More generally,

$$
b \leftarrow b - \alpha A_{i}^{(1)} (g_{i} - x_{i}).
$$

**Parameters:**

- **b** – The array to modify inplace.
- **a** – List of bilinear forms, where `a[i]` is the form that
  generates the matrix :math”A\_{i}. All forms in `a` must
  share the same test function space. The trial function
  spaces can differ.
- **bcs** –

  Boundary conditions that provide the $g_{i}$ values.
  `bcs1[i]` is the sequence of boundary conditions on
  $u_{i}$. Helper functions exist to build a
  list-of-lists of DirichletBC from a list of forms `a`
  and a flat list of DirichletBC objects `bcs`:

  ```
  bcs1 = fem.bcs_by_block(
      fem.extract_function_spaces([a], 1),
      bcs
  )
  ```
- **x0** – The array $x_{i}$ above. If `None` it is set to
  zero.
- **alpha** – Scalar used in the modification of `b`.
- **constants** – Packed constant data appearing in the forms `a`. If
  `None`, the constant data will be packed by the function.
- **coeffs** – Packed coefficient data appearing in the forms `a`. If
  `None`, the coefficient data will be packed by the
  function.

Note

Ghost contributions are not accumulated (not sent to owner).
Caller is responsible for reverse-scatter to update the ghosts.

Note

Boundary condition values are *not* set in `b` by this
function. Use [`dolfinx.fem.DirichletBC.set()`](https://docs.fenicsproject.org/dolfinx/v0.10.0/python/generated/dolfinx.fem.html#dolfinx.fem.DirichletBC.set "dolfinx.fem.DirichletBC.set") to set values
in `b`.
