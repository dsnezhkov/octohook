#!/root/Code/exfilhook/venv/bin/python
from __future__ import print_function
import threading
import bottle
import sys
import yaml
from Queue import Queue
from kweb.webservice import SSLWSGIRefServer, WService
from kweb.webrouter import WRouter
from kcmd.cmdservice import ConCommander2
from klib.configuration import Configurator
import atexit
import logging

def quit_gracefully():
    logging.info('Bye')

def cmdservice_worker(data_q, config):
    cc2 = ConCommander2(config)
    cc2.setup(data_q)
    cc2.do_loop()
    return


def web_server_worker(data_q, config):
    wsapp = WService(queue=data_q, config=config)
    wrouter = WRouter(wsapp)
    wrouter.route_server()

    # Start SSL-wrapped bottle
    logging.info('Starting Webservice server (daemon) ')
    sslsrv = SSLWSGIRefServer(host=config.server()['web']['host'],
                              port=config.server()['web']['port'])
    bottle.run(server=sslsrv, debug=config.server()['web']['debug'],
               quiet=config.server()['web']['quiet'])

    return


def web_client_worker(data_q, config):
    wsapp = WService(queue=data_q, config=config)
    wrouter = WRouter(wsapp)

    wrouter.route_client()
    # Start SSL-wrapped bottle
    sslsrv = SSLWSGIRefServer(host=config.client()['web']['host'],
                              port=config.client()['web']['port'])
    logging.info('Starting Webservice client (daemon) ')
    bottle.run(server=sslsrv, debug=config.client()['web']['debug'],
               quiet=config.client()['web']['quiet'])

    return


def threader(config):
    data_queue = Queue(config.boot()['queue_watermark'])
    config.thread_queue = Queue(3)

    if config.roles()['web']['client'] == True:
        wct = threading.Thread(target=web_client_worker,
                            args=(data_queue, config))
        wct.daemon = True
        wct.start()

    if config.roles()['web']['server'] == True:
        wst = threading.Thread(target=web_server_worker,
                            args=(data_queue, config))
        wst.daemon = True
        wst.start()

    logging.info('Starting Command server, use <Ctrl-D> , `q`, `quit` to quit')
    cst = threading.Thread(target=cmdservice_worker, args=(data_queue, config))
    cst.start()
    return


def bootstrap(startargs):
    if len(sys.argv) != 2:
        logging.critical("Need config File")
        return

    cfgfile = startargs[1]
    logo="""

 _________________________________________________________________
 |____|____|____|____|____|____|____|____|____|____|____|____|____
 ____|____|____|____|____|____|____|____|____|____|____|____|____|
             ____         __          __  __               __
            / __ \ _____ / /_ ____   / / / /____   ____   / /__
           / / / // ___// __// __ \ / /_/ // __ \ / __ \ / //_/
          / /_/ // /__ / /_ / /_/ // __  // /_/ // /_/ // ,<
          \____/ \___/ \__/ \____//_/ /_/ \____/ \____//_/|_|
                        When Cats Have 9 lives....

 _________________________________________________________________
 |____|____|____|____|____|____|____|____|____|____|____|____|___|_
  ___|____|____|____|____|____|____|____|____|____|____|____|____|_

    """
    print(logo)
    logging.debug("Trying to load from {}".format(cfgfile))
    try:
        with open(cfgfile, 'r') as ymlfile:
            config = Configurator(yaml.load(ymlfile))
        threader(config)
    except IOError as e:
        logging.critical("Unable to open config file {}".format(e))

if __name__ == '__main__':
    logging.basicConfig(filename='logs/octohook.log',
                        format='%(asctime)s:%(levelname)s:%(message)s',
                        level=logging.INFO)
    atexit.register(quit_gracefully)
    bootstrap(sys.argv)
