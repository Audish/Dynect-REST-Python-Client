Overview
--------
A minimal client for some of DynECT's REST API, most notably record CRUD.

Written by Yaniv Aknin, based on work by Zach Goldberg.

Quick Usage
-----------

 >>> dyn = DynectDNSClient('customer', 'user', 'password', 'default.example.com')
 >>> dyn.getRecords('test.default.example.com', recordType='ANY')
 [u'/REST/ARecord/default.example.com/test.default.example.com/1234']
 >>> dyn.getRecord('test.default.example.com', recordType='A', recordID=1234)
 {u'status': u'success', u'data': {u'zone': u'dev.audish.com', u'rdata':
 {u'address': u'4.3.2.1'}, u'fqdn': u'testserver.dev.audish.com', u'record_type':
 u'A', u'ttl': 60, u'record_id': 16217457}, u'job_id': 25065704, u'msgs':
 [{u'INFO': u'get: Found the record', u'LVL': u'INFO', u'ERR_CD': None,
 u'SOURCE': u'API-B'}]}
 >>> dyn.updateRecord('4.3.2.1', 'test.default.example.com', TTL=120)
 >>>

Caveats / TODO
--------------

Much more should be done to make this really a full-fledged dynect client. Among
others:
 - switch to requests_
 - better response/exception abstraction
 - add support for more API features (services, etc)
 - refine distinction between broad operations (without recordID) and recordID
   specific operations
 - remove various needless constraints (resetting TTL on every PUT, for example)

.. _requests: https://github.com/kennethreitz/requests
