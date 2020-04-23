from aiharness.fileutils import JsonLineFileReader, JsonDirectoryFilter, list_dir, list_file


class Test_JsonLineFileReader():
    def test_empty_file(self):
        result = JsonLineFileReader('./empty.file').pipe()
        assert result == 0

    def test_json_file(self):
        result = JsonLineFileReader('./test.json').pipe()
        assert result == 5


class Test_JsonDirectoryFilter():
    def test(self):
        JsonDirectoryFilter('./test_data', './test_data/new', self.filter).run()

    def filter(self, json):
        return True


def test_list_file():
    print(list_file('./test_data'))
