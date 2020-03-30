from aiharness.configclasses import configclass

from aiharness import harnessutils as utils
from aiharness.inspector import Inspector

log = utils.getRootLogger()


@configclass()
class Address:
    phone: int = None
    home: str = None


@configclass()
class User:
    name: str = None
    online: bool = False
    address: Address = Address()


class TestInspector():
    def test_field_type(self):
        type = Inspector.field_type(User(), 'name')
        assert type == str
        assert Inspector.field_type(User(), 'n') is None
        type = Inspector.field_type(User(), 'address.phone', True)
        assert type == int

    def test_get_attr(self):
        o = User()
        o.name = 'test'
        o.address.phone = 123
        assert Inspector.get_attr(o, 'name') == 'test'
        assert Inspector.get_attr(o, 'n') is None
        assert Inspector.get_attr(o, 'address.phone', True) == 123

    def test_set_attr_from(self):
        o1 = User()
        o2 = User()
        o1.name = '1'

        Inspector.set_attr_from(o1, o2, 'name')
        assert o2.name == '1' and o1.name == o2.name
        Inspector.set_attr_from(None, None, 'name')
        Inspector.set_attr_from(o1, None, 'name')
        Inspector.set_attr_from(None, o2, 'name')
        Inspector.set_attr_from(o1, o2, None)
        Inspector.set_attr_from(o1, o2, 'n')
        o1.address.phone = 123
        Inspector.set_attr_from(o1, o2, 'address.phone')
        assert o2.address.phone == 123

    def test_dict2obj(self):
        dict = {"name": "test", "online": "True"}
        o: User = Inspector.dict2obj(dict, User())
        assert o.name == 'test' and o.online and Inspector.field_type(o, 'online') == bool
