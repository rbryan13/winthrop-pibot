#!/usr/bin/env python

import os

def deploy():
    src = "~/school/pyserv/serv"
    dest = "pi:py/"
    #os.system("scp -r {0} {1}".format(src, dest))
    os.system("rsync -a {0} {1}".format(src, dest))

deploy()
