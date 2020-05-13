from typing import List

from ai_harness import harnessutils as utils
import yaml
import argparse

log = utils.getLogger('aiharness')


def test_yaml():
    data = yaml.load(stream=open('arguments.yaml', 'r'), Loader=utils.Loader)
    assert data is not None


def test_load_config():
    conf = utils.load_yaml('arguments.yaml')
    assert conf is not None


def test_argparse():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model-name')
    args = parser.parse_known_args()
    log.info(args)


def test_array():
    def create(a: List[int], b: int):
        for i in a:
            log.info(i)
