from __future__ import print_function
import cmd2
import threading,os, sys
from uuid import uuid4
from yaml import load, dump, scanner
from Queue import Queue
from time import sleep
from github import Github
from github.GithubException import GithubException
from github.GithubObject import NotSet
import ghlib

class ConCommander(cmd2.Cmd):
    def __init__(self, config):
      cmd2.Cmd.__init__(self)
      self.config=config

      if self.config['roles']['cmd'] == 'client':
         self.prompt=config['client']['cmd']['prompt']
         self.templatedir=config['client']['cmd']['template_dir']

      if self.config['roles']['cmd'] == 'server':
         self.prompt=config['server']['cmd']['prompt']

      self.agentid=config['boot']['agentid']
      self.git_user_name=config['github']['git_user_name']
      self.git_app_token=config['github']['git_app_token'] 
      self.git_repo_name=config['github']['git_repo_name'] 

    def setup(self,data_q ):
      self.data_q=data_q
      self.out_watch=None

    def gitshell_watcher(self):
      t = threading.currentThread()
      print("Watcher thread {}".format(t))
      while getattr(t, "do_run", True):
        if not self.data_q.empty():
           ghlib.checkIssueOutput(self.git_repo, self.data_q.get())
        sleep(1)
      print("Stopping RTM")
      return

    def do_rtm(self, comm):
      """Real Time output monitoring"""
      print("Command {} received".format(comm))

      if comm == 'gshstart':
         if self.out_watch is None or (not self.out_watch.isAlive()):
            self.out_watch = threading.Thread(target=self.gitshell_watcher)
            self.out_watch.daemon=True
            print("Starting new thread ({})".format(comm))
            self.out_watch.start()
         else:
            print("Watchdog already running({})".format(self.out_watch.ident))

      if comm == 'gshstop':
         print("Wishing to stop thread ({})".format(comm))
         if self.out_watch is not None and self.out_watch.isAlive():
            self.out_watch.do_run=False
            self.out_watch.join()
         else:
            print("Watchdog not started")

    def do_rdq(self, line):
      """Read Data"""
      if not self.data_q.empty():
         print(self.data_q.get())

    def do_EOF(self, line):
      return True

    def postcmd(self, stop, line):
      if not self.data_q.empty():
        print("Queued ({}) ".format(self.data_q.qsize()))
      return stop

    def do_execute(self, arg):
      """execute <command [arguments]>
      Send `command` and its arguments to server """
      if arg:
         print("Executing {}".format(arg.parsed.dump()))
         stream = file(os.path.join(self.templatedir, 'execlocal.tmpl'), 'r')  
         instructions=load(stream)
         instructions['issue']['body']['request'][0]['execlocal']['command']=\
								arg.parsed.statement.args
         self.git_issue=ghlib.createIssueFromInstructions(self.agentid, self.git_repo, instructions)

         if self.git_issue is not None:
            print("Created task: ({}) - {}".format(self.git_issue.number, self.git_issue.title))
      else:
         print('Need command')

    def do_checkoutput(self, task_number):
      """checkoutput <task number>
      Check output of `task` from server """
      if task_number:
         print("Checking status and output of task ({})".format(task_number))
         ghlib.checkIssueOutput(self.git_repo, task_number)
      else:
         print('Need task number')

    def do_checkstates(self, top=5):
      """checkstates <number>
      Check status of tasks"""
      if top:
        print("Checking status of {} tasks for agent ({})".format(top, self.agentid))
        ghlib.checkIssueStates(self.git_repo, self.agentid, int(top))
      else:
        print("Need number of tasks  for agent:{} to check".format(self.agentid))



    def preloop(self):

      self.git = Github(self.git_user_name, self.git_app_token)
      self.git_user=self.git.get_user()
      #print("== List of repos  for user {}...".format(user))
      #for repo in self.g.get_user().get_repos():
      #  print(repo.name)

      #self.reqfile="./instructions"
      self.git_repo=ghlib.checkRepoExists(self.git_user,self.git_repo_name)
      if self.git_repo is None:
         #repo.create_file('/agent1/filename2', 'commitmessage', 'content')
         #Create issue with a request
         self.git_repo=ghlib.createRepo(self.git_user,self.git_repo_name) 

