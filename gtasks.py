import glob
import subprocess
import shlex
import delegator

class FileTask:
    def __init__(self, responder, data):
        self.responder = responder
        self.data = data

    def execute(self):
        print("FileTask Execute() for agentid {} with data: {} ".format(
                    self.responder.agentid, self.data))
        response_data = glob.glob(self.data['location'])
        print("{}".format(response_data))

        self.responder.setData(",".join(response_data))


class ExecLProcessTask:
    def __init__(self, responder, data):
        self.responder = responder
        self.data = data

    def execute(self):
        print("ExecProcessTask Execute() for agentid {} with data: {} ".
              format(self.responder.agentid, self.data['command']))
        rprocess=delegator.chain(self.data['command'])

        so=None
        se=None
        response_data=""
        encoder_error=False

        try:
            so=rprocess.out
            se=rprocess.err
        except UnicodeDecodeError as uee:
            se="Error in Unicode Decoding of input: " + uee.message
            encoder_error=True

        if rprocess.subprocess.exitstatus != 0 or encoder_error:
            response_data=se
        else:
            response_data=so

        print("sending to Repnder data: {} ".format(response_data))
        self.responder.setData(response_data)

    def execute_shell(self):
        print("ExecProcessTask Execute() for agentid {} with data: {} ".format(
                    self.responder.agentid, self.data))

        process = subprocess.Popen(
            shlex.split(self.data['command']),
            stdout=subprocess.PIPE,  stderr=subprocess.PIPE, shell=True)
        so, se = process.communicate()

        response_data = ""
        if process.returncode == 0:
            # some utilities (eg. curl) report progress on stderr, not error
            if len(se) != 0:
                response_data += se

            print("Process success: ".format(process.returncode))
            response_data += so
        else:
            print("Process error: ".format(process.returncode))
            response_data = se

        print("Response: {}".format(response_data))

        self.responder.setData(response_data)
