from aiharness.arguments import *
import logging


@dataclass()
class TestObj:
    name: str = ''
    age: int = 0
    address: str = ''
    online: bool = False
    company: str = ''
    product: str = ''


log = logging.getLogger()
log.setLevel('INFO')

if __name__ == '__main__':
    obj: TestObj = Arguments(TestObj()) \
        .set_from_yaml('arguments.yaml').parse()
    log.info(obj)
