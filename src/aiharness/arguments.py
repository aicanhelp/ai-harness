from dataclasses import dataclass
from aiharness.harnessutils import set_attr, field_type

import argparse

import yaml
import logging

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

log = logging.getLogger()


@dataclass()
class Argument:
    name: str
    default: str
    required: bool = False
    action: str = None
    help: str = ''


class Arguments:
    def __init__(self, destObj=None):
        self.parser = argparse.ArgumentParser()
        self.destObj = destObj

    def set_with_object(self, argument: Argument):
        t = str
        if self.destObj is not None:
            t = field_type(self.destObj, argument.name)
        self.parser.add_argument('--' + argument.name,
                                 default=argument.default,
                                 type=t,
                                 required=argument.required,
                                 action=argument.action,
                                 help=argument.help)
        return self

    def set_with_dict(self, argument: dict):
        t = str
        if self.destObj is not None:
            t = field_type(self.destObj, argument.get('name'))
        self.parser.add_argument('--' + argument.get('name'),
                                 default=argument.get('default'),
                                 type=t,
                                 required=argument.get('required'),
                                 action=argument.get('action'),
                                 help=argument.get('help'))

    def set_with_objects(self, arguments: []):
        for argument in arguments:
            if type(argument) is Argument:
                self.set_with_object(argument)
            if type(argument) is dict:
                self.set_with_dict(argument)
        return self

    def parse(self, args=None):
        args, _ = self.parser.parse_known_args(args)
        if self.destObj is None:
            return args

        for k, _ in self.destObj.__dict__.items():
            set_attr(args, self.destObj, k)

        return self.destObj

    def set_from_yaml(self, yaml_file):
        with open(yaml_file, 'r') as stream:
            data = yaml.load(stream=stream, Loader=Loader)
            self.set_with_objects(data)
            return self
