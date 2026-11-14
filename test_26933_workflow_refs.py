#!/usr/bin/env python3
"""Closed-world ONLY 26932 successful source authority; inherited actual verification, one new APK."""
import re,sys
from build_26933_incremental import R,fail

def main():
 s=(R/'.github/workflows/build-26933-change-aware.yml').read_text()
 if len(s.splitlines())<275:fail('17-stage real compiler/historical provenance procedure weakened')
 needed=('TRIGGER_26933.txt','verify_26904_v3_safety.py','verify_26904_v2_safety.py',
    'test_26903_v3_archive_receipt.py','test_26925_shader_abi.py --payload',
    'test_26930_shader_contract.py --payload',
    'test_26931_native_integrity.py --apk','prepare_26933_lkr_from_successful_26932.py',
    'build_26931_incremental.py seal','build_26932_incremental.py seal',
    'test_26932_shader_contract.py --payload','test_26932_math.py --payload',
    'build_26933_incremental.py seal','build_26933_incremental.py fetch',
    'build_26933_incremental.py prepare','test_26933_patch_proof.py --live',
    'test_26933_highlight_math.py --live','compile_26904_shaders_v2.sh',
    'verify_26904_v3_cmake_handoff.py --handoff','compile_26933_shaders.sh',
    'build_26933_incremental.py verify-compiled','build_26933_incremental.py finalize',
    'verify_26906_native_cache.py postflight',':app:assembleDebug',
    'actions/cache/restore@v4','actions/cache/save@v4','actions/upload-artifact@v4')
 for key in needed:
  if key not in s:fail('missing real compiler/targeted regression/source contract '+key)
 if 'python3 -S prepare_26931_rawlens_binaries.py' in s or 'releases/tags/2.2.86' in s:
  fail('live Actions workflow must never query external RawLens release API')
 if s.count('actions/upload-artifact@v4')!=1 or s.count('./gradlew --no-daemon --build-cache :app:assembleDebug --stacktrace')!=1:fail('duplicate APK build/publisher')
 # No previous published source is reconstructed: only the successful 26932
 # Actions artifact is fetched, authenticated and directly seeded.
 for bad in ('build_26932_incremental.py fetch','build_26932_incremental.py prepare',
             'build_26931_incremental.py fetch','build_26931_incremental.py prepare',
             'build_26932_incremental.py finalize','build_26931_incremental.py finalize',
             'build_26930_incremental.py fetch','build_26930_incremental.py prepare',
             'build_26929_incremental.py fetch','build_26929_incremental.py prepare',
             'build_26928_incremental.py fetch','build_26928_incremental.py prepare',
             'build_26927_incremental.py fetch','build_26927_incremental.py prepare',
             'build_26926_incremental.py fetch','build_26926_incremental.py prepare',
             'build_26923_incremental.py fetch','build_26923_incremental.py prepare'):
  if bad in s:fail('older base incorrectly reconstructed or rebuilt '+bad)
 order=('build_26932_incremental.py seal','build_26933_incremental.py seal',
        'build_26933_incremental.py fetch','build_26933_incremental.py prepare',
        'test_26933_patch_proof.py --live','verify_26906_native_cache.py preflight',
        'compile_26904_shaders_v2.sh','verify_26904_v3_cmake_handoff.py --handoff',
        'prepare_26933_lkr_from_successful_26932.py','test_26931_native_integrity.py --native',
        'compile_26933_shaders.sh','build_26933_incremental.py verify-compiled',
        './gradlew --no-daemon --build-cache :app:assembleDebug --stacktrace',
        'test_26931_native_integrity.py --apk','build_26933_incremental.py finalize',
        'actions/upload-artifact@v4')
 pos=0
 for key in order:
  x=s.find(key,pos)
  if x<0:fail('wrong successful 26932 seed, real 26933 GLSL/NDK/assemble execution order '+key)
  pos=x+len(key)
 steps=re.findall(r'^\s+- name: (.+)$',s,re.M)
 if len(steps)!=len(set(steps)):fail('duplicate Actions stage names')
 refs=set(re.findall(r'python3 -S ([a-zA-Z0-9_]+\.py)',s))
 refs.update(re.findall(r'\bbash ([a-zA-Z0-9_]+\.sh)',s));refs.add('gradlew')
 expected=(R/'26933_EXPECTED_ACTION_EXECUTABLES.txt').read_text().splitlines()
 if sorted(set(expected))!=expected or any('/' in x or '..' in x for x in expected):fail('stale or bad expected executable list')
 missing=sorted(refs-set(expected));unused=sorted(set(expected)-refs)
 if missing or unused:fail('missing/unused executable refs missing='+str(missing)+' unused='+str(unused))
 if '--on-actions' in sys.argv:
  for p in expected:
   if not (R/p).is_file():fail('mandatory historical/current executable missing from actual GitHub checkout '+p)
 print('PASS only latest successful 26932 source, '+str(len(refs))+' exact executable references and one new full 26933 APK compilation')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
