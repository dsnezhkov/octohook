from  __future__ import unicode_literals
import delegator
#import subprocess
#import shlex

class PutLFileTask:
    def __init__(self, responder, data):
        self.responder = responder
        self.data = data
        self.file_name = self.data['location']

    def execute(self):
        file_data=""
        print("PutLFileTask Put() for agentid {} with data: {} ".format(
                    self.responder.agentid, self.data))

        try:
            with open(self.file_name, mode='rb') as f:
                file_data=f.read()
        except IOError as err:
            response_data = "Error reading the file {0}: {1}".format(
                self.file_name, err)

        response_data = "Will Put file {0} async. Check progress.".format(self.file_name)
        self.responder.setFile(self.file_name,file_data)
        self.responder.setData(",".join(response_data))


class ExecLProcessTask:
    def __init__(self, responder, data):
        self.responder = responder
        self.data = data

    def execute(self):
        print("ExecProcessTask Execute() for agentid {} with data: {} ".
              format(self.responder.agentid, self.data['command']))
        response_data=""

        try:
            so=""
            se=""
            se_conv_error=False
            so_conv_error=False
            rprocess=delegator.chain(self.data['command'])

            try:
                so=rprocess.out
            except UnicodeDecodeError as ude:
                so_conv_error=True

            try:
                se=rprocess.err
            except UnicodeDecodeError as ude:
                se_conv_error=True

            if so_conv_error:
                response_data += "Standard Output Conversion Fault"
            else:
                response_data += so

            if se_conv_error:
                response_data += "Standard Error Conversion Fault"
            else:
                if not so_conv_error and not se == so:
                    response_data += se

            print("Se: {} ".format(se))
            print("So: {} ".format(so))
            print("eq?: {} ".format(so == se))

        except IOError as ioe:
            response_data += "IOError {}. Check you command syntax".format(ioe)

        print("Sending to Responder data: {} ".format(response_data))
        self.responder.setData(response_data)
