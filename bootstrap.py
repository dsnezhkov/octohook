#!/root/Code/exfilhook/venv/bin/python
from __future__ import print_function
import threading, cmd2, bottle, sys, json, yaml
from time import sleep
from Queue import Queue
from kweb.webservice import  SSLWSGIRefServer, WService
from kweb.webrouter import   WRouter
from kcmd.cmdservice import  ConCommander
import click


def cmdservice_worker(data_q, config):
    cc=ConCommander(config)
    cc.setup(data_q)
    cc.cmdloop()
    return

def web_server_worker(data_q, config):
    wsapp = WService(queue=data_q, config=config)
    wrouter = WRouter(wsapp)
    wrouter.route_server()

    # Start SSL-wrapped bottle
    print('Starting Webservice server (daemon) ')
    sslsrv = SSLWSGIRefServer(host=config['server']['web']['host'], port=config['server']['web']['port'])
    bottle.run(server=sslsrv, debug=config['server']['web']['debug'], quiet=config['server']['web']['quiet'])

    return

def web_client_worker(data_q, config):
    wsapp = WService(queue=data_q, config=config)
    wrouter = WRouter(wsapp)

    wrouter.route_client()
    # Start SSL-wrapped bottle
    sslsrv = SSLWSGIRefServer(host=config['client']['web']['host'], port=config['client']['web']['port'])
    print('Starting Webservice client (daemon) ')
    bottle.run(server=sslsrv, debug=config['client']['web']['debug'], quiet=config['client']['web']['quiet'])

    return

def threader(config):
    data_queue = Queue(config['boot']['queue_watermark'])

    if config['roles']['web']['client'] == True:
       wct=threading.Thread(target=web_client_worker, args=(data_queue,config))
       wct.daemon=True
       wct.start()

    if config['roles']['web']['server'] == True:
       wst=threading.Thread(target=web_server_worker, args=(data_queue,config))
       wst.daemon=True
       wst.start()

    print('Starting Command server, use <Ctrl-D> , `q`, `quit` to quit')
    cst = threading.Thread(target=cmdservice_worker, args=(data_queue,config))
    cst.start()

    return

def bootstrap(startargs):
    if len(sys.argv) < 1:
       raise

    cfgfile=startargs[1]

    print("Trying to load from {}".format(cfgfile))
    try:
       with open(cfgfile, 'r') as ymlfile:
          config = yaml.load(ymlfile)
       threader(config)
    except IOError as e:
       print("Unable to open config file {}".format(e))

if __name__ == '__main__':
    bootstrap(sys.argv)

