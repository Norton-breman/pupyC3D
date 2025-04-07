# pupyC3D (c) by Antoine MARIN antoine.marin@univ-rennes2.fr
#
# pupyC3D is licensed under a
# Creative Commons Attribution-NonCommercial 4.0 International License.
#
# You should have received a copy of the license along with this
# work. If not, see <https://creativecommons.org/licenses/by-nc/4.0/>.

import os
import warnings
import struct
import math
import numpy as np
from decoder import *

#Base class for Parameters and ParameterGroups
class Metadata:

    def __init__(self, name:str, group_id:int):
        self.name = name
        self.description = ''
        self.group_id = group_id

    def read_from_buffer(self, buffer:ProcStream):
        return 0

    def write_to_buffer(self, buffer: ProcStream):
        buffer.write_int8(len(self.name))
        buffer.write_int8(self.group_id)
        buffer.write_string(self.name)

    def _get_offset(self):
        return 2 + len(self.description) + 1

    def get_size(self):
        return 2 + len(self.name) + self._get_offset()


class Parameter(Metadata):

    def __init__(self, name:str, group_id:int):
        super(Parameter, self).__init__(name, group_id)
        self.data_type = 0
        self.value = None

    def read_from_buffer(self, buffer:ProcStream):
        offset = 0
        self.data_type = buffer.get_int8()
        offset += 1
        n_dim = buffer.get_int8()
        offset += 1
        if n_dim == 0:
            if self.data_type == 1:
                self.value = buffer.get_int8()
            elif self.data_type == 2:
                self.value = buffer.get_uint16()
            elif self.data_type == 4:
                self.value = buffer.get_float()
            data_size = abs(self.data_type)
        else:
            dims = []
            for i in range(n_dim):
                dims.append(buffer.get_uint8())
                offset += 1
            prod = math.prod(dims[:n_dim])
            if self.data_type == -1:
                if len(dims) >= 2:
                    row = 1
                    inc2 = 1
                    while inc2 < n_dim:
                        row *= dims[inc2]
                        inc2 += 1
                    data = []
                    for i in range(row):
                        data.append(buffer.get_string(dims[0]).strip())
                    data = np.array(data)
                    if data.size == 0:
                        data = np.empty((dims[:]), str)
                else:
                    data = np.array([buffer.get_string(prod).strip()])
            elif self.data_type == 1:
                data = np.array([buffer.get_int8() for _ in range(prod)]).reshape(dims)
            elif self.data_type == 2:
                data = np.array([buffer.get_uint16() for _ in range(prod)]).reshape(dims)
            elif self.data_type == 4:
                data = np.array([buffer.get_float() for _ in range(prod)]).reshape(dims)
            else:
                data = np.array([])

            self.value = data
            data_size = prod * abs(self.data_type)
        offset += data_size
        desc_len = buffer.get_uint8()
        self.description = buffer.get_string(desc_len)
        offset += desc_len
        return offset

    def write_to_buffer(self, buffer: ProcStream, last_entry=False):
        super(Parameter, self).write_to_buffer(buffer)
        if last_entry:
            offset = 0
        else:
            offset = self._get_offset()
        buffer.write_uint16(offset)
        buffer.write_int8(self.data_type)

        dims = self.__get_dim()
        n_dim = len(dims)
        buffer.write_int8(n_dim)
        if n_dim == 0:
            if self.data_type == 1:
                buffer.write_int8(self.value)
            elif self.data_type == 2:
                buffer.write_uint16(self.value)
            elif self.data_type == 4:
                buffer.write_float(self.value)
        else:
            for each in dims:
                buffer.write_uint8(each)
            data = self.value.flatten()
            for each in data:
                if self.data_type == 1:
                    buffer.write_int8(each)
                elif self.data_type == 2:
                    buffer.write_uint16(each)
                elif self.data_type == 4:
                    buffer.write_float(each)
                elif self.data_type == -1:
                    buffer.write_string(each.ljust(dims[0]))

        buffer.write_uint8(len(self.description))
        buffer.write_string(self.description)

    def _get_offset(self):
        offset = 2 + 1 + 1 #offset, data_type, dim
        if not isinstance(self.value, np.ndarray):
            offset += self.data_type#value
        else:
            # n_dimension
            dims = self.__get_dim()
            n_dim = len(dims)
            offset += n_dim
            # data size
            prod = math.prod(dims[:n_dim])
            data_size = prod * abs(self.data_type)
            offset += data_size

        offset +=1 # desc length
        offset += len(self.description) #desc
        return offset

    def __get_dim(self):
        if not isinstance(self.value, np.ndarray):
            dims  = []
        else:
            dims = self.value.shape
            if self.data_type == -1:
                if dims[0] == 1:
                    dims = [len(self.value[0])]
                else:
                    if self.value.size > 0:
                        d1 = max([len(x) for x in self.value])
                        dims = [d1, dims[0]]
        return dims


class ParameterGroup(Metadata):

    def __init__(self, name:str, group_id:int):
        super(ParameterGroup, self).__init__(name, group_id)
        self.parameters = dict()

    def add_parameter(self, name)->Parameter:
        if name not in self.parameters:
            param = Parameter(name, -self.group_id)
            self.parameters[param.name] = param
            return param
        warnings.warn('Parameter %s already exists' %name)
        return self.parameters[name]

    def remove_parameter(self, name):
        if name in self.parameters:
            self.parameters.pop(name)
            return True
        return False

    def read_from_buffer(self, buffer:ProcStream):
        desc_len = buffer.get_uint8()
        offset = 1
        desc = buffer.get_string(desc_len)
        offset += desc_len
        self.description = desc
        return offset

    def write_to_buffer(self, buffer: ProcStream, last_entry=False):
        super(ParameterGroup, self).write_to_buffer(buffer)
        # offset = 2 + len(self.description) + 1
        offset = self._get_offset()
        buffer.write_uint16(offset)
        buffer.write_uint8(len(self.description))
        buffer.write_string(self.description)


class C3DFile:

    def __init__(self, filename:str=''):
        self.filename = filename
        self.__decoder = None
        self.header = dict()
        self.groups = dict()
        self.data = dict()
        if os.path.exists(filename):
            self.read_file()

    def read_file(self):
        if os.path.exists(self.filename):
            with open(self.filename, 'rb') as handle:
                self.__read_header(handle)
                self.__read_parameters(handle)
                self.__read_data(handle)
        else:
            raise FileNotFoundError(self.filename)

    def write(self, filename:str='', **kwargs):
        overwrite = kwargs.get('overwrite', True)
        if filename == '':
            filename = self.filename
        if os.path.exists(filename) and not overwrite:
            warnings.warn('File %s already exist. If you wish to overwrite it set ''overwrite'' argument to True' %filename)
            return
        with open(filename, 'wb') as handle:
            self.__write_header(handle)
            self.__write_parameters(handle)
            self.__write_data(handle)

    def add_parameter_group(self, name, gid=0)->ParameterGroup:
        assert(gid <= 0)
        if gid == 0:
            g = self.get_parameter_group(name)
        else:
            g = self.get_parameter_group(gid)
        if g is not None:
            return None
        if gid == 0:
            ids = list(self.groups.keys())
            gid = ids[0]
            # find first missing id
            for number in ids:
                if number != gid:
                    break
                gid -= 1
        self.groups[gid] = ParameterGroup(name, gid)
        return self.groups[gid]

    def remove_parameter_group(self, group)->bool:
        g = self.get_parameter_group(group)
        if g is not None:
            self.groups.pop(g.group_id)
            return True
        return False

    def get_parameter_group(self, group_id)->ParameterGroup:
        if isinstance(group_id, int):
            return self.groups.get(group_id, None)
        elif isinstance(group_id, str):
            g = {v.name: v for v in self.groups.values()}
            return g.get(group_id, None)
        else:
            raise TypeError('Argument ''group_id'' should be either str or int')

    def add_parameter(self, name, gid):
        group = self.get_parameter_group(gid)
        if group is not None:
            param = group.add_parameter(name)
            return param
        return None

    def remove_parameter(self, name, group_id):
        g = self.get_parameter_group(group_id)
        if g is not None:
            return g.remove_parameter(name)
        return False

    def get_parameter(self, group_id, param_name):
        g = self.get_parameter_group(group_id)
        return g.parameters.get(param_name, None)

    def __read_header(self, handle):
        handle.seek(0)
        # check if it's a c3d file
        self.header['parameter_block'], magic = struct.unpack('BB', handle.read(2))
        if magic != 80:
            warnings.warn('%s is not a c3d file!' %self.filename)
            return
        # go to the start of the parameter block
        handle.seek((self.header['parameter_block'] - 1) * 512 + 3)
        # find the good encoder
        processor = struct.unpack('B', handle.read(1))[0]
        if processor == PROCESSOR_INTEL:
            self.__decoder = DecoderIntel(handle)
        elif processor == PROCESSOR_DEC:
            self.__decoder = DecoderDec(handle)
        elif processor == PROCESSOR_MIPS:
            self.__decoder = DecoderMips(handle)

        #  start reading header
        handle.seek(2)
        self.header['point_count'] = self.__decoder.get_uint16()
        self.header['analog_count'] = self.__decoder.get_uint16()
        self.header['first_frame'] = self.__decoder.get_uint16()
        self.header['last_frame'] = self.__decoder.get_uint16()
        self.header['max_gap'] = self.__decoder.get_uint16()
        self.header['scale_factor'] = self.__decoder.get_float()
        self.header['data_block'] = self.__decoder.get_uint16()
        self.header['analog_per_frame'] = self.__decoder.get_uint16()
        if self.header['analog_per_frame'] > 0 and self.header['analog_count'] > 0:
            self.header['analog_count'] /= self.header['analog_per_frame']
            self.header['analog_count'] = int(self.header['analog_count'])
        if self.header['analog_per_frame'] == 0:
            self.header['analog_per_frame'] = 1
        self.header['frame_rate'] = self.__decoder.get_float()

        handle.read(270)
        label_range_section = self.__decoder.get_uint16()
        label_first_block = self.__decoder.get_uint16()
        label_event_fmt = self.__decoder.get_uint16()  # 2 or 4 char
        if label_event_fmt == 12345:
            self.header['long_event_labels'] = True
        else:
            self.header['long_event_labels'] = False
        num_events = self.__decoder.get_uint16()

        if num_events > 0:
            tmp_event = []
            self.header['events'] = dict()
            handle.read(2)
            for i in range(num_events):
                event_time = self.__decoder.get_float()
                event_frame = event_time * self.header['frame_rate'] + 1
                tmp_event.append([event_time, event_frame])
            handle.seek(198 * 2)
            if self.header['long_event_labels']:
                num_char = 4
            else:
                num_char = 2
            for i in range(num_events):
                name = self.__decoder.get_string(num_char)
                self.header['events'][name] = tmp_event[i]

    def __write_header(self, handle):
        if self.__decoder == 0:
            self.__decoder = DecoderIntel(handle)
        else:
            self.__decoder.handle = handle

        handle.seek(0)
        self.__decoder.write_uint8(self.header['parameter_block'])
        self.__decoder.write_uint8(80)

        if isinstance(self.__decoder, DecoderIntel):
            processor = PROCESSOR_INTEL
        elif isinstance(self.__decoder, DecoderDec):
            processor = PROCESSOR_DEC
        elif isinstance(self.__decoder, DecoderMips):
            processor = PROCESSOR_MIPS
        else:
            raise ValueError('Processor not supported')

        handle.seek((self.header['parameter_block'] - 1) * 512 + 3)
        self.__decoder.write_uint8(processor)

        handle.seek(2)
        self.__decoder.write_uint16(self.header['point_count'])
        if self.header['analog_per_frame'] > 0 and self.header['analog_count'] > 0:
            analog_count = self.header['analog_count']* self.header['analog_per_frame']
        else:
            analog_count = self.header['analog_count']
        self.__decoder.write_uint16(analog_count)
        self.__decoder.write_uint16(self.header['first_frame'])
        self.__decoder.write_uint16(self.header['last_frame'])
        self.__decoder.write_uint16(self.header['max_gap'])
        self.__decoder.write_float(self.header['scale_factor'])
        data_block = self.__get_parameters_blocknum() + 2
        self.__decoder.write_uint16(data_block)
        if self.header['analog_per_frame'] == 1:
            analog_per_frame = 0
        else:
            analog_per_frame = self.header['analog_per_frame']
        self.__decoder.write_uint16(analog_per_frame)
        self.__decoder.write_float(self.header['frame_rate'])

        # TODO : Add event list

    def __read_parameters(self, handle):
        handle.seek((self.header['parameter_block'] - 1) * 512)
        handle.read(4)
        last_entry = False
        while not last_entry:
            nb_char_label = self.__decoder.get_int8()
            if nb_char_label == 0:
                break
            group_id = self.__decoder.get_int8()
            name = self.__decoder.get_string(abs(nb_char_label))
            if group_id < 0:#group
                current = self.add_parameter_group(name, group_id)
            else:#parameter
                group = self.get_parameter_group(-group_id)
                if group is not None:
                    current = group.add_parameter(name)
                else :
                    current = Parameter(name, group_id)

            offset = self.__decoder.get_uint16()
            if offset == 0:
                last_entry = True
            offset -= 2
            offset -= current.read_from_buffer(self.__decoder)

    def __write_parameters(self, handle):
        handle.seek((self.header['parameter_block'] - 1) * 512 + 2)
        self.__decoder.write_uint8(self.__get_parameters_blocknum())
        handle.seek((self.header['parameter_block'] - 1) * 512+4)
        groups = list(self.groups.values())
        for g in groups:
            g.write_to_buffer(self.__decoder)
        for group in groups:
            params = list(group.parameters.values())
            for param in params:
                if group == groups[-1] and param == params[-1]:
                    param.write_to_buffer(self.__decoder, True)
                else:
                    param.write_to_buffer(self.__decoder)

    def __get_parameters_blocknum(self):
        parameters_size = 0
        for g in self.groups.values():
            parameters_size += g.get_size()
            for p in g.parameters.values():
                parameters_size += p.get_size()
        return math.ceil(parameters_size/512)

    def __read_data(self, handle):
        handle.seek((512 * (self.header['data_block'] - 1)))
        nb_frames = self.header['last_frame'] - self.header['first_frame'] + 1
        point_used = self.header['point_count']
        if point_used > 0:
            scale = abs(self.header['scale_factor'])
            is_float = self.header['scale_factor'] < 0
            point_scale = [scale, 1][is_float]
            names_param = self.get_parameter('POINT', 'LABELS')
            marker_names = names_param.value.tolist()
            self.data['POINTS'] = dict()
            for each in marker_names:
                self.data['POINTS'][each] = np.zeros([nb_frames, 4])

        analog_used = self.header['analog_count']
        if analog_used > 0:
            offsets = np.zeros((analog_used,), int)
            param = self.get_parameter('ANALOG', 'OFFSET')
            if param is not None:
                offsets = param.value

            scales = np.ones((analog_used,), float)
            param = self.get_parameter('ANALOG', 'SCALE')
            if param is not None:
                scales = param.value

            gen_scale = 1.
            param = self.get_parameter('ANALOG', 'GEN_SCALE')
            if param is not None:
                gen_scale = param.value
            names_param = self.get_parameter('ANALOG', 'LABELS')
            if names_param is not None:
                analog_names = names_param.value.tolist()

            self.data['ANALOGS'] = dict()
            for each in analog_names:
                self.data['ANALOGS'][each] = np.zeros([nb_frames*self.header['analog_per_frame'], 1])

        rot_param = self.get_parameter_group('ROTATION')
        if rot_param is not None:
            names_param = self.get_parameter('ROTATION', 'LABELS')
            rotation_names = names_param.value.tolist()
            self.data['ROTATIONS'] = dict()
            for each in rotation_names:
                self.data['ROTATIONS'][each] = np.zeros([nb_frames, 4, 4])

        for i in range(nb_frames):
            if point_used > 0:
                self.__read_point_frame(i, is_float, point_scale, marker_names)
            if rot_param is not None:
                self.__read_rotation_frame(i, rotation_names)
            if analog_used >0:
                self.__read_analog_frame(i, is_float, self.header['analog_per_frame'], offsets, scales, gen_scale, analog_names)

    def __read_point_frame(self, frame_num, is_float, point_scale, marker_names):
        for j, m in enumerate(marker_names):
            if is_float:
                p = np.array([self.__decoder.get_float(), self.__decoder.get_float(), self.__decoder.get_float(),
                              self.__decoder.get_float()])
            else:
                p = np.array([self.__decoder.get_uint16(), self.__decoder.get_uint16(), self.__decoder.get_uint16(),
                              self.__decoder.get_uint16()])
            p = p * point_scale
            self.data['POINTS'][m][frame_num, :] = p

    def __read_analog_frame(self, frame_num, is_float, sub_frames, offsets, scales, gen_scale, analog_names):
        if frame_num == 315:
            stop = 1
        for j in range(int(sub_frames)):
            for k, analog in enumerate(analog_names):
                if is_float:
                    c = self.__decoder.get_float()
                else:
                    c = self.__decoder.get_uint16()
                self.data['ANALOGS'][analog][frame_num*sub_frames+j] = (c-offsets[k]) * scales[k]*gen_scale

    def __read_rotation_frame(self, frame_num, rotation_names):
        for i, name in enumerate(rotation_names):
            p = np.array([[self.__decoder.get_float(), self.__decoder.get_float(), self.__decoder.get_float(),
                           self.__decoder.get_float()],
                          [self.__decoder.get_float(), self.__decoder.get_float(), self.__decoder.get_float(),
                           self.__decoder.get_float()],
                          [self.__decoder.get_float(), self.__decoder.get_float(), self.__decoder.get_float(),
                           self.__decoder.get_float()],
                          [self.__decoder.get_float(), self.__decoder.get_float(), self.__decoder.get_float(),
                           self.__decoder.get_float()]])
            self.data['ROTATIONS'][name][frame_num, :, :] = p.transpose()

    def __write_data(self, handle):
        handle.seek((512 * (self.header['data_block'] - 1)))
        point_used = self.header['point_count']>0
        if point_used:
            scale = abs(self.header['scale_factor'])
            is_float = self.header['scale_factor'] < 0
            point_scale = [scale, 1][is_float]
            names_param = self.get_parameter('POINT', 'LABELS')
            marker_names = names_param.value.tolist()

        analog_used = self.header['analog_count']
        if analog_used > 0:
            offsets = np.zeros((analog_used,), int)
            param = self.get_parameter('ANALOG', 'OFFSET')
            if param is not None:
                offsets = param.value

            scales = np.ones((analog_used,), float)
            param = self.get_parameter('ANALOG', 'SCALE')
            if param is not None:
                scales = param.value

            gen_scale = 1.
            param = self.get_parameter('ANALOG', 'GEN_SCALE')
            if param is not None:
                gen_scale = param.value
            names_param = self.get_parameter('ANALOG', 'LABELS')
            if names_param is not None:
                analog_names = names_param.value.tolist()

        rot_param = self.get_parameter_group('ROTATION')
        if rot_param is not None:
            names_param = self.get_parameter('ROTATION', 'LABELS')
            rotation_names = names_param.value.tolist()

        nb_frames = self.header['last_frame'] - self.header['first_frame'] + 1
        for i in range(nb_frames):
            if point_used:
                self.__write_point_frame(marker_names, i, is_float, point_scale)
            if rot_param is not None:
                self.__write_rotation_frame(i, rotation_names)
            if analog_used:
                self.__write_analog_frame(i, self.header['analog_per_frame'], analog_names, is_float, scales, gen_scale, offsets)

    def __write_point_frame(self, marker_names, frame_num, is_float, point_scale):
        for j, m in enumerate(marker_names):
            p = self.data['POINTS'][m][frame_num, :]/point_scale
            for i in range(4):
                if is_float:
                    self.__decoder.write_float(p[i])
                else:
                    self.__decoder.write_uint16(p[i])

    def __write_analog_frame(self, frame_num, sub_frames, analog_names, is_float, scales, gen_scale, offsets):
        for j in range(int(sub_frames)):
            for k, analog in enumerate(analog_names):
                data = self.data['ANALOGS'][analog][frame_num*sub_frames+j]
                c = ((data/gen_scale/scales[k]))+offsets[k]
                if is_float:
                    self.__decoder.write_float(c)
                else:
                    self.__decoder.write_uint16(c)

    def __write_rotation_frame(self, frame_num, rotation_names):
        for i, name in enumerate(rotation_names):
            r = self.data['ROTATIONS'][name][frame_num, :, :].transpose()
            for j in range(4):
                for k in range(4):
                    self.__decoder.write_float(r[j,k])
