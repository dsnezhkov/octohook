from  __future__ import unicode_literals
import glob
import subprocess
import shlex
import delegator
import codecs

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

        so=""
        se=""
        se_conv_error=False
        so_conv_error=False
        response_data=""

        try:
            so=rprocess.out
        except UnicodeDecodeError as ude:
            so_conv_error=True

        try:
            se=rprocess.err
        except UnicodeDecodeError as ude:
            se_conv_error=True

        if so_conv_error:
            response_data += "Output Conversion Error"
        else:
            response_data += so

        if se_conv_error:
            response_data += "Output Conversion Error"
        else:
            response_data += se

        print("sending to Responder data: {} ".format(response_data))
        self.responder.setData(response_data)
