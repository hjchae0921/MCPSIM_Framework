# dolfinx.fem.bcs_by_block

```python
dolfinx.fem.bcs_by_block(spaces: Iterable[FunctionSpace | None], bcs: Iterable[DirichletBC]) → list[list[DirichletBC]]
```

Arrange Dirichlet boundary conditions by the function space that
they constrain.

Given a sequence of function spaces `spaces` and a sequence of
DirichletBC objects `bcs`, return a list where the ith entry is
the list of DirichletBC objects whose space is contained in
`space[i]`.
