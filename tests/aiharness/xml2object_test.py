from ai_harness import xml2object
from ai_harness import harnessutils as utils

log = utils.getLogger('test')


def test_xml2object():
    obj = xml2object.parse('configuration.xml')
    assert len(obj.configuration.group) == 2
    assert obj.configuration.group[0]['name'] == 'model'
    assert obj.configuration.group[0].arg[0]['name'] == 'test1'
    assert hasattr(obj.configuration, 'group')
    assert isinstance(obj.configuration.group, list)
