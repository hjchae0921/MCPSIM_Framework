# dolfinx.fem.petsc.cffi_utils

```python
class dolfinx.fem.petsc.cffi_utils
```

Bases: `object`

Utility attributes for working with CFFI (ABI mode) and Numba.

Registers Numba’s complex types with CFFI.

If PETSc is available, CFFI convenience functions for calling PETSc C
functions are also created. These are typically called from within
Numba functions.

Note

[CFFI](https://cffi.readthedocs.io/) and [Numba](https://numba.pydata.org/) must be available to use these
utilities.

Examples

A typical use of these utility functions is:

```
import numpy as np
import numpy.typing as npt
def set_vals(A: int,
             m: int, rows: npt.NDArray[PETSc.IntType],
             n: int, cols: npt.NDArray[PETSc.IntType],
             data: npt.NDArray[PETSc.ScalarType], mode: int):
    MatSetValuesLocal(A, m, ffi.from_buffer(rows), n,
                      ffi.from_buffer(cols),
                      ffi.from_buffer(rows(data), mode)
```
