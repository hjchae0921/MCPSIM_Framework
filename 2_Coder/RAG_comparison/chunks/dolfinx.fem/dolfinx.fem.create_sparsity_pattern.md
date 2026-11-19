# dolfinx.fem.create_sparsity_pattern

```python
dolfinx.fem.create_sparsity_pattern(a: Form)
```

Create a sparsity pattern from a bilinear form.

**Parameters:**

**a** – Bilinear form to build a sparsity pattern for.

**Returns:**

Sparsity pattern for the form `a`.

Note

The pattern is not finalised, i.e. the caller is responsible for
calling `assemble` on the sparsity pattern.
