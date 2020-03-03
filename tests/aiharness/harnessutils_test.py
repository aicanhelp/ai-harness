from aiharness import harnessutils as utils
import yaml

log = utils.getRootLogger()


def test_yaml():
    data = yaml.load(stream=open('arguments.yaml', 'r'), Loader=utils.Loader)
    assert data is not None


def test_load_config():
    conf = utils.load_config('arguments.yaml')
    assert conf is not None
