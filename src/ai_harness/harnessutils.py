import yaml
import logging
import logging.config
from ai_harness import xml2object

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper


def load_yaml(file: str):
    try:
        with open(file, 'r') as stream:
            return yaml.load(stream=stream, Loader=Loader)
    except FileNotFoundError:
        print('File Not Found: ' + file)
        return None


conf = load_yaml('logging.yaml')
if conf is not None:
    logging.config.dictConfig(conf)


def getLogger(name: str):
    return logging.getLogger(name)


def getRootLogger():
    return logging.getLogger('root')


log = getRootLogger()


def load_xml(xml_file):
    try:
        return xml2object.parse(xml_file)
    except Exception as e:
        log.error(e)
    return None
