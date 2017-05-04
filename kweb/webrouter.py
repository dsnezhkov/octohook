import bottle
import logging

class WRouter(object):
    def __init__(self, wsapp):
        self.wsapp = wsapp

    def route_server(self, sconfig):
        resource='/server/'
        if 'web' in sconfig and 'hook_route' in sconfig['web']:
            resource=sconfig['web']['hook_route']
        else:
            logging.error(
                "Webrouter: No valid resource route found. Taking defaults {}".
                    format(resource))
        logging.info("Webrouter: starting routing on {}".format(resource))
        bottle.route(resource, 'POST')(self.wsapp.exf_server)

    def route_client(self, cconfig):
        resource='/client/'
        if 'web' in cconfig and 'hook_route' in cconfig['web']:
            resource=cconfig['web']['hook_route']
        else:
            logging.error(
                "Webrouter: No valid resource route found. Taking defaults {}".
                    format(resource))
        logging.info("Webrouter: starting routing on {}".format(resource))
        bottle.route(resource, 'POST')(self.wsapp.exf_client)
