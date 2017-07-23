from __future__ import print_function
from __future__ import unicode_literals
import threading
import os
import logging
from yaml import load
from time import sleep
from github import Github
from klib import ghlib
from prompt_toolkit import prompt
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.contrib.completers import WordCompleter
import time
from getpass import getuser
from socket import gethostname
from pygments.token import Token
from kcmd.cmdlook import ServerStyle, ClientStyle

from prompt_toolkit.shortcuts import clear
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

class ConCommander2:
    def __init__(self, config):
        self.config = config
        self.role_server=False
        self.role_client=False

        if self.config.roles()['cmd'] == 'client':
            self.role_client=True
            self.role_human="Client"
            self.templatedir = config.client()['cmd']['template_dir']

        if self.config.roles()['cmd'] == 'server':
            self.role_server=True
            self.role_human="Server"


        self.agentid = config.boot()['agentid']
        self.git_user_name = config.github()['git_user_name']
        self.git_app_token = config.github()['git_app_token']
        self.git_repo_name = config.github()['git_repo_name']
        self.git = Github(self.git_user_name, self.git_app_token)
        self.git_user = self.git.get_user()

        self.git_cissue=None
        self.rtm_poll_freq=config.github()['git_rlimit']

        logging.debug("== List of repos  for user {}...".format(self.git_user))
        #for repo in self.g.get_user().get_repos():
        #    logging.debug(repo.name)

        self.git_repo = ghlib.checkRepoExists(self.git_user, self.git_repo_name)
        if self.git_repo is None:
            # repo.create_file('/agents/UUID/filename', 'commitmessage', 'content')
            # Create issue with a request
            self.git_repo = ghlib.createRepo(self.git_user, str(self.git_repo_name))

    def setup(self, data_q):
        self.data_q = data_q
        self.out_watch = None

    # Style Based Configuration
    def _get_bottom_toolbar_tokens(self, cli):

        tcontent='[{}] Task: {}'.format(self.role_human, self.git_cissue)

        return [
            (Token.Toolbar, tcontent ),
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

    def _get_title(self):
        return 'OctoHook'

    def do_loop(self):
        history = InMemoryHistory()
        gh_completer_client = WordCompleter(
            ['execute', 'put', 'checkissues',
             'viewissue', 'rtm', 'clear', 'viewhooks'],
            ignore_case=True, match_middle=True)
        gh_completer_server = WordCompleter(
            ['clear', 'viewhooks'],
            ignore_case=True, match_middle=True)

        while True:
            result=None
            if  self.role_server:
                try:
                    result = prompt(completer=gh_completer_server,
                      style=ServerStyle, vi_mode=True,
                      enable_history_search=True,
                      reserve_space_for_menu=4,
                      complete_while_typing=True,
                      display_completions_in_columns=True,
                      wrap_lines=True,
                      get_prompt_tokens=self._get_prompt_tokens,
                      get_rprompt_tokens=self._get_rprompt_tokens,
                      get_bottom_toolbar_tokens=self._get_bottom_toolbar_tokens,
                      enable_system_bindings=True,
                      get_title=self._get_title,
                      history = history,
                      auto_suggest=AutoSuggestFromHistory(),
                      patch_stdout=True)
                except  KeyboardInterrupt:
                    logging.warning("^D to exit")
                except  EOFError:
                    return

            if  self.role_client:
                try:
                    result = prompt(completer=gh_completer_client,
                      style=ClientStyle, vi_mode=True,
                      enable_history_search=True,
                      reserve_space_for_menu=4,
                      complete_while_typing=True,
                      display_completions_in_columns=True,
                      get_rprompt_tokens=self._get_rprompt_tokens,
                      wrap_lines=True,
                      get_prompt_tokens=self._get_prompt_tokens,
                      get_bottom_toolbar_tokens=self._get_bottom_toolbar_tokens,
                      enable_system_bindings=True,
                      get_title=self._get_title,
                      history = history,
                      auto_suggest=AutoSuggestFromHistory(),
                      patch_stdout=True)
                except  KeyboardInterrupt:
                    logging.warning("^D to exit")
                except  EOFError:
                    return

            if not result:
                pass
            else:
                cmdargs=""
                tokens=result.split(' ')

                if len(tokens) > 0:
                    cmd=tokens[0] # get command
                    logging.debug("cmd:[{}]".format(cmd))

                    if cmd == 'clear':
                        clear()
                    elif cmd == 'help':
                        print("""
                              System: Alt-!
                              Exit: Ctlr-D
                              Skip: Ctrl-C
                              Search: Vi mode standard
                              """)

                    elif cmd == 'viewhooks':
                        self.do_viewHooks()

                    elif cmd  == 'execute':
                        cmdargs=result.split(' ', 1) # get arguments
                        if len(cmdargs) > 1: # Args exist
                            logging.debug("Cmdargs:" )
                            logging.debug(cmdargs)
                            self.do_execute(cmdargs[1])
                        else:
                            print("Execute: Mising command arguments")
                            logging.error("Execute: Missing command arguments")

                    elif cmd  == 'rtm':
                        if len(tokens)  == 2:
                            comm=tokens[1]
                            self.do_rtm(comm)
                        else:
                            print("RTM: Mising command arguments:  <on|off>")
                            logging.warning("RTM: Mising command arguments:  <on|off>")

                    elif cmd  == 'put':
                        cmdargs=result.split(' ', 1) # get arguments
                        if len(cmdargs) > 0: # Args exist
                            logging.debug("Cmdargs:" )
                            logging.debug(cmdargs)
                            self.do_put(cmdargs[1])
                        else:
                            print("PUT: Missing command arguments")
                            logging.error("PUT: Missing command arguments")
                    elif cmd  == 'checkissues':
                        top=5 # top issue to display states for
                        ghlib.checkIssueStates(self.git_repo,
                                                    self.agentid, top)
                    elif cmd  == 'viewissue':
                        if len(tokens)  == 2:
                            issue_number=tokens[1]
                            comments_contents=ghlib.getClosedIssueComments(
                                self.git_repo, issue_number)
                            for x in comments_contents:
                                print(x)
                        else:
                            print("ViewIssue: Need Issue number ")
                            logging.warning("ViewIssue: Need Issue number ")
                    else:
                        print("Unsupported  Command")
                        logging.warning("Unsupported  Command")
                else:
                   print("Invalid Command")
                   logging.warning("Invalid Command")


    def do_viewHooks(self):
        """ View  Hooks  """
        for hook in  self.git_repo.get_hooks():
            print("HookId:{}, Name:{}, Active?{}, Destination:{}".
                  format(hook.id, hook.name, hook.active, hook.config['url']))

    def createIssue(self, instructions):
        self.git_issue = ghlib.createIssueFromInstructions(
            self.agentid, self.git_repo, instructions)

        if self.git_issue is not None:
            logging.info("Created task: ({}) - {}".
                    format(self.git_issue.number, self.git_issue.title))
            self.git_cissue=self.git_issue.number
            return  True
        else:
            return  False

    def do_execute(self, arg):
        """execute <command [arguments]>
        Send `command` and its arguments to server """
        if arg:
            logging.info("Executing {}".format(arg))
            stream = open(os.path.join(self.templatedir, 'execlocal.tmpl'), 'r')
            instructions = load(stream)
            stream.close()
            instructions['issue']['body']['request'][0]['execlocal']['command']\
                = str(arg)
            self.createIssue(instructions)
        else:
            logging.error('Need some command')

    def do_put(self, arg):
        """put </path/to/file>
        Send `path to file` to server. File uplaoded to GH in agent space """
        if arg:
            logging.info("Executing {}".format(arg))
            stream = open(os.path.join(self.templatedir, 'putlocal.tmpl'), 'r')
            instructions = load(stream)
            stream.close()
            instructions['issue']['body']['request'][0]['putlocal']['location']\
                = str(arg)

            self.createIssue(instructions)
        else:
            logging.error('Need /path/to/file on server')


    def do_rtm(self, comm):
        """Real Time output monitoring"""
        logging.debug("Command {} received".format(comm))

        if comm == 'on':
            if self.out_watch is None or (not self.out_watch.isAlive()):
                self.out_watch = threading.Thread(target=self.gitshell_watcher)
                self.out_watch.daemon = True
                self.out_watch.do_run =  True
                self.data_q.queue.clear()
                print("Request to start rtm thread")
                logging.info("Request to start rtm thread ".format(comm))
                self.out_watch.start()
            else:
                print("RTM already running")
                logging.warning("Watchdog already running({})".
                      format(self.out_watch.ident))

        elif comm == 'off':
            print("Request to stop rtm thread")
            logging.info("Request to stop rtm thread ({})".format(comm))
            if self.out_watch is not None and self.out_watch.isAlive():
                self.out_watch.do_run = False
                self.out_watch.join()
            else:
                print("RTM not started yet")
                logging.warning("Watchdog not started")


    def gitshell_watcher(self):
        t = threading.currentThread()
        logging.debug("Watcher thread init {}".format(t))
        while getattr(t, "do_run", True):
            if not self.data_q.empty():
                logging.debug("Polling Queue for Closed Issues")
                comment_list=ghlib.getClosedIssueComments(
                        self.git_repo,
                        self.data_q.get())
                if comment_list:
                    for comment in comment_list:
                        print(comment)
                        logging.debug("Polling Wait for {} ".
                                      format(self.rtm_poll_freq))
                        sleep(self.rtm_poll_freq)
        logging.debug("Watcher thread de-init {}".format(t))
        return
