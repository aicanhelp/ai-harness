from dataclasses import dataclass
from aiharness import harnessutils as utils

import argparse


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
            t = utils.field_type(self.destObj, argument.name)
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
            t = utils.field_type(self.destObj, argument.get('name'))
        self.parser.add_argument('--' + argument.get('name'),
                                 default=argument.get('default'),
                                 type=t,
                                 required=argument.get('required'),
                                 action=argument.get('action'),
                                 help=argument.get('help'))

    def set_with_objects(self, arguments: []):
        if arguments is None:
            return self
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
            utils.set_attr(args, self.destObj, k)

        return self.destObj

    def set_from_yaml(self, yaml_file):
        self.set_with_objects(utils.load_config(yaml_file))
        return self
