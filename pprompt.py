from __future__ import unicode_literals
from prompt_toolkit import prompt
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.contrib.completers import WordCompleter
from prompt_toolkit.shortcuts import create_eventloop
from pygments.style import Style
from pygments.token import Token
from pygments.styles.default import DefaultStyle
import subprocess
import shlex
from threading import Thread
from time import sleep

gh_completer = WordCompleter(['execute', 'rtm', 'gshstart', 'gshstop'],
                               ignore_case=True)

class DocumentStyle(Style):
    styles = {
        Token.Menu.Completions.Completion.Current: 'bg:#00aaaa #000000',
        Token.Menu.Completions.Completion: 'bg:#008888 #ffffff',
        Token.Menu.Completions.ProgressButton: 'bg:#003333',
        Token.Menu.Completions.ProgressBar: 'bg:#00aaaa',
    }
    styles.update(DefaultStyle.styles)

def get_bottom_toolbar_tokens(cli):
    return [(Token.Toolbar, ' Info ')]




stuff = False

def wait_a_bit():
    global stuff
    while True:
        sleep(2)
        stuff = True


def print_a_bit(context):
    global stuff
    while not context.input_is_ready():
        if stuff:
            print('got stuff')
            stuff = False


def main():
    history = InMemoryHistory()

    t = Thread(target=wait_a_bit)
    t.daemon = True
    t.start()

    while True:
        text = prompt('> ', completer=gh_completer,
                      style=DocumentStyle, history=history,
                      eventloop=create_eventloop(inputhook=print_a_bit),
                      get_bottom_toolbar_tokens=get_bottom_toolbar_tokens,
                      patch_stdout=True)
        print('You entered:', text)
        #process = subprocess.Popen(
        #    shlex.split(text),
        #    stdout=subprocess.PIPE,  stderr=subprocess.PIPE, shell=True)
        #so, se = process.communicate()
        #print(so)
        #print(se)

    print('GoodBye!')

if __name__ == '__main__':
    main()
