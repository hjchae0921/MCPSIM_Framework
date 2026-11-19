# dolfinx.mesh.EntityMap

```python
class dolfinx.mesh.EntityMap(entity_map)
```

Bases: `object`

A bidirectional map that relates entities in two different
topologies.

Initialise an entity map from a C++ EntityMap object.

**Parameters:**

**entity\_map** – A C++ EntityMap object

Note

EntityMap objects should not usually be created using this
initializer directly.
