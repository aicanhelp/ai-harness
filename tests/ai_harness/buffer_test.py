from ai_harness.buffer import *


class Test_Buffer:
    def test_buffer(self):
        buffer = Buffer()
        buffer.write_int(1).seek(0)
        assert buffer.read_int() == 1
        buffer.write_ints([1] * 10).seek(0)
        assert buffer.read_ints(10) == [1] * 10
        buffer.close()

    def test_buffer2(self):
        buffer = Buffer2()
        buffer.write_int(1).seek(0)
        assert buffer.read_int() == 1
        buffer.write_ints([1] * 10).seek(0)
        assert buffer.read_ints(10) == [1] * 10
        buffer.close()


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
