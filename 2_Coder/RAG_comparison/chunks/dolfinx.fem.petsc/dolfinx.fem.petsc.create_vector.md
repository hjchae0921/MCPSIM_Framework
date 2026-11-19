# dolfinx.fem.petsc.create_vector

```python
dolfinx.fem.petsc.create_vector(V: FunctionSpace | Sequence[FunctionSpace | None], /, kind: str | None = None) → Vec
```

Create a PETSc vector that is compatible with a linear form(s)
or functionspace(s).
Three cases are supported:

1. For a single space `V`, if `kind` is `None` or is
   `PETSc.Vec.Type.MPI`, a ghosted PETSc vector which is compatible
   with `V` is created.
2. If `V` is a sequence of functionspaces and `kind` is `None` or
   is `PETSc.Vec.Type.MPI`, a ghosted PETSc vector which is
   compatible with `V` is created. The created vector `b`
   is initialized such that on each MPI process `b = [b_0, b_1, ...,
   b_n, b_0g, b_1g, ..., b_ng]`, where `b_i` are the entries
   associated with the ‘owned’ degrees-of-freedom for `V[i]` and
   `b_ig` are the ‘unowned’ (ghost) entries for `V[i]`.

   For this case, the returned vector has an attribute `_blocks`
   that holds the local offsets into `b` for the (i) owned and
   (ii) ghost entries for each `V_i`. It can be accessed by
   `b.getAttr("_blocks")`. The offsets can be used to get views
   into `b` for blocks, e.g.:

   ```
   >>> offsets0, offsets1, = b.getAttr("_blocks")
   >>> offsets0
   (0, 12, 28)
   >>> offsets1
   (28, 32, 35)
   >>> b0_owned = b.array[offsets0[0]:offsets0[1]]
   >>> b0_ghost = b.array[offsets1[0]:offsets1[1]]
   >>> b1_owned = b.array[offsets0[1]:offsets0[2]]
   >>> b1_ghost = b.array[offsets1[1]:offsets1[2]]
   ```
3. If `L/V` is a sequence of linear forms/functionspaces and `kind`
   is `PETSc.Vec.Type.NEST`, a PETSc nested vector (a ‘nest’ of
   ghosted PETSc vectors) which is compatible with `L/V` is created.

**Parameters:**

- **V** – Function space or a sequence of such.
- **kind** – PETSc vector type (`VecType`) to create.

**Returns:**

A PETSc vector with a layout that is compatible with `V`. The
vector is not initialised to zero.
