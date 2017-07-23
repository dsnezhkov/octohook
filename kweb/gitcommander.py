from  __future__ import unicode_literals
import threading
import importlib
import yaml
from github import Github
import time
from os import path
import logging

class CommandResponder:

    def __init__(self, config, agentid, issue):
        self.config = config
        self.agentid = agentid
        self.issue = issue

        #logging.debug(yaml.dump(config))

        self.ghuser_name = config.github()['git_user_name']
        self.ghtoken = config.github()['git_app_token']
        self.ghrepo_name = config.github()['git_repo_name']
        self.gh_rlimit = config.github()['git_rlimit']
        self.ghcomm_limit = config.github()['git_comm_limit']

        self.gh = Github(self.ghuser_name, self.ghtoken)
        self.ghuser = self.gh.get_user()
        self.ghrepo = self.ghuser.get_repo(self.ghrepo_name)
        self.ghissue = self.ghrepo.get_issue(self.issue)

    def _task_chunks(self, s, n):
        for start in range(0, len(s), n):
            yield s[start:start+n]

    def setFile(self, file_name, file_data):
        self.ghrepo.create_file(
             '/agents/' + self.agentid + '/'+ path.basename(file_name),
            "Issue: " + str(self.ghissue.number), file_data)

    def setData(self, task_data):

        logging.debug("CommandResponder: Uploading data size {} for agent {}"
              "to GH (notify issue {} )".
              format(len(task_data), self.agentid, self.issue))
        # We can get no output from a command, fill in the blank for API.
        if len(task_data) == 0:
            task_data="No Output"
        # We can hit the limit of comment post. Split the output
        if len(task_data) < self.ghcomm_limit:
            self.commentIssue(task_data)
        else:
            for task_chunk in self._task_chunks(task_data, (self.ghcomm_limit-1)):
                self.commentIssue(task_chunk)
                time.sleep(self.gh_rlimit)

        self.closeIssue()

    def commentIssue(self, task_data):
        self.ghissue.create_comment(task_data)
        logging.debug("CommandResponder: Comment made on Issue ({})".
                      format(self.ghissue.number))

    def closeIssue(self):
        self.ghissue.edit(state="closed")
        logging.debug("CommandResponder: Issue ({}) closed ".
                      format(self.ghissue.number))


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
        module = importlib.import_module("ktasks.gtasks")
        task = getattr(module, str(task_switcher.get(self.task)))
        itask = task(self.responder, self.data)

        itask.execute()


class GitEventWatcher:
    def __init__(self, agentid, queue):
        self.agentid = agentid
        self.queue = queue

    """ Check for proper GH call format  """
    def watch_issue_closed(self, call):

        if 'action' in call:
            if call['action'] == 'closed' and \
              'issue' in call and \
              'labels' in call['issue'] and \
              'number' in call['issue'] and \
              'name' in call['issue']['labels'][0] and \
              call['issue']['labels'][0]['name'] == self.agentid:

                logging.debug("Client: Ag:{} Is:{} Ac:{}".format(
                    call['issue']['labels'][0]['name'],
                    call['issue']['number'],
                    call['action'],
                    )
                )
                self.queue.put(call['issue']['number'])
        else:
            logging.error("GitEvent: Call arrived with no action")
            return False


class CommandParser:

    def __init__(self, config, agentid, issue):
        self.config = config
        self.agentid = agentid
        self.issue = issue

    def parse(self, request):

        if 'request' in request:
            logging.debug("CommandParser: Request received {}".
                  format(request['request']))
            if len(request['request']) == 0 or len(request['request']) > 10:
                logging.error("CommandParser: number of commands in request "
                      "needs to be 1...10")

            else:
                for command in request['request']:
                    logging.debug(command)
                    cmd_switcher = {
                        'putlocal': 'putlocal',
                        'execlocal': 'execlocal'
                    }
                    cmd = cmd_switcher.get(list(command.keys())[0], "nosuchcommand")
                    getattr(CommandParser(self.config, self.agentid, self.issue),
                            str(cmd))(command)
        else:
            logging.error("CommandParser: Invalid request. no 'request' directive?")
            logging.debug(yaml.dump(request))

    # Put()'ing content via <file> resource on server
    # {'put':
    #   {
    #       'resource': 'file',    <===
    #       'location': '/path/to/file'
    #   }
    # }
    def putlocal(self, command):
        cmd_params = command[CommandParser.putlocal.__name__]
        logging.info("CommandParser: Executing put: {}".format(cmd_params))
        # {'resource': 'file'}
        if 'resource' in cmd_params:
            res_switcher = {
                'file': 'f_putlocal'
                }
            cmd = res_switcher.get(cmd_params['resource'], "nosuchresource")
            getattr(CommandParser(self.config, self.agentid, self.issue),
                    str(cmd))(cmd_params)
        else:
            logging.error("CommandParser: No resource specified: {}".format(cmd_params))

    # Put()'ing content via <file> resource on server
    # {'put':
    #   {
    #       'resource': 'file',
    #       'location': '/path/to/file'  <===
    #   }
    # }
    def f_putlocal(self, cmd_params):
        logging.debug("CommandParser: Executing put on file: {}".
              format(cmd_params))

        if 'location' in cmd_params:
            crouter = CommandRouter(self.config, 'put_local_file', self.agentid,
                                    self.issue, cmd_params)
            thread = threading.Thread(target=crouter.run)
            thread.start()
        else:
            logging.error("CommandParser: No method specified: {}".format(cmd_params))


    # Exec()'ing <command> on server
    def execlocal(self, command):
        logging.info("CommandParser: Executing Local exec: {}".format(command))
        cmd_params = command[CommandParser.execlocal.__name__]
        if 'resource' in cmd_params:
            res_switcher = {
                'process': 'c_execlocal'
            }
            cmd = res_switcher.get(cmd_params['resource'], "nosuchresource")
            getattr(CommandParser(self.config, self.agentid, self.issue),
                    str(cmd))(cmd_params)
        else:
            logging.error("CommandParser: No resource specified: {}".format(cmd_params))

    # Exec()'ing <command> via <process> resource on server
    def c_execlocal(self, cmd_params):
        logging.debug("CommandParser: Executing Local exec -> process: {}".
              format(cmd_params))

        if 'command' in cmd_params:
            crouter = CommandRouter(self.config, 'exec_local_process', self.agentid,
                                    self.issue, cmd_params)
            thread = threading.Thread(target=crouter.run)
            thread.start()
        else:
            logging.error("CommandParser: No method specified: {}".format(cmd_params))

    def nosuchcommand(self, command):
        logging.error("CommandParser: No such command {}".format(command))

    def nosuchresource(self, command):
        logging.error("CommandParser: No such resource {}".format(command))

    def nosuchfilemethod(self, command):
        logging.error("CommandParser: No such file method {}".format(command))
