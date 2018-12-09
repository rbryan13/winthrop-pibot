
import datetime
import hashlib
import json
import logging
import re

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404

log = logging.getLogger(__name__)

# ----8<-----Add to urls.py
    # /myip/set/thenode?ip=192.168.13.44,192.168.60.102&token=2887ac01
    #    => OK
    # /myip/get/thenode?token=29e04abb
    #    => 192.168.13.44,192.168.60.102
    #url(r'^myip/(?P<verb>get|set)/(?P<nodename>.*?)/', myip.myip.myip),
# ---->8-----


def myip(request, verb, nodename):
    if verb == "set":
        return doset(request, nodename)
    elif verb == "get":
        return doget(request, nodename)
    else:
        log.debug("Unrecognized verb '{0}'".format(verb))
        raise Http404()

reValidIP = re.compile(r'^\d+\.\d+\.\d+\.\d+$')

def doset(request, nodename):
    ips = request.GET.get("ip")
    if not ips:
        log.debug("no ip in set")
        raise Http404()
    if not confirmToken(request.GET.get("token"), ["set", nodename, ips]):
        log.debug("token not confirmed in set")
        raise Http404()
    ips = ips.split(',')
    for ip in ips:
        if not reValidIP.match(ip):
            log.debug("failed ip validation in set")
            raise Http404()
    data = readData()
    data[nodename] = ips
    writeData(data)
    log.debug("for {0} saved {1}".format(nodename, ips))
    return HttpResponse("OK")

def doget(request, nodename):
    #if not confirmToken(request.GET.get("token"), ["get", nodename]):
    #    log.debug("token not confirmed in get")
    #    raise Http404()
    data = readData()
    ips = data.get(nodename)
    if not ips:
        log.debug("no data stored for '{0}'".format(nodename))
        raise Http404()
    log.debug("for {0} read {1}".format(nodename, ips))
    return HttpResponse(ips)

dataFilename = "/var/log/django/myip.dat"

def readData():
    with open(dataFilename, "r") as inf:
        j = inf.read()
    return json.loads(j) if j else {}

def writeData(data):
    j = json.dumps(data)
    with open(dataFilename, "w") as outf:
        outf.write(j)

def confirmToken(token, parts):
    secret = b"secret-token"
    m = hashlib.md5()
    m.update(secret)
    for part in parts:
        m.update(part.encode("utf-8"))
    longDigest = m.hexdigest()
    shortDigest = longDigest[15:31]
    if (token == shortDigest):
        return True
    else:
        log.debug("token mismatch {0} {1}".format(token, longDigest))
        return False
