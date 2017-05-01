from  __future__ import unicode_literals
import glob
import subprocess
import shlex
import delegator

class PutLFileTask:
    def __init__(self, responder, data):
        self.responder = responder
        self.data = data

    def execute(self):
        print("PutLFileTask Execute() for agentid {} with data: {} ".format(
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
