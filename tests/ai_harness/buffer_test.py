from ai_harness.buffer import *


class Test_Buffer:
    def test_buffer_bool(self):
        with Buffer() as buffer:
            assert buffer.write(T_Bool, True).seek().read(T_Bool)
            assert buffer.seek().write_bool(True).seek().read_bool()
            assert buffer.seek().write_bools([True, False]).seek().read_bools(2) == [True, False]

    def test_buffer_byte(self):
        with Buffer() as buffer:
            assert buffer.write(T_Byte, 9).seek().read(T_Byte) == 9
            assert buffer.seek().write_byte(9).seek().read_byte() == 9
            assert buffer.seek().write_bytes([5, 6]).seek().read_bytes(2) == [5, 6]

    def test_buffer_short(self):
        with Buffer() as buffer:
            assert buffer.write(T_Short, 9).seek().read(T_Short) == 9
            assert buffer.seek().write_short(9).seek().read_short() == 9
            assert buffer.seek().write_shorts([5, 6]).seek().read_shorts(2) == [5, 6]

    def test_buffer_int(self):
        with Buffer() as buffer:
            assert buffer.write(T_Int, 99).seek().read(T_Int) == 99
            assert buffer.seek().write_int(99).seek().read_int() == 99
            assert buffer.seek().write_ints([5, 6]).seek().read_ints(2) == [5, 6]

    def test_buffer_float(self):
        with Buffer() as buffer:
            assert buffer.write(T_Float, 99).seek().read(T_Float) == 99
            assert buffer.seek().write_float(99).seek().read_float() == 99
            assert buffer.seek().write_floats([5, 6]).seek().read_floats(2) == [5, 6]

    def test_file_buffer(self):
        with open('./test_data/buffer', 'bw') as f:
            buffer = Buffer(f)
            buffer.write_int(1)
        with open('./test_data/buffer', 'br') as f1:
            buffer = Buffer(f1)
            assert buffer.read_int() == 1


class Test_ObjectListSerializer():

    def test_write_read(self):
        f_types = [T_Int, L_Int, T_Byte, T_Bool]

        with ObjectListSerializer(f_types) as serializer:
            object1 = [1, [1, 2, 3, 4, 5], None, False]
            object2 = [2, [1, 2, 3, 4, 5], None, True]
            object3 = [3, [1, 2, 3, 4, 5], 5, False]
            serializer.write(*object1).write_list([object2, object3])
            read_objects = [o for o in serializer.read_iter()]
            assert len(read_objects) == 3
            assert read_objects[0] == object1 and read_objects[1] == object2 and read_objects[2] == object3


class Test_Benchmark_Buffer:
    global_buffer = Buffer()

    def benchmark_write_read_one(self):
        buffer = Buffer()
        for i in range(1000000): buffer.write_int(1).seek(0).read_int()
        buffer.close()

    def benchmark_write_read_list(self):
        buffer = Buffer()
        for i in range(100000): buffer.write_ints([1] * 10).seek(0).read_ints(10)
        buffer.close()

    def benchmark_global_write_read_one(self):
        buffer = self.global_buffer
        for i in range(1000000): buffer.write_int(1).seek(0).read_int()

    def benchmark_global_write_read_list(self):
        buffer = self.global_buffer
        for i in range(100000): buffer.write_ints([1] * 10).seek(0).read_ints(10)

    def test_buffer_benchmark_one(self, benchmark):
        benchmark(self.benchmark_write_read_one)

    def test_buffer_benchmark_list(self, benchmark):
        benchmark(self.benchmark_write_read_list)

    def test_buffer_benchmark_global_one(self, benchmark):
        benchmark(self.benchmark_global_write_read_one)

    def test_buffer_benchmark_global_list(self, benchmark):
        benchmark(self.benchmark_global_write_read_list)
