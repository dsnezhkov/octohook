from  __future__ import unicode_literals
import threading
import importlib
import yaml
from github import Github
import time


class CommandResponder:

    def __init__(self, config, agentid, issue):
        self.config = config
        self.agentid = agentid
        self.issue = issue

        #print(yaml.dump(config))

        self.ghuser_name = config.github()['git_user_name']
        self.ghtoken = config.github()['git_app_token']
        self.ghrepo_name = config.github()['git_repo_name']

        self.gh = Github(self.ghuser_name, self.ghtoken)
        self.ghuser = self.gh.get_user()
        self.ghrepo = self.ghuser.get_repo(self.ghrepo_name)
        self.ghissue = self.ghrepo.get_issue(self.issue)

    def _recordData(self):
        pass

    def _task_chunks(self, s, n):
        for start in range(0, len(s), n):
            yield s[start:start+n]

    def setData(self, task_data):
        # https://developer.github.com/v3/#rate-limiting
        comment_dlimit=65536
        wait_rlimit=2 # 2 seconds

        print("CommandResponder: Uploading data size {} for agent {}"
              "to GH (notify issue {} )".
              format(len(task_data), self.agentid, self.issue))
        # We can hit the limit of comment post. Split the output
        if len(task_data) < comment_dlimit:
            self.commentIssue(task_data)
        else:
            for task_chunk in self._task_chunks(task_data, (comment_dlimit-1)):
                self.commentIssue(task_chunk)
                time.sleep(wait_rlimit)

        self.closeIssue()

    def commentIssue(self, task_data):
        self.ghissue.create_comment(task_data)
        print("CommandResponder: Comment made on Issue")

    def closeIssue(self):
        self.ghissue.edit(state="closed")
        print("CommandResponder: Issue closed ")


class CommandRouter:

    def __init__(self, config, task, agentid, issue, data):
        self.config = config
        self.task = task
        self.data = data
        self.responder = CommandResponder(config, agentid, issue)

    def run(self):
        task_switcher = {
         "put_local_file": "PutLFileTask",
         "exec_local_process": "ExecLProcessTask"
        }
        module = importlib.import_module("gtasks")
        task = getattr(module, str(task_switcher.get(self.task)))
        itask = task(self.responder, self.data)

        itask.execute()


class GitEventWatcher:
    def __init__(self, agentid, queue):
        self.agentid = agentid
        self.queue = queue

    def watch_issue_closed(self, call):

        if 'action' in call:
            if call['action'] == 'closed' and \
              'issue' in call and \
              'labels' in call['issue'] and \
              'number' in call['issue'] and \
              'name' in call['issue']['labels'][0] and \
              call['issue']['labels'][0]['name'] == self.agentid:

                print("Client: Ag:{} Is:{} Ac:{}".format(
                    call['issue']['labels'][0]['name'],
                    call['issue']['number'],
                    call['action'],
                    )
                )
                self.queue.put(call['issue']['number'])
        else:
            print("Client: This call has no action")
            return False


class CommandParser:

    def __init__(self, config, agentid, issue):
        self.config = config
        self.agentid = agentid
        self.issue = issue

    def parse(self, request):

        if 'request' in request:
            print("CommandParser: Request received {}".
                  format(request['request']))
            if len(request['request']) == 0 or len(request['request']) > 10:
                print("CommandParser: number of commands in request "
                      "needs to be 1...10")

            else:
                for command in request['request']:
                    print(command)
                    cmd_switcher = {
                        'putlocal': 'putlocal',
                        'execlocal': 'execlocal'
                    }
                    cmd = cmd_switcher.get(command.keys()[0], "nosuchcommand")
                    getattr(CommandParser(self.config, self.agentid, self.issue),
                            str(cmd))(command)
        else:
            print("CommandParser: Invalid request. no 'request' directive?")
            print(yaml.dump(request))

    # Put()'ing content via <file> resource on server
    # {'put':
    #   {
    #       'resource': 'file',    <===
    #       'location': '/path/to/file'
    #   }
    # }
    def putlocal(self, command):
        cmd_params = command[CommandParser.putlocal.__name__]
        print("CommandParser: Executing Local put: {}".format(cmd_params))
        # {'resource': 'file'}
        if 'resource' in cmd_params:
            res_switcher = {
                'file': 'f_putlocal'
                }
            cmd = res_switcher.get(cmd_params['resource'], "nosuchresource")
            getattr(CommandParser(self.config, self.agentid, self.issue),
                    str(cmd))(cmd_params)
        else:
            print("CommandParser: No resource specified: {}".format(cmd_params))

    # Put()'ing content via <file> resource on server
    # {'put':
    #   {
    #       'resource': 'file',
    #       'location': '/path/to/file'  <===
    #   }
    # }
    def f_putlocal(self, cmd_params):
        print("CommandParser: Executing Local put -> file: {}".
              format(cmd_params))

        if 'location' in cmd_params:
            crouter = CommandRouter(self.config, 'put_local_file', self.agentid,
                                    self.issue, cmd_params)
            thread = threading.Thread(target=crouter.run)
            thread.start()
        else:
            print("CommandParser: No method specified: {}".format(cmd_params))


    # Exec()'ing <command> on server
    def execlocal(self, command):
        print("CommandParser: Executing Local exec: {}".format(command))
        cmd_params = command[CommandParser.execlocal.__name__]
        if 'resource' in cmd_params:
            res_switcher = {
                'process': 'c_execlocal'
            }
            cmd = res_switcher.get(cmd_params['resource'], "nosuchresource")
            getattr(CommandParser(self.config, self.agentid, self.issue),
                    str(cmd))(cmd_params)
        else:
            print("CommandParser: No resource specified: {}".format(cmd_params))

    # Exec()'ing <command> via <process> resource on server
    def c_execlocal(self, cmd_params):
        print("CommandParser: Executing Local exec -> process: {}".
              format(cmd_params))

        if 'command' in cmd_params:
            crouter = CommandRouter(self.config, 'exec_local_process', self.agentid,
                                    self.issue, cmd_params)
            thread = threading.Thread(target=crouter.run)
            thread.start()
        else:
            print("CommandParser: No method specified: {}".format(cmd_params))

    def nosuchcommand(self, command):
        print("CommandParser: No such command {}".format(command))

    def nosuchresource(self, command):
        print("CommandParser: No such resource {}".format(command))

    def nosuchfilemethod(self, command):
        print("CommandParser: No such file method {}".format(command))
