#!/usr/bin/env python2
import sys
from corewar import disas

if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) == 2:
        infile = open(args[0], 'r')
        outfile = open(args[1], 'w+')
        disas.disassemble(infile, outfile)
        infile.close()
        outfile.close()
    else:
        print 'Usage: %s <infile> <outfile>' % (sys.argv[0])
