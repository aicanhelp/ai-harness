from dataclasses import dataclass

from aiharness.configuration import ArgType
from aiharness import harnessutils as utils

log = utils.getLogger('aiharness')


@dataclass
class Address:
    phone: ArgType = ArgType(139, "phone help")
    home: ArgType = ArgType("beijing", "phone help")
    office: ArgType = ArgType("shenzhen", "phone help")


@dataclass
class Config:
    name: ArgType = ArgType("name", "name help")
    age: ArgType = ArgType(10, "age help")
    address: Address = Address()


def test_ArgType():
    arg: ArgType = ArgType(1, '')
    arg.set('100', 'test')
    assert arg.type == int
    arg = ArgType(arg + 100)
    log.info(arg)
    log.info(arg.help)
