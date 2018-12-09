#!/usr/bin/env python3

import hashlib
import platform
import re
import subprocess

# did you do "pip install requests"?
import requests

def register():
    nodename = getMyNodeName()
    ips = getMyIpAddresses()
    ips = ",".join(ips)
    token = generateToken(["set", nodename, ips])
    # https://host/myip/set/foobar/?ip=123.45.67.1&token=4ae98c43c976a794
    url = "https://host/myip/set/{0}/?ip={1}&token={2}".format(nodename, ips, token)
    r = requests.get(url)
    if r.status_code == 200:
        print("successfully registered as {0} at {1}".format(nodename, ips))
    else:
        print("Failed {0}: {1}".format(r.status_code, r.text))
        print("URL was {0}".format(url))

def getMyNodeName():
    return platform.node()

reLocalIP = re.compile(r' (192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+)/')

def getMyIpAddresses():
    #"ip addr"
    p = subprocess.run(["ip", "addr"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    if p.stderr:
        print("ip addr printed to stderr: >>{0}<<".format(p.stderr.decode("latin-1")))
        raise ValueError
    lines = p.stdout.decode("latin-1").split("\n")
    def extractIP(line):
        line = line.strip()
        match = reLocalIP.search(line)
        return match.group(1) if match else None
    return list(ip for ip in (extractIP(line) for line in lines) if ip)

def generateToken(parts):
    secret = b'secret-token'
    m = hashlib.md5()
    m.update(secret)
    for part in parts:
        m.update(part.encode("utf-8"))
    longDigest = m.hexdigest()
    shortDigest = longDigest[15:31]
    return shortDigest

# ****************************************
if __name__ == "__main__":
    register()
