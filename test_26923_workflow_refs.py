#!/usr/bin/env python3
"""26923 regression for run 43280180906: no stale/missing executable refs.

Read the exact uploaded Actions YAML from disk BEFORE historical replay and
before modifying app/src. Standard-library only; do not depend on generated APK
or toolchain. Includes wrapper-indirected historical compiler dependencies.
"""
from pathlib import Path
import re
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
WORKFLOW = '.github/workflows/build-26923-change-aware.yml'
WRAPPER_DEPS = (
    'compile_26906_tone_glsl.sh',
    'compile_26920_lk_shaders.sh',
    'test_26920_source.py',
    'test_26920_vulkan_abi.py',
    'test_26921_guard.py',
    'test_26922_source.py',
    'test_26923_source.py',
    'test_26923_math_host.py',
    'build_26923_incremental.py',
)
COMPILER_WRAPPERS = (
    'compile_26923_lk_shaders.py',
    'compile_26923_shaders.sh',
    'compile_26923_hr_spirv.sh',
)
# The failed run called test_26922_guard.py, which never existed in the
# successful 26922 sealed payload. Do not silently invent a stub file.
REJECT = ('test_26922_guard.py',)
RUN_RE = re.compile(r'\b(?:python3?\s+-S\s+|bash\s+|chmod\s+\+x\s+)(?:\./)?([\w./-]+\.(?:py|sh)|gradlew)\b')

def required_from_yaml(source):
    return set(RUN_RE.findall(source))

def scan(directory, source):
    refs = required_from_yaml(source) | set(WRAPPER_DEPS) | set(COMPILER_WRAPPERS)
    missing = sorted(x for x in refs if not (directory / x).is_file())
    prohibited = sorted(x for x in REJECT if x in source)
    return refs, missing, prohibited

def self_test():
    with tempfile.TemporaryDirectory(prefix='p26923_actions_ref_fixture_') as d:
        root=Path(d)
        fixture='python3 -S test_26922_source.py --payload\npython3 -S test_26923_source.py --live\nbash compile_26923_shaders.sh\n'
        refs = required_from_yaml(fixture) | set(WRAPPER_DEPS) | set(COMPILER_WRAPPERS)
        for x in refs:
            p=root/x;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('fixture')
        a,b,c=scan(root,fixture)
        assert a==refs and not b and not c
        mutant=fixture.replace('test_26922_source.py','test_26922_guard.py')
        _,bad,prohibited=scan(root,mutant)
        assert bad==['test_26922_guard.py'] and prohibited==['test_26922_guard.py'],(bad,prohibited)
        (root/'compile_26920_lk_shaders.sh').unlink()
        _,bad,_=scan(root,fixture)
        assert 'compile_26920_lk_shaders.sh' in bad
    print('PASS 26923 reference scanner catches historical nonexistent script and missing indirect compiler dependencies')

if __name__=='__main__':
    self_test()
    if '--self-test' in sys.argv:
        raise SystemExit(0)
    wf=(ROOT/WORKFLOW).read_text()
    assert 'test_26922_source.py --payload' in wf, 'Historical 26922 source must run against immutable payload'
    assert 'python3 -S test_26923_workflow_refs.py' in wf, 'Preflight workflow references gate removed'
    assert wf.index('python3 -S test_26923_workflow_refs.py')<wf.index('python3 -S verify_26911_handoff.py'), 'Preflight must run first'
    refs, missing, forbidden=scan(ROOT,wf)
    inventory=set((ROOT/'26923_EXPECTED_ACTION_EXECUTABLES.txt').read_text().splitlines())
    assert refs==inventory, f'Executable reference inventory drift: missing={sorted(inventory-refs)}, extra={sorted(refs-inventory)}'
    assert len(refs)>=80, f'Unexplained historical regression commands removed: {len(refs)}'
    assert not forbidden, f'Historical nonexistent references in workflow: {forbidden}'
    assert not missing, f'Missing required top-level or indirect workflow references: {missing}'
    print(f'PASS 26923 {len(refs)} executable references exist in checked-out source (including indirect compiler wrappers), 26922 payload correctly scoped')
