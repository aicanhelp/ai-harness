from aiharness import harnessutils as utils
from aiharness.inspector import Inspector
from wrapt import ObjectProxy
import argparse


class ArgType(ObjectProxy):
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


class XmlConfiguration:
    def __init__(self, config):
        if config is None:
            raise ValueError("target config type can not be none.")

        if type(config) == type:
            self.config = config()

    def __set_xml2arg(self, groupObj, argXml):
        argName = argXml['name'].replace('-', '_')
        argObj: ArgType = getattr(groupObj, argName)
        if argObj is None:
            return
        argObj.set(argXml['default'], argXml['help'])

    def __set_xml2group(self, groupObj, groupXml):
        if not hasattr(groupXml, 'arg'):
            return
        if isinstance(groupXml.arg, list):
            for arg in groupXml.arg:
                self.__set_xml2arg(groupObj, arg)
        else:
            self.__set_xml2arg(groupObj, groupXml.arg)

    def __find_set_xml2group(self, config, groupXml):
        groupName = groupXml['name'].replace('-', '_')
        groupHelp = groupXml['help']
        groupObj = getattr(config, groupName)
        if groupObj is None:
            return
        setattr(groupObj, 'help', groupHelp)
        self.__set_xml2group(groupObj, groupXml)

    def load(self, xml_files: []):
        """
        Function for loading the xml_file into the configuration object.
        This function can be called multiple times to load multiple xml files.
        And the configuration value will be overrode by the following xml configuration.
        :param xml_file:
        :return: configuration object
        """
        if xml_files is None:
            return self.config
        for xml_file in xml_files:
            xml = utils.load_xml(xml_file)

            if xml is None:
                return self.config

            # if has group, set the args in the groups
            if hasattr(xml.configuration, 'group'):
                if isinstance(xml.configuration.group, list):
                    for group in xml.configuration.group:
                        self.__find_set_xml2group(self.config, group)
                else:
                    self.__find_set_xml2group(self.config, xml.configuration.group)
            ## set other args
            if hasattr(xml.configuration, 'arg'):
                self.__set_xml2group(self.config, xml.configuration)

        return self.config


class Arguments:
    def __init__(self, configObj=None, grouped=True):
        self.parser = argparse.ArgumentParser()
        self.destObj = configObj
        self.grouped = grouped
        self.groups = dict()
        self.arg_obj(configObj)

    def __get_type_action(self, argument: ArgType):
        action = 'store'
        t = type(ArgType)
        if t == bool:
            if argument.default:
                return t, 'store_false'
            else:
                return t, 'store_true'
        return t, action

    def __get_group(self, groupName, help=''):
        group = self.groups.get(groupName)
        if group is not None:
            return group
        group = self.parser.add_argument_group(groupName, help)
        self.groups.setdefault(groupName, group)
        return group

    def __prepare_arg(self, name, parser, group):
        argName = name
        if group is not None and not self.grouped:
            argName = group + '.' + argName
        if parser is None:
            if group is None:
                parser = self.parser
            else:
                parser = self.__get_group(group)
        return argName, parser

    def arg(self, name, argument: ArgType, parser=None, group=None):
        argName, parser = self.__prepare_arg(name, parser, group)

        t, action = self.__get_type_action(argument)

        parser.add_argument('--' + argName,
                            default=argument,
                            required=False,
                            action=action,
                            help=argument.help)
        return self

    def arg_obj(self, obj, groupName=None):
        if obj is None:
            return self
        parser = self.parser
        for k, v in obj.__dict__.items():
            if isinstance(v, ArgType):
                self.arg(k, v, parser, groupName)
            else:
                if groupName is not None:
                    continue
                if self.grouped:
                    groupHelp = ''
                    if hasattr(v, 'help'):
                        groupHelp = getattr(v, 'help')
                    parser = self.__get_group(k, groupHelp)
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
