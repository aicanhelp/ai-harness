from dataclasses import dataclass
from wrapt import ObjectProxy

from aiharness.configuration import ArgType, Arguments, XmlConfiguration
from aiharness import harnessutils as utils

log = utils.getLogger('aiharness')


@dataclass
class Address:
    phone: ArgType = ArgType(139, "phone help")
    home: ArgType = ArgType("beijing", "phone help")
    test = False


@dataclass
class Education:
    school: ArgType = ArgType('ustb', "phone help")
    grade: ArgType = ArgType("master", "phone help")


@dataclass
class Config:
    name: ArgType = ArgType("test", "name help")
    age: ArgType = ArgType(10, "age help")
    address: Address = Address()
    education: Education = Education()


class Test_XmlConfiguration:
    def test_load_empty(self):
        config: Config = XmlConfiguration(Config).load([])
        assert config.address.phone == 139
        config = XmlConfiguration(Config).load(['config/configuration0.xml'])
        assert config.address.phone == 139

    def test_load_one_level(self):
        config: Config = XmlConfiguration(Config).load(['config/configuration1.xml'])
        assert config.age == 80

    def test_load_one_group(self):
        config: Config = XmlConfiguration(Config).load(['config/configuration2.xml'])
        assert config.address.phone == 136 and config.address.help == "groupHelp"

    def test_load_one_group_arg(self):
        config: Config = XmlConfiguration(Config).load(['config/configuration3.xml'])
        assert config.address.phone == 136 and config.age == 80

    def test_load_full(self):
        config: Config = XmlConfiguration(Config).load(['config/configuration.xml'])
        assert config.address.phone == 136 and config.age == 80 and config.education.school == 'beijing'

    def test_load_multiple(self):
        config: Config = XmlConfiguration(Config).load(
            ['config/configuration1.xml', 'config/configuration2.xml', 'config/configuration3.xml'])
        assert config.address.phone == 136 and config.age == 80 \
               and config.name == 'FinalName'


class Test_Arguments:
    def test_argtype(self):
        arg: ArgType = ArgType(1, 'test')
        arg.set(10, 'test2')
        assert arg == 10 and arg.help == 'test2'

    def test_arg(self):
        arguments = Arguments(grouped=False)
        arguments.arg('name', ArgType('test', 'test name help'))
        args = arguments.parse()
        assert args.name == 'test'
        arguments.arg('address.home', ArgType('beijing', 'address home help'))
        args = arguments.parse()
        assert getattr(args, 'address.home') == 'beijing'
        args: Config = arguments.parseTo(Config())
        assert args.name == 'test' and args.address.home == 'beijing'
        arguments.arg('phone', ArgType(139, 'address phone help'), group='address')
        args = arguments.parse()
        assert getattr(args, 'address.phone') == 139
        args: Config = arguments.parseTo(Config())
        assert args.name == 'test' and args.address.phone == 139

    def test_arg_with_obj(self):
        config: Config = Config()
        arguments = Arguments(config)
        args: Config = arguments.parse()
        assert args.name == 'test' and args.age == 10 and args.address.phone == 139

    def test_with_xmlfile(self):
        config: Config = XmlConfiguration(Config).load(['config/configuration.xml'])
        arguments = Arguments(config)
        config: Config = arguments.parse()
        assert config.address.phone == 136 and config.age == 80 and config.education.school == 'beijing'
