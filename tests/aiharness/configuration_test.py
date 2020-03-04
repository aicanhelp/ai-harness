from aiharness.arguments import *
from aiharness.configuration import ArgType, Arguments

log = utils.getLogger('aiharness')


@dataclass
class Address:
    phone: ArgType = ArgType(139, "phone help")
    home: ArgType = ArgType("beijing", "phone help")
    office: ArgType = ArgType("shenzhen", "phone help")


@dataclass
class Config:
    name: ArgType = ArgType("test", "name help")
    age: ArgType = ArgType(10, "age help")
    address: Address = Address()


class Test_Configuration:
    def test_argtype(self):
        arg: ArgType = ArgType(1, 'test')
        arg.set(10, 'test2')
        assert arg == 10 and arg.help == 'test2'

    def test_arg(self):
        arguments = Arguments()
        arguments.arg('name', ArgType('test', 'test name help'))
        args = arguments.parse()
        assert args.name == 'test'
        arguments.arg('address.home', ArgType('beijing', 'address home help'))
        args = arguments.parse()
        assert getattr(args, 'address.home') == 'beijing'
        args: Config = arguments.parseTo(Config())
        assert args.name == 'test' and args.address.home == 'beijing'

    def test_arg_with_obj(self):
        config: Config = Config()
        arguments = Arguments(config)
        args: Config = arguments.parse()
        assert args.name == 'test' and args.age == 10 and args.address.phone == 139
