from aiharness.arguments import Arguments
from aiharness import harnessutils as utils
from dataclasses import dataclass


@dataclass()
class TestObj:
    name: str = ''
    age: int = 0
    address: str = ''
    online: bool = False
    company: str = ''
    product: str = ''


log = utils.getLogger('aiharness')

obj: TestObj = Arguments(TestObj()) \
    .set_from_yaml('arguments.yaml').parse()
log.info(obj)
