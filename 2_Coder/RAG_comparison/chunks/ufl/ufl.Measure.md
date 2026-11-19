# ufl.Measure

```python
class ufl.Measure(integral_type, domain=None, subdomain_id='everywhere', metadata=None, subdomain_data=None)
```

Bases: `object`

Representation of an integration measure.

The Measure object holds information about integration properties
to be transferred to a Form on multiplication with a scalar
expression.
