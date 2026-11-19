# dolfinx.fem.Form.num_integrals

```python
num_integrals(integral_type: _IntegralType, kernel_index: int) → int
```

Number of integrals of a given type for a specific cell type.

**Parameters:**

- **integral\_type** – The type of integral to count.
- **kernel\_index** – In the case of mixed topology, we have a kernel
  per cell type. For single-cell type meshes, this is zero.
