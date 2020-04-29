from aiharness.fileutils import PipeHandler, FileReaderPipeLine, DefaultJsonDirectoryFilter, \
    list_dir, list_file, join_path, JsonZipFilesFilter, extract_zip


class TestFirstPipeHanlder(PipeHandler):
    def handle(self, input, previous_input: tuple):
        return [0]


class TestPipeHanlder(PipeHandler):
    def handle(self, input, previous_input: tuple):
        return input.append(input[-1] + 1)


class TestLastPipeHanler(PipeHandler):
    def __init__(self):
        self.total = []

    def handle(self, input, previous_input: tuple):
        self.total.append(input)
        return input


def test_jion_path():
    assert join_path(None) is None
    assert join_path(None, 'a') == 'a'
    assert join_path('a', None) == 'a'
    assert join_path('a', 'b') == 'a/b'
    assert join_path('a', 'b', None) == 'a/b'
    assert join_path('a', None, 'b') == 'a/b'
    assert join_path('a', 'b', 'c') == 'a/b/c'


class Test_FileReaderPipeline():
    def test_empty_file(self):
        result = FileReaderPipeLine('./empty.file').end()
        assert result == 0

    def test_json_file(self):
        result = FileReaderPipeLine('./test.json').end()
        assert result == 5

    def function_pipe_handler(self, input, previous_input: tuple):
        return input.append(input[-1] + 1)

    def test_pipe_handlers(self):
        pipeline = FileReaderPipeLine('./test.json')
        lastHandler = TestLastPipeHanler()
        pipeline.mid_pipe(TestFirstPipeHanlder, TestPipeHanlder(),
                          TestPipeHanlder, TestPipeHanlder(), self.function_pipe_handler,
                          lastHandler)
        result = pipeline.end()
        assert result == 5 and lastHandler.total[0] == [0, 1, 2, 3, 4]


class Test_JsonDirectoryFilter():
    def test(self):
        DefaultJsonDirectoryFilter('./test_data/json', '../../build/test_data/json').pipe_handlers(self.filter).run()

    def test_news(self):
        DefaultJsonDirectoryFilter('./test_data/news', '../../build/test_data/news').pipe_handlers(self.filter).run()

    def filter(self, input, previous_input: tuple):
        if len(input.content) < 50:
            return False
        return input.content + '\n\n'


def test_extract_zip():
    extract_zip('./test_data/wiki_zh2019.zip', '../../build/test_data')


class TestJsonZipFilter():
    def test(self):
        JsonZipFilesFilter('./test_data/wiki_zh2019.zip', '../../build/test_data', pattern='wiki*').pipe_handlers(
            self.filter).run()

    def test_to_one(self):
        JsonZipFilesFilter('./test_data/wiki_zh2019.zip', '../../build/test_data', 'all.json',
                           pattern='wiki*').pipe_handlers(
            self.filter).run()

    def filter(self, input, previous_input: tuple):
        if len(input.text) < 100:
            return False
        text = input.text.split('\n\n')
        text = [self.remove_last_r(t) for t in text[1:]]
        return ''.join(text) + '\n\n'

    def remove_last_r(self, text: str):
        if text == '\n' or len(text) == 0:
            return ''
        last = -1
        while text[last] == '\n':
            last = last - 1
        if last == -1:
            return text
        return text[:last + 1]


def test_list_file():
    print(list_file('./test_data'))
