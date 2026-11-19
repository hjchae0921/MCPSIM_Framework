# ufl.measure.MeasureSum

```python
class ufl.measure.MeasureSum(*measures)
```

Bases: `object`

Represents a sum of measures.

This is a notational intermediate object to translate the notation
:   f\*(ds(1)+ds(3))

into
:   f\*ds(1) + f\*ds(3)
