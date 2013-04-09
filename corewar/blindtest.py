import os, random
from termcolor import colored, cprint
from subprocess import PIPE
from itertools import permutations
from .types import Champion
from .vm import VM
from . import util

"""
TODO:
    - Add melee
"""

# Utils

def remove_duplicate_champs(champs):
    unchamps = []
    basenames = []
    for champ in champs:
        if os.path.basename(champ) not in basenames:
            unchamps.append(champ)
            basenames.append(os.path.basename(champ))
    return unchamps

# Classes

class Report:
    def __init__(self, champs, winner):
        self.champs = champs
        self.winner = winner

# Variables
count = 0
total = 0

# Functions

def one(expected, champs, display, shuffle = False):
    global count, total
    vm = VM()
    vm.add(champs)

    if shuffle:
        vm.shuffle()

    if display:
        util.tprint('Battle', '%s / %s' % (colored('%d' % (count), 'yellow'), colored('%d' % (total), 'yellow')))
        util.tprint('Champions', ', '.join([colored(champ.champion.name, 'blue', attrs = ['bold']) for champ in vm.champions]))
    count += 1
    winner = vm.launch(stdout = PIPE)
    report = None
    if winner:
        if display:
            if winner.champion.filename == expected.filename:
                color = 'green'
            else:
                color = 'red'
            util.tprint('Winner', colored(winner.champion.name, color, attrs = ['bold']))
        report = Report(champs, winner.champion)

    if display:
        print ''
    return report

def run(filename, champ_filenames, display = True, **kwargs):
    global count, total
    champ_filenames = remove_duplicate_champs(champ_filenames)

    while filename in champ_filenames:
        champ_filenames.remove(filename)

    champion = Champion.fromfile(filename)
    champions = map(Champion.fromfile, champ_filenames)

    if display:
        util.tprint('Champion', colored(champion.name, 'cyan', attrs = ['bold']))
        print ''

    win = 0
    defeat = 0
    reports = []

    count = 1
    total = 0
    if 'one' in kwargs and kwargs['one']:
        total += len(champions) * 2
    if 'melee' in kwargs and kwargs['melee']:
        for (num, nchamps) in melees:
            total += num

    # One vs One
    if 'one' in kwargs and kwargs['one']:
        for champ in champions:
            report = one(champion, [champion, champ], display)
            if report:
                reports.append(report)
                if report.winner == champion:
                    win += 1
                else:
                    defeat += 1
            report = one(champion, [champ, champion], display)
            if report:
                reports.append(report)
                if report.winner == champion:
                    win += 1
                else:
                    defeat += 1

    # Melee
    if 'melees' in kwargs and kwargs['melees']:
        if isinstance(kwargs['melees'], (bool)):
            kwargs['melees'] = [(16, 8)]
        for (num, nchamps) in kwargs['melees']:
            for i in range(num):
                champs = list(random.sample(champions, nchamps - 1)) + [champion]
                report = one(champion, champs, display, True)
                if report:
                    reports.append(report)
                    if report.winner == champion:
                        win += 1
                    else:
                        defeat += 1

    return (win, defeat, reports)
