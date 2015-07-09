import unittest
import textwrap
import yaml

from lymph.config import Configuration
from lymph.exceptions import ConfigurationError


class ConfigurationTests(unittest.TestCase):
    def load_yaml(self, yml):
        return Configuration(yaml.load(textwrap.dedent(yml)))

    def test_setdefault_without_previous_value(self):
        config = Configuration({
            'nested': {}
        })
        config.setdefault('foo', 1)
        self.assertEqual(config.get('foo'), 1)
        config.setdefault('nested.foo', 2)
        self.assertEqual(config.get('nested.foo'), 2)

    def test_setdefault_with_previous_value(self):
        config = Configuration({
            'foo': 1,
            'nested': {
                'foo': 2
            }
        })
        config.setdefault('foo', 0)
        self.assertEqual(config.get('foo'), 1)
        config.setdefault('nested.foo', 0)
        self.assertEqual(config.get('nested.foo'), 2)

    def test_get_missing_key(self):
        config = Configuration({'a': {'b': 1}, 'c': None})

        self.assertIsNone(config.get('x'))
        self.assertEqual(config.get('x', 2), 2)

        self.assertIsNone(config.get('x.x'), None)
        self.assertEqual(config.get('x.x', 2), 2)

        self.assertIsNone(config.get('c.x'), None)
        self.assertEqual(config.get('c.x', 2), 2)

    def test_set_in_empty_sections(self):
        config = self.load_yaml("""
        foo:
        """)
        # yaml doesn't know that we expect `foo` to be a dict
        self.assertIsNone(config.get('foo'))
        config.set('foo.bar', 1)
        self.assertEqual(config.get('foo.bar'), 1)

    def test_update(self):
        config = Configuration({'a': 1, 'b': {'c': 2}})
        config.update({'a': 2})
        self.assertEqual(config.get('a'), 2)
        self.assertEqual(config.get('b.c'), 2)

    def test_contains(self):
        config = Configuration({'a': {'b': 1}})
        self.assertTrue('a' in config)
        self.assertFalse('foo' in config)
        view = config.get('a')
        self.assertTrue('b' in view)
        self.assertFalse('foo' in view)

    def test_env_replacement(self):
        config = Configuration({
            'replace': 'prefix_$(env.FOO_BAR)_suffix',
            'type_conversion': 'prefix_$(env.FOURTYTWO)',
            'keep_int': '$(env.FOURTYTWO)',
            'keep_dict': '$(env.DICT)',
            'no_parens': '$env.FOO_BAR',
            'no_namespace': '$(FOO_BAR)',
            'nested': '$(var.nested.foo)',
            'dashes': '$(var.dashed-name)',
        }, env={
            'FOO_BAR': '42',
            'FOURTYTWO': 42,
            'DICT': {},
        }, var=Configuration({
            'dashed-name': True,
            'nested': {
                'foo': 1764,
            }
        }))
        self.assertEqual(config.get('replace'), 'prefix_42_suffix')
        self.assertEqual(config.get('type_conversion'), 'prefix_42')
        self.assertEqual(config.get('keep_int'), 42)
        self.assertEqual(config.get('keep_dict'), {})
        self.assertEqual(config.get('no_parens'), '$env.FOO_BAR')
        self.assertEqual(config.get('no_namespace'), '$(FOO_BAR)')
        self.assertEqual(config.get('nested'), 1764)
        self.assertEqual(config.get('dashes'), True)

    def test_missing_env_replacement(self):
        self.assertRaises(ConfigurationError, Configuration, {
            'missing': '$(env.MISSING)'
        }, env={})
        self.assertRaises(ConfigurationError, Configuration, {
            'bad_namespace': '$(env.FOO_BAR)',
        }, other={})


class ConfigurableThing(object):
    def __init__(self, config):
        self.config = config

    @classmethod
    def from_config(cls, config):
        return cls(dict(config.items()))


class CreateInstanceTest(unittest.TestCase):
    config = Configuration({
        "thing": {
            "class": "%s:ConfigurableThing" % __name__,
            "param": 41
        },
        "section": {
            "thing": {
                "class": "%s:ConfigurableThing" % __name__,
                "param": 42
            },
        }
    })

    def test_create_instance(self):
        obj = self.config.create_instance('thing')
        self.assertIsInstance(obj, ConfigurableThing)
        self.assertEqual(obj.config['param'], 41)

    def test_create_instance_on_view(self):
        config = self.config.get('section')
        obj = config.create_instance('thing')
        self.assertIsInstance(obj, ConfigurableThing)
        self.assertEqual(obj.config['param'], 42)


class GetInstanceTest(unittest.TestCase):
    config = Configuration({
        "thing": {
            "class": "%s:ConfigurableThing" % __name__,
        }
    })

    def test_creates_instance_based_on_configuration(self):
        instance = self.config.get_instance("thing")
        self.assertIsInstance(instance, ConfigurableThing)

    def test_returns_the_same_instance_on_multiple_invocations(self):
        instance_1 = self.config.get_instance("thing")
        instance_2 = self.config.get_instance("thing")
        self.assertIs(instance_1, instance_2)


class GetDependencyTest(unittest.TestCase):
    config = Configuration({
        "dependencies": {
            "thing": {
                "class": "%s:ConfigurableThing" % __name__
            },
        },
        "key": {
            "client": "dep:thing",
        }
    })

    def test_creates_instance_based_on_configuration(self):
        instance = self.config.get_instance("key.client")
        self.assertIsInstance(instance, ConfigurableThing)

    def test_returns_the_same_instance_on_multiple_invocations(self):
        instance_1 = self.config.get_instance("key.client")
        instance_2 = self.config.get_instance("key.client")
        self.assertIs(instance_1, instance_2)
