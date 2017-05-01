from __future__ import print_function
from __future__ import unicode_literals
import cmd2
import threading
import os
from yaml import load
from time import sleep
from github import Github
import ghlib
from prompt_toolkit import prompt
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.contrib.completers import WordCompleter
from pygments.style import Style
from pygments.token import Token
from pygments.styles.default import DefaultStyle
import time
from getpass import getuser
from socket import gethostname

class ConCommander(cmd2.Cmd):
    def __init__(self, config):
        cmd2.Cmd.__init__(self)
        self.config = config

        if self.config.roles()['cmd'] == 'client':
            self.prompt = config.client()['cmd']['prompt']
            self.templatedir = config.client()['cmd']['template_dir']

        if self.config.roles()['cmd'] == 'server':
            self.prompt = config.server()['cmd']['prompt']

        self.agentid = config.boot()['agentid']
        self.git_user_name = config.github()['git_user_name']
        self.git_app_token = config.github()['git_app_token']
        self.git_repo_name = config.github()['git_repo_name']

    def setup(self, data_q):
        self.data_q = data_q
        self.out_watch = None

    def gitshell_watcher(self):
        t = threading.currentThread()
        print("Watcher thread init {}".format(t))
        while getattr(t, "do_run", True):
            if not self.data_q.empty():
                ghlib.checkIssueOutput(self.git_repo, self.data_q.get())
                #self.poutput("RTM")
                #self.perror("RTM")
                #self.pfeedback("RTM")
            sleep(1)
        print("Watcher thread de-init {}".format(t))
        return

    def do_rtm(self, comm):
        """Real Time output monitoring"""
        print("Command {} received".format(comm))

        if comm == 'gshstart':
            if self.out_watch is None or (not self.out_watch.isAlive()):
                self.out_watch = threading.Thread(target=self.gitshell_watcher)
                self.out_watch.daemon = True
                print("Starting new thread ({})".format(comm))
                self.out_watch.start()
            else:
                print("Watchdog already running({})".
                      format(self.out_watch.ident))

        if comm == 'gshstop':
            print("Wishing to stop thread ({})".format(comm))
            if self.out_watch is not None and self.out_watch.isAlive():
                self.out_watch.do_run = False
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
            instructions = load(stream)
            instructions['issue']['body']['request'][0]['execlocal']['command']\
                = arg.parsed.statement.args

            self.git_issue = ghlib.createIssueFromInstructions(
                self.agentid, self.git_repo, instructions)

            if self.git_issue is not None:
                print("Created task: ({}) - {}".
                      format(self.git_issue.number, self.git_issue.title))
        else:
            print('Need command to exec on server')

    def do_put(self, arg):
        """put </path/to/file/>
        Send `path to file` to server. File uplaoded to GH in agent space """
        if arg:
            print("Executing {}".format(arg.parsed.dump()))
            stream = file(os.path.join(self.templatedir, 'putlocal.tmpl'), 'r')
            instructions = load(stream)
            instructions['issue']['body']['request'][0]['putlocal']['location']\
                = arg.parsed.statement.args

            self.git_issue = ghlib.createIssueFromInstructions(
                self.agentid, self.git_repo, instructions)

            if self.git_issue is not None:
                print("Created task: ({}) - {}".
                      format(self.git_issue.number, self.git_issue.title))
        else:
            print('Need /path/to/file on server')


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
            print("Checking status of {} tasks for agent ({})".
                  format(top, self.agentid))
            ghlib.checkIssueStates(self.git_repo, self.agentid, int(top))
        else:
            print("Need number of tasks  for agent:{} to check".
                  format(self.agentid))

    def preloop(self):

        self.git = Github(self.git_user_name, self.git_app_token)
        self.git_user = self.git.get_user()
        # print("== List of repos  for user {}...".format(user))
        # for repo in self.g.get_user().get_repos():
        # print(repo.name)

        # self.reqfile="./instructions"
        self.git_repo = ghlib.checkRepoExists(self.git_user, self.git_repo_name)
        if self.git_repo is None:
            # repo.create_file('/agent1/filename2', 'commitmessage', 'content')
            # Create issue with a request
            self.git_repo = ghlib.createRepo(self.git_user, self.git_repo_name)


###################################
class ServerStyle(Style):

    styles = {
    Token.Menu.Completions.Completion.Current: 'bg:#00aaaa #000000',
    Token.Menu.Completions.Completion: 'bg:#008888 #ffffff',
    Token.Menu.Completions.ProgressButton: 'bg:#003333',
    Token.Menu.Completions.ProgressBar: 'bg:#00aaaa',
    # User input.
    Token:          '#ff0066',
    Token.Toolbar:  '#000000 bg:#ff6600',

    # Prompt.
    Token.Username: '#ffffff',
    Token.At:       '#00aa00',
    Token.Marker:   '#00aa00',
    Token.Host:     '#008888',
    Token.DTime:    '#884444 underline',
    }
    styles.update(DefaultStyle.styles)

class ClientStyle(Style):

    styles = {
    Token.Menu.Completions.Completion.Current: 'bg:#00aaaa #000000',
    Token.Menu.Completions.Completion: 'bg:#008888 #ffffff',
    Token.Menu.Completions.ProgressButton: 'bg:#003333',
    Token.Menu.Completions.ProgressBar: 'bg:#00aaaa',
    # User input.
    Token:          '#ff0066',
    Token.Toolbar:  '#000000 bg:#ffcc66',

    # Prompt.
    Token.Username: '#884444',
    Token.At:       '#00aa00',
    Token.Marker:   '#00aa00',
    Token.Host:     '#008888',
    Token.DTime:    '#884444 underline',
    }
    styles.update(DefaultStyle.styles)



class ConCommander2:
    def __init__(self, config):
        self.config = config
        self.role_server=False
        self.role_client=False

        if self.config.roles()['cmd'] == 'client':
            self.role_client=True
            self.templatedir = config.client()['cmd']['template_dir']

        if self.config.roles()['cmd'] == 'server':
            self.role_server=True


        self.agentid = config.boot()['agentid']
        self.git_user_name = config.github()['git_user_name']
        self.git_app_token = config.github()['git_app_token']
        self.git_repo_name = config.github()['git_repo_name']
        self.git = Github(self.git_user_name, self.git_app_token)
        self.git_user = self.git.get_user()
        # print("== List of repos  for user {}...".format(user))
        # for repo in self.g.get_user().get_repos():
        # print(repo.name)

        self.git_repo = ghlib.checkRepoExists(self.git_user, self.git_repo_name)
        if self.git_repo is None:
            # repo.create_file('/agent1/filename2', 'commitmessage', 'content')
            # Create issue with a request
            self.git_repo = ghlib.createRepo(self.git_user, self.git_repo_name)

    def _get_bottom_toolbar_tokens(self, cli):

        return [
            (Token.Toolbar, "Client" if self.role_client else "Server" ),
        ]

    def _get_prompt_tokens(self, cli):

        return [
            (Token.Username, getuser()),
            (Token.At,       '@'),
            (Token.Host,     gethostname()),
            (Token.Marker,    '> '),
        ]

    def _get_rprompt_tokens(self, cli):

        tb_time = time.strftime("%d %b %Y %H:%M:%S", time.gmtime())
        return [
            (Token.DTime, tb_time),
        ]

    def do_loop(self):
        history = InMemoryHistory()
        gh_completer = WordCompleter(
                ['execute', 'put',
                 'rtm', 'gshstart', 'gshstop'],
                               ignore_case=True)
        while True:
            if  self.role_server:
                try:
                    result = prompt(completer=gh_completer,
                      style=ServerStyle, history=history, vi_mode=True,
                      enable_history_search=True,
                      reserve_space_for_menu=4,
                      complete_while_typing=True,
                      display_completions_in_columns=True,
                      wrap_lines=True,
                      get_prompt_tokens=self._get_prompt_tokens,
                      get_rprompt_tokens=self._get_rprompt_tokens,
                      get_bottom_toolbar_tokens=self._get_bottom_toolbar_tokens,
                      patch_stdout=True)
                except  KeyboardInterrupt as ke:
                    print("^D to exit")

            if  self.role_client:
                try:
                    result = prompt(completer=gh_completer,
                      style=ClientStyle, history=history, vi_mode=True,
                      enable_history_search=True,
                      reserve_space_for_menu=4,
                      complete_while_typing=True,
                      display_completions_in_columns=True,
                      get_rprompt_tokens=self._get_rprompt_tokens,
                      wrap_lines=True,
                      get_prompt_tokens=self._get_prompt_tokens,
                      get_bottom_toolbar_tokens=self._get_bottom_toolbar_tokens,
                      patch_stdout=True)
                except  KeyboardInterrupt as ke:
                    print("^D to exit")

            if not result:
                print("Need a Valid Command")
            else:
                cmdargs=""
                tokens=result.split(' ')
                print("Tokens:" )
                print(tokens)

                if len(tokens) > 0:
                    cmd=tokens[0] # get command
                    print("cmd:[{}]".format(cmd))

                    if cmd  == 'execute':
                        cmdargs=result.split(' ', 1) # get arguments
                        if len(cmdargs) > 0: # Args exist
                            print("Cmdargs:" )
                            print(cmdargs)
                            self.do_rtm('gshstart')
                            self.do_execute(cmdargs[1])
                        else:
                            print("Possibly missing command arguments")

                    elif cmd  == 'put':
                        cmdargs=result.split(' ', 1) # get arguments
                        if len(cmdargs) > 0: # Args exist
                            print("Cmdargs:" )
                            print(cmdargs)
                            self.do_rtm('gshstart')
                            self.do_put(cmdargs[1])
                        else:
                            print("Possibly missing command arguments")
                    else:
                        print("Unsupported  Command")
                else:
                   print("Invalid Command")


    def setup(self, data_q):
        self.data_q = data_q
        self.out_watch = None

    def do_rtm(self, comm):
        """Real Time output monitoring"""
        print("Command {} received".format(comm))

        if comm == 'gshstart':
            if self.out_watch is None or (not self.out_watch.isAlive()):
                self.out_watch = threading.Thread(target=self.gitshell_watcher)
                self.out_watch.daemon = True
                print("Starting new thread ({})".format(comm))
                self.out_watch.start()
            else:
                print("Watchdog already running({})".
                      format(self.out_watch.ident))

        if comm == 'gshstop':
            print("Wishing to stop thread ({})".format(comm))
            if self.out_watch is not None and self.out_watch.isAlive():
                self.out_watch.do_run = False
                self.out_watch.join()
            else:
                print("Watchdog not started")

    def gitshell_watcher(self):
        t = threading.currentThread()
        print("Watcher thread init {}".format(t))
        while getattr(t, "do_run", True):
            if not self.data_q.empty():
                comment_list=ghlib.getClosedIssueComments(
                        self.git_repo,
                        self.data_q.get())
                if comment_list:
                    for comment in comment_list:
                        print(comment)
                        sleep(2)  # Pause for polling: GH throttling
        print("Watcher thread de-init {}".format(t))
        return

    def do_execute(self, arg):
        """execute <command [arguments]>
        Send `command` and its arguments to server """
        if arg:
            print("Executing {}".format(arg))
            stream = file(os.path.join(self.templatedir, 'execlocal.tmpl'), 'r')
            instructions = load(stream)
            instructions['issue']['body']['request'][0]['execlocal']['command']\
                = str(arg)

            self.git_issue = ghlib.createIssueFromInstructions(
                self.agentid, self.git_repo, instructions)

            if self.git_issue is not None:
                print("Created task: ({}) - {}".
                      format(self.git_issue.number, self.git_issue.title))
                #self.do_rtm('gshstart')
        else:
            print('Need command')

    def do_put(self, arg):
        """put </path/to/file>
        Send `path to file` to server. File uplaoded to GH in agent space """
        if arg:
            print("Executing {}".format(arg))
            stream = file(os.path.join(self.templatedir, 'putlocal.tmpl'), 'r')
            instructions = load(stream)
            instructions['issue']['body']['request'][0]['putlocal']['location']\
                = str(arg)

            self.git_issue = ghlib.createIssueFromInstructions(
                self.agentid, self.git_repo, instructions)

            if self.git_issue is not None:
                print("Created task: ({}) - {}".
                      format(self.git_issue.number, self.git_issue.title))
                #self.do_rtm('gshstart')
        else:
            print('Need /path/to/file on server')



