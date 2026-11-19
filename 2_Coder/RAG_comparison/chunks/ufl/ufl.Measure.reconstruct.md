# ufl.Measure.reconstruct

```python
reconstruct(integral_type=None, subdomain_id=None, domain=None, metadata=None, subdomain_data=None)
```

Construct a new Measure object with some properties replaced with new values.

Example:
:   <dm = Measure instance>
    b = dm.reconstruct(subdomain\_id=2)
    c = dm.reconstruct(metadata={ “quadrature\_degree”: 3 })

Used by the call operator, so this is equivalent:
:   b = dm(2)
    c = dm(0, { “quadrature\_degree”: 3 })
