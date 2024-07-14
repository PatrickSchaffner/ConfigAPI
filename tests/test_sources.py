from pathlib import Path

from pytest import fixture, mark, raises, param
from unittest.mock import patch, MagicMock

from configapi.sources import (
    ConfigSource,
    FileConfigSource,
    PackageResourceConfigSource,
    NotWritableException,
)
from configapi.types import ConfigDict

from . import files


@mark.parametrize('toml, configs', [
    param('', {}, id='empty'),
    param('var = {x0 = true, y1 = "test"}', {'var.x0': True, 'var.y1': 'test'}, id='nested'),
])
@patch('configapi.sources.format_configs')
def test_ConfigSource(formatter, toml: str, configs: ConfigDict) -> None:
    with patch.multiple(ConfigSource, __abstractmethods__=set(),
                        read_only=False,
                        read_toml=MagicMock(return_value=toml),
                        write_toml=MagicMock(),
                        ):
        formatter.return_value = toml
        src = ConfigSource()
        src.read_toml.return_value = toml
        
        src.write_dict(configs)
        formatter.assert_called_once_with(configs)
        src.write_toml.assert_called_once_with(toml)

        assert src.read_dict() == configs
        src.read_toml.assert_called_once_with()


def test_ConfigSource_read_only() -> None:
    with patch.multiple(ConfigSource, __abstractmethods__=set(),
                        read_only=True,
                        write_toml=MagicMock(),
                        ):
        src = ConfigSource()

        with raises(NotWritableException) as exc_info:
            src.write_dict({})
        assert type(exc_info.value) == NotWritableException
        src.write_toml.assert_not_called()


@mark.parametrize('configs', [
    param({}, id='empty'),
    param({'var.x0': True, 'var.y1': 'test'}, id='nested'),
    param({'a.b': [{'c': {'d': True}}]}, id='dict_in_array'),
])
def test_ConfigSource_formatter(configs: ConfigDict) -> None:
    with patch.multiple(ConfigSource, __abstractmethods__=set(),
                        read_only=False,
                        write_toml=MagicMock(),
                        read_toml=MagicMock(),
                        ):
        src = ConfigSource()
        src.write_dict(configs)
        src.read_toml.return_value = src.write_toml.call_args_list[0][0][0] # first call, args, first arg
        assert src.read_dict() == configs


@mark.parametrize('read_only', [
    param(False, id='writable'),
    param(True, id='readonly'),
])
def test_FileConfigSource_read_only(read_only) -> None:
    src = FileConfigSource('test.toml', read_only=read_only)
    assert src.read_only == read_only


def test_FileConfigSource_read_toml(fs) -> None:
    config_toml = 'a = {b = 0, c = {d= 1}}'
    testfile = 'test-configs.toml'

    src = FileConfigSource(testfile)
    assert src.read_toml() == ''

    fs.create_file(testfile, contents=config_toml)
    assert src.read_toml() == config_toml


def test_FileConfigSource_write_toml(fs) -> None:
    config_toml = '[project]\nversion = "5.2.0"\n'
    testfile = 'test-configs.toml'

    src = FileConfigSource(testfile)
    src.write_toml(config_toml)

    assert Path(testfile).read_text() == config_toml


def test_PackageResourceConfigSource_read_toml() -> None:
    testfile = 'package-resource-configs.toml'
    testcontent = 'package.resource = true'

    src = PackageResourceConfigSource(files, testfile)
    assert src.read_toml() == testcontent

    src = PackageResourceConfigSource('tests.files', testfile)
    assert src.read_toml() == testcontent


def test_PackageResourceConfigSource_write_toml() -> None:
    src = PackageResourceConfigSource(files, 'test-configs.toml')
    assert src.read_only
    with raises(NotWritableException) as exc_type:
        src.write_toml('test = true')
    assert type(exc_type.value) == NotWritableException


@mark.parametrize('encoding, is_default', [
    ('utf8', True),
    ('ascii', False),
])
@patch('configapi.sources.get_data')
def test_PackageResourceConfigSource_encoding(get_data, is_default, encoding) -> None:
    testcontents = 'repo.version = 0'
    testfile = 'test-configs.toml'
    decode = get_data.return_value.decode
    decode.return_value = testcontents

    enc_kwarg = {'encoding': encoding} if not is_default else {}
    src = PackageResourceConfigSource(files, testfile, **enc_kwarg)
    assert src.read_toml() == testcontents

    get_data.assert_called_once_with('tests.files', testfile)
    decode.assert_called_once_with(encoding)
