import logging
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed

log = logging.getLogger(__name__)


class Executor():
    def __init__(self, fn, worker_num=mp.cpu_count(),
                 defaultWorkerFinished=None,
                 onFinished=None,
                 onError=None):
        self.fn = fn
        self.worker_num = worker_num
        self.onFinished = onFinished
        self.onError = onError
        self.defaultWorkerFinished = defaultWorkerFinished
        self.onWorkersFinished = dict()
        self.futures = []
        self.results = []

    def on_worker_finished(self, workerId, defaultWorkerFinished):
        self.onWorkersFinished.setdefault(workerId, defaultWorkerFinished)

    def __done_call_back(self, i):
        executor = self

        def call_back(future):
            executor.futures.remove(future)
            executor.results.append(future.result)
            onWorkerFinished = executor.onWorkersFinished.get(i)
            if onWorkerFinished:
                onWorkerFinished(i, future.result)
            elif executor.defaultWorkerFinished:
                self.defaultWorkerFinished(i, future.result)

            if len(executor.futures) == 0 and executor.onFinished:
                executor.onFinished()

        return call_back

    def start(self):
        log.info("Starting executor with worker number: " + str(self.worker_num))
        try:
            with ProcessPoolExecutor(max_workers=self.worker_num) as executor:
                for i in range(self.worker_num):
                    future = executor.submit(self.fn, i)
                    self.futures.append(future)
                    future.add_done_callback(self.__done_call_back(i))
        except Exception as ex:
            log.error(ex)
            if self.onError:
                self.onError(ex)
        return self

    def get(self):
        as_completed(self.futures)

        return self.results


class BatchExecutor():
    def __init__(self, items, worker_num=mp.cpu_count(), check_count=10000):
        self.items = items
        self.max_index = len(items)
        self.worker_num = worker_num
        self.batch_size = (self.max_index // worker_num) + 1
        self.check_count = check_count

    def run(self):
        result = []
        futures = []

        log.info("Start Batch handler Excecutor to handle data, len: " + str(self.max_index))
        try:
            with ProcessPoolExecutor(max_workers=self.worker_num) as executor:
                from_index, to_index = 0, 0
                for i in range(self.worker_num):
                    to_index = (1 + i) * self.batch_size
                    if to_index >= self.max_index:
                        to_index = self.max_index
                    futures.append(executor.submit(self.handle_items, from_index, to_index))
                    from_index = to_index
                for f in as_completed(futures):
                    result.append(f.result())
        except Exception as ex:
            log.error(ex)
        return result

    def handle_items(self, from_index, to_index):
        raise NotImplementedError()


class BatchHandlerExecutor(BatchExecutor):
    def __init__(self, items, fn, worker_num=mp.cpu_count(), check_count=10000):
        super().__init__(items, worker_num, check_count)
        self.fn = fn

    def handle_items(self, from_index, to_index):
        result = []

        for i in range(from_index, to_index):
            result.append(self.fn(i, self.items[i]))
            if i % self.check_count == 0:
                log.info("handle items %d of %d" % (i, self.max_index))
        return result
