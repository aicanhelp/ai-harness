import torch.multiprocessing as mp
from torch.nn.parallel import DistributedDataParallel as DDP
from torch.utils.data import DataLoader
from torch.utils.data.distributed import DistributedSampler
import torch.distributed as dist
import torch
from aiharness.configuration import *


@configclass()
class TrainConfig():
    cuda: bool = field(True, 'whether uses cuda')
    gpus: str = field('0', 'gpus will be used')
    batch_size: int = field(32, 'batch size')
    max_grad_norm: float = field(1.0, 'max gradient normalization')
    grad_acc: int = field(1, 'gradient accumulation')
    num_epochs: int = field(1, 'epoches of training')
    num_workers: int = field(1, 'thread number of dataloader')
    eval_epoch: bool = field(False, 'eval on each epoch')
    rank_from: int = field(0, 'what is the range from for the rank')
    world_size: int = field(1, 'the world size for the distributed training')
    dist_backend: str = field('nccl', 'the backend of distributed')
    dist_url: str = field('tcp://127.0.0.1:23456', 'the master url of distributed')

    def update(self):
        self.gpus = [int(i) for i in self.gpus.split(',')]
        if not self.cuda or torch.cuda.device_count() == 0:
            self.gpus = []
            self.cuda = False
        if self.cuda and torch.cuda.device_count() > 0:
            self.gpus = [i for i in range(0, torch.cuda.device_count())]

        self.world_size = max(self.world_size, len(self.gpus))


class TrainDataBulk():
    def __init__(self, config: TrainConfig, train_dataset, eval_dataset=None, collate_fn=None):
        self._config = config
        self.train_dataset = train_dataset
        self.eval_dataset = eval_dataset

        self.train_dataloader, self.eval_dataloader, self.train_sampler = self._generate_dataloader(collate_fn)

    def _generate_dataloader(self, collate_fn):
        train_sampler = None
        if self._config.cuda:
            train_sampler = DistributedSampler(self.train_dataset)
        train_dataloader = DataLoader(self.train_dataset, batch_size=self._config.batch_size,
                                      shuffle=(train_sampler is None),
                                      pin_memory=False,
                                      sampler=train_sampler,
                                      num_workers=self._config.num_workers,
                                      collate_fn=collate_fn)
        eval_dataloader = None
        if self.eval_dataset is not None:
            eval_dataloader = DataLoader(self.eval_dataset, batch_size=self._config.batch_size,
                                         shuffle=False,
                                         num_workers=self._config.num_workers,
                                         collate_fn=collate_fn)

        return train_dataloader, eval_dataloader, train_sampler

    def set_train_epoch(self, epoch):
        if self.train_sampler is None:
            return
        self.train_sampler.set_epoch(epoch)


class TrainModel():
    def __init__(self, config: TrainConfig, model, criterion, device=-1):
        self.config = config
        self.model = model
        self.criterion = criterion
        self.device = device

    def to(self, device: int = -1):
        if device < 0: return self
        newModel = DDP(self.model, device_ids=[device], output_device=device)
        newCriterion = self.criterion.cuda()
        return TrainModel(self.config, newModel, newCriterion, device)

    def __make_input_target(self, batch_data):
        input = batch_data[0]
        if self.device >= 0:
            input = input.cuda(non_blocking=True)
        if len(batch_data) == 1:
            return input, input

        target = batch_data[1]
        if self.device >= 0:
            target = target.cuda(non_blocking=True)
        return input, target

    def __call__(self, batch_data, train=False):
        input, target = self.__make_input_target(batch_data)
        output = self.model(input)
        loss = self.criterion(input, target)
        if train:
            loss.backward()
            self.__clip_grad_norm()
        return loss, output

    def __clip_grad_norm(self):
        if self.config.max_grad_norm <= 0:
            return
        torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.config.max_grad_norm)

    def eval(self):
        self.model.eval()

    def train(self):
        self.model.train()


class OptScheduler():
    def __init__(self, config: TrainConfig, optimizer, scheduler):
        self.config = config
        self.optimizer = optimizer
        self.scheduler = scheduler

    def step(self):
        self.optimizer.step()
        self.optimizer.zero_grad()
        if self.scheduler is not None:
            self.scheduler.step()


class BaseTrainTask():
    def __init__(self, i, trainConfig: TrainConfig, model: TrainModel, data: TrainDataBulk):
        self.id = i
        self.config = trainConfig
        self.data_bulk = data
        self.model = model


class GradAccumulator():
    def __init__(self, config: TrainConfig, scheduler: OptScheduler):
        self.config = config
        self.scheduler = scheduler
        self.running_loss = 0
        self.overall_step = 0

    def step(self, batch_idx, loss):
        if (batch_idx + 1) % self.config.grad_acc == 0:
            self.running_loss += loss.item()
            self.scheduler.step()
            self.overall_step += 1
            return True
        return False


class ExecutorEventHandler():
    def onInited(self, config: TrainConfig):
        pass

    def onStart(self, config: TrainConfig):
        pass

    def onDistInited(self, i, config: TrainConfig):
        pass

    def onCpuStart(self, config: TrainConfig):
        pass

    def onDistStart(self, i, config: TrainConfig):
        pass

    def onTrainTaskCreated(self, task: BaseTrainTask):
        pass

    def onTrainTaskStart(self, task: BaseTrainTask):
        pass

    def onTrainTaskEpochStart(self, epoch, task: BaseTrainTask):
        pass

    def onTrainTaskEpochGradAcc(self, gradAcc: GradAccumulator, task: BaseTrainTask):
        pass

    def onTrainTaskEpochEnd(self, epoch, task: BaseTrainTask):
        pass

    def onTrainTaskEpochEvalEnd(self, epoch, task: BaseTrainTask):
        pass

    def onTrainTaskEvalEnd(self, task: BaseTrainTask):
        pass


class TrainBuilder():
    def __init__(self, trainConfig: TrainConfig):
        self.trainConfig = trainConfig

    def model(self, *args) -> TrainModel:
        pass

    def data(self, *args) -> TrainDataBulk:
        pass

    def scheduler(self, model: TrainModel, *args) -> OptScheduler:
        pass

    def eventHandler(self, *args) -> ExecutorEventHandler:
        pass


class TrainExecutor():
    def __init__(self, trainerBuilder: TrainBuilder):
        self.config = trainerBuilder.trainConfig
        self.config.update()
        self.origin_model = trainerBuilder.model()
        self.data_bulk = trainerBuilder.data()
        self.optScheduler = trainerBuilder.scheduler(self.origin_model)
        self.eventHandler = trainerBuilder.eventHandler()
        if self.eventHandler is None:
            self.eventHandler = ExecutorEventHandler()
        self.eventHandler.onInited(self.config)

    def __init_dist_environment(self, i):
        rank = self.config.rank_from + i
        local_rank = int(self.config.gpus[i])
        dist.init_process_group(backend=self.config.dist_backend,
                                init_method=self.config.dist_url, rank=rank, world_size=self.config.world_size)
        torch.cuda.set_device(int(local_rank))
        self.eventHandler.onDistInited(i, self.config)
        return local_rank

    def _start_distributed_task(self, i):
        self.eventHandler.onDistStart(i, self.config)
        local_rank = self.__init_dist_environment(i)
        model = self.origin_model.to(local_rank)
        task = TrainTask(i, self, model)
        task()

    def start(self):
        self.eventHandler.onStart(self.config)
        if not self.config.cuda:
            self.eventHandler.onCpuStart(self.config)
            task = TrainTask(-1, self, self.origin_model)
            task()
        else:
            mp.spawn(self._start_distributed_task, nprocs=len(self.config.gpus), join=True)


class TrainTask(BaseTrainTask):
    def __init__(self, i, executor: TrainExecutor, model: TrainModel):
        super().__init__(i, executor.config, model, executor.data_bulk)
        self.executor = executor
        self.config = executor.config
        self.gradAcc = GradAccumulator(self.config, self.executor.optScheduler)
        self.eventHandler = executor.eventHandler
        self.eval = TrainEval(self)

    def __call__(self, *args, **kwargs):
        self.eventHandler.onTrainTaskStart(self)
        for epoch in range(self.config.num_epochs):
            self.eventHandler.onTrainTaskEpochStart(epoch, self)
            TrainEpoch(epoch, self)()

            if self.config.eval_epoch:
                self.eval()
                self.eventHandler.onTrainTaskEpochEvalEnd(epoch, self)

            self.eventHandler.onTrainTaskEpochEnd(epoch, self)

        if not self.config.eval_epoch:
            self.eval()
            self.eventHandler.onTrainTaskEvalEnd(self)


class TrainEval():
    def __init__(self, task: TrainTask):
        self.task = task

    def __call__(self, *args, **kwargs):
        if self.task.data_bulk.eval_dataloader is None:
            return
        self.task.model.eval()
        with torch.no_grad():
            for batch_idx, batch_data in enumerate(self.task.data_bulk.eval_dataloader):
                loss, output = self.task.model(batch_data)


class TrainEpoch():
    def __init__(self, epoch, task: TrainTask):
        self.epoch = epoch
        self.task = task

    def __call__(self, *args, **kwargs):
        self.task.eventHandler.onTrainTaskEpochStart(self.epoch, self.task)
        self.task.data_bulk.set_train_epoch(self.epoch)
        self.task.model.train()
        for batch_idx, batch_data in enumerate(self.task.data_bulk.train_dataloader):
            TrainEpochBatch(self, batch_idx, batch_data)


class TrainEpochBatch():
    def __init__(self, epoch: TrainEpoch, batch_idx, batch_data):
        self.epoch = epoch
        self.batch_idx = batch_idx
        self.batch_data = batch_data

    def __call__(self, batch_idx, batch_data):
        try:
            loss, output = self.epoch.task.model(self.batch_data)
            if self.epoch.task.gradAcc.step(self.batch_idx, loss):
                self.epoch.task.eventHandler.onTrainTaskEpochGradAcc(self.epoch.task.gradAcc, self.epoch.task)
        except RuntimeError as exception:
            if "out of memory" in str(exception):
                if hasattr(torch.cuda, 'empty_cache'):
                    torch.cuda.empty_cache()
            else:
                raise exception
