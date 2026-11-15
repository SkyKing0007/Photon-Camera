#!/usr/bin/env python3
"""Exact complete inherited 26934 historical command block, 26935 source and real compiler gates.
The original 26934 historical commands are compared by a SHA of all 141
in-order executed python/bash invocations, not merely a few remembered labels.
"""
import pathlib,re,sys,hashlib
from build_26935_incremental import R,fail
HISTORICAL='bce2979074eba73c9fa7defa4ee5657bb3ba619d705b2bb79334b1f901a7648b'

def main():
 wf=R/'.github/workflows/build-26935-change-aware.yml'
 s=wf.read_text()
 if len(s.splitlines())<300:fail('26935 workflow truncated, original 26934 full historical regression lost')
 a=s.index('      - name: Checkout intended experimental branch')
 b=s.index('      - name: Preserve successful 26934 visual-white')
 commands=re.findall(r'^\s+(?:python3 -S|bash)\s+\S+(?:.*)$',s[a:b],re.M)
 if len(commands)!=141 or hashlib.sha256(('\n'.join(commands)+'\n').encode()).hexdigest()!=HISTORICAL:
  fail('EXACT original successful 26934 historical command stages modified/reordered/removed (includes 26886/87 26903 26904)')
 required=('TRIGGER_26935.txt','verify_26904_v3_safety.py','verify_26904_v2_safety.py',
    'test_26903_v3_archive_receipt.py','test_26925_shader_abi.py --payload',
    'build_26934_incremental.py seal','test_26934_shader_contract.py --payload',
    'test_26935_guard_host.py','test_26935_sealed_negatives.py',
    'build_26935_incremental.py seal','build_26935_incremental.py fetch',
    'build_26935_incremental.py prepare','test_26935_patch_proof.py --live',
    'test_26935_source.py --live','test_26934_highlight_math.py --live',
    'compile_26904_shaders_v2.sh','verify_26904_v3_cmake_handoff.py --handoff',
    'prepare_26935_lkr_from_successful_26934.py','test_26931_native_integrity.py --native',
    'compile_26935_shaders.sh','build_26935_incremental.py verify-compiled',
    ':app:assembleDebug --stacktrace','test_26931_native_integrity.py --cmake',
    'test_26931_native_integrity.py --apk',
    'build_26935_incremental.py finalize', 'actions/cache/restore@v4',
    'actions/cache/save@v4','actions/upload-artifact@v4')
 for key in required:
  if key not in s:fail('missing exact inherited/real current compilation gate '+key)
 if s.count('actions/upload-artifact@v4')!=1 or s.count('./gradlew --no-daemon --build-cache :app:assembleDebug --stacktrace')!=1:
  fail('must run exactly one full real APK assemble and one publish')
 # No earlier compiled source reconstruction, native github release API or legacy build.
 banned=('build_26934_incremental.py fetch','build_26934_incremental.py prepare',
         'build_26934_incremental.py finalize','prepare_26934_lkr_from_successful_26933.py',
         'python3 -S prepare_26931_rawlens_binaries.py','releases/tags/2.2.86')
 for key in banned:
  if key in s:fail('unsafe older source compilation/fetch/API fallback '+key)
 order=('build_26934_incremental.py seal','build_26935_incremental.py seal',
        'test_26935_guard_host.py','build_26935_incremental.py fetch',
        'build_26935_incremental.py prepare','test_26935_patch_proof.py --live',
        'verify_26906_native_cache.py preflight','compile_26904_shaders_v2.sh',
        'verify_26904_v3_cmake_handoff.py --handoff',
        'prepare_26935_lkr_from_successful_26934.py',
        'test_26931_native_integrity.py --native','compile_26935_shaders.sh',
        'build_26935_incremental.py verify-compiled',
        './gradlew --no-daemon --build-cache :app:assembleDebug --stacktrace',
        'test_26931_native_integrity.py --cmake','build_26935_incremental.py finalize',
        'actions/upload-artifact@v4')
 pos=0
 for key in order:
  x=s.find(key,pos)
  if x<0:fail('wrong successful 26934 sourced real 26935 execution order at '+key)
  pos=x+len(key)
 steps=re.findall(r'^\s+- name: (.+)$',s,re.M)
 if len(steps)!=len(set(steps)):fail('duplicate Actions stages')
 refs=set(re.findall(r'python3 -S ([a-zA-Z0-9_]+\.py)',s))
 refs.update(re.findall(r'\bbash ([a-zA-Z0-9_]+\.sh)',s));refs.add('gradlew')
 exp=(R/'26935_EXPECTED_ACTION_EXECUTABLES.txt').read_text().splitlines()
 if sorted(set(exp))!=exp or any('/' in p or '..' in p for p in exp):fail('bad executable manifest')
 if refs!=set(exp):fail('missing/unused executable refs '+str(sorted(refs^set(exp))))
 if '--on-actions' in sys.argv:
  for path in exp:
   if not (R/path).is_file():fail('Actions checkout missing expected mandatory executable '+path)
 print('PASS exact 141 historic 26934 regression commands in order + one real 26935 native/GLSL/Kotlin/Java/APK job; '+str(len(refs))+' executable refs')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
