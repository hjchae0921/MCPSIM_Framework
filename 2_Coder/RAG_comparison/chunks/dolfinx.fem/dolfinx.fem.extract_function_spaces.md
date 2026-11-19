# dolfinx.fem.extract_function_spaces

```python
dolfinx.fem.extract_function_spaces(forms: Form | Sequence[Form] | Sequence[Sequence[Form]], index: int = 0) → FunctionSpace | list[None | FunctionSpace]
```

Extract common function spaces from an array of forms.

If `forms` is a list of linear forms, this function returns of list
of the corresponding test function spaces. If `forms` is a 2D
array of bilinear forms, for `index=0` the list of common test
function spaces for each row is returned, and if `index=1` the
common trial function spaces for each column are returned.

**Parameters:**

- **forms** – A list of forms or a 2D array of forms.
- **index** – Index of the function space to extract. If `index=0`,
  the test function spaces are extracted, if `index=1` the
  trial function spaces are extracted.

**Returns:**

List of function spaces.
