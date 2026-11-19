# basix.ufl.blocked_element

```python
basix.ufl.blocked_element(sub_element: _ElementBase, shape: tuple[int, ...], symmetry: bool | None = None) → _ElementBase
```

Create a UFL compatible blocked element.

**Parameters:**

- **sub\_element** – Element used for each block.
- **shape** – Value shape of the element. For scalar-valued families,
  this can be used to create vector and tensor elements.
- **symmetry** – Set to `True` if the tensor is symmetric. Valid for
  rank 2 elements only.

**Returns:**

A blocked finite element.
