# dolfinx.mesh.Mesh

```python
class dolfinx.mesh.Mesh(msh: Mesh_float32 | Mesh_float64, domain: Mesh | None)
```

Bases: `object`

A mesh.

Initialize mesh from a C++ mesh.

**Parameters:**

- **msh** – A C++ mesh object.
- **domain** – A UFL domain.

Note

Mesh objects should usually be constructed using
[`create_mesh()`](https://docs.fenicsproject.org/dolfinx/v0.10.0/python/generated/dolfinx.mesh.html#dolfinx.mesh.create_mesh "dolfinx.mesh.create_mesh") and not using this class initializer.
This class is combined with different base classes that
depend on the scalar type used in the Mesh.
