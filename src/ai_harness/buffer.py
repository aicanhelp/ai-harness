import io, struct
from typing import List

from dataclasses import dataclass

TYPES = []


@dataclass()
class Byte_Type:
    id: int = 0
    c: str = ''
    len: int = 0

    def __init__(self, id: int, c: str, len: int):
        TYPES.insert(id, self)
        self.id = id
        self.c = c
        self.len = len

    def is_list(self):
        return self.id > 10


T_Bool = Byte_Type(1, '?', 1)
T_Byte = Byte_Type(2, 'b', 1)
T_Short = Byte_Type(3, 'h', 2)
T_Int = Byte_Type(4, 'i', 4)
T_Float = Byte_Type(5, 'f', 4)

L_Bool = Byte_Type(11, '?', 1)
L_Byte = Byte_Type(12, 'b', 1)
L_Short = Byte_Type(13, 'h', 2)
L_Int = Byte_Type(14, 'i', 4)
L_Float = Byte_Type(15, 'f', 4)


class Buffer():
    def __init__(self, buf=None):
        self._buf = io.BytesIO() if not buf else buf
        self._external = not buf
        self._buf.writable()

    def writes(self, fmt, *values):
        self._buf.write(struct.pack(fmt, *values))
        return self

    def reads(self, fmt, v_len):
        content = self._buf.read(v_len)
        if not content: return None
        return struct.unpack(fmt, content)

    def write(self, t: Byte_Type, value):
        self._buf.write(struct.pack(t.c, value))
        return self

    def write_bool(self, value):
        return self.write(T_Bool, value)

    def write_byte(self, value):
        return self.write(T_Byte, value)

    def write_short(self, value):
        return self.write(T_Short, value)

    def write_int(self, value):
        return self.write(T_Int, value)

    def write_float(self, value):
        return self.write(T_Float, value)

    def write_list(self, t: Byte_Type, values):
        self._buf.write(struct.pack(t.c * len(values), *values))
        return self

    def write_bools(self, values):
        return self.write_list(T_Bool, values)

    def write_bytes(self, values):
        return self.write_list(T_Byte, values)

    def write_shorts(self, values):
        return self.write_list(T_Short, values)

    def write_ints(self, values):
        return self.write_list(T_Int, values)

    def write_floats(self, values):
        return self.write_list(T_Float, values)

    def read(self, t: Byte_Type):
        content = self._buf.read(t.len)
        if not content: return None
        return struct.unpack(t.c, content)[0]

    def read_bool(self) -> bool:
        return self.read(T_Bool)

    def read_byte(self) -> int:
        return self.read(T_Byte)

    def read_short(self) -> int:
        return self.read(T_Short)

    def read_int(self) -> int:
        return self.read(T_Int)

    def read_float(self) -> float:
        return self.read(T_Float)

    def read_list(self, t: Byte_Type, length=1) -> List:
        content = self._buf.read(t.len * length)
        if not content: return None
        return list(struct.unpack(t.c * length, content))

    def read_bools(self, length=1) -> List[bool]:
        return self.read_list(T_Bool, length)

    def read_bytes(self, length=1) -> List[int]:
        return self.read_list(T_Byte, length)

    def read_shorts(self, length=1) -> List[int]:
        return self.read_list(T_Short, length)

    def read_ints(self, length=1) -> List[int]:
        return self.read_list(T_Int, length)

    def read_floats(self, length=1) -> List[float]:
        return self.read_list(T_Int, length)

    def seek(self, position=0):
        self._buf.seek(position)
        return self

    def write_buffer(self, buffer):
        self._buf.write(buffer.get_buffer())
        return self

    def get_buffer(self):
        return self._buf.getbuffer()

    def close(self):
        if not self._external and self._buf and not self._buf.closed: self._buf.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class ObjectListSerializer:
    def __init__(self, obj_fields_types: List[Byte_Type], buf=None):
        self._buffer = Buffer(buf)
        self._obj_fields_types = obj_fields_types
        self._field_number = len(self._obj_fields_types)
        assert self._obj_fields_types, 'The types of fields must be input'

    def __build_write_fmt(self, *obj_fields):
        fmt = ''
        t_sizes, t_values = [], []
        for t, v in zip(self._obj_fields_types, obj_fields):
            t_len = 0 if v is None else (len(v) if t.id > 10 else 1)
            fmt = fmt + (t.c * t_len)
            t_sizes.append(t_len)
            if t_len > 0: t_values.append(v) if t.id < 10 else t_values.extend(v)
        return fmt, t_sizes, t_values

    def write(self, *obj_fields):
        fmt, t_sizes, t_values = self.__build_write_fmt(*obj_fields)
        self._buffer.write_bytes(t_sizes)
        self._buffer.writes(fmt, *t_values)
        return self

    def write_list(self, obj_list):
        for obj in obj_list: self.write(*obj)
        return self

    def __build_read_fmt_len(self, v_lens):
        fmt = ''
        all_len = 0
        for t, l in zip(self._obj_fields_types, v_lens):
            fmt = fmt + t.c * l
            all_len = all_len + t.len * l
        return fmt, all_len

    def __build_read_obj(self, v_lens, v_list):
        start = 0
        for t, l in zip(self._obj_fields_types, v_lens):
            v = None
            if l > 0:
                end = start + l
                v = v_list[start] if l == 1 and t.id < 10 else list(v_list[start:end])
                start = end
            yield v

    def read_iter(self):
        self._buffer.seek()
        while True:
            v_lens = self._buffer.read_bytes(self._field_number)
            if not v_lens: break
            fmt, all_len = self.__build_read_fmt_len(v_lens)
            v_list = self._buffer.reads(fmt, all_len)
            if not v_list: break
            yield [v for v in self.__build_read_obj(v_lens, v_list)]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._buffer: self._buffer.close()
