import bottle

class WRouter(object):
    def __init__(self, wsapp):
       self.wsapp=wsapp

    def route_server():
       if role is not None:
		    bottle.route("/exfil1/", 'POST')(wsapp.exf_server)

    def route_client():
       if role is not None:
          bottle.route("/exfil2/", 'POST')(wsapp.exf_client)
