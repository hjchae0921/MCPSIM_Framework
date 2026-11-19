# dolfinx.fem.Function.eval

```python
eval(x: Buffer | _SupportsArray[dtype[Any]] | _NestedSequence[_SupportsArray[dtype[Any]]] | bool | int | float | complex | str | bytes | _NestedSequence[bool | int | float | complex | str | bytes], cells: Buffer | _SupportsArray[dtype[Any]] | _NestedSequence[_SupportsArray[dtype[Any]]] | bool | int | float | complex | str | bytes | _NestedSequence[bool | int | float | complex | str | bytes], u=None) → ndarray
```

Evaluate Function at points x.

Points where x has shape (num\_points, 3), and cells has shape
(num\_points,) and cell[i] is the index of the cell containing
point x[i]. If the cell index is negative the point is ignored.
