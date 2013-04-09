import struct, os

class Header:
    FORMAT = '>I128sQ2048s'
    def __init__(self, name, size, comment):
        self.name = name
        self.size = size
        self.comment = comment
    @staticmethod
    def fromfile(infile):
        header_data = infile.read(struct.calcsize(Header.FORMAT))
        (magic, prog_name, prog_size, comment) = struct.unpack(Header.FORMAT, header_data)
        return Header(prog_name.rstrip('\0'), prog_size, comment.rstrip('\0'))

class Champion:
    def __init__(self, path, filename, header, instructions = []):
        self.filename = filename
        self.path = path
        self.header = header
        self.instructions = instructions

        self.name = header.name.strip()
        self.comment = header.comment.strip()
    def encode(self):
        o = {}
        o['filename'] = self.filename
        o['path'] = self.path
        o['name'] = self.name
        o['comment'] = self.comment
        o['size'] = self.header.size
        return o
    @staticmethod
    def fromfile(cfile):
        if isinstance(cfile, (str)):
            cfilename = cfile
            cfile = open(cfilename, 'r')
            header = Header.fromfile(cfile)
            cfile.close()
            return Champion(cfilename, os.path.basename(cfilename), header)
        elif isinstance(cfile, (file)):
            header = Header.fromfile(cfile)
            return Champion(cfile.name, cfile.name, header)
        elif isinstance(cfile, (Champion)):
            return cfile
        return None
