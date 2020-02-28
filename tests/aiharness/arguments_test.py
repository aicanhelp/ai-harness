from aiharness.arguments import *
import logging

log = logging.getLogger()


@dataclass()
class TestObj:
    name: str = ''
    age: int = 0
    address: str = ''
    online: bool = False
    company: str = ''
    product: str = ''


class TestArguments:
    def test_set_with_object(self):
        arguments = Arguments(TestObj())
        argument = Argument(name="name", default="1", required=False, help="Help")
        arguments.set_with_object(argument)
        obj = arguments.parse()
        assert isinstance(obj, TestObj)
        assert obj.name == '1'
        return

    def test_arguments(self):
        args = [
            Argument(name="name", default="1", required=False, help="Help"),
            Argument(name="age", default="2", required=False, help="Help"),
            Argument(name="address", default="3", required=False, help="Help"),
            Argument(name="online", default="True", required=False, help="Help")
        ]
        arguments = Arguments(TestObj())
        arguments.set_with_objects(args)
        obj: TestObj = arguments.parse()
        assert obj.name == '1' and obj.age == 2 and obj.address == '3' and obj.online

    def test_yaml_arguments(self):
        arguments = Arguments(TestObj())
        arguments.set_from_yaml('arguments.yaml')
        obj: TestObj = arguments.parse()
        assert obj.name == 'test'

