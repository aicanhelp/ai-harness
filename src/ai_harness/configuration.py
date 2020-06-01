from ai_harness import harnessutils as utils
from ai_harness.inspector import Inspector
import argparse
from ai_harness.configclasses import configclass, field, fields, Field, is_configclass


def arg(value, help):
    return field(default=value, metadata={"help": help})


class ConfigInspector:
    def __init__(self, config):
        self.config = config
        self.fields = self._get_fields()
        self.configClasses = self._get_configClasses()

    def _get_fields(self):
        fieldDict = dict()
        for field in fields(self.config):
            fieldDict.setdefault(field.name, field)
        return fieldDict

    def _get_configClasses(self):
        configClassesDict = dict()
        for k, v in self.config.__dict__.items():
            if v is None:
                continue
            if is_configclass(v):
                configClassesDict.setdefault(k, v)
        return configClassesDict

    def is_configClass(self, fieldName):
        return self.configClasses.__contains__(fieldName)

    def get_field(self, name):
        return self.fields.get(name)

    def set(self, name, value=None, help=None):
        if not hasattr(self.config, name):
            return
        field = self.get_field(name)
        if field is None:
            return

        if value is not None:
            setattr(self.config, name, field.type(value))

        if help is not None and help != '':
            field.help = help

    def value(self, name):
        getattr(self.config, name)

    def help(self, name):
        field = self.get_field(name)
        if field is not None:
            return field.help
        if hasattr(self.config, name):
            attr = getattr(self.config, name)
            if attr is not None and hasattr(attr, 'help'):
                return getattr(attr, 'help')
        return None


class XmlConfiguration:
    def __init__(self, config):
        if config is None:
            raise ValueError("target config type can not be none.")

        if type(config) == type:
            self.config = config()
        self.configInspector = ConfigInspector(self.config)

    def __set_xml2arg(self, groupInspector, argXml):
        argName = argXml['name'].replace('-', '_')
        groupInspector.set(argName, argXml['default'], argXml['help'])

    def __set_xml2group(self, groupObj, groupXml):
        if not hasattr(groupXml, 'arg'):
            return
        groupInspector = ConfigInspector(groupObj)
        if isinstance(groupXml.arg, list):
            for arg in groupXml.arg:
                self.__set_xml2arg(groupInspector, arg)
        else:
            self.__set_xml2arg(groupInspector, groupXml.arg)

    def __find_set_xml2group(self, config, groupXml):
        groupName = groupXml['name'].replace('-', '_')
        groupHelp = groupXml['help']
        groupField = self.configInspector.get_field(groupName)
        groupObj = getattr(config, groupName)
        if groupField is not None:
            self.configInspector.set(groupName, help=groupHelp)
        else:
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


class ComplexArguments:
    def __init__(self, sub_arg_objs: dict, grouped=True):
        self._parser = argparse.ArgumentParser()
        self._subparsers = self._parser.add_subparsers(help='sub-command help')
        self._sub_arg_objs = sub_arg_objs
        self._grouped = grouped
        self._arg_objs = {}
        self.__create_args()

    def __create_args(self):
        for sub, arg_obj in self._sub_arg_objs.items():
            if arg_obj is None:
                continue
            parser = self._subparsers.add_parser(sub, help='{} help'.format(sub))
            self._arg_objs[sub] = Arguments(arg_obj, parser, self._grouped)
            parser.set_defaults(func=sub)

    def _get_arg_obj(self, sub, args):
        argument: Arguments = self._arg_objs[sub]
        for k, _ in args.__dict__.items():
            Inspector.set_attr_from(args, argument.destObj, k, False, True)
        return argument.destObj

    def parse(self, args=None):
        args, _ = self._parser.parse_known_args(args)
        if not self._arg_objs:
            return None
        return self._get_arg_obj(args.func, args)


class Arguments:
    def __init__(self, configObj, parser=None, grouped=True):
        self.parser = argparse.ArgumentParser() if parser is None else parser
        self.destObj = configObj
        self.grouped = grouped
        self.groups = dict()
        self.configInspector = ConfigInspector(self.destObj)
        self._arg_obj(self.configInspector, self.parser)

    def __get_type_action(self, field):
        action = 'store'
        if field.type == bool:
            if field.default:
                return 'store_false'
            else:
                return 'store_true'
        return action

    def __get_group(self, groupName, help=''):
        group = self.groups.get(groupName)
        if group is not None:
            return group
        group = self.parser.add_argument_group(groupName, help)
        self.groups.setdefault(groupName, group)
        return group

    def _arg(self, field, v, parser, group=None):
        name = field.name
        if group is not None:
            name = group + '.' + name

        action = self.__get_type_action(field)
        required = True
        if v is None:
            required = False
        name = name.replace('_', '-')
        parser.add_argument('--' + name,
                            default=v,
                            required=required,
                            action=action,
                            help=field.help)
        return self

    def _arg_obj(self, configInspector, parser, groupName=None):
        for name, field in configInspector.fields.items():
            v = configInspector.value(name)
            if not configInspector.is_configClass(name):
                self._arg(field, v, parser, groupName)

        for k, v in configInspector.configClasses.items():
            if self.grouped:
                parser = self.__get_group(k, configInspector.help(k))
                self._arg_obj(ConfigInspector(v), parser, k)
            else:
                self._arg_obj(ConfigInspector(v), self.parser, k)

        return self

    def parse(self, args=None):
        args, _ = self.parser.parse_known_args(args)

        for k, _ in args.__dict__.items():
            Inspector.set_attr_from(args, self.destObj, k, False, True)

        return self.destObj
