from __future__ import print_function
import threading
import cmd2
from Queue import Queue
import bottle
from time import sleep
import sys
import json, yaml
from webservice import  SSLWSGIRefServer, WService
from cmdservice import  ConCommander


def cmdservice_worker(data_q ):
    cc=ConCommander()
    cc.setup(data_q)
    cc.cmdloop()
    return

def webservice_worker(data_q):
    wsapp = WService(queue=data_q)

    # Routes 
    bottle.route("/exfil1/", 'POST')(wsapp.exf_server)
    bottle.route("/exfil2/", 'POST')(wsapp.exf_client)

    # Start Regulr bottle 
    #bottle.run(host='0.0.0.0', port=8080, debug=True, quiet=True)

    # Start SSL-wrapped bottle
    sslsrv = SSLWSGIRefServer(host="0.0.0.0", port=8080)
    bottle.run(server=sslsrv, debug=True, quiet=False)
    return

if __name__ == '__main__':

    data_queue = Queue(10)

    print('Starting Webservice server')
    wst=threading.Thread(target=webservice_worker, args=(data_queue,))
    wst.daemon=True
    wst.start()

    print('Starting Command server, use <Ctrl-D> to quit')
    cst = threading.Thread(target=cmdservice_worker, args=(data_queue,))
    cst.start()

