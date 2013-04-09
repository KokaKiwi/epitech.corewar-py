import os, fnmatch, sys
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
