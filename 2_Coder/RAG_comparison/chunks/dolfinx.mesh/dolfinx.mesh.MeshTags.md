# dolfinx.mesh.MeshTags

```python
class dolfinx.mesh.MeshTags(meshtags)
```

Bases: `object`

Mesh tags associate data (markers) with a subset of mesh entities of
a given dimension.

Initialize tags from a C++ MeshTags object.

**Parameters:**

**meshtags** – C++ mesh tags object.

Note

MeshTags objects should not usually be created using this
initializer directly.

A Python mesh is passed to the initializer as it may have
UFL data attached that is not attached the C + + Mesh that is
associated with the C + + `meshtags` object. If mesh is
passed, `mesh` and `meshtags` must share the same C + +
mesh.
