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


@dataclass()
class ComplexTextObj:
    model: TestObj = TestObj()


class TestArguments:
    def test_set_with_object(self):
        arguments = Arguments(TestObj)
        argument = Argument(name="name", default="1", help="Help")
        arguments.set_with_object(argument)
        obj = arguments.parse()
        assert isinstance(obj, TestObj)
        assert obj.name == '1'
        return

    def test_arguments(self):
        args = [
            Argument(name="name", default="1", help="Help"),
            Argument(name="age", default="2", help="Help"),
            Argument(name="address", default="3", help="Help"),
            Argument(name="online", default="True", help="Help")
        ]
        arguments = Arguments(TestObj)
        arguments.set_with_objects(args)
        obj: TestObj = arguments.parse()
        assert obj.name == '1' and obj.age == 2 and obj.address == '3' and obj.online

    def test_yaml_argument_list(self):
        arguments = Arguments(TestObj)
        arguments.set_from_yaml('argument-list.yaml')
        obj: TestObj = arguments.parse()
        assert obj.name == 'test'

    def test_complex_argument_yaml(self):
        arguments = Arguments(ComplexTextObj)
        arguments.set_from_yaml('arguments.yaml')
        obj: ComplexTextObj = arguments.parse()
        assert obj.model.name == 'test'
