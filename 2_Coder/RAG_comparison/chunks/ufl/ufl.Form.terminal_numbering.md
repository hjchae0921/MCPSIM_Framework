# ufl.Form.terminal_numbering

```python
terminal_numbering()
```

Return a contiguous numbering for all counted objects in the form.

The returned object is mapping from terminal to its number (an integer).

The numbering is computed per type so [`Coefficient`](https://docs.fenicsproject.org/ufl/2025.2.1/api-doc/ufl.html#ufl.Coefficient "ufl.Coefficient"),
[`Constant`](https://docs.fenicsproject.org/ufl/2025.2.1/api-doc/ufl.html#ufl.Constant "ufl.Constant"), etc will each be numbered from zero.
