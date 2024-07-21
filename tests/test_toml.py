from typing import Callable, Any, List

from pytest import mark, raises, param

from configapi.toml import (
    parse_toml,
    parse_configs,
    format_toml,
    format_configs,
    nested_dict,
    flat_dict,
    TOMLDict,
    ConfigDict,
    KeyCollisionException
)


@mark.parametrize('toml_str, toml_dict', [
    param(
        '''
        project.version = 1.4
        [repo]
        remote = true
        urls = {origin = 'localhost'}
        timeout = 30
        [[env]]
        name = 'priority'
        value = ['dev', 'test', 'prod']
        ''',
        {
            'project': {'version': 1.4},
            'repo': {
                'remote': True, 'timeout': 30,
                'urls': {'origin': 'localhost'},
            },
            'env': [{
                'name': 'priority',
                'value': ['dev', 'test', 'prod']
            }],
        }, 
        id='base',
    ),
    param(
        '''
        repo.remote = true
        repo.urls.origin = 'localhost'
        ''',
        {'repo': {'remote': True, 'urls': {'origin': 'localhost'}}},
        id='flat',
    ),
])
def test_parse_toml(toml_str:str, toml_dict:TOMLDict) -> None:
    assert parse_toml(toml_str) == toml_dict


@mark.parametrize('toml_str, config_dict', [
    param(
        '''
        project.version = 1.4
        [repo]
        remote = true
        urls = {origin = 'localhost'}
        timeout = 30
        [[env]]
        content.value = ['dev', 'test', 'prod']
        ''',
        {
            'project.version': 1.4,
            'repo.remote': True,
            'repo.timeout': 30,
            'repo.urls.origin': 'localhost',
            'env': [{
                'content': {'value': ['dev', 'test', 'prod']}
            }]
        }, 
        id='base',
    ),
    param(
        '''
        repo.remote = true
        repo.urls.origin = 'localhost'
        ''',
        {'repo.remote': True, 'repo.urls.origin': 'localhost'},
        id='flat',
    ),
])
def test_parse_configs(toml_str : str, config_dict : ConfigDict) -> None:
    assert parse_configs(toml_str) == config_dict


@mark.parametrize('toml_dict', [
    param(
        {'project': 1.4,
        'repo': {'remote': True, 'timeout': 30},
        'env': [{'content': {'labels': ['dev', 'test', 'prod']}}]
        },
        id='base',
    ),
])
def test_format_toml(toml_dict : TOMLDict) -> None:
    assert parse_toml(format_toml(toml_dict)) == toml_dict


@mark.parametrize('config_dict', [
    param(
        {'project.version': 1.4,
         'repo.remote': True,
         'repo.timeout': 30,
         'repo.urls.origin': 'localhost',
         'env': [{'content': {'labels': ['dev', 'test', 'prod']}}],
        },
        id='base',
    ),
])
def test_format_configs(config_dict : ConfigDict) -> None:
    assert parse_configs(format_configs(config_dict)) == config_dict


@mark.parametrize('config_dict, toml_dict', [
    param(
        {'a.b.c': True, 'd': [{'e': 0}]},
        {'a': {'b': {'c': True}}, 'd': [{'e': 0}]},
        id='base',
    ),
])
def test_nested_flat_dict_conversion(config_dict : ConfigDict, toml_dict : TOMLDict) -> None:
    assert nested_dict(config_dict) == toml_dict
    assert flat_dict(toml_dict) == config_dict


@mark.parametrize('funcs, config_dict, collision_key', [
    param(
        [nested_dict, format_configs],
        {'repo': 'origin',
         'repo.name': 'origin',},
        'repo',
        id='nested'
    ),
    param(
        [nested_dict, format_configs],
        {'repo': {'name': 'remote'},
         'repo.name': 'origin',},
        'repo.name',
        id='duplicate',
    ),
])
def test_key_collisions(funcs : List[Callable[[ConfigDict], Any]], config_dict : ConfigDict, collision_key : str) -> None:
    for func in funcs:
        with raises(KeyCollisionException) as exc_info:
            func(config_dict)
        assert type(exc_info.value) == KeyCollisionException
        assert exc_info.value.key == collision_key


def test_KeyCollisionException():
    exc = KeyCollisionException('this.key')
    assert isinstance(exc, Exception)
    assert exc.key == 'this.key'
    assert str(exc) == "Key 'this.key' already assigned."
