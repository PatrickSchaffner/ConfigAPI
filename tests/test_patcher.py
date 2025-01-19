from pytest import raises, mark, fixture
from unittest.mock import patch

from configapi.patcher import Patcher, PatchType, Version
from configapi.types import ConfigDict


def empty_patch() -> PatchType:
    return lambda cfg: cfg


def test_Patcher_call():
    p = Patcher()
    configs = {'key': 'value'}
    assert p(configs) == p.update(configs)


def test_Patcher_target_version_auto():
    p = Patcher()
    p.register(version='1.0.12', patch=empty_patch())
    assert p.target_version == Version('1.0.12')
    p.register(version='1.0.9', patch=empty_patch())
    assert p.target_version == Version('1.0.12')
    p.register(version='1.1.0', patch=empty_patch())
    assert p.target_version == Version('1.1.0')


def test_Patcher_target_version():
    p = Patcher(target_version='5.2.1')
    assert p.target_version == Version('5.2.1')


def test_Patcher_register():
    mocks = {v: empty_patch() for v in ['1.0.5', '1.7.2']}
    
    patcher = Patcher()
    for (v, p) in mocks.items():
        patcher.register(version=v, patch=p)
    
    n_patches = len(list(iter(patcher)))
    with raises(ValueError) as exc_info:
        patcher.register(version='1.0.5', patch=empty_patch())
    assert type(exc_info.value) == ValueError
    assert len(list(iter(patcher))) == n_patches

    for (v, p) in patcher:
        v = str(v)
        assert v in mocks
        assert p == mocks[v]
        del mocks[v]
    assert len(mocks) == 0


def test_Patcher_update():
    patcher = Patcher(target_version='2.0.1')

    def mock_patch(name) -> PatchType:
        def _mock(configs: ConfigDict) -> ConfigDict:
            if 'patched.count' not in configs:
                configs['patched.count'] = 0
            configs['patched.count'] += 1
            configs['patched.by'] = name
            return configs
        return _mock
    
    patcher.register(version='1.0.0', patch=mock_patch('one'))
    patcher.register(version='2.0.0', patch=mock_patch('two'))
    patcher.register(version='3.0.0', patch=mock_patch('three'))

    (cfg, changed) = patcher.update({})
    assert changed
    assert cfg == {'patched.count': 2, 'patched.by': 'two', 'version': '2.0.0'}
    
    (cfg, changed) = patcher({'version': '2.0.0'})
    assert not changed
    assert cfg == {'version': '2.0.0'}

    (cfg, changed) = patcher({'version': '1.94.99'})
    assert changed
    assert cfg == {'version': '2.0.0', 'patched.count': 1, 'patched.by': 'two'}


