#!/usr/bin/env python2
import argparse, sys, json
from corewar import util, blindtest
from termcolor import colored, cprint
from corewar.types import Champion

# Arguments

parser = argparse.ArgumentParser()
parser.add_argument('-d', '--directory', action = 'append', default = [], help = 'Add champions directories.')
parser.add_argument('champions', nargs = '*')

# Tournoi

def ratio(win, defeat):
    if win + defeat != 0:
        return float(win) / (win + defeat) * 100
    return 0

def ratio_str(win, defeat):
    s = '%s / %s / %s / %s' % (colored('Win: %3d' % (win), 'green', attrs = ['bold']),
                               colored('Defeat: %3d' % (defeat), 'red', attrs = ['bold']),
                               colored('Total: %3d' % (win + defeat), 'white', attrs = ['bold']),
                               colored('%3d%%' % (ratio(win, defeat)), 'yellow', attrs = ['bold']))
    return s

def results(win, defeat, count, total):
    print ' %s %s (%s / %s)' % (colored('->', 'white', attrs = ['bold']),
                                ratio_str(win, defeat),
                                colored('%3d' % (count), 'yellow'),
                                colored('%3d' % (total), 'yellow'))

class Rank:
    def __init__(self, champion):
        self.champion = champion
        self.win = 0
        self.defeat = 0
    def ratio(self):
        return ratio(self.win, self.defeat)
    def encode(self):
        o = {}
        o['champion'] = self.champion.encode()
        o['win'] = self.win
        o['defeat'] = self.defeat
        o['ratio'] = self.ratio()
        return o


def main(champions):
    # Pre-selection
    ranks = {}
    count = 1
    total = len(champions)

    for champion in champions:
        ranks[champion] = Rank(Champion.fromfile(champion))

    util.tprint('Champions', '%d' % (len(champions)))
    print ''

    util.tprint('Pre-selections (one VS one)')
    for champion in champions:
        rank = ranks[champion]
        util.twrite('Champion', '%s' % (colored('%-32s' % (rank.champion.name), 'cyan', attrs = ['bold'])))
        (win, defeat, reports) = blindtest.run(champion, champions, False, one = True)
        results(win, defeat, count, total)
        rank.win += win
        rank.defeat += defeat

        count += 1
    print ''

    ladder = [key for (key, value) in sorted(ranks.items(), key = lambda item: item[1].ratio(), reverse = True)]

    melees = [
        (128, min(8, len(champions)))
    ]

    best = ladder[0:16]

    count = 1
    total = len(best)

    best = ladder[0:16]

    util.tprint('Matches (Melee)')
    for champion in best:
        rank = ranks[champion]
        util.twrite('Champion', '%s' % (colored('%-32s' % (rank.champion.name), 'cyan', attrs = ['bold'])))
        (win, defeat, reports) = blindtest.run(champion, best, False, melees = melees)
        results(win, defeat, count, total)
        rank.win += win
        rank.defeat += defeat

        count += 1
    print ''

    ranks = sorted(ranks.values(), key = lambda rank: rank.ratio(), reverse = True)
    winner = ranks[0]
    util.tprint('Winner', '%s %s %s' % (colored('%-32s' % (winner.champion.name), 'green', attrs = ['bold']),
                                        colored('->', 'white', attrs = ['bold']),
                                        ratio_str(winner.win, winner.defeat)))

    result_file = open('logs/result.json', 'w+')
    result_file.write(json.dumps([rank.encode() for rank in ranks], indent=4, separators=(',', ': '), sort_keys = False))
    result_file.close()

if __name__ == "__main__":
    args = parser.parse_args()
    util.Logger.install('tournoi.log', 'w+')
    champions = args.champions
    for d in args.directory:
        champions += util.find(d, '*.cor')
    champions = blindtest.remove_duplicate_champs(champions)
    if len(champions) > 0:
        try:
            main(champions)
        except KeyboardInterrupt, e:
            print 'Exiting...'
            sys.exit(0)
    else:
        print 'There are no champions!'
