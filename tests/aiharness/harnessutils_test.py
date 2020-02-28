from dataclasses import dataclass

from aiharness import harnessutils as utils
import yaml

log = utils.getRootLogger()


@dataclass()
class User:
    name: str = None


def test_field_type():
    type = utils.field_type(User(), 'name')
    assert type == str
    assert utils.field_type(User(), 'n') is None


def test_set_attr():
    o1 = User()
    o2 = User()
    o1.name = '1'
    utils.set_attr(o1, o2, 'name')
    assert o2.name == '1' and o1.name == o2.name
    utils.set_attr(None, None, 'name')
    utils.set_attr(o1, None, 'name')
    utils.set_attr(None, o2, 'name')
    utils.set_attr(o1, o2, None)
    utils.set_attr(o1, o2, 'n')


def test_yaml():
    data = yaml.load(stream=open('arguments.yaml', 'r'), Loader=utils.Loader)
    assert data is not None


def test_load_config():
    conf = utils.load_config('arguments.yaml')
    assert conf is not None
