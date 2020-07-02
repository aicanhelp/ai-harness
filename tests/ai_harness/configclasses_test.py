from typing import Optional

from ai_harness.configclasses import configclass, field, fields, is_configclass
from ai_harness import harnessutils as utils

log = utils.getLogger('aiharness')


@configclass
class Address:
    phone: str = field("139", "phone nubmer")


@configclass
class Config:
    name: str = field(default='TestName', help="name help")
    age: int = field(default=10, help="age help")
    value: Optional[int] = field(None, "value")
    address: Address = field(Address(), "Address help")

    def update(self):
        self.name = 1000


class Test_Dataclasses:
    def test_field(self):
        config = Config()
        config.update()
        config.age = '1000'
        for f in fields(config):
            if str(type(f.type)) == "typing.Union":
                log.info(f.type)
            if f.name == 'name':
                f.help = "change"
                log.info(config)
            log.info(is_configclass(f.default))
        return
