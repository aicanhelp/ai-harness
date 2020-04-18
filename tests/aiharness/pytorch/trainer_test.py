import torch
from torch import nn, optim
from torch.utils.data import Dataset

from aiharness.pytorch.trainer import TrainConfig, TrainExecutor, TrainModel, OptScheduler, TrainDataBulk, \
    TrainBuilder, ExecutorEventHandler, utils, BaseTrainTask, GradAccumulator

log = utils.getLogger('aiharness')


class ToyModel(nn.Module):
    def __init__(self):
        super(ToyModel, self).__init__()
        self.net1 = nn.Linear(10, 10)
        self.relu = nn.ReLU()
        self.net2 = nn.Linear(10, 5)

    def forward(self, x):
        return self.net2(self.relu(self.net1(x)))


class MyTrainModelBuilder():
    def __init__(self, trainConfig: TrainConfig):
        self.trainConfig = trainConfig

    def _build_pytoch_model(self):
        return ToyModel()

    def _build_criterion(self):
        return nn.MSELoss()

    def __call__(self) -> TrainModel:
        return TrainModel(self.trainConfig, self._build_pytoch_model(), self._build_criterion())


class MyOptSchedulerBuilder():
    def __init__(self, trainConfig: TrainConfig, model: TrainModel):
        self.trainConfig = trainConfig
        self.model = model

    def _build_optimizer(self):
        return optim.SGD(self.model.model.parameters(), lr=0.001)

    def _build_scheduler(self):
        return None

    def __call__(self) -> OptScheduler:
        return OptScheduler(self.trainConfig, self._build_optimizer(), self._build_scheduler())


class MyDataset(Dataset):

    def __init__(self, data_list):
        self.data_list = data_list

    def __getitem__(self, index):
        return self.data_list[index]

    def __len__(self):
        return len(self.data_list)


class MyDataBulkBuilder():
    def __init__(self, trainConfig: TrainConfig):
        self.trainConfig = trainConfig

    def _build_data(self):
        datalist = [torch.randn(20, 10) for i in range(0, 1000)]
        return MyDataset(datalist), None

    def _collate_fn(self, batch):
        return None

    def __call__(self) -> TrainDataBulk:
        d, v = self._build_data()
        return TrainDataBulk(self.trainConfig, d, v, None)


class MyEventHandler(ExecutorEventHandler):
    def onInited(self, config: TrainConfig):
        log.info('onInited')

    def onStart(self, config: TrainConfig):
        log.info('onStart')

    def onDistInited(self, i, config: TrainConfig):
        log.info('onDistInited')

    def onCpuStart(self, config: TrainConfig):
        log.info('onCpuStart')

    def onDistStart(self, i, config: TrainConfig):
        log.info('onDistStart')

    def onTrainTaskCreated(self, task: BaseTrainTask):
        log.info('onTrainTaskCreated')

    def onTrainTaskStart(self, task: BaseTrainTask):
        log.info('onTrainTaskStart')

    def onTrainTaskEpochStart(self, epoch, task: BaseTrainTask):
        log.info('onTrainTaskEpochStart')

    def onTrainTaskEpochGradAcc(self, gradAcc: GradAccumulator, task: BaseTrainTask):
        log.info('onTrainTaskEpochGradAcc')

    def onTrainTaskEpochEnd(self, epoch, task: BaseTrainTask):
        log.info('onTrainTaskEpochEnd')

    def onTrainTaskEpochEvalEnd(self, epoch, task: BaseTrainTask):
        log.info('onTrainTaskEpochEvalEnd')

    def onTrainTaskEvalEnd(self, task: BaseTrainTask):
        log.info('onTrainTaskEvalEnd')


class MyTrainBuilder(TrainBuilder):
    def __init__(self, trainConfig: TrainConfig):
        super().__init__(trainConfig)

    def model(self) -> TrainModel:
        return MyTrainModelBuilder(self.trainConfig)()

    def data(self) -> TrainDataBulk:
        return MyDataBulkBuilder(self.trainConfig)()

    def scheduler(self, model: TrainModel, *args) -> OptScheduler:
        return MyOptSchedulerBuilder(self.trainConfig, model)()

    def eventHandler(self) -> ExecutorEventHandler:
        return MyEventHandler()


class Test_TrainExecutor:
    def test_executor(self):
        config = TrainConfig()
        log.info(config)
        trainBuilder = MyTrainBuilder(config)
        executor = TrainExecutor(trainBuilder)
        executor.start()
