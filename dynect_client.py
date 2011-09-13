import urllib2
import json
from functools import wraps

__version__ = (0, 0, 1)

# NOTE: When receiving POST/PUT rdata, the API expects certain fields depending on the record type; hence operations
#       like addRecord will accept JSON serializable dict-like data, and send it to the server. However, to make
#       everyone's life easier, if these methods receive string data, they will try to convert it to a single-argument
#       dict using the field name fetched from the table below. In other words, if you want to support more record
#       types that receive just a single rdata argument, add them to this dict.
API_FIELDNAMES = dict(A='address', CNAME='cname')
API_BASE_URL = "https://api2.dynect.net/REST/"

class DynectException(Exception):
    def __init__(self, original):
        self.original = original
class LoginFailure(DynectException):
    def __init__(self, response):
        self.response = response

class DynectDNSClient(object):
    def __init__(self, customerName, userName, password, defaultDomain=None, autoPublish=True):
        self.customerName = customerName
        self.userName = userName
        self.password = password
        self.defaultDomain = defaultDomain
        self.autoPublish = autoPublish
        self.sessionToken = None
        self.debug = False

    def defaultDomain(wrapped):
        @wraps(wrapped)
        def wrapper(self, *args, **kwargs):
            kwargs['domainName'] = kwargs.get('domainName') or self.defaultDomain
            return wrapped(self, *args, **kwargs)
        return wrapper

    @defaultDomain
    def getRecords(self, hostName, recordType="ANY", domainName=None):
        return self._request('%sRecord/%s/%s/' % (recordType, domainName, hostName))['data']

    @defaultDomain
    def getRecord(self, hostName, recordID, recordType, domainName=None):
        return self._request('%sRecord/%s/%s/%s/' % (recordType, domainName, hostName, recordID))

    def _modifyRecord(self, method, data, hostName, recordType, TTL, domainName):
        if isinstance(data, basestring):
            data = self.convertToAPIMapping(recordType, data)
        self._request("%sRecord/%s/%s/" % (recordType, domainName, hostName), dict(ttl=str(TTL), rdata=data), method)
        self.considerAutoPublish(domainName)

    @defaultDomain
    def addRecord(self, data, hostName, recordType="A", TTL=3600, domainName=None):
        self._modifyRecord('POST', data, hostName, recordType, TTL, domainName)

    @defaultDomain
    def updateRecord(self, data, hostName, recordType="A", TTL=3600, domainName=None):
        self._modifyRecord('PUT', data, hostName, recordType, TTL, domainName)

    @defaultDomain
    def deleteRecord(self, hostName, recordType="A", domainName=None):
        data = self.getRecords(hostName, recordType, domainName)
        if not data:
            return False

        url = data[0]
        url = url.replace("/REST/", "")
        self._request(url, None, "DELETE")
        self.considerAutoPublish(domainName)

    def convertToAPIMapping(self, recordType, data):
        if recordType not in API_FIELDNAMES:
            raise NotImplementedError("not familiar with %s records" % (recordType,))
        if API_FIELDNAMES[recordType] is None:
            raise TypeError("%s records have more than one argument and must receive map data" % (recordType,))
        return {API_FIELDNAMES[recordType]: data}

    def considerAutoPublish(self, domainName=None):
        if self.autoPublish:
            self.publish(domainName=domainName)

    @defaultDomain
    def publish(self, domainName=None):
        self._request("Zone/%s" % domainName, {"publish": True}, method="PUT")

    def _login(self):
        self.sessionToken = ''
        try:
            response = self._request("Session/", {'customer_name': self.customerName,
                                                  'user_name': self.userName,
                                                  'password': self.password})
        finally:
            self.sessionToken = None
        if response['status'] != 'success':
            raise LoginFailure(response)
        self.sessionToken = response['data']['token']

    def _request(self, url, post=None, method=None):
        if self.sessionToken is None:
            self._login()
        fullurl = API_BASE_URL + url
        if self.debug:
            print fullurl

        if post:
            postdata = json.dumps(post)
            if self.debug:
                print postdata
            req = MethodRequest(fullurl, postdata)
        else:
            req = MethodRequest(fullurl)

        req.add_header('Content-Type', 'application/json')
        req.add_header('Auth-Token', self.sessionToken)
        if method:
            req.method = method

        try:
            resp = urllib2.urlopen(req)
            if method:
                return resp
            else:
                return json.loads(resp.read())

        except urllib2.HTTPError, error:
            raise DynectException(error)

class MethodRequest(urllib2.Request):
    def __init__(self, *args, **kwargs):
        urllib2.Request.__init__(self, *args, **kwargs)
        self.method = None

    def get_method(self):
        if self.method:
            return self.method
        return urllib2.Request.get_method(self)
