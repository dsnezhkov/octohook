from __future__ import print_function
import threading
from Queue import Queue
import bottle
from time import sleep
import sys
import json, yaml
from gitcommander import CommandParser

class SSLWSGIRefServer(bottle.ServerAdapter):
    def run(self, handler):
        from wsgiref.simple_server import make_server, WSGIRequestHandler
        import ssl
        if self.quiet:
            class QuietHandler(WSGIRequestHandler):
                def log_request(*args, **kw): pass
            self.options['handler_class'] = QuietHandler
        srv = make_server(self.host, self.port, handler, **self.options)
        srv.socket = ssl.wrap_socket (
            srv.socket,
            certfile='hook.pem'  # path to certificate
            )
        srv.serve_forever()

class WService(object):
   def __init__(self,param):
     self.param   = param
     self.q = self.param
     print("init with = %s" % self.param)

   def server(self):
      if request.method == 'POST':
         call=json.loads(request.data)
         print("Incoming request: {}".format(call['action']))
         #print(call)
         if 'action' in call:
            if call['action'] == 'labeled':
               #process newly created issue
               if 'issue' in call:
                  if 'body' in call['issue'] and \
                        'labels' in call['issue'] and \
                        'name' in call['issue']['labels'][0]:
                        try:

                           # which agent is calling us 
                           agentid=call['issue']['labels'][0]['name']
                           issue=call['issue']['number']

                           # what is this agent's instructions
                           body=yaml.load(call['issue']['body'])                    
                           print("Instructions from: ({}) : ".format(agentid))
                           c=CommandParser(agentid, issue)
                           c.parse(body)
                        except yaml.scanner.ScannerError as yse:
                           print("This body of this issue cannot be parsed: {}".format(yse))
                           print(call['issue']['body'])
                  else:
                     print("This issue does not have a body or named labels")
                     #print(call)
               else:
                  print("This call is not a valid labeled issue")
                  #print(call)
            else:
               print("This call is not a labeled issue")
               #print(call)
         else:
            print("This call has no action")
            #print(call)


