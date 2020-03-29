from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from aiharness import harnessutils as utils
from threading import current_thread
from time import sleep

from aiharness.executors import BatchHandlerExecutor, Executor

log = utils.getLogger('aiharness')


def _handleQueueItem(index, item):
    log.info(str(item) + '===' + current_thread().name)
    return item


def _onWorkerFinished(index, item):
    log.info("Worker Finished--" + str(index))


def _onWorkerFinished1(index, item):
    log.info("Worker1 Finished--" + str(index))


def _onFinished():
    log.info("Executor Finished")


def _execute(processId):
    sleep(1)
    log.info("executing-----" + str(processId))
    return 0

def testExecutor():
    executor = Executor(_execute, 4, defaultWorkerFinished=_onWorkerFinished, onFinished=_onFinished)
    executor.on_worker_finished(1, _onWorkerFinished1)
    assert len(executor.start().get()) == 4

def testBatchHandlerExecutor():
    items = [i for i in range(100)]
    executor = BatchHandlerExecutor(items, _handleQueueItem)
    result = executor.run()
    log.info(str(result) + str(isinstance(items, list)))
