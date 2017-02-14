import glob
import subprocess
import shlex 

class FileTask:
	def __init__(self,responder, data):
		self.responder=responder
		self.data=data
	def execute(self):
		print("FileTask Execute() for agentid {} with data: {} ".format(
					self.responder.agentid, self.data))
		response_data=glob.glob(self.data['location'])
		print("{}".format(response_data))

		self.responder.setData(",".join(response_data))

class ExecLProcessTask:
	def __init__(self,responder, data):
		self.responder=responder
		self.data=data
	def execute(self):
		print("ExecProcessTask Execute() for agentid {} with data: {} ".format(
					self.responder.agentid, self.data))

		process = subprocess.Popen(shlex.split(self.data['command']), 
						stdout=subprocess.PIPE,  stderr=subprocess.PIPE)
		so, se = process.communicate()

		if process.returncode == 0:
			print("Process error: ".format(process.returncode))
			response_data=so.decode('utf-8')
		else:
			print("Process success: ".format(process.returncode))
			response_data=se.decode('utf-8')

		print("{}".format(response_data))

		self.responder.setData(response_data)
		

		

