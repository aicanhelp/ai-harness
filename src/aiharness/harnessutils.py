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


def field_type(obj, name):
    if obj is None:
        return None
    field = type(obj).__dict__.get('__dataclass_fields__').get(name)
    if field is None:
        return None
    return field.type


def set_attr(o1, o2, attr):
    if o1 is None or o2 is None or attr is None:
        return
    t = field_type(o2, attr)
    if t is not None and hasattr(o1, attr):
        v = getattr(o1, attr)
        if v is not None:
            setattr(o2, attr, t(v))
