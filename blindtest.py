#!/usr/bin/env python2
import sys, argparse, os
from corewar import blindtest, util
from termcolor import colored, cprint

# Variables

winners = util.find('champs', '*.cor')

# Arguments

parser = argparse.ArgumentParser()
parser.add_argument('-n', '--nodisplay', action = 'store_false', dest = 'display')
parser.add_argument('-d', '--display', action = 'store_true', default = True)
parser.add_argument('-o', '--one', action = 'store_false', default = True)
parser.add_argument('-m', '--melee', action = 'store_true', default = False)
parser.add_argument('champion')

# Main

def writereports(outfile, reports, expected, win = True):
    for report in reports:
        if report.winner.filename == expected:
            winned = True
        else:
            winned = False
        if win == winned:
            outfile.write('- %s\n' % (', '.join(['%s (%s)' % (champ.name, champ.path) for champ in report.champs])))

def writelog(outfile, filename, win, defeat, ratio, reports):
    outfile.write('Ratio   : %s / %s / %s / %s\n\n' % ('Win: %d' % (win),
                                                       'Defeat: %d' % (defeat),
                                                       'Total: %s' % (win + defeat),
                                                       '%d%%' % (ratio)))

    outfile.write('Defeats :\n')
    writereports(outfile, reports, filename, False)

    outfile.write('\n')
    outfile.write('Wins    :\n')
    writereports(outfile, reports, filename, True)

def main(filename, display, one, melee):
    (win, defeat, reports) = blindtest.run(filename, winners, display, one = one, melee = melee)

    if win + defeat != 0:
        ratio = float(win) / (win + defeat) * 100
    else:
        ratio = 0
    if display:
        ratio_str = '%s / %s / %s / %s' % (colored('Win: %d' % (win), 'green', attrs = ['bold']),
                                           colored('Defeat: %d' % (defeat), 'red', attrs = ['bold']),
                                           colored('Total: %d' % (win + defeat), 'white', attrs = ['bold']),
                                           colored('%d%%' % (ratio), 'yellow', attrs = ['bold']))
        util.tprint('Ratio', ratio_str)
        print ''

    logfilename = os.path.basename(filename).replace('.cor', '.log')
    logfile = open('logs/%s' % (logfilename), 'w+')
    writelog(logfile, filename, win, defeat, ratio, reports)
    logfile.close()

if __name__ == "__main__":
    args = parser.parse_args()
    try:
        main(args.champion, args.display, args.one, args.melee)
    except KeyboardInterrupt, e:
        print 'Exiting...'
