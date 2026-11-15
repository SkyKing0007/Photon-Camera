#!/usr/bin/env python3
"""Exact unweakened 141 historical commands, full graph closed-world and build order.
The successful 26935 V2 workflow is retained as an exact independent reference.
"""
import sys,hashlib,re
from build_26936_incremental import R,fail
HIST='bce2979074eba73c9fa7defa4ee5657bb3ba619d705b2bb79334b1f901a7648b'

def main():
 s=(R/'.github/workflows/build-26936-change-aware.yml').read_text()
 if len(s.splitlines())<305:fail('truncated proven 26935 mandatory workflow')
 a=s.index('      - name: Checkout intended experimental branch')
 b=s.index('      - name: Preserve successful 26934 visual-white')
 cmds=re.findall(r'^\s+(?:python3 -S|bash)\s+\S+(?:.*)$',s[a:b],re.M)
 if len(cmds)!=141 or hashlib.sha256(('\n'.join(cmds)+'\n').encode()).hexdigest()!=HIST:
  fail('historical successful 26935 141 ordered real compiler/regression invocations changed; do not weaken 26886/87 26903 26904')
 required=('verify_26904_v3_safety.py','verify_26904_v2_safety.py',
   'test_26903_v3_archive_receipt.py','build_26934_incremental.py seal',
   'build_26935_incremental.py seal','test_26935_guard_host.py',
   'test_26935_sealed_negatives.py','test_26936_sealed_negatives.py',
   'test_26936_source.py --live','test_26936_guard_host.py --live',
   'test_26936_highlight_math.py --live','test_26936_shader_contract.py --live',
   'test_26936_patch_proof.py --live','test_26931_native_integrity.py --native',
   'test_26931_native_integrity.py --cmake','test_26931_native_integrity.py --apk',
   'compile_26904_shaders_v2.sh','verify_26904_v3_cmake_handoff.py --handoff',
   'prepare_26936_lkr_from_successful_26935.py',
   'compile_26936_shaders.sh','build_26936_incremental.py seal',
   'build_26936_incremental.py fetch','build_26936_incremental.py prepare',
   'build_26936_incremental.py verify-compiled','build_26936_incremental.py finalize',
   'TRIGGER_26936.txt',':app:assembleDebug --stacktrace',
   'actions/cache/restore@v4','actions/cache/save@v4','actions/upload-artifact@v4')
 for k in required:
  if k not in s:fail('successful 26935 real compiler or 26936 regression reference missing '+k)
 banned=('build_26935_incremental.py fetch','build_26935_incremental.py prepare',
   'build_26935_incremental.py finalize','build_26934_incremental.py fetch',
   'build_26934_incremental.py prepare','build_26934_incremental.py finalize',
   'prepare_26931_rawlens_binaries.py','releases/tags/2.2.86',
   'prepare_26936_lkr_from_successful_26934.py')
 for k in banned:
  if k in s:fail('stale/incorrect previous source/RawLens GitHub 403 execution path '+k)
 if s.count('actions/upload-artifact@v4')!=1 or s.count('./gradlew --no-daemon --build-cache :app:assembleDebug --stacktrace')!=1:
  fail('exactly one real assembly and one publisher mandatory')
 pos=0
 ordered=('build_26934_incremental.py seal','build_26935_incremental.py seal',
   'build_26936_incremental.py seal','build_26936_incremental.py fetch',
   'build_26936_incremental.py prepare','test_26936_source.py --live',
   'test_26936_patch_proof.py --live','verify_26906_native_cache.py preflight',
   'compile_26904_shaders_v2.sh','verify_26904_v3_cmake_handoff.py --handoff',
   'prepare_26936_lkr_from_successful_26935.py',
   'test_26931_native_integrity.py --native','compile_26936_shaders.sh',
   'build_26936_incremental.py verify-compiled',
   './gradlew --no-daemon --build-cache :app:assembleDebug --stacktrace',
   'test_26931_native_integrity.py --cmake','test_26931_native_integrity.py --apk',
   'build_26936_incremental.py finalize','actions/upload-artifact@v4')
 for key in ordered:
  loc=s.find(key,pos)
  if loc<0:fail('expected ordered real historical/current mandatory gate missing/reordered '+key)
  pos=loc+len(key)
 stages=re.findall(r'^\s+- name: (.+)$',s,re.M)
 if len(stages)!=len(set(stages)):fail('duplicate stage names')
 refs=set(re.findall(r'python3 -S ([a-zA-Z0-9_]+\.py)',s))
 refs.update(re.findall(r'\bbash ([a-zA-Z0-9_]+\.sh)',s));refs.add('gradlew')
 expected=(R/'26936_EXPECTED_ACTION_EXECUTABLES.txt').read_text().splitlines()
 if not expected or expected!=sorted(set(expected)) or any('/' in x or '..' in x for x in expected):
  fail('missing/unsorted executable manifest')
 if set(expected)!=refs:fail('stale/missing/wrong executable references '+str(sorted(set(expected)^refs)))
 if '--on-actions' in sys.argv:
  for k in expected:
   if not (R/k).is_file():fail('historical current executable missing in actual Actions checkout '+k)
 print('PASS immutable 141 prior successful commands, '+str(len(refs))+' closed-world real executable references, current dualABI Java/Kotlin/GLSL/SPIRV/assemble/publish order')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
