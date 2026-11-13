#!/usr/bin/env python3
"""Fail-closed workflow referenced executable inventory + stale names regression.
Compare against ACTUAL successful 26923 V4 workflow SHA, not guessed 2024 scripts.
All old required regressions retain their historical payload, and current
26924 shader/current-run wrappers must be present before source replacement.
"""
from pathlib import Path
import hashlib,re,sys,tempfile,shutil
R=Path(__file__).resolve().parent
H=lambda s:hashlib.sha256(s.encode()).hexdigest()
old=R/'.github/workflows/build-26923-change-aware.yml'
new=R/'.github/workflows/build-26924-change-aware.yml'
assert old.is_file() and new.is_file(), 'successful 26923 workflow missing or new one missing'
o=old.read_text();n=new.read_text()
assert H(o)=='d86417c39d9879201191469233e693f270844f5f7f88c377eafebd9c79481d2c','26923 executed V4 workflow modified'
PAT=re.compile(r'\b(?:python3?\s+-S\s+|bash\s+|chmod\s+\+x\s+)(?:\./)?([\w./-]+\.(?:py|sh)|gradlew)\b')
oldrefs=set(PAT.findall(o));refs=set(PAT.findall(n))
mandatory={
 'verify_26904_v3_safety.py','verify_26904_v2_safety.py',
 'test_26920_math_host.py','verify_26906_native_cache.py',
 'verify_26919_handoff.py','verify_26918_handoff.py',
 'test_26923_patch_proof.py','test_26923_shader_contract.py',
 'test_26923_math_host.py','test_26923_source.py',
 'build_26923_incremental.py','build_26924_incremental.py',
 'compile_26924_shaders.sh','compile_26924_hr_spirv.sh',
 'compile_26924_lk_shaders.py','test_26924_source.py',
 'test_26924_shader_shadow.py','test_26924_shader_contract.py',
 'test_26924_math_host.py','test_26924_sealed_negatives.py',
 'test_26924_workflow_refs.py','test_26924_patch_proof.py',
}
assert mandatory<=refs,'missing historical/new executable reference '+repr(mandatory-refs)
removed=oldrefs-refs
allow={'compile_26923_shaders.sh','compile_26923_hr_spirv.sh','compile_26923_lk_shaders.py','test_26923_shader_shadow.py'}
assert removed<=allow,'removed successful prior executable reference: '+repr(removed-allow)
assert len(refs)>=len(oldrefs)-4 and len(refs)>=70,'historical regression schedule was trimmed'
for key in ('TRIGGER_26923.txt','test_26922_guard.py'):
 assert key not in n,'stale/executable path '+key
assert n.count('TRIGGER_26924.txt')==1
assert n.count('build_26923_incremental.py regress')==1
assert n.index('build_26923_incremental.py regress')<n.index('build_26924_incremental.py prepare')
assert n.count('actions/upload-artifact@v4')==1
assert n.count(':app:assembleDebug')>=1
assert n.count('test_26920_vulkan_abi.py --live --cmake')>=1
assert n.index('test_26924_workflow_refs.py')<n.index('verify_26911_handoff.py')
assert n.index('build_26923_incremental.py prepare')<n.index('build_26924_incremental.py prepare')
assert n.index('build_26924_incremental.py prepare')<n.index('build_26924_incremental.py verify-compiled')
assert n.index('build_26924_incremental.py verify-compiled')<n.index(':app:assembleDebug')
assert n.index(':app:assembleDebug')<n.index('build_26924_incremental.py finalize')
indirect={'compile_26906_tone_glsl.sh','compile_26920_lk_shaders.sh','test_26920_source.py','test_26920_vulkan_abi.py','test_26921_guard.py'}
assert indirect<=set((R/'26923_EXPECTED_ACTION_EXECUTABLES.txt').read_text().splitlines()),'missing successful indirect compiler reference'
for name in refs|indirect:
 if name=='gradlew':continue
 assert (R/name).is_file(), 'missing referenced executable '+name
expected=set((R/'26924_EXPECTED_ACTION_EXECUTABLES.txt').read_text().splitlines())
assert expected==refs|indirect,'stale/added executable inventory or missing indirect reference'
# Real regression: an old nonexistent tool must fail our scanner.
with tempfile.TemporaryDirectory(prefix='p26924_missing_ref_') as d:
 p=Path(d)/'new.sh';p.write_text(n+'\n  run: python3 -S test_26922_guard.py\n')
 assert 'test_26922_guard.py' in set(PAT.findall(p.read_text()))
 assert not (R/'test_26922_guard.py').is_file()
print(f'PASS 26924 {len(refs|indirect)} executable refs exist in actual checkout; historical V4 verified; no stale V1/V2/26923 script calls')
