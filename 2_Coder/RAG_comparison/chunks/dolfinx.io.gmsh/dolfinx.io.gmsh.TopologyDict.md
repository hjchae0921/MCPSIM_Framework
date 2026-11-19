# dolfinx.io.gmsh.TopologyDict

```python
class dolfinx.io.gmsh.TopologyDict
```

Bases: `TypedDict`

TopologyDict is a TypedDict for storing the topology of the marked
cell.

**Parameters:**

- **topology** – 2D array containing the topology of the marked cell.
- **cell\_data** – List with the corresponding markers.

Note

The TypedDict is only used for type hinting, and does not
enforce the structure of the dictionary, but rather provides
a hint to the user and the type checker.
