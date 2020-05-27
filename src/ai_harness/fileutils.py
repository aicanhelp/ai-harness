import os
from inspect import isfunction, ismethod

from box import Box
from dataclasses import dataclass

from ai_harness.tqdmutils import ProgressBar
from boltons.fileutils import mkdir_p
from pathlib import Path
import zipfile


def _instance_filter(handler):
    if handler is None:
        raise Exception('The Pipe handler can not be None')
    t = type(handler)
    if t == type:
        return handler()

    return handler


def list_file(path, pattern='*'):
    p = Path(path)
    if not p.exists():
        print('Directory is not exists.')
    return [x.name for x in p.glob(pattern) if x.is_file()]


def list_dir(path, pattern='*'):
    p = Path(path)
    if not p.exists():
        print('Directory is not exists.')
    return [x.name for x in p.glob(pattern) if x.is_dir()]


def list(path, pattern='*', file=True):
    if file:
        return list_file(path, pattern)
    else:
        return list_dir(path, pattern)


def zip_files(out_file, *input_files):
    def addToZip(zf, path, zippath):
        if os.path.isfile(path):
            zf.write(path, zippath, zipfile.ZIP_DEFLATED)
        elif os.path.isdir(path):
            if zippath:
                zf.write(path, zippath)
            for nm in os.listdir(path):
                addToZip(zf,
                         os.path.join(path, nm), os.path.join(zippath, nm))
        # else: ignore

    with zipfile.ZipFile(out_file, 'w') as zf:
        for path in input_files[2:]:
            zippath = os.path.basename(path)
            if not zippath:
                zippath = os.path.basename(os.path.dirname(path))
            if zippath in ('', os.curdir, os.pardir):
                zippath = ''
            addToZip(zf, path, zippath)


def join_path(*files):
    result = files[0]
    for file in files[1:]:
        if result is None:
            result = file
            continue
        if file is None:
            continue
        result = os.path.join(result, file)
    return result


def extract_zip(zip_file, dest_dir, members=None):
    if not zipfile.is_zipfile(zip_file):
        return
    mkdir_p(dest_dir)
    with zipfile.ZipFile(zip_file, 'r') as zf:
        zf.extractall(dest_dir, members)


class EmptyLineFilter():
    def __call__(self, line, *args):
        return line == '\n'


class FileLineReader():
    def __init__(self, bar_step_size=1000, exclude_empty_line=True):
        self._handlers = ()
        self._exclude_empty_line = exclude_empty_line
        self._bar = ProgressBar(bar_step_size)

    def pipe(self, *handlers):
        self._handlers = self._handlers + handlers
        return self

    def _read_line(self, file):
        with open(file, 'r') as f:
            count = 0
            while True:
                self._bar.update()
                read_line = f.readline()

                if len(read_line) == 0:
                    return count

                if self._exclude_empty_line and read_line.strip() == '':
                    continue

                input = read_line
                result = ()

                for handler in self._handlers:
                    if handler is None:
                        continue

                    next = handler(input, result)

                    if not next and type(next) == bool:
                        break
                    elif next and type(next) != bool:
                        pass
                    else:
                        next = input

                    result = result + (input,)
                    input = next
                count = count + 1

    def read(self, file, *args):
        try:
            return self._read_line(file)
        finally:
            self._bar.close()


class PathNavigator():
    def on_item(self, onFolder=None, onFile=None, *args):
        pass

    def nav(self, dir, *args):
        pass


@dataclass
class NavState:
    folder_count = 0
    file_count = 0

    def folders(self, count):
        self.folder_count = self.folder_count + count
        return self

    def files(self, count):
        self.file_count = self.file_count + count
        return self

    def inc_folder(self):
        self.folder_count = self.folder_count + 1
        return self

    def inc_file(self):
        self.file_count = self.file_count + 1
        return self


class DirNavigator(PathNavigator):
    def __init__(self, folder_pattern=None, file_pattern=None, bar_step_size=10):
        self._folder_pattern = folder_pattern if folder_pattern else '*'
        self._file_pattern = file_pattern if file_pattern else '*'
        self._onFolder, self._onFile, self._onZipFile = None, None, None
        self._bar = ProgressBar(bar_step_size)
        self._folderFilters, self._fileFilters = (), ()

    def on_item(self, onFolder=None, onFile=None, onZipFile=None):
        self._onFolder, self._onFile, self._onZipFile = onFolder, onFile, onZipFile
        return self

    def filters(self, folderFilters=None, fileFilters=None):
        self._folderFilters, self._fileFilters = folderFilters, fileFilters
        return self

    def folder_filters(self, *folderFilters):
        self._folderFilters = self._folderFilters + folderFilters
        return self

    def file_filters(self, *fileFilters):
        self._fileFilters = self._fileFilters + fileFilters
        return self

    def __filter(self, filters, name, dir):
        if not filters:
            return True
        for filter in filters:
            if not filter(name, dir):
                return False
        return True

    def _loop_dir(self, parent, dir, state: NavState):
        file_dir = join_path(self._base_dir, parent, dir)
        relate_dir = join_path(parent, dir)
        folders = list_dir(file_dir, self._folder_pattern)
        files = list_file(file_dir, self._file_pattern)

        for d in folders:
            self._bar.update()
            if not self.__filter(self._folderFilters, d, relate_dir):
                continue
            state.inc_folder()
            if not self._onFolder or self._onFolder(d, relate_dir):
                self._loop_dir(relate_dir, d, state)

        for f in files:
            self._bar.update()
            if not self.__filter(self._fileFilters, f, relate_dir):
                continue
            if zipfile.is_zipfile(f) and self._onZipFile:
                self._onZipFile(f, relate_dir)
                continue
            state.inc_file()
            if self._onFile:
                self._onFile(f, relate_dir)

    def nav(self, dir, *args):
        navState = NavState()
        self._base_dir = dir
        self._loop_dir(None, '', navState)
        self._bar.close()
        return (navState.folder_count, navState.file_count)


class DirNavigatorWithZip(DirNavigator):
    def __init__(self, folder_pattern=None, file_pattern=None):
        super().__init__(folder_pattern, file_pattern)

    def __handle_zip_file(self, unzip_dir):
        def handle_zip(zipfile, dir):
            to_zip_dir = join_path(unzip_dir, dir, 'unzip_' + os.path.basename(zipfile))
            extract_zip(zipfile, to_zip_dir)
            super().nav(to_zip_dir)

        return handle_zip

    def nav(self, dir, unzip_dir=None, *args):
        super().on_item(onZipFile=self.__handle_zip_file(unzip_dir))
        super().nav(dir)


class To_Json():
    def __call__(self, line, *args):
        return Box.from_json(line)


class Line_origin():
    def __call__(self, input, previous_input: tuple):
        return previous_input[0]


class Line_Writer():
    def __init__(self, output_file):
        self._out_writer = open(self._get_filename(output_file), 'w')

    def _get_filename(self, output_file):
        if os.path.exists(output_file):
            suffix = output_file.split('.')
            if suffix and suffix[-1].isnumeric():
                return "".join(suffix[:-1]) + '.' + str(int(suffix) + 1)
            return output_file + '.0'
        return output_file

    def __call__(self, input, previous_input: tuple = None):
        self._out_writer.write(input)

    def close(self):
        if not self._out_writer.closed:
            self._out_writer.close()


class JsonFileLineReader(FileLineReader):
    def __init__(self, bar_step_size=1000):
        super().__init__(bar_step_size)
        self.handlers = [To_Json]


class FileLineReadAndWrite():
    def __init__(self, out_dir, bar_step_size=100):
        self.bar_step_size = bar_step_size
        self.out_dir = out_dir
        self.filters = ()

    def filter(self, *filters):
        self.filters = self.filters + filters

    def read(self, file, relate_dir, writer=None):
        myWriter = writer
        if not writer:
            myWriter = self._writer(file, relate_dir, self.out_dir)
        filters = self.filters + (myWriter,)
        file_reader = FileLineReader(self.bar_step_size).pipe(*filters)
        file_reader.read(file)
        if not writer:
            myWriter.close()

    def _writer(self, file, relate_dir, out_dir):
        out_dir = join_path(out_dir, relate_dir)
        mkdir_p(out_dir)
        out_file = join_path(out_dir, os.path.basename(file))
        return Line_Writer(out_file)


class DefaultDirectoryFilter():
    def __init__(self, output, unzip_dir=None, folder_pattern='*', file_pattern='*', bar_step_size=100):
        self.browser = self._create_browser(unzip_dir, folder_pattern, file_pattern)
        self.readWrite = FileLineReadAndWrite(output, bar_step_size=bar_step_size)

    def _create_browser(self, unzip_dir, folder_pattern='*', file_pattern='*'):
        if unzip_dir:
            return DirNavigatorWithZip(folder_pattern, file_pattern)
        else:
            return DirNavigator(folder_pattern, file_pattern)

    def line_filters(self, *filters):
        self.readWrite.filter(*filters)
        return self

    def path_filters(self, folder_filters, file_filters):
        self.browser.filters(folder_filters, file_filters)
        return self

    def _on_file(self, writer=None):
        def onFile(file, relate_dir):
            file = join_path(self._base_dir, relate_dir, file)
            self.readWrite.read(file, relate_dir, writer)

        return onFile

    def handle(self, dir, outfile=None):
        writer = None
        self._base_dir = dir
        if outfile:
            writer = Line_Writer(outfile)
        self.browser.on_item(onFile=self._on_file(writer)).nav(dir)
        if writer:
            writer.close()


class DefaultJsonDirectoryFilter(DefaultDirectoryFilter):
    def __init__(self, output, unzip_dir=None, dir_pattern='*', file_pattern='*', bar_step_size=100):
        super().__init__(output, unzip_dir, dir_pattern, file_pattern, bar_step_size)
        super().line_filters(To_Json())
