# dolfinx.fem.finiteelement

```python
dolfinx.fem.finiteelement(cell_type: CellType, ufl_e: _ElementBase, FiniteElement_dtype: dtype) → FiniteElement
```

Create a DOLFINx element from a basix.ufl element.

**Parameters:**

- **cell\_type** – Element cell type, see `mesh.CellType`
- **ufl\_e** – UFL element, holding quadrature rule and other properties of
  the selected element.
- **FiniteElement\_dtype** – Geometry type of the element.
