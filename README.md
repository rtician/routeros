#RouterOS
[![Build Status](https://travis-ci.org/rtician/routeros.svg?branch=master)](https://travis-ci.org/rtician/routeros)

RouterOS is a API client for Mikrotik RouterOS.

### How can I install it?
```
$ pip install routeros 
```
The usage of a virtualenv is recommended.

### How to use it?
```
from routeros import login

routeros = login('user', 'password', 'host')
routeros.talk('/interface/print')

{u'.id': u'*6',
  u'actual-mtu': u'1500',
  u'default-name': u'wlan1',
  u'disabled': u'false',
  u'fast-path': u'true',
  u'fp-rx-byte': u'461972',
  u'fp-rx-packet': u'3742',
  u'fp-tx-byte': u'0',
  u'fp-tx-packet': u'0',
  u'l2mtu': u'1600',
  u'last-link-down-time': u'nov/16/2017 00:00:00',
  u'last-link-up-time': u'nov/16/2017 00:00:00',
  u'link-downs': u'12',
  u'mac-address': u'00:00:00:00:00:00',
  u'max-l2mtu': u'2290',
  u'mtu': u'1500',
  u'name': u'wlan1',
  u'running': u'false',
  u'rx-byte': u'461972',
  u'rx-drop': u'0',
  u'rx-error': u'0',
  u'rx-packet': u'3742',
  u'tx-byte': u'3728276',
  u'tx-drop': u'0',
  u'tx-error': u'0',
  u'tx-packet': u'3869',
  u'tx-queue-drop': u'0',
  u'type': u'wlan'})
```

