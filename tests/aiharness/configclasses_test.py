from aiharness.configclasses import configclass, field, fields, is_configclass
from aiharness import harnessutils as utils

log = utils.getLogger('aiharness')


@configclass
class Address:
    phone: str = field("139", "phone nubmer")


@configclass
class Config:
    name: str = field(default='TestName', help="name help")
    age: int = field(default=10, help="age help")
    address: Address = field(Address(), "Address help")


class Test_Dataclasses:
    def test_field(self):
        config = Config()
        for f in fields(config):
            if f.name == 'name':
                f.help = "change"
                log.info(config)
            log.info(is_configclass(f.default))
        return
