import urllib2
import json
from functools import wraps

__version__ = (0, 0, 1)

class DynectDNSClient:
    def __init__(self, customerName, userName, password, defaultDomain=None, autoPublish=True):
        self.customerName = customerName
        self.userName = userName
        self.password = password
        self.defaultDomain = defaultDomain
        self.autoPublish = autoPublish
        self.sessionToken = None

    def defaultDomain(wrapped):
        @wraps(wrapped)
        def wrapper(self, *args, **kwargs):
            kwargs['domainName'] = kwargs.get('domainName') or self.defaultDomain
            return wrapped(self, *args, **kwargs)
        return wrapper

    @defaultDomain
    def getRecords(self, hostName, type="A", domainName=None):
        try:
            response = self._request('ANYRecord/%s/%s/' % (domainName, hostName), None)
            return response['data']
        except urllib2.HTTPError, e:
            if e.code == 404:
                return None
            else:
                raise e

    @defaultDomain
    def addRecord(self, data, hostName, type="A", TTL=3600, domainName=None):
        url, fieldName = self._api_details(type)
        url = "%s/%s/%s/" % (url, domainName, hostName)
        data = {"ttl": str(TTL),
                        "rdata": { fieldName: data }}

        response = self._request(url, data)
        if response['status'] != 'success':
            return False

        response = self.considerAutoPublish(domainName)
        return True

    @defaultDomain
    def deleteRecord(self, data, hostName, type="A", domainName=None):
        data = self.getRecords(hostName, type, domainName)
        if not data:
            return False

        url = data[0]
        url = url.replace("/REST/", "")
        try:
            self._request(url, None, "DELETE")
            self.considerAutoPublish(domainName)
        except:
            return False

        return True

    def _api_details(self, type):
        if type == "A":
            return ("ARecord", "address")
        else:
            return ("CNameRecord", "cname")

    def considerAutoPublish(self, domainName=None):
        if self.autoPublish:
            self.publish(domainName=domainName)

    @defaultDomain
    def publish(self, domainName=None):
        self._request("Zone/%s" % domainName, {"publish": True}, type="PUT")

    def _login(self):
        response = self._request("Session/", {'customer_name': self.customerName,
                                              'user_name': self.userName,
                                              'password': self.password})
        if response['status'] != 'success':
            return
        self.sessionToken = response['data']['token']

    def _request(self, url, post, type=None):
        fullurl = "https://api2.dynect.net/REST/%s" % url

        if post:
            postdata = json.dumps(post)
            req = MethodRequest(fullurl, postdata)
        else:
            req = MethodRequest(fullurl)

        req.add_header('Content-Type', 'application/json')
        req.add_header('Auth-Token', self.sessionToken)
        if type:
            setattr(req, "method", type)

        try:
            resp = urllib2.urlopen(req)
            if type:
                return resp
            else:
                return json.loads(resp.read())

        except urllib2.HTTPError, e:
            if e.code == 400:
                self._login()
                return self._request(url, post)
            else:
                raise e

class MethodRequest(urllib2.Request):
    def __init__(self, *args, **kwargs):
        urllib2.Request.__init__(self, *args, **kwargs)
        self.method = None

    def get_method(self):
        if self.method:
            return self.method
        return urllib2.Request.get_method(self)
