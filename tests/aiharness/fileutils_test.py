from aiharness.fileutils import JsonLineFileReader


class Test_JsonLineFileReader():
    def test_empty_file(self):
        result = JsonLineFileReader('./empty.file').pipe()
        assert len(result) == 0

    def test_json_file(self):
        result = JsonLineFileReader('./test.json').pipe()
        assert len(result) > 0
        assert result[0].a == 1
