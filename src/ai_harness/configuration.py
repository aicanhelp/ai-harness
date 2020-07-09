from ai_harness import harnessutils as utils
from ai_harness.inspector import Inspector
import argparse
from ai_harness.configclasses import configclass, field, fields, Field, is_configclass, make_configclass, merge_fields, \
    export, to_json_string


def arg(value, help):
    return field(default=value, metadata={"help": help})


class ConfigInspector:
    def __init__(self, config):
        self.config = config
        self.fields = self._get_fields(config)
        self.configClasses = self._get_configClasses(config)

    def _get_fields(self, config):
        fieldDict = dict()
        for field in fields(config): fieldDict.setdefault(field.name, field)
        return fieldDict

    def _get_configClasses(self, config):
        configClassesDict = dict()
        for k, v in config.__dict__.items():
            if v is None: continue
            if is_configclass(v): configClassesDict.setdefault(k, v)
        return configClassesDict

    def is_configClass(self, fieldName):
        return self.configClasses.__contains__(fieldName)

    def get_field(self, name):
        return self.fields.get(name)

    def get_field_with_parent(self, name, root_parent=None):
        root_parent = self.config if not root_parent else root_parent
        this_field = self._get_fields(root_parent).get(name)
        if this_field: return root_parent, this_field
        for sub_name, sub_config in self._get_configClasses(root_parent).items():
            parent, this_field = self.get_field_with_parent(name, sub_config)
            if this_field: return sub_config, this_field
        return None, None

    def set(self, name, value=None, help=None, parse_name=False):
        parent = self.config
        if parse_name:
            attributes = name.split('.')
            name = attributes[-1]

            for attr in attributes[:-1]:
                parent = self._get_configClasses(parent).get(attr)
            this_field = self._get_fields(parent).get(name)
        else:
            parent, this_field = self.get_field_with_parent(name, parent)

        if this_field is None: return
        if value is not None: setattr(parent, name, this_field.type(value))
        if help is not None and help != '': this_field.help = help

    def value(self, name):
        getattr(self.config, name)

    def help(self, name):
        field = self.get_field(name)
        if field is not None: return field.help
        if hasattr(self.config, name):
            attr = getattr(self.config, name)
            if attr is not None and hasattr(attr, 'help'): return getattr(attr, 'help')
        return None


class XmlConfiguration:
    def __init__(self, config):
        if config is None: raise ValueError("target config type can not be none.")

        if type(config) == type: self.config = config()
        self.configInspector = ConfigInspector(self.config)

    def __set_xml2arg(self, groupInspector, argXml):
        argName = argXml['name'].replace('-', '_')
        groupInspector.set(argName, argXml['default'], argXml['help'])

    def __set_xml2group(self, groupObj, groupXml):
        if not hasattr(groupXml, 'arg'): return
        groupInspector = ConfigInspector(groupObj)
        if isinstance(groupXml.arg, list):
            for arg in groupXml.arg: self.__set_xml2arg(groupInspector, arg)
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
            if groupObj is None: return
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
        if xml_files is None: return self.config
        for xml_file in xml_files:
            xml = utils.load_xml(xml_file)

            if xml is None: return self.config

            # if has group, set the args in the groups
            if hasattr(xml.configuration, 'group'):
                if isinstance(xml.configuration.group, list):
                    for group in xml.configuration.group: self.__find_set_xml2group(self.config, group)
                else:
                    self.__find_set_xml2group(self.config, xml.configuration.group)
            ## set other args
            if hasattr(xml.configuration, 'arg'): self.__set_xml2group(self.config, xml.configuration)

        return self.config


class ComplexArguments:
    def __init__(self, sub_arg_objs: dict, with_group_prefix=False, conflict_error=False):
        self._conflict_handler = 'error' if conflict_error else 'resolve'
        self._parser = argparse.ArgumentParser(conflict_handler=self._conflict_handler)
        self._subparsers = self._parser.add_subparsers(help='sub-command help', dest='cmd')
        self._subparsers.required = True
        self._sub_arg_objs = sub_arg_objs
        self._with_group_prefix = with_group_prefix
        self._conflict_error = conflict_error
        self._arg_objs = {}
        self.__create_args()

    def __create_args(self):
        for sub, arg_obj in self._sub_arg_objs.items():
            if arg_obj is None: continue
            parser = self._subparsers.add_parser(sub, conflict_handler=self._conflict_handler,
                                                 help='{} help'.format(sub))
            self._arg_objs[sub] = Arguments(arg_obj, parser, self._with_group_prefix, self._conflict_error)

    def _get_arg_obj(self, sub, args):
        argument: Arguments = self._arg_objs[sub]
        return argument.set_values(args, self._with_group_prefix)

    def parse(self, args=None):
        args, _ = self._parser.parse_known_args(args)
        # print("parsed input args:{}".format(str(args)))
        if not self._arg_objs: return None, None
        return args.cmd, self._get_arg_obj(args.cmd, args)


class Arguments:
    def __init__(self, configObj, parser=None, with_group_prefix=False, conflict_error=False):
        self.parser = argparse.ArgumentParser(
            conflict_handler='error' if conflict_error else 'resolve') if parser is None else parser
        self.destObj = configObj
        self.with_group_prefix = with_group_prefix
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
        if group is not None: return group
        group = self.parser.add_argument_group(groupName, help)
        self.groups.setdefault(groupName, group)
        return group

    def _arg(self, field, v, parser, group=None):
        name = field.name
        if group is not None: name = group + '.' + name

        action = self.__get_type_action(field)
        required = True
        if v is None: required = False
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
            parser = self.__get_group(k, configInspector.help(k))
            group_name = k if self.with_group_prefix else None
            self._arg_obj(ConfigInspector(v), parser, group_name)

        return self

    def set_values(self, args, with_group_prefix=False):
        for k, v in args.__dict__.items():
            if v: self.configInspector.set(k, v, None, with_group_prefix)
        return self.destObj

    def parse(self, args=None, with_group_prefix=False):
        args, _ = self.parser.parse_known_args(args)

        return self.set_values(args, with_group_prefix)
