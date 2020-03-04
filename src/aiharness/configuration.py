from dataclasses import dataclass

from aiharness import harnessutils as utils
from aiharness.inspector import Inspector
from aiharness.objectproxy import ObjectWrapper
import argparse


class ArgType(ObjectWrapper):
    help = None
    type = None

    def __init__(self, v, h=None):
        super().__init__(v)
        self.help = h
        self.type = type(v)

    def set(self, v, h=None):
        super().__init__(self.type(v))
        self.help = h
        return self


@dataclass
class Arg:
    name: str
    arg: ArgType
    group: str = None


def __set_xml2group(groupObj, groupXml):
    for arg in groupXml.arg:
        argName = arg['name'].replace('-', '_')
        argObj: ArgType = getattr(groupObj, argName)
        if argObj is None:
            continue
        argObj.set(groupXml['default'], groupXml['help'])


def __find_set_xml2group(config, groupXml):
    groupName = groupXml['name'].replace('-', '_')
    groupObj = getattr(config, groupName)
    if groupObj is None:
        return
    __set_xml2group(groupObj, groupXml)


def load_xml2obj(xml_file, configType):
    if configType is None:
        raise ValueError("target config type can not be none.")

    config = configType()

    xml = utils.load_xml(xml_file)

    if config is None:
        return

    if hasattr(xml.configuration, 'group'):
        if isinstance(xml.configuration.group, list):
            for group in xml.configuration.group:
                __find_set_xml2group(config, group)
        else:
            __find_set_xml2group(config, xml.configuration.group)
    else:
        __set_xml2group(config, xml.configuration)

    return config


class Arguments:
    def __init__(self, configObj=None):
        self.parser = argparse.ArgumentParser()
        self.destObj = configObj
        self.arg_obj(configObj)

    def __get_type_action(self, argument: ArgType):
        action = 'store'
        t = type(ArgType)
        if t == bool:
            if argument.default:
                return t, 'store_true'
            else:
                return t, 'store_false'
        return t, action

    def args(self, args: [Arg]):
        arg: Arg
        for arg in args:
            self.arg(arg.name, arg.arg, arg.group)

    def arg(self, name, argument: ArgType, group=None):
        argName = name
        if group is not None:
            argName = group + '.' + argName
        argName = argName.replace('_', '-')

        t, action = self.__get_type_action(argument)

        self.parser.add_argument('--' + argName,
                                 default=argument,
                                 required=False,
                                 action=action,
                                 help=argument.help)
        return self

    def arg_obj(self, obj, group=None):
        if obj is None:
            return self
        for k, v in obj.__dict__.items():
            if isinstance(v, ArgType):
                self.arg(k, v, group)
            else:
                self.arg_obj(v, k)
        return self

    def parse(self, args=None):
        return self.parseTo(self.destObj, args)

    def parseTo(self, dest, args=None):
        args, _ = self.parser.parse_known_args(args)
        if dest is None:
            return args

        for k, _ in args.__dict__.items():
            Inspector.set_attr_from(args, dest, k, False, True)

        return dest
