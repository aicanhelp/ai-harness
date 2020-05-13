from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from ai_harness import harnessutils as utils
from threading import current_thread
from time import sleep

from ai_harness.executors import BatchHandlerExecutor, Executor, QueueExecutor

log = utils.getLogger('aiharness')


class Test_Executor:
    def _onWorkerFinished(self, index, item):
        log.info("Worker Finished--" + str(index))

    def _onWorkerFinished1(self, index, item):
        log.info("Worker1 Finished--" + str(index))

    def _onFinished(self, ):
        log.info("Executor Finished")

    def _execute(processId):
        sleep(1)
        log.info("executing-----" + str(processId))
        return 0

    def testExecutor(self):
        executor = Executor(self._execute, 4, defaultWorkerFinished=self._onWorkerFinished, onFinished=self._onFinished)
        executor.on_worker_finished(1, self._onWorkerFinished1)
        assert len(executor.start().get()) == 4


class Test_BatchHandlerExecutor:
    def _handleQueueItem(self, index, item):
        log.info(str(item) + '===' + current_thread().name)
        return item

    def testBatchHandlerExecutor(self):
        items = [i for i in range(100)]
        executor = BatchHandlerExecutor(items, self._handleQueueItem)
        result = executor.run()
        log.info(str(result) + str(isinstance(items, list)))


class Test_QueueExecutor:
    def test_queueExecutor(self):
        items = [i for i in range(100)]
        executor = QueueExecutor(items)
        executor.run(self._handleQueueItem)

    def _handleQueueItem(self, items):
        log.info(str(items))
        return items
