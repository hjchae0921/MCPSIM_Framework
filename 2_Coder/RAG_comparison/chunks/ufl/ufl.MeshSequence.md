# ufl.MeshSequence

```python
class ufl.MeshSequence(meshes: Sequence[Mesh])
```

Bases: [`AbstractDomain`](https://docs.fenicsproject.org/ufl/2025.2.1/api-doc/ufl.html#ufl.domain.AbstractDomain "ufl.domain.AbstractDomain"), [`UFLObject`](https://docs.fenicsproject.org/ufl/2025.2.1/api-doc/ufl.core.html#ufl.core.ufl_type.UFLObject "ufl.core.ufl_type.UFLObject")

Symbolic representation of a mixed mesh.

This class represents a collection of meshes that, along with
a `MixedElement`, represent a mixed function space defined on
multiple domains. This abstraction allows for defining the
mixed function space with the conventional [`FunctionSpace`](https://docs.fenicsproject.org/ufl/2025.2.1/api-doc/ufl.html#ufl.FunctionSpace "ufl.FunctionSpace")
class and integrating multi-domain problems seamlessly.

Currently, all component meshes must have the same cell type (and
thus the same topological dimension).

Currently, one can only perform cell integrations when
[`MeshSequence`](https://docs.fenicsproject.org/ufl/2025.2.1/api-doc/ufl.html#ufl.MeshSequence "ufl.MeshSequence") is used.

```python3
cell = triangle
mesh0 = Mesh(FiniteElement("Lagrange", cell, 1, (2,), identity_pullback, H1))
mesh1 = Mesh(FiniteElement("Lagrange", cell, 1, (2,), identity_pullback, H1))
domain = MeshSequence([mesh0, mesh1])
elem0 = FiniteElement("Lagrange", cell, 1, (), identity_pullback, H1)
elem1 = FiniteElement("Lagrange", cell, 2, (), identity_pullback, H1)
elem = MixedElement([elem0, elem1])
V = FunctionSpace(domain, elem)
v = TestFunction(V)
v0, v1 = split(v)
```
