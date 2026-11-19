# dolfinx.mesh.Geometry

```python
class dolfinx.mesh.Geometry(geometry: Geometry_float32 | Geometry_float64)
```

Bases: `object`

The geometry of a [`dolfinx.mesh.Mesh`](https://docs.fenicsproject.org/dolfinx/v0.10.0/python/generated/dolfinx.mesh.html#dolfinx.mesh.Mesh "dolfinx.mesh.Mesh")

Initialize a geometry from a C++ geometry.

**Parameters:**

**geometry** – The C++ geometry object.

Note

Geometry objects should usually be constructed with the
[`create_geometry()`](https://docs.fenicsproject.org/dolfinx/v0.10.0/python/generated/dolfinx.mesh.html#dolfinx.mesh.create_geometry "dolfinx.mesh.create_geometry") and not using this class
initializer. This class is combined with different base
classes that depend on the scalar type used in the Geometry.
