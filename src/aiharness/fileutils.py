import os
from inspect import isfunction, ismethod

from box import Box
from aiharness.tqdmutils import ProgressBar
from boltons.fileutils import mkdir_p
from pathlib import Path
import zipfile


class PipeHandler():

    def handle(self, input, previous_input: tuple):
        '''
        For the FileReaderPipeLine to define the handler in each step
        :param current: the input of current setup, actually it is the output of last setup
        :param previous: the inputs of the previous setup
        :return: None or the result of this handler, if the return is None, the input will be as the return by the FileReaderPipeline
        '''
        return input

    def __call__(self, input, previous_input: tuple):
        return self.handle(input, previous_input)

    def final(self):
        pass


class FunctionPipeHandler(PipeHandler):
    def __init__(self, f):
        self._f = f

    def handle(self, input, previous_input: tuple):
        return self._f(input, previous_input)


class PipeFilter(PipeHandler):

    def handle(self, input, previous_input: tuple):
        '''
        For the FileReaderPipeLine to define the filter in each step
        :param current: the input of current setup, actually it is the output of last setup
        :param previous: the inputs of the previous setup
        :return: None or the result of this filter,
        if the return is None, FileReaderPipeline will end this Pipeline.( Note: this is the different with the PipeHandler)
        '''
        return True


def _instance_handler(handler):
    if handler is None:
        raise Exception('The Pipe handler can not be None')
    t = type(handler)
    if t == type:
        if handler != PipeHandler and not issubclass(handler, PipeHandler):
            raise Exception('The Pipe handler should be PipeHandler or PipeFilter')
        return handler()
    else:
        if isfunction(handler) or ismethod(handler):
            return FunctionPipeHandler(handler)
        if not isinstance(handler, PipeHandler):
            raise Exception('The Pipe handler should be PipeHandler or PipeFilter')

    return handler


class HandlerContainer():
    def __init__(self):
        self._handlers = ()

    def head(self, *handlers):
        if not handlers:
            return
        self._handlers = handlers + self._handlers

    def tail(self, *handlers):
        if not handlers:
            return
        self._handlers = self._handlers + handlers

    def before(self, handler, *handlers):
        if not handlers:
            return
        if not handler:
            self._handlers = handlers
        for i, handler in enumerate(self._handlers):
            if handler == handler:
                self._handlers = self._handlers[:i] + handlers + self._handlers[i:]

    def after(self, handler, *handlers):
        if not handlers:
            return
        if not handler:
            self._handlers = handlers
        for i, handler in enumerate(self._handlers):
            if handler == handler:
                self._handlers = self._handlers[:i + 1] + handlers + self._handlers[i + 1:]

    def all(self):
        return self._handlers


class PipelineHandlers():
    def __init__(self):
        self.pre_handlers: HandlerContainer = HandlerContainer()
        self.post_handlers: HandlerContainer = HandlerContainer()
        self.handlers: HandlerContainer = HandlerContainer()

    def all_handlers(self):
        return self.pre_handlers.all() + self.handlers.all() + self.post_handlers.all()


class FileReaderPipeLine():
    def __init__(self, file_path):
        self._file_path = file_path
        self._onEmptyLine = None
        self.handlers_container: PipelineHandlers = PipelineHandlers()

    def on_empty_line(self, onEmptyLine):
        self._onEmptyLine = onEmptyLine
        return self

    def pipe(self, *handlers):
        self.handlers_container.handlers.tail(*handlers)
        return self

    def _execute_pipes(self, handlers):
        count = 0
        with open(self._file_path, 'r') as f:
            while True:
                read_line = f.readline()

                if len(read_line) == 0:
                    return count
                if read_line == '\n':
                    if self._onEmptyLine is not None:
                        self._onEmptyLine()
                    continue

                result = ()
                input = read_line
                for handler in handlers:
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

    def end(self):
        can_handlers = self.handlers_container.all_handlers()
        if not can_handlers:
            handlers = [PipeHandler()]
        else:
            handlers = [_instance_handler(handler) for handler in can_handlers]

        result = self._execute_pipes(handlers)

        for handler in handlers:
            handler.final()

        return result


class JsonHandler(PipeHandler):
    def handle(self, input, previous_input: tuple):
        return Box.from_json(input)


class TextWriteHandler(PipeHandler):
    def __init__(self, output_file):
        self._out_writer = open(output_file, 'w')

    def handle(self, input, previous_input: tuple):
        self._out_writer.write(input)

    def final(self):
        if not self._out_writer.closed:
            self._out_writer.close()


class OriginTextWriteHandler(TextWriteHandler):
    def __init__(self, output_file):
        super().__init__(output_file)

    def handle(self, input, previous_input: tuple):
        self._out_writer.write(previous_input[0])


class JsonWriteHandler(PipeHandler):
    def __init__(self, output_file):
        self._out_writer = open(output_file, 'w')

    def handle(self, input, previous_input: tuple):
        self._out_writer.write(input.to_json())


class DefaultProgressBarHandler(PipeHandler):
    def __init__(self, bar_step_size=100):
        self._bar = ProgressBar(bar_step_size)

    def handle(self, input, previous_input: tuple):
        self._bar.update()

    def final(self):
        self._bar.close()


class JsonReaderPipeline(FileReaderPipeLine):
    def __init__(self, input_file):
        super().__init__(input_file)
        super().handlers_container.handlers.head(JsonHandler)


class DefaultFileLineFilter(FileReaderPipeLine):
    def __init__(self, input_file, output_file, bar_step_size=100):
        super().__init__(input_file)
        self._out_writer = OriginTextWriteHandler(output_file)
        self._bar = DefaultProgressBarHandler(bar_step_size)
        self.handlers_container.post_handlers.tail(self._out_writer, self._bar)


class DefaultJsonFileFilter(DefaultFileLineFilter):
    def __init__(self, input_file, output_file, bar_step_size=100):
        super().__init__(input_file, output_file, bar_step_size)
        self.handlers_container.handlers.head(JsonHandler)


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
    mkdir_p(dest_dir)
    with zipfile.ZipFile(zip_file, 'r') as zf:
        zf.extractall(dest_dir, members)


class DirectoryNavigator():
    def __init__(self, work_dir, pattern='*', bar_step_size=1):
        self.work_dir = os.fspath(work_dir)
        self.pattern = pattern
        self._bar = ProgressBar(bar_step_size)

    def _loop_dir(self, dir, handler=None):
        file_dir = join_path(self.work_dir, dir)
        for file in list_file(file_dir, self.pattern):
            if handler is not None:
                handler(join_path(file_dir, file), dir)
                self._bar.update()
        for d in list_dir(file_dir):
            self._loop_dir(join_path(dir, d), handler)

    def run(self, handler=None):
        print('Processing files in directory: ' + self.work_dir)
        self._loop_dir(None, handler)
        self._bar.close()


class DefaultJsonDirectoryFilter():
    def __init__(self, input, output, pattern='*', bar_step_size=100):
        self.nav = DirectoryNavigator(input, pattern, 1)
        self.input = input
        self.output = output
        self._bar_step_size = bar_step_size
        self._handlers = None

    def pipe_handlers(self, *handlers):
        self._handlers = handlers
        return self

    def _handler_json_file(self, file, dir):
        out_dir = join_path(self.output, dir)
        out_file = join_path(out_dir, os.path.basename(file))
        mkdir_p(out_dir)
        DefaultJsonFileFilter(file, out_file, self._bar_step_size).pipe(*(self._handlers)).end()

    def run(self):
        mkdir_p(self.output)
        self.nav.run(self._handler_json_file)


class JsonZipFilesFilter(DefaultJsonDirectoryFilter):
    def __init__(self, zip_file, work_dir=None, pattern='*', bar_step_size=100):
        self.unzip_dir, self.out_dir = JsonZipFilesFilter.__make_input_dir(zip_file, work_dir)
        super().__init__(self.unzip_dir, self.out_dir, pattern, bar_step_size)
        self.zip_file = zip_file

    @staticmethod
    def __make_input_dir(zip_file, work_dir):
        unzip_dir = join_path(work_dir, 'unzip_' + os.path.basename(zip_file))
        out_dir = join_path(work_dir, 'out_' + os.path.basename(zip_file))
        return unzip_dir, out_dir

    def run(self):
        if not os.path.exists(self.zip_file):
            return

        print('Processing files in zip file: ' + self.zip_file)
        if not os.path.exists(self.unzip_dir):
            extract_zip(self.zip_file, self.unzip_dir)
        super().run()
