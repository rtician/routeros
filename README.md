# RouterOS
[![Build Status](https://travis-ci.org/rtician/routeros.svg?branch=master)](https://travis-ci.org/rtician/routeros)

RouterOS is a API client for Mikrotik RouterOS.

### How can I install it?
```
$ pip install routeros 
```
The usage of a virtualenv is recommended.

### How to use it?
```python
In [1]: from routeros import login

In [2]: routeros = login('user', 'password', '10.1.0.1')

In [3]: routeros('/ip/pool/print')
Out[3]: 
({'.id': '*1', 'name': 'dhcp', 'ranges': '192.168.88.10-192.168.88.254'},
 {'.id': '*2', 'name': 'hs-pool-8', 'ranges': '10.5.50.2-10.5.50.254'})

In [4]: routeros.close()

In [5]: 

```

### Also can use query
Query can consult specific attributes on routeros.

**Methods:**

> - query.has(*args)
> - query.hasnot(*args)
> - query.equal(**kwargs)
> - query.lower(**kwargs)
> - query.greater(**kwargs)

```python
In [1]: from routeros import login

In [2]: routeros = login('user', 'password', '10.1.0.1')

In [3]: routeros.query('/ip/pool/print').equal(name='dhcp')
Out[3]: ({'.id': '*1', 'name': 'dhcp', 'ranges': '192.168.88.10-192.168.88.254'},)

In [4]: routeros.close()

In [5]: 

```

### How to use non-default (8728) API port for login, such as 9999

```python
routeros = login('user', 'password', '10.1.0.1', 9999)
```

### How to use pre-v6.43 login method

```python
routeros = login('user', 'password', '10.1.0.1', 8728, True)
```
