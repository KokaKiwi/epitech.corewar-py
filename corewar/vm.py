import random, subprocess
from collections import namedtuple
from resource import *
from .types import Champion

TEXT_EXECUTABLE     = './corewar_vm'
GRAPHIC_EXECUTABLE  = './corewar_vm-gui'

DATA_MAX_SIZE       = 512 * 1024 * 1024     # 512 Mio
STACK_MAX_SIZE      = 16 * 1024 * 1024      # 16 Mio

PositionalChampion = namedtuple('PositionalChampion', 'champion num')

def setlimits():
    data_soft, data_hard = getrlimit(RLIMIT_DATA)
    stack_soft, stack_hard = getrlimit(RLIMIT_STACK)
    setrlimit(RLIMIT_DATA, (DATA_MAX_SIZE, data_hard))
    setrlimit(RLIMIT_STACK, (STACK_MAX_SIZE, stack_hard))

class VM:
    def __init__(self, executable = TEXT_EXECUTABLE):
        self.executable = executable
        self.champions = []
        self.pos_champions = {}
        self.num = 1
    def add(self, champion):
        if isinstance(champion, (list, tuple)):
            for champ in champion:
                self.add(champ)
        elif isinstance(champion, (str)):
            self.add(Champion.fromfile(champion))
        elif isinstance(champion, (Champion)):
            champ = PositionalChampion(champion, self.num)
            self.champions.append(champ)
            self.pos_champions[self.num] = champ
            self.num += 1
    def shuffle(self):
        random.shuffle(self.champions)
    def launch(self, stdout = None, stderr = None):
        cmd = [self.executable]

        for champ in self.champions:
            cmd += ['-n', '%d' % (champ.num), champ.champion.path]

        process = subprocess.Popen(cmd, stdout = stdout, stderr = stderr, preexec_fn = setlimits)
        process.wait()
        winner_no = process.returncode
        winner = None
        if winner_no in self.pos_champions:
            winner = self.pos_champions[winner_no]
        return winner
