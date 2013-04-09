#!/usr/bin/env python2
import sys, struct
import ply.lex as lex
import ply.yacc as yacc

"""
TODO:
    - Ajouter le support de sti/ldi.
    - Ajouter le support des boucles imbriquees.
"""

# Globales
labels_pos = {}
labels_loc = []
comments_loc = []
counter = 0
lineno = 1

HARDCODE = False

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

# Ops

class op_live:
    @staticmethod
    def size(args):
        return 5
    @staticmethod
    def encode(opcode, args):
        return struct.pack('>Bi', opcodes['live'], args[0].getValue())

class op_zjmp:
    @staticmethod
    def size(args):
        return 3
    @staticmethod
    def encode(opcode, args):
        return struct.pack('>BH', opcodes['zjmp'], args[0].getValue() & 0xffff)

class op_fork:
    @staticmethod
    def size(args):
        return 3
    @staticmethod
    def encode(args):
        return struct.pack('>BH', opcodes['fork'], args[0].getValue() & 0xffff)

class op_lfork:
    @staticmethod
    def size(args):
        return 3
    @staticmethod
    def encode(opcode, args):
        return struct.pack('>BH', opcodes['lfork'], args[0].getValue() & 0xffff)

class op_sti:
    @staticmethod
    def size(args):
        size = 2
        for arg in args:
            if isinstance(arg, (Register)):
                size += 1
            else:
                size += 2
        return size
    @staticmethod
    def codbyte(args):
        cod = 0b00000000
        offset = 0
        for arg in args:
            a = 0x00
            if isinstance(arg, Direct):
                a = 0x03
            elif isinstance(arg, Indirect):
                a = 0x03
            elif isinstance(arg, Register):
                a = 0x01
            cod |= (a << ((3 - offset) * 2))
            offset += 1
        return cod
    @staticmethod
    def encode(opcode, args):
        s = struct.pack('>BB', opcodes[opcode], op_default.codbyte(args))
        for arg in args:
            if isinstance(arg, (Register, Indirect)):
                s += arg.encode()
            elif isinstance(arg, (Direct)):
                s += struct.pack('>H', arg.getValue() & 0xffff)

class op_ldi(op_sti):
    pass

class op_default:
    @staticmethod
    def size(args):
        size = 2
        for arg in args:
            size += arg.size()
        return size
    @staticmethod
    def codbyte(args):
        cod = 0b00000000
        offset = 0
        for arg in args:
            a = 0x00
            if isinstance(arg, Direct):
                a = 0x02
            elif isinstance(arg, Indirect):
                a = 0x03
            elif isinstance(arg, Register):
                a = 0x01
            cod |= (a << ((3 - offset) * 2))
            offset += 1
        return cod
    @staticmethod
    def encode(opcode, args):
        s = struct.pack('>BB', opcodes[opcode], op_default.codbyte(args))
        for arg in args:
            s += arg.encode()
        return s

def get_op(opcode):
    if 'op_%s' % (opcode) in globals():
        return globals()['op_%s' % (opcode)]
    else:
        return op_default

# Functions

def fn_add(args):
    return reduce(lambda x, y: x + y, args)

def fn_sub(args):
    return reduce(lambda x, y: x - y, args)

def fn_mul(args):
    return reduce(lambda x, y: x * y, args)

def fn_div(args):
    return reduce(lambda x, y: x / y, args)

def fn_mod(args):
    return reduce(lambda x, y: x % y, args)

def fn_size(args):
    parsed = yacc.parse(args[0])
    if parsed != None:
        (labels, inst) = parsed
        return inst.size()
    else:
        return 0

def fn_encode(args):
    global comments_loc
    parsed = yacc.parse(args[0])
    if parsed != None:
        (labels, inst) = parsed
        old_comments_loc = comments_loc
        comments_loc = []
        s = ''.join(['%02x' % (ord(b)) for b in inst.encode()])
        comments_loc = old_comments_loc
        value = int(s, 16)

        hex_str = ' '.join(['%02x' % (ord(b)) for b in inst.encode()])
        comments_loc.append('%s -> %s' % (args[0], hex_str))
        return value
    else:
        return 0

# Classes

def sti_size(args):
    size = 2
    for arg in args:
        size += arg.size()
    return size

class Instruction:
    def __init__(self, opcode, args, labels = []):
        self.opcode = opcode
        self.args = args
        self.labels = labels
    def __str__(self):
        global comments_loc
        s = ''
        if len(self.labels) > 0 and not HARDCODE:
            for label in self.labels:
                s += '%s:' % (label)
                if label != self.labels[-1]:
                    s += ' '
            s += '\n'
        s1 = ''
        if not HARDCODE:
            s1 += '    '
        s1 += '%s' % (self.opcode)
        for arg in self.args:
            s1 += ' %s' % (arg)
            if arg != self.args[-1]:
                s1 += ','
        pre_size = len(s1)
        s += s1
        if len(comments_loc) > 0 and not HARDCODE:
            first = True
            for comment in comments_loc:
                if first:
                    s += '  # %s' % (comment)
                    first = False
                else:
                    s += '\n%*s  # %s' % (pre_size, ' ', comment)
        comments_loc = []
        return s
    def size(self):
        if self.opcode[0] == '.':
            return 0
        return get_op(self.opcode).size(self.args)
    def encode(self):
        if self.opcode[0] == '.':
            return ''
        return get_op(self.opcode).encode(self.opcode, self.args)

class Direct:
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return '%%%s' % (self.value)
    def size(self):
        return 4
    def encode(self):
        return struct.pack('>I', self.value.getValue())
    def getValue(self):
        return self.value.getValue()

class Indirect:
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return '%s' % (self.value)
    def size(self):
        return 2
    def encode(self):
        return struct.pack('>h', self.value.getValue())
    def getValue(self):
        return self.value.getValue()

class Register:
    def __init__(self, name):
        self.name = name
    def __str__(self):
        return '%s' % (self.name)
    def size(self):
        return 1
    def encode(self):
        return struct.pack('>B', int(self.name[1:]))
    def getValue(self):
        return self.name

class String:
    def __init__(self, content):
        self.content = content
    def __str__(self):
        return '"%s"' % (self.content)
    def getValue(self):
        encoded = self.content
        encoded = encoded.replace('\\\\', '\\')
        return encoded

class Offset:
    def __init__(self, value, offset):
        self.value = value
        self.offset = offset
    def __str__(self):
        return '%d' % (self.getValue())
    def getValue(self):
        return self.value.getValue() + self.offset.getValue()

class Function:
    def __init__(self, name, args):
        self.name = name
        self.args = args
    def __str__(self):
        return '%d' % (self.getValue())
    def getValue(self):
        return globals()['fn_%s' % (self.name)]([arg.getValue() for arg in self.args])

class Number:
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return '%d' % (self.value)
    def getValue(self):
        return self.value

class Label:
    def __init__(self, name):
        self.name = name
    def __str__(self):
        if not HARDCODE:
            return ':%s' % (self.name)
        else:
            return '%d' % (self.getValue())
    def getValue(self):
        return labels_pos[self.name] - counter

# Lexer

tokens = ('COMMA', 'COLON', 'LABEL', 'DIRECT', 'NUMBER', 'STRING', 'IDENTIFIER', 'LPAREN', 'RPAREN')

t_COMMA             = r','
t_COLON             = r':'
t_LABEL             = r'[a-zA-Z\._][a-zA-Z0-9\._]*:'
t_DIRECT            = r'\%'
t_NUMBER            = r'[+-]*[0-9]+'
t_STRING            = r'"[^"]*"|\'[^\']*\''
t_IDENTIFIER        = r'[a-zA-Z\._][a-zA-Z0-9\._]*'
t_LPAREN            = r'\('
t_RPAREN            = r'\)'
t_ignore_COMMENT    = r'[#][^\n]*'

t_ignore            = " \t"

def t_newline(t):
    r'\n+'
    t.lexer.lineno += t.value.count("\n")

def t_error(t):
    print "Illegal character '%s'" % (t.value[0])
    t.lexer.skip(1)

lex.lex()

# Parser

def p_line(t):
    'line : labels instruction'
    t[0] = (t[1], t[2])

def p_line_unique(t):
    'line : instruction'
    t[0] = ([], t[1])

def p_line_empty(t):
    'line : labels'
    t[0] = (t[1], None)

def p_labels(t):
    'labels : labels label'
    t[0] = t[1] + [t[2]]

def p_labels_empty(t):
    'labels : label'
    t[0] = [t[1]]

def p_label(t):
    'label : LABEL'
    name = t[1][:-1]
    labels_pos[name] = counter
    t[0] = name

def p_instruction(t):
    'instruction : IDENTIFIER args'
    t[0] = Instruction(t[1], t[2])

def p_instruction_empty(t):
    'instruction : IDENTIFIER'
    t[0] = Instruction(t[1], [])

def p_args(t):
    'args : args COMMA arg'
    t[0] = t[1] + [t[3]]

def p_args_unique(t):
    'args : arg'
    t[0] = [t[1]]

def p_arg_direct(t):
    'arg : DIRECT value'
    t[0] = Direct(t[2])

def p_arg_indirect(t):
    'arg : value'
    t[0] = Indirect(t[1])

def p_arg_register(t):
    'arg : IDENTIFIER'
    t[0] = Register(t[1])

def p_arg_string(t):
    'arg : STRING'
    t[0] = String(t[1][1:-1])

def p_value_number(t):
    'value : NUMBER'
    t[0] = Number(int(t[1]))

def p_value_label(t):
    'value : COLON IDENTIFIER'
    t[0] = Label(t[2])

def p_value_offset(t):
    'value : value LPAREN value RPAREN'
    t[0] = Offset(t[1], t[3])

def p_value_function(t):
    'value : IDENTIFIER LPAREN fn_args RPAREN'
    t[0] = Function(t[1], t[3])

def p_value_function_empty(t):
    'value : IDENTIFIER LPAREN RPAREN'
    t[0] = Function(t[1], [])

def p_fn_args(t):
    'fn_args : fn_args COMMA fn_value'
    t[0] = t[1] + [t[3]]

def p_fn_args_unique(t):
    'fn_args : fn_value'
    t[0] = [t[1]]

def p_fn_value(t):
    'fn_value : value'
    t[0] = t[1]

def p_fn_value_string(t):
    'fn_value : STRING'
    t[0] = String(t[1][1:-1])

def p_error(t):
    if t != None:
        print "Syntax error at line %d : %s" % (lineno, t.value)

yacc.yacc()

# Utils
def handle_line(infile, instructions, line):
    global counter, lineno, labels_loc
    parsed = yacc.parse(line)
    if parsed != None:
        (labels, inst) = parsed
        labels_loc += labels
        if inst != None:
            if inst.opcode[0] == '.' and 'special_%s' % (inst.opcode[1:]) in globals():
                globals()['special_%s' % (inst.opcode[1:])](infile, instructions, inst.args)
            else:
                inst.labels = labels_loc
                instructions.append(inst)
                labels_loc = []
            counter += inst.size()
    else:
        instructions.append(None)
    lineno += 1

# Specials

def special_loop(infile, instructions, args):
    loop_lines = []
    depth = 0
    while True:
        line = infile.readline()
        if not line:
            raise EOFError()
        trimmed = line.strip()
        if trimmed.startswith('.endloop'):
            break
        loop_lines.append(line)
    step = 1
    if len(args) >= 3:
        step = args[2].getValue()
    if len(args) == 1:
        start = 0
        end = args[0].getValue()
    elif len(args) >= 2:
        start = args[0].getValue()
        end = args[1].getValue() + step
    else:
        raise Exception()
    for i in range(start, end, step):
        for line in loop_lines:
            formatted = line.replace('$', '%d' % (i))
            handle_line(infile, instructions, formatted)

# K Assembler

def assemble(infile, outfile):
    global counter
    instructions = []
    while True:
        line = infile.readline()
        if not line:
            break
        handle_line(infile, instructions, line)

    counter = 0
    for inst in instructions:
        if inst != None:
            outfile.write('%s\n' % (inst))
            counter += inst.size()
        elif not HARDCODE:
            outfile.write('\n')
    if len(labels_loc) > 0 and not HARDCODE:
        s = ''
        for label in labels_loc:
            s += '%s:' % (label)
            if label != labels_loc[-1]:
                s += ' '
        s += '\n'
        outfile.write(s)
