from pathlib import Path

from pytest import fixture, mark, raises, param
from unittest.mock import patch, MagicMock

from configapi.sources import (
    ConfigSource,
    InMemoryConfigSource,
    FileConfigSource,
    PackageResourceConfigSource,
    NotWritableException,
)
from configapi.types import ConfigDict

from . import files


@fixture(scope='function')
def mock_config_source(request):
    toml, read_only = request.param
    with patch.multiple(ConfigSource, __abstractmethods__=set(),
                        read_toml=MagicMock(return_value=toml),
                        write_toml=MagicMock(),
                        ):
        src = ConfigSource(read_only=read_only)
        yield src

config_source_parametrize = mark.parametrize('mock_config_source, configs', [
    param(('', False), {}, id='empty'),
    param(('var = {x0 = true, y1 = "test"}', False), {'var.x0': True, 'var.y1': 'test'}, id='nested'),
    param(('a.b = [{c = {d = true}}]', False), {'a.b': [{'c': {'d': True}}]}, id='dict_in_array'),
], indirect=['mock_config_source'])


@config_source_parametrize
def test_ConfigSource_read_dict(mock_config_source, configs):
    src = mock_config_source
    assert src.read_dict() == configs
    src.read_toml.assert_called_once_with()


@config_source_parametrize
@patch('configapi.sources.format_configs')
def test_ConfigSource_write_dict(format_configs, mock_config_source, configs):
    src = mock_config_source
    toml = src.read_toml.return_value
    format_configs.return_value = toml
    src.write_dict(configs)
    format_configs.assert_called_once_with(configs)
    src.write_toml.assert_called_once_with(toml)


@mark.parametrize('mock_config_source', [('', True)], indirect=True)
def test_ConfigSource_read_only(mock_config_source) -> None:
    src = mock_config_source
    with raises(NotWritableException) as exc_info:
        src.write_dict({})
    assert type(exc_info.value) == NotWritableException
    src.write_toml.assert_not_called()


@config_source_parametrize
def test_ConfigSource_formatter(mock_config_source, configs: ConfigDict):
    src = mock_config_source
    src.write_dict(configs)
    src.write_toml.assert_called_once()
    # return the formatted TOML file contents (output from format_configs) from read_toml()
    src.read_toml.return_value = src.write_toml.call_args_list[0][0][0] # first call, args, first arg
    assert src.read_dict() == configs
    src.read_toml.assert_called_once()


@mark.parametrize('method', [
    'read_toml',
    'write_toml',
])
def test_ConfigSource_abstract_methods(method):
    m = getattr(ConfigSource, method)
    a = [MagicMock() for _ in range(m.__code__.co_argcount)]
    with raises(NotImplementedError) as exc_info:
        m(*a)
    assert type(exc_info.value) == NotImplementedError


def test_InMemoryConfigSource():
    configs = {'a.b': [0, 1], 'a.c': True}
    src = InMemoryConfigSource(configs=configs)
    assert src.configs is configs

    configs = {'a.b': [0, 1], 'a.c': False}
    src.configs = configs
    assert src.configs is configs

    assert src.read_dict() == configs
    assert src.read_dict() is not configs

    assert src.read_toml() == '[a]\nb = [\n    0,\n    1,\n]\nc = false\n'

    src.write_dict({'a.b': [1, 0]})
    assert src.configs == {'a.b': [1, 0]}
    assert src.configs is configs

    src.write_toml('[a]\nb = 1')
    assert src.configs == {'a.b': 1}


def test_InMemoryConfigSource_read_only():
    src = InMemoryConfigSource(read_only=True)
    assert src.configs == {}

    configs = {'a.b': [0, 1], 'a.c': False}
    src.configs = configs
    assert src.configs is configs

    with raises(NotWritableException) as exc_info:
        src.write_dict({})
    assert type(exc_info.value) == NotWritableException
    assert src.configs is configs

    with raises(NotWritableException) as exc_info:
        src.write_toml('')
    assert type(exc_info.value) == NotWritableException
    assert src.configs is configs


@mark.parametrize('filename', [
    '.test.toml',
    'C:/Users/admin/cfg.toml',
    '/unix/path.toml',
    './local.toml',
    '~/.user-cfg.toml',
])
def test_FileConfigSource_file(filename):
    path = Path(filename)
    assert FileConfigSource(filename).file == path
    assert FileConfigSource(path).file == path


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
    assert src.resource == (files.__name__, testfile)
    assert src.encoding == 'utf8'

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
    assert src.encoding == encoding

    get_data.assert_called_once_with('tests.files', testfile)
    decode.assert_called_once_with(encoding)
