from box import Box
import io


class FileReaderPipe():
    def __init__(self, file_path, read_batch=1):
        self._file_path = file_path
        self.read_batch = read_batch

    def pipe(self, *pipes):
        if pipes is None:
            return
        total_results = []
        with open(self._file_path, 'r') as f:
            read_lines = f.readlines(self.read_batch)
            if len(read_lines) == 0:
                return total_results
            result = read_lines
            if self.read_batch == 1:
                result = read_lines[0]
            for pipe in pipes:
                if pipe is None:
                    continue
                result = pipe(result)
            total_results.append(result)
        return total_results


class JsonLineFileReader(FileReaderPipe):
    def __init__(self, file_path, read_batch=1):
        super().__init__(file_path, read_batch)

    def _to_json_object(self, lines):
        if self.read_batch == 1:
            return Box.from_json(lines)
        return [Box.from_json(line) for line in lines]

    def pipe(self, *pipes):
        return super().pipe(self._to_json_object, *pipes)
