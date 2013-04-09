#!/usr/bin/env python2
import sys, argparse, os
from corewar import blindtest, util
from termcolor import colored, cprint

# Arguments

parser = argparse.ArgumentParser()
parser.add_argument('-n', '--nodisplay', action = 'store_false', dest = 'display', help = 'Don\'t display result messages.')
parser.add_argument('-d', '--display', action = 'store_true', default = True, help = 'Display result message [default=true].')
parser.add_argument('-w', '--winners', action = 'append', default = [], help = 'Add champions directories')
parser.add_argument('-o', '--one', action = 'store_false', default = True, help = 'Disable one vs one blindtests.')
parser.add_argument('-m', '--melee', action = 'store_true', default = False, help = 'Enable melee blindtests.')
parser.add_argument('champion')
parser.add_argument('champions', nargs = '*')

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

def main(filename, champions, display, one, melee):
    util.Logger.install(os.path.basename(filename).replace('.cor', '.stdout.log'), 'w+')
    (win, defeat, reports) = blindtest.run(filename, champions, display, one = one, melee = melee)

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
        champions = args.champions
        for wdir in args.winners:
            champions += util.find(wdir, '*.cor')
        main(args.champion, champions, args.display, args.one, args.melee)
    except KeyboardInterrupt, e:
        print 'Exiting...'
