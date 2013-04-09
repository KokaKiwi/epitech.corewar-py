import os, fnmatch, sys, re
from termcolor import colored, cprint

def find(folder, pattern):
    matches = []
    for root, dirnames, filenames in os.walk(folder):
      for filename in fnmatch.filter(filenames, pattern):
          matches.append(os.path.join(root, filename))
    return matches

def tstr(label, message = None):
    s = ''
    s += colored(':: ', 'grey', attrs = ['bold'])
    s += colored('%-10s' % (label), 'yellow', attrs = ['bold'])
    if message:
        s += ' : '
        s += message
    return s

def twrite(label, message = None):
    sys.stdout.write(tstr(label, message))
    sys.stdout.flush()

def tprint(label, message = None):
    print tstr(label, message)

strip_ANSI_escape_sequences_sub = re.compile(r'\x1b\[[;\d]*[A-Za-z]', re.VERBOSE).sub

def strip_ANSI_escape_sequences(s):
    return strip_ANSI_escape_sequences_sub("", s)

strip_colors = strip_ANSI_escape_sequences

class Logger(object):
    def __init__(self, filename = 'stdout.log', mode = 'a'):
        self.term = sys.stdout
        self.logfile = open('logs/%s' % (filename), mode)
    def write(self, message):
        self.term.write(message)
        self.logfile.write(strip_colors(message))
    def flush(self):
        self.term.flush()
        self.logfile.flush()
    @staticmethod
    def install(*args, **kwargs):
        sys.stdout = Logger(*args, **kwargs)
