# pupyC3D (c) by Antoine MARIN antoine.marin@univ-rennes2.fr
#
# pupyC3D is licensed under a
# Creative Commons Attribution-NonCommercial 4.0 International License.
#
# You should have received a copy of the license along with this
# work. If not, see <https://creativecommons.org/licenses/by-nc/4.0/>.

import struct as _struct

# Processor type constants for C3D file format
PROCESSOR_INTEL = 84
PROCESSOR_DEC = 85
PROCESSOR_MIPS = 86


class ProcStream(object):
    """Binary stream processor for reading and writing C3D data.
    
    Provides methods for reading/writing various data types from/to
    binary streams with proper byte ordering and encoding.
    
    Attributes:
        handle: File handle for binary I/O operations
    """

    def __init__(self, handle):
        """Initialize stream processor.
        
        Args:
            handle: Binary file handle (opened in 'rb' or 'wb' mode)
        """
        self.handle = handle

    def close_handle(self):
        """Close the file handle."""
        self.handle.close()

    def get_int8(self):
        """Read signed 8-bit integer.
        
        Returns:
            int: Signed 8-bit integer value
        """
        return _struct.unpack('b', self.handle.read(1))[0]

    def get_uint8(self):
        """Read unsigned 8-bit integer.
        
        Returns:
            int: Unsigned 8-bit integer value
        """
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
        """Read 32-bit floating point value.
        
        Returns:
            float: 32-bit float value
        """
        return _struct.unpack('f', self.handle.read(4))[0]

    def get_string(self, numChar):
        """Read string of specified length.
        
        Args:
            numChar (int): Number of characters to read
            
        Returns:
            str: Decoded string using latin1 encoding
        """
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
        """Write string to binary stream.
        
        Args:
            data (str): String to write, encoded as ASCII
        """
        self.handle.write(data.encode('ascii'))


class DecoderIntel(ProcStream):
    """Intel processor-specific decoder for C3D files.
    
    Uses little-endian byte ordering (Intel/x86 format).
    """

    def __init__(self, handle):
        """Initialize Intel decoder.
        
        Args:
            handle: Binary file handle
        """
        super(DecoderIntel, self).__init__(handle)


class DecoderDec(ProcStream):
    """DEC processor-specific decoder for C3D files.
    
    Uses DEC-specific floating point format with special handling.
    """

    def __init__(self, handle):
        """Initialize DEC decoder.
        
        Args:
            handle: Binary file handle
        """
        super(DecoderDec, self).__init__(handle)

    def get_float(self):
        """Read DEC-format floating point value.
        
        DEC format requires byte swapping and scaling by 1/4.
        
        Returns:
            float: Converted DEC float value
        """
        tmp = self.handle.read(4)
        tmp = tmp[2:] + tmp[:2]
        val = _struct.unpack('f', tmp)[0]
        return val/4.


class DecoderMips(ProcStream):
    """MIPS processor-specific decoder for C3D files.
    
    Uses big-endian byte ordering (MIPS format).
    """

    def __init__(self, handle):
        """Initialize MIPS decoder.
        
        Args:
            handle: Binary file handle
        """
        super(DecoderMips, self).__init__(handle)

    def get_int8(self):
        """Read signed 8-bit integer with big-endian byte order.
        
        Returns:
            int: Signed 8-bit integer value
        """
        return _struct.unpack('>b', self.handle.read(1))[0]

    def get_uint8(self):
        return _struct.unpack('>B', self.handle.read(1))[0]

    def get_uint16(self):
        return _struct.unpack('>H', self.handle.read(2))[0]

    def get_float(self):
        """Read 32-bit float with big-endian byte order.
        
        Returns:
            float: 32-bit float value
        """
        return _struct.unpack('>f', self.handle.read(4))[0]