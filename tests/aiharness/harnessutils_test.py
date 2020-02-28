from dataclasses import dataclass

from aiharness import harnessutils
import yaml
import logging

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

log = logging.getLogger()


@dataclass()
class User:
    name: str = None


def test_field_type():
    type = harnessutils.field_type(User(), 'name')
    assert type == str
    assert harnessutils.field_type(User(), 'n') is None


def test_set_attr():
    o1 = User()
    o2 = User()
    o1.name = '1'
    harnessutils.set_attr(o1, o2, 'name')
    assert o2.name == '1' and o1.name == o2.name
    harnessutils.set_attr(None, None, 'name')
    harnessutils.set_attr(o1, None, 'name')
    harnessutils.set_attr(None, o2, 'name')
    harnessutils.set_attr(o1, o2, None)
    harnessutils.set_attr(o1, o2, 'n')


def test_yaml():
    data = yaml.load(stream=open('arguments.yaml', 'r'), Loader=Loader)
    logging.info(data)

    return
