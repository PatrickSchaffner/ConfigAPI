from typing import Dict

from pytest import fixture, raises, mark

from configfiles import ConfigDict, ConfigValue
from configfiles.view import dotindex


@fixture(params=[
    {'repo': {'name': 'origin', 'url': 'https://localhost'}},
    {'repo': 0, 'urls': [
        {'name': 'origin', 'url': 'https://localhost'},
        {'name': 'remote', 'url': './proj/'}
    ]},
    {'version': '0.0.5', 'repo': [], 'environment': {
        'prod': {'database': 'proddb', 'log': True},
        'dev': {'database': 'devdb', 'log': False},
    }},
])
def nested_dict(request) -> ConfigDict:
    return request.param.copy()


@fixture
def flat_dict(nested_dict: ConfigDict) -> Dict[str, ConfigValue]:
    flat_dict = {}
    def _flatten(dct: ConfigDict, base=None):
        for (key, val) in dct.items():
            name = key if base is None else base+dotindex.SEPARATOR+key
            if isinstance(val, dict):
                _flatten(val, name)
            else:
                flat_dict[name] = val
    _flatten(nested_dict)
    return flat_dict


def test_get_values(nested_dict: ConfigDict, flat_dict: Dict[str, ConfigValue]) -> None:
    for (key, val) in flat_dict.items():
        assert dotindex.get(nested_dict, key) == val


def test_get_dicts(nested_dict: ConfigDict) -> None:
    def _assert_nested(expected, base=None):
        for (key, val) in expected.items():
            name = key if base is None else base+dotindex.SEPARATOR+key
            actual = dotindex.get(nested_dict, name)
            if not isinstance(actual, dict):
                continue
            assert actual is val
    _assert_nested(nested_dict)


@mark.parametrize('configs', [
    {'not_repo': {}},
    {'repo': 0},
    {'repo': {'not_url': []}},
    {'repo': {'url': False}},
    {'repo': {'url': {}}},
])
def test_get_notfound(configs: ConfigDict) -> None:
    with raises(dotindex.DotIndexException) as exc_info:
        dotindex.get(configs, 'repo.url.notfound', raise_missing=True)
    assert type(exc_info.value) == dotindex.NotFoundException
    assert isinstance(exc_info.value, KeyError)
    assert dotindex.get(configs, 'repo.url.notfound', raise_missing=False) is None


def test_contains_values(nested_dict: ConfigDict, flat_dict: Dict[str, ConfigValue]) -> None:
    for key in flat_dict.keys():
        assert dotindex.contains(nested_dict, key)
    assert not dotindex.contains(nested_dict, 'repo.url.notfound')


def test_contains_dicts(nested_dict: ConfigDict) -> None:
    def _assert_nested(expected, base=None):
        for (key, val) in expected.items():
            if not isinstance(val, dict):
                continue
            name = key if base is None else base+dotindex.SEPARATOR+key
            assert dotindex.contains(nested_dict, name)
            _assert_nested(val, name)
    _assert_nested(nested_dict)


@mark.parametrize('configs, key, remove_empty, expected', [
    ({'a': {'b': {'c': 0}}, 'd': 1}, 'a.b.c', True, {'d': 1}),
    ({'a': {'b': {'c': 0}}, 'd': 1}, 'a.b', True, {'d': 1}),
    ({'a': {'b': {'c': 0}}, 'd': 1}, 'a', True, {'d': 1}),
    ({'a': {'b': {'c': 0}}, 'd': 1}, 'a.b.c', False, {'a': {'b': {}}, 'd': 1}),
    ({'a': {'b': 0, 'c': []}}, 'a', False, {}),
    ({'a': {'b': 0}}, 'a.b', True, {}),
])
def test_delete(configs: ConfigDict, key: str, remove_empty: bool, expected: ConfigDict) -> None:
    assert dotindex.delete(configs, key, remove_empty=remove_empty)
    assert configs == expected


def test_delete_notfound(nested_dict: ConfigDict) -> None:
    with raises(dotindex.DotIndexException) as exc_info:
        dotindex.delete(nested_dict, 'repo.url.notfound')
    assert type(exc_info.value) == dotindex.NotFoundException
    assert isinstance(exc_info.value, KeyError)
    assert not dotindex.delete(nested_dict, 'repo.url.notfound', raise_missing=False)

@mark.parametrize('configs, key, value, create_parents, expected', [
    ({}, 'a.b.c', 2, True, {'a': {'b': {'c': 2}}}),
    ({'a': []}, 'a', dict(b=['c']), False, {'a': {'b': ['c']}}),
    ({}, 'b', dict(f='g'), False, {'b': {'f': 'g'}}),
])
def test_set(configs:ConfigDict, key:str, value:ConfigValue, create_parents:bool, expected: ConfigDict) -> None:
    assert dotindex.set(configs, key, value, create_parents=create_parents)
    assert configs == expected


def test_set_parent_missing(nested_dict:ConfigDict) -> None:
    with raises(dotindex.DotIndexException) as exc_info:
        dotindex.set(nested_dict, 'repo.nonexistant.path', None, create_parents=False)
    assert type(exc_info.value) == dotindex.NotFoundException
    assert isinstance(exc_info.value, KeyError)


def test_set_raise_missing(nested_dict:ConfigDict) -> None:
    with raises(dotindex.DotIndexException) as exc_info:
        dotindex.set(nested_dict, 'repo.newentry', 0, create_parents=True, raise_missing=True)
    assert type(exc_info.value) == dotindex.NotFoundException
    assert isinstance(exc_info.value, KeyError)


@mark.parametrize('configs, key, value, valid', [
    ({'a': True}, 'a', False, True),
    ({'a': 0}, 'a', None, True),
    ({'a': 'txt'}, 'a', 5, False),
    ({'a': 'txt'}, 'a', {'b': 5}, False),
    ({'node': {'b': 0}}, 'node', 'txt', False),
    ({'node': {'b': 0}}, 'node', {'b': []}, True),
])
def test_set_typesafe_replace(configs:ConfigDict, key:str, value:ConfigValue, valid:bool) -> None:
    if valid:
        assert dotindex.set(configs, key, value, typesafe_replace=True)
    else:
        with raises(dotindex.DotIndexException) as exc_info:
            dotindex.set(configs, key, value, typesafe_replace=True)
        assert type(exc_info.value) == dotindex.UnsafeReplaceException


def test_set_unchanged() -> None:
    configs = {'a': 0}
    actual = configs.copy()
    assert not dotindex.set(actual, 'a', 0)
    assert actual == configs
    assert dotindex.set(actual, 'a', 1)
    assert actual != configs
