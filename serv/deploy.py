#!/usr/bin/env python3

import os

def deploy():
    src = "/mnt/transport/school/winthrop-pibot/serv/"
    #src = "~/school/pyserv/serv"
    dest = "pir:py/serv"
    #os.system("scp -r {0} {1}".format(src, dest))
    os.system("rsync -a {0} {1}".format(src, dest))

deploy()
