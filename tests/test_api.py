import unittest
from mock import Mock

from routeros.api import Parser, RouterOS


class TestRouteros(unittest.TestCase):
    def setup(self):
        self.api = RouterOS(protocol=Mock())


class TestParser(unittest.TestCase):
    def setUp(self):
        self.attributes = (
            {
                'attr': '=.id=value',
                'key': '.id',
                'value': 'value',
            },
            {
                'attr': '=name=ether1',
                'key': 'name',
                'value': 'ether1',
            },
            {
                'attr': '=comment=',
                'key': 'comment',
                'value': '',
            }
        )
    
    def test_parse_word(self):
        for attribute in self.attributes:
            self.assertEqual(Parser.parse_word(attribute['attr']),
                             (attribute['key'], attribute['value']))
        
    def test_compose_word(self):
        for attribute in self.attributes:
            attr = Parser.compose_word(attribute['key'], attribute['value'])
            self.assertEqual(attribute['attr'], attr)
