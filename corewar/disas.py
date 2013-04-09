import sys, struct
from collections import namedtuple

def enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    return type('Enum', (), enums)

opcodes = {
    'live'  : 0x01,
    'ld'    : 0x02,
    'st'    : 0x03,
    'add'   : 0x04,
    'sub'   : 0x05,
    'and'   : 0x06,
    'or'    : 0x07,
    'xor'   : 0x08,
    'zjmp'  : 0x09,
    'ldi'   : 0x0a,
    'sti'   : 0x0b,
    'fork'  : 0x0c,
    'lld'   : 0x0d,
    'lldi'  : 0x0e,
    'lfork' : 0x0f,
    'aff'   : 0x10
}
opcodes = {v:k for k, v in opcodes.items()}
offsets = {}
offsets_values = []

types = enum('REGISTER', 'DIRECT','INDIRECT')

HEADER_FORMAT = '>I128sQ2048s'

LABELS = True
COMMENTS = True

# Utils

def decode_args(cod):
    args = []
    for i in range(4):
        carg = (cod >> ((3 - i) * 2)) & 0x03
        if carg == 0x00:
            args.append(None)
        elif carg == 0x01:
            args.append(types.REGISTER)
        elif carg == 0x02:
            args.append(types.DIRECT)
        elif carg == 0x03:
            args.append(types.INDIRECT)
    return args

# Decode

def decode(value):
    comments = []
    if value > 0:
        comments.append('%08x' % (value))
        while value & 0xff000000 == 0:
            value = value << 8
        opcode = (value & 0xff000000) >> 24
        if opcode in opcodes:
            opcode_str = opcodes[opcode]
            s = '%s' % (opcode_str)
            if opcode_str in ('live'):
                s += ' 0x%06x' % (value & 0xffffff)
            elif opcode_str in ('zjmp', 'fork', 'lfork'):
                val = (value & 0x00ffff00) >> 8
                val = struct.unpack('<h', struct.pack('<H', val & 0xffff))[0]
                s += ' %d' % (val)
            else:
                cod = (value & 0x00ff0000) >> 16
                targs = decode_args(cod)
                for targ in targs:
                    if targ == types.REGISTER:
                        s += ' reg'
                    elif targ == types.DIRECT:
                        s += ' dir'
                    elif targ == types.INDIRECT:
                        s += ' ind'
            comments.append(s)
    return comments

# Classes

class Instruction:
    def __init__(self, opcode, args):
        self.opcode = opcode
        self.args = args
        self.labels = []
        self.comments = []
    def __str__(self):
        s = ''
        if len(self.labels) > 0 and LABELS:
            s += '\n'
            for label in self.labels:
                s += '%s:' % (label)
                if label != self.labels[-1]:
                    s += ' '
            s += '\n'
        s1 = '    %s' % (opcodes[self.opcode])
        for arg in self.args:
            s1 += ' %s' % (arg)
            if arg != self.args[-1]:
                s1 += ','
        pre_size = len(s1)
        s += s1
        if len(self.comments) > 0 and COMMENTS:
            first = True
            for comment in self.comments:
                if first:
                    s += '  # %s' % (comment)
                    first = False
                else:
                    s += '\n%*s  # %s' % (pre_size, ' ', comment)
        return s
    def resolve(self):
        for arg in self.args:
            arg.resolve(self)

class Direct:
    def __init__(self, value):
        self.value = value
        self.type = types.DIRECT
    def __str__(self):
        return '%%%s' % (self.value)
    def resolve(self, inst):
        if opcodes[inst.opcode] in ('ld'):
            inst.comments += decode(self.value)
        if opcodes[inst.opcode] in ('sti', 'ldi') and LABELS:
            roffset = inst.offset + self.value
            last_offset = -1
            for ioffset in offsets_values:
                if ioffset <= roffset:
                    last_offset = ioffset
                else:
                    break
            if last_offset != -1 and last_offset != inst.offset:
                label_name = 'label_%d' % (last_offset)
                instr = offsets[last_offset]
                if label_name not in instr.labels:
                    instr.labels.append(label_name)
                val = roffset - last_offset
                self.value = ':%s' % (label_name)
                if val != 0:
                    self.value += '(%d)' % (val)
        if opcodes[inst.opcode] in ('st', 'fork', 'lfork', 'zjmp') and LABELS:
            roffset = inst.offset + self.value
            last_offset = -1
            for ioffset in offsets_values:
                if ioffset <= roffset:
                    last_offset = ioffset
                else:
                    break
            if last_offset != -1 and last_offset != inst.offset:
                label_name = 'label_%d' % (last_offset)
                instr = offsets[last_offset]
                if label_name not in instr.labels:
                    instr.labels.append(label_name)
                val = roffset - last_offset
                self.value = ':%s' % (label_name)
                if val != 0:
                    self.value += '(%d)' % (val)

class Indirect:
    def __init__(self, value):
        self.value = value
        self.type = types.INDIRECT
    def __str__(self):
        return '%s' % (self.value)
    def resolve(self, inst):
        if LABELS:
            roffset = inst.offset + self.value
            last_offset = -1
            for ioffset in offsets_values:
                if ioffset <= roffset:
                    last_offset = ioffset
                else:
                    break
            if last_offset != -1 and last_offset != inst.offset:
                label_name = 'label_%d' % (last_offset)
                instr = offsets[last_offset]
                if label_name not in instr.labels:
                    instr.labels.append(label_name)
                val = roffset - last_offset
                self.value = ':%s' % (label_name)
                if val != 0:
                    self.value += '(%d)' % (val)

class Register:
    def __init__(self, num):
        self.num = num
        self.type = types.REGISTER
    def __str__(self):
        return 'r%s' % (self.num)
    def resolve(self, inst):
        pass

# Opcodes

def op_live(opcode, infile):
    value = struct.unpack('>i', infile.read(4))[0]
    args = [Direct(value)]
    return Instruction(opcode, args)

def op_zjmp(opcode, infile):
    value = struct.unpack('>h', infile.read(2))[0]
    args = [Direct(value)]
    return Instruction(opcode, args)

def op_fork(opcode, infile):
    value = struct.unpack('>h', infile.read(2))[0]
    args = [Direct(value)]
    return Instruction(opcode, args)

def op_lfork(opcode, infile):
    value = struct.unpack('>h', infile.read(2))[0]
    args = [Direct(value)]
    return Instruction(opcode, args)

def op_sti(opcode, infile):
    cod = ord(infile.read(1))
    targs = decode_args(cod)
    args = []
    for targ in targs:
        if targ == types.REGISTER:
            args.append(Register(ord(infile.read(1))))
        elif targ == types.DIRECT:
            args.append(Direct(struct.unpack('>h', infile.read(2))[0]))
        elif targ == types.INDIRECT:
            args.append(Direct(struct.unpack('>h', infile.read(2))[0]))
    return Instruction(opcode, args)

def op_ldi(opcode, infile):
    return op_sti(opcode, infile)

def op_default(opcode, infile):
    cod = ord(infile.read(1))
    targs = decode_args(cod)
    args = []
    for targ in targs:
        if targ == types.REGISTER:
            args.append(Register(ord(infile.read(1))))
        elif targ == types.DIRECT:
            args.append(Direct(struct.unpack('>i', infile.read(4))[0]))
        elif targ == types.INDIRECT:
            args.append(Indirect(struct.unpack('>h', infile.read(2))[0]))
    return Instruction(opcode, args)

# K Disassembler

def disassemble(infile, outfile):
    header_data = infile.read(struct.calcsize(HEADER_FORMAT))
    (magic, prog_name, prog_size, comment) = struct.unpack(HEADER_FORMAT, header_data)
    prog_name = prog_name.rstrip('\0')
    comment = comment.rstrip('\0')

    outfile.write('    .name "%s"\n' % (prog_name))
    outfile.write('    .comment "%s"\n\n' % (comment))

    instructions = []
    start_offset = infile.tell()
    cur_offset = 0
    while True:
        opcode = infile.read(1)
        if len(opcode) == 0:
            break
        opcode = ord(opcode)
        if opcode and opcode in opcodes:
            opcode_str = opcodes[opcode]
            if 'op_%s' % (opcode_str) in globals():
                inst = globals()['op_%s' % (opcode_str)](opcode, infile)
            else:
                inst = op_default(opcode, infile)
            inst.offset = cur_offset
            inst.comments.append(inst.offset)
            offsets[inst.offset] = inst
            offsets_values.append(inst.offset)
            instructions.append(inst)
        cur_offset = infile.tell() - start_offset

    offsets_values.sort()

    for inst in instructions:
        inst.resolve()

    for inst in instructions:
        outfile.write('%s\n' % (inst))
