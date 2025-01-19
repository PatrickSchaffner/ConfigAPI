from pathlib import Path

from pytest import raises, mark
from unittest.mock import MagicMock

from configapi.scope import Scope
from configapi.patcher import Patcher
from configapi.sources import (
    ConfigSource,
    FileConfigSource,
    InMemoryConfigSource,
    PackageResourceConfigSource,
    NotWritableException,
)

from . import files


@mark.parametrize('source, expected_type, expected_autosave', [
    (Path.cwd() / 'config.toml', FileConfigSource, True),
    ('config.toml', FileConfigSource, True),
    ((files, 'config.toml'), PackageResourceConfigSource, False),
    (('pkgname', 'config.toml'), PackageResourceConfigSource, False),
    ({'a': 'b'}, InMemoryConfigSource, True),
])
def test_Scope_init(source, expected_type, expected_autosave):
    scope = Scope(source)
    assert isinstance(scope.source, expected_type)
    assert scope.writable != scope.source.read_only
    assert scope.autosave_updates == expected_autosave


def test_Scope_init_errors():
    with raises(ValueError) as exc_info:
        _ = Scope(None)
    assert type(exc_info.value) == ValueError


@mark.parametrize('changed, read_only, autosave_updates, write_expected', [
    (False, False, False, False),
    (True, False, False, False),
    (False, True, False, False),
    (True, True, False, False),
    (False, False, True, False),
    (True, False, True, True),
    (False, True, True, False),
    (True, True, True, False),
])
def test_Scope_load(changed: bool, read_only: bool, autosave_updates: bool, write_expected: bool):
    cfgs_orig = {'a.b': 'c'}
    cfgs_patched = {'a.c': 'b'} if changed else cfgs_orig

    patcher: Patcher = MagicMock(spec=Patcher)
    patcher.return_value = (cfgs_patched, changed)

    source: ConfigSource = MagicMock(spec=ConfigSource)
    source.read_dict.return_value = cfgs_orig
    source.read_only = read_only

    scope: Scope = Scope(source, patcher, autosave_updates=autosave_updates)
    assert not scope.writable == read_only
    assert scope.autosave_updates == autosave_updates
    assert scope.source == source

    if read_only and changed and autosave_updates:
        with raises(NotWritableException) as exc_info:
            scope.load()
        assert type(exc_info.value) == NotWritableException
    else:
        scope.load()

    source.read_dict.assert_called_once_with()
    patcher.assert_called_once_with(cfgs_orig)
    if write_expected:
        source.write_dict.assert_called_once_with(cfgs_patched)
    else:
        source.write_dict.assert_not_called()


def test_Scope_save(fs):
    cfg_file = Path('./test-cfg.toml')
    fs.create_file(cfg_file, contents='''
    [project]
    name = "test_Scope"
    ''')

    scope: Scope = Scope(cfg_file)
    scope.load()
    scope['version'] = 0
    scope.save()

    txt = cfg_file.read_text()
    assert '[project]\nname = "test_Scope"' in txt
    assert 'version = 0' in txt


def test_Scope_dict(fs):
    cfg_file = Path('./test-cfg.toml')
    fs.create_file(cfg_file, contents='''
    [project]
    name = "test_Scope"
    ''')

    scope: Scope = Scope(cfg_file)
    scope.load()

    assert 'test_Scope' not in scope
    assert 'project.name' in scope

    assert scope['project.name'] == 'test_Scope'
    with raises(KeyError):
        _ = scope['does.not.exist']

    scope['version'] = 0
    assert scope.keys() == {'project.name', 'version'}
    assert set(scope.items()) == {('project.name', 'test_Scope'), ('version', 0)}

    del scope['project.name']
    assert set(scope.values()) == {0}
