#!/usr/bin/env python2
from corewar.vm import VM

vm = VM('./corewar_vm-gui')

winners = [
    'champs/2001/forky+bedo/Forky+bedo.cor',
    'champs/2001/paki/Paki.cor',
    'champs/La_Vilaine_Du_Marais.cor',
    'champs/Octobre_Rouge_V4.2.cor',
    'champs/jc.cor',
    'champs/toto.cor',
    'champs/raid_aerien.cor'
]

vm.add('luffy.cor')
vm.add('champs/toto.cor')
# vm.add(winners)

winner = vm.launch()
if winner:
    print winner.champion.name
