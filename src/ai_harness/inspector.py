class NoneAttr:
    pass


class Inspector:
    @staticmethod
    def parse_attribute(instance, name, with_type=False, parse=False):
        parent = instance
        if parse:
            attributes = name.split('.')
            name = attributes[-1]

            for attr in attributes[:-1]:
                parent = getattr(instance, attr, NoneAttr)
                if parent == NoneAttr:
                    return None, None, None

        if not with_type:
            return parent, name, None

        field = type(parent).__dict__.get('__configclass_fields__').get(name)
        if field is None:
            return parent, name, None
        return parent, name, field.type

    @staticmethod
    def field_type(instance, name: str, parse=False):
        _, _, type = Inspector.parse_attribute(instance, name, True, parse)
        return type

    @staticmethod
    def get_attr(instance, name, parse=False):
        parent, name, _ = Inspector.parse_attribute(instance, name, False, parse)
        if parent is None:
            return None
        return getattr(parent, name, None)

    @staticmethod
    def get_attr_with_type(instance, name, parse=False):
        parent, name, type = Inspector.parse_attribute(instance, name, True, parse)
        if parent is None:
            return None, None
        return getattr(parent, name, None), type

    @staticmethod
    def set_attr_from(fromO, toO, attr, parseFrom=True, parseTo=True):
        if fromO is None or toO is None or attr is None:
            return toO
        parent = toO
        name = attr
        t = None
        if parseTo:
            parent, name, t = Inspector.parse_attribute(parent, attr, True, parseTo)
            if parent is None or not hasattr(parent, name):
                return toO

        v = Inspector.get_attr(fromO, attr, parseFrom)

        if v is None:
            return toO

        if t is None:
            setattr(parent, name, v)
        else:
            setattr(parent, name, t(v))

        return toO

    @staticmethod
    def dict2obj(dict: dict, obj):
        for k, v in dict.items():
            setattr(obj, k, v)
        return obj

    @staticmethod
    def initialize_attr(instance, attr, parse=False):
        if instance is None or attr is None:
            return instance
        if getattr(instance, attr) is not None:
            return instance
        t = Inspector.field_type(instance, attr, parse)
        if attr is None:
            return instance
        setattr(instance, attr, t())
