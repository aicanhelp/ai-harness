from box import Box
from aiharness.tqdmutils import ProgressBar
from boltons.fileutils import iter_find_files, mkdir_p
from pathlib import Path
import os


class FileReaderPipe():
    def __init__(self, file_path):
        self._file_path = file_path
        self.onEmptyLine = None

    def on_empty_line(self, onEmptyLine):
        self.onEmptyLine = onEmptyLine

    def pipe(self, *pipes):
        if pipes is None:
            return
        count = 0
        with open(self._file_path, 'r') as f:
            while True:
                read_line = f.readline()

                if len(read_line) == 0:
                    return count
                if read_line == '\n':
                    if self.onEmptyLine is not None:
                        self.onEmptyLine()
                    continue

                result = read_line
                for pipe in pipes:
                    if pipe is None:
                        continue
                    result = pipe((read_line, result))
                count = count + 1


class JsonLineFileReader(FileReaderPipe):
    def __init__(self, file_path):
        super().__init__(file_path)

    def _to_json_object(self, input):
        return Box.from_json(input[1])

    def pipe(self, *pipes):
        return super().pipe(self._to_json_object, *pipes)


class JsonFileFilter():
    def __init__(self, input_json_file, output_json_file, filter):
        self._file_reader = JsonLineFileReader(input_json_file)
        self._out_writer = open(output_json_file, 'w')
        self._filter = filter
        self._bar = ProgressBar()

    def _write(self, result):
        if self._filter is None:
            return
        if self._filter(result[1]):
            self._out_writer.write(result[0])
        self._bar.update()

    def run(self):
        self._file_reader.pipe(self._write)
        if not self._out_writer.closed:
            self._out_writer.close()
        self._bar.close()
        if not self._out_writer.closed:
            self._out_writer.close()


def list_file(path, pattern='*'):
    p = Path(path)
    return [x.name for x in p.glob(pattern) if x.is_file()]


def list_dir(path, pattern='*'):
    p = Path(path)
    return [x.name for x in p.glob(pattern) if x.is_dir()]


class JsonDirectoryFilter():
    def __init__(self, input, output, filter):
        self._input = input
        self._output = output
        self._filter = filter

    def run(self):
        mkdir_p(self._output)
        for file in list_file(self._input):
            output_file = self._output + '/' + file
            print('Processing Json file: %s to %s' % (file, output_file))
            JsonFileFilter(self._input + '/' + file, output_file, self._filter).run()
