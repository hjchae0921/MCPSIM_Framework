# dolfinx.fem.petsc.numba_utils

```python
class dolfinx.fem.petsc.numba_utils
```

Bases: `object`

Utility attributes for working with Numba and PETSc.

These attributes are convenience functions for calling PETSc C
functions from within Numba functions.

Note

[Numba](https://numba.pydata.org/) must be available
to use these utilities.

Examples

A typical use of these utility functions is:

```
import numpy as np
import numpy.typing as npt
def set_vals(A: int,
             m: int, rows: npt.NDArray[PETSc.IntType],
             n: int, cols: npt.NDArray[PETSc.IntType],
             data: npt.NDArray[PETSc.ScalarTYpe], mode: int):
    MatSetValuesLocal(A, m, rows.ctypes, n, cols.ctypes,
                      data.ctypes, mode)
```
