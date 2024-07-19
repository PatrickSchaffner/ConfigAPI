from pathlib import Path

from pytest import raises, mark
from unittest.mock import MagicMock

from configapi.types import ConfigDict
from configapi.api import Configs, Scope
from configapi.patcher import Patcher
from configapi.sources import ConfigSource, NotWritableException

from . import files


@mark.parametrize('changed, read_only, autosave_updates, write_expected', [
    (False, False, False, False),
    (True,  False, False, False),
    (False, True,  False, False),
    (True,  True,  False, False),
    (False, False, True,  False),
    (True,  False, True,  True ),
    (False, True,  True,  False),
    (True,  True,  True,  False),
])
def test_Scope_load(changed:bool, read_only:bool, autosave_updates:bool, write_expected:bool):
    cfgs_orig = {'a.b': 'c'}
    cfgs_patched = {'a.c': 'b'} if changed else cfgs_orig

    patcher : Patcher = MagicMock(spec=Patcher)
    patcher.return_value = (cfgs_patched, changed)

    source : ConfigSource = MagicMock(spec=ConfigSource)
    source.read_dict.return_value = cfgs_orig
    source.read_only = read_only

    scope : Scope = Scope(source, patcher, autosave_updates=autosave_updates)
    assert not scope.writable == read_only

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

    scope : Scope = Scope(cfg_file)
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

    scope : Scope = Scope(cfg_file)
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

        
def test_Configs(fs):
    cfg_proj = Path('project-configs.toml')
    fs.create_file(cfg_proj, contents='version="0.8.5"\nproject.author = "me"')

    configs : Configs = Configs({
        'default': (files, 'example-defaults.toml'),
        'project': cfg_proj,
    }, target_version='1.0.0')

    @configs.patch('0.9.2')
    def _patch(cfgs: ConfigDict) -> ConfigDict:
        if 'project.author' in cfgs:
            if 'project.authors' not in cfgs:
                cfgs['project.authors'] = [cfgs['project.author']]
            del cfgs['project.author']
        return cfgs
    
    configs.load()
    assert configs.project['project.authors'] == ['me']
    assert configs.default['project.authors'] == ['dev', 'tester']
    assert configs['project.authors'] == ['me']
    assert configs.origin('project.authors') == 'project'
    assert configs.origin('project.name') == 'default'
