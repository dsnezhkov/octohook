import bottle


class WRouter(object):
    def __init__(self, wsapp):
        self.wsapp = wsapp

    def route_server(self):
        bottle.route("/exfil1/", 'POST')(self.wsapp.exf_server)

    def route_client(self):
        bottle.route("/exfil2/", 'POST')(self.wsapp.exf_client)
