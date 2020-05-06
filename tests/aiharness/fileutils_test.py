from aiharness.fileutils import DefaultJsonDirectoryFilter, \
    list_dir, list_file, join_path, extract_zip, FileLineReader, DirNavigator


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
        result = FileLineReader().read('./empty.file')
        assert result == 0

    def test_json_file(self):
        result = FileLineReader().read('./test.json')
        assert result == 5

    def function_pipe_handler(self, input, previous_input: tuple):
        return len(previous_input) + 1

    def test_pipe_handlers(self):
        count = FileLineReader().pipe(self.function_pipe_handler,
                                      self.function_pipe_handler, self.function_pipe_handler,
                                      self.function_pipe_handler).read('./test.json')
        assert count == 5


class Test_DirNavigator():
    def exclude(self, pattern):
        def exclude(fileName, *args):
            if fileName.find(pattern) > -1:
                return False
            return True

        return exclude

    def test_navigate_all(self):
        folder_count, file_count = DirNavigator().file_filters().file_filters(self.exclude('.DS_Store')).nav(
            './test_data')
        assert (file_count == 4 and folder_count == 2)


def test_list_file():
    print(list_file('./test_data'))
