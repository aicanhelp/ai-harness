import io, struct


class Buffer():
    def __init__(self):
        self._buf = io.BytesIO()

    def write_int(self, int_value):
        self._buf.write(struct.pack('i', int_value))
        return self

    def write_ints(self, int_values):
        self._buf.write(struct.pack('i' * len(int_values), *int_values))
        return self

    def read_int(self):
        return struct.unpack('i', self._buf.read(4))[0]

    def read_ints(self, len=1):
        return list(struct.unpack('i' * len, self._buf.read(4 * len)))

    def seek(self, position):
        self._buf.seek(position)
        return self

    def close(self):
        if self._buf and not self._buf.closed: self._buf.close()
