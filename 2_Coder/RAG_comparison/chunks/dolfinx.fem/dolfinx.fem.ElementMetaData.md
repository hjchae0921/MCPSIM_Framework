# dolfinx.fem.ElementMetaData

```python
class dolfinx.fem.ElementMetaData(family: str, degree: int, shape: tuple[int, ...] | None = None, symmetry: bool | None = None)
```

Bases: `NamedTuple`

Data for representing a finite element

**Parameters:**

- **family** – Element type.
- **degree** – Polynomial degree of the element.
- **shape** – Shape for vector/tensor valued elements that are
  constructed from blocked scalar elements (e.g., Lagrange).
- **symmetry** – Symmetry option for blocked tensor elements.

Create new instance of ElementMetaData(family, degree, shape, symmetry)
