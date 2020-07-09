from argparse import ArgumentParser

from ai_harness.configclasses import to_json_string
from ai_harness.configuration import *
from ai_harness import harnessutils as utils

log = utils.getLogger('aiharness')


@configclass
class Address:
    phone: int = field(139, "phone help")
    home: str = field("beijing", "phone help")
    test: bool = False


@configclass
class Education:
    school: str = field('ustb', "phone help")
    grade: str = field("master", "phone help")


@configclass
class Additions:
    test: str = field('test')


@configclass
class Config:
    name: str = field("test", "name help")
    age: int = field(10, "age help")
    address: Address = Address()
    education: Education = Education()
    a_address: str = None


class Test_ConfigInspector:
    def test_get_field(self):
        config = Config()
        inspector = ConfigInspector(config)
        p, f = inspector.get_field_with_parent('name')
        assert f.type == str

    def test_set(self):
        config = Config()
        inspector = ConfigInspector(config)
        inspector.set('name', 'AAA')
        assert config.name == 'AAA'
        inspector.set('education.school', 'TTT', parse_name=True)
        assert config.education.school == 'TTT'
        inspector.set('school', 'SSS')
        assert config.education.school == 'SSS'


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
        assert config.address.phone == 136 and ConfigInspector(config).help('address') == "groupHelp"

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


class Test_ArgumentParser:
    def test_configclass(self):
        Address(phone='189', home='beijing', test=True)

    def test_duplicate(self):
        parser = ArgumentParser(conflict_handler='resolve')
        parser.add_argument('--name', default=None)
        parser.add_argument('--name', default=None)


class Test_Arguments:
    def test_arg_with_obj(self):
        config: Config = Config()
        arguments = Arguments(config)
        args: Config = arguments.parse()
        assert args.name == 'test' and args.age == 10 and args.address.phone == 139

    def test_args_setting(self):
        config: Config = Config()
        arguments = Arguments(config)
        args: Config = arguments.parse(['--a-address=test', '--school=beijing'])
        assert args.a_address == 'test' and args.education.school == 'beijing'

    def test_with_xmlfile(self):
        config: Config = XmlConfiguration(Config).load(['config/configuration.xml'])
        arguments = Arguments(config)
        config: Config = arguments.parse()
        assert config.address.phone == 136 and config.age == 80 and config.education.school == 'beijing'


class Test_ComplexArguments:
    def test_arg_with_obj(self):
        config: Config = Config()
        config.task = "test"
        config.a_address = Address()
        arguments = ComplexArguments({"test": config, "test2": Config()}, with_group_prefix=True)
        cmd, args = arguments.parse(["test", "--name=tttt", "--a-address.phone=138"])
        print(args, config.task)
        assert config.name == 'tttt' and args.age == 10 and config.a_address.phone == 138

    def test_dynamic_additions(self):
        new_cls = merge_fields(Config, Additions)
        dest_obj = new_cls()
        print(to_json_string(dest_obj))
        arguments = Arguments(dest_obj)
        args = arguments.parse()
        assert args.test
        args.test = 'hello'
        additions = export(args, Additions)
        assert additions.test == 'hello'
