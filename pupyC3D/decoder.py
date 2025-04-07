# pupyC3D (c) by Antoine MARIN antoine.marin@univ-rennes2.fr
#
# pupyC3D is licensed under a
# Creative Commons Attribution-NonCommercial 4.0 International License.
#
# You should have received a copy of the license along with this
# work. If not, see <https://creativecommons.org/licenses/by-nc/4.0/>.

import struct as _struct

PROCESSOR_INTEL = 84
PROCESSOR_DEC = 85
PROCESSOR_MIPS = 86


class ProcStream(object):

    def __init__(self, handle):
        self.handle = handle

    def close_handle(self):
        self.handle.close()

    def get_int8(self):
        return _struct.unpack('b', self.handle.read(1))[0]

    def get_uint8(self):
        return _struct.unpack('B', self.handle.read(1))[0]

    def get_int16(self):
        return _struct.unpack('h', self.handle.read(2))[0]

    def get_uint16(self):
        return _struct.unpack('H', self.handle.read(2))[0]

    def get_int32(self):
        return _struct.unpack('i', self.handle.read(4))[0]

    def get_uint32(self):
        return _struct.unpack('I', self.handle.read(4))[0]

    def get_float(self):
        return _struct.unpack('f', self.handle.read(4))[0]

    def get_string(self, numChar):
        return self.handle.read(numChar).decode('latin1')

    def write_int8(self, data):
        val = _struct.pack('b', data)
        self.handle.write(val)

    def write_uint8(self, data):
        val = _struct.pack('B', data)
        self.handle.write(val)

    def write_uint16(self, data):
        val = _struct.pack('H', data)
        self.handle.write(val)

    def write_float(self, data):
        val = _struct.pack('f', data)
        self.handle.write(val)

    def write_string(self, data):
         self.handle.write(data.encode('ascii'))


class DecoderIntel(ProcStream):

    def __init__(self, handle):
        super(DecoderIntel, self).__init__(handle)


class DecoderDec(ProcStream):

    def __init__(self, handle):
        super(DecoderDec, self).__init__(handle)

    def get_float(self):
        tmp = self.handle.read(4)
        tmp = tmp[2:] + tmp[:2]
        val = _struct.unpack('f', tmp)[0]
        return val/4.


class DecoderMips(ProcStream):

    def __init__(self, handle):
        super(DecoderMips, self).__init__(handle)

    def get_int8(self):
        return _struct.unpack('>b', self.handle.read(1))[0]

    def get_uint8(self):
        return _struct.unpack('>B', self.handle.read(1))[0]

    def get_uint16(self):
        return _struct.unpack('>H', self.handle.read(2))[0]

    def get_float(self):
        return _struct.unpack('>f', self.handle.read(4))[0]