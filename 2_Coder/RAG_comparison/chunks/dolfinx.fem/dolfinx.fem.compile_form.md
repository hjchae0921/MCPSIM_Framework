# dolfinx.fem.compile_form

```python
dolfinx.fem.compile_form(comm: ~mpi4py.MPI.Intracomm, form: ~ufl.form.Form, form_compiler_options: dict | None = {'scalar_type': <class 'numpy.float64'>}, jit_options: dict | None = None) → CompiledForm
```

Compile UFL form without associated DOLFINx data.

**Parameters:**

- **comm** – The MPI communicator used when compiling the form
- **form** – The UFL form to compile
- **form\_compiler\_options** – See [`ffcx_jit`](https://docs.fenicsproject.org/dolfinx/v0.10.0/python/generated/dolfinx.jit.html#dolfinx.jit.ffcx_jit "dolfinx.jit.ffcx_jit")
- **jit\_options** – See [`ffcx_jit`](https://docs.fenicsproject.org/dolfinx/v0.10.0/python/generated/dolfinx.jit.html#dolfinx.jit.ffcx_jit "dolfinx.jit.ffcx_jit").
