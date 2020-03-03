from dataclasses import dataclass
from aiharness import harnessutils as utils
from aiharness.inspector import Inspector

import argparse


@dataclass()
class Argument:
    name: str = None
    default: str = None
    help: str = ''


class Arguments:
    def __init__(self, argType):
        self.parser = argparse.ArgumentParser()
        self.destObj = argType()

    def __get_type_action(self, argument: Argument, argName):
        t = 'store'
        if self.destObj is not None:
            t = Inspector.field_type(self.destObj, argName, True)
        if t == bool:
            if argument.default:
                return t, 'store_true'
            else:
                return t, 'store_false'
        return t, None

    def set_with_object(self, argument: Argument, group=None):
        argName = argument.name
        if group is not None:
            argName = group + '.' + argName
        t, action = self.__get_type_action(argument, argName)

        self.parser.add_argument('--' + argName,
                                 default=t(argument.default),
                                 required=False,
                                 action=action,
                                 help=argument.help)
        return self

    def set_with_objects(self, arguments: [], group=None):
        if arguments is None:
            return self
        for argument in arguments:
            if type(argument) is Argument:
                self.set_with_object(argument, group)
            if type(argument) is dict:
                self.set_with_object(Inspector.dict2obj(argument, Argument()), group)
        return self

    def set_with_dict_tree(self, d: dict):
        if dict is None:
            return self
        for k, v in d.items():
            if v is None:
                t = Inspector.get_attr_with_type(self.destObj, v)

            self.set_with_objects(v, k)

    def parse(self, args=None):
        args, _ = self.parser.parse_known_args(args)
        if self.destObj is None:
            return args

        for k, _ in args.__dict__.items():
            Inspector.set_attr_from(args, self.destObj, k, False, True)

        return self.destObj

    def set_from_yaml(self, yaml_file):
        config = utils.load_config(yaml_file)
        if type(config) == list:
            self.set_with_objects(config)
        else:
            self.set_with_dict_tree(config)
        return self
