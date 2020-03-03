import yaml
import logging
import logging.config

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper


def load_config(file: str):
    try:
        with open(file, 'r') as stream:
            return yaml.load(stream=stream, Loader=Loader)
    except FileNotFoundError:
        print('File Not Found: ' + file)
        return None


conf = load_config('logging.yaml')
if conf is not None:
    logging.config.dictConfig(conf)


def getLogger(name: str):
    return logging.getLogger(name)


def getRootLogger():
    return logging.getLogger('root')


