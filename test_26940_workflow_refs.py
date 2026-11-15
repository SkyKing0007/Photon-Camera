#!/usr/bin/env python3
"""Pin exact inherited 26939 141 historical Actions commands and entire 26940 execution graph."""
import sys,hashlib,re
from build_26940_incremental import R,fail
HIST='bce2979074eba73c9fa7defa4ee5657bb3ba619d705b2bb79334b1f901a7648b'
def main():
 s=(R/'.github/workflows/build-26940-change-aware.yml').read_text()
 if len(s.splitlines())<340:fail('truncated 26939-equivalent workflow')
 a=s.index('      - name: Checkout intended experimental branch')
 b=s.index('      - name: Preserve successful 26934 visual-white')
 cmds=re.findall(r'^\s+(?:python3 -S|bash)\s+\S+(?:.*)$',s[a:b],re.M)
 digest=hashlib.sha256(('\n'.join(cmds)+'\n').encode()).hexdigest()
 if len(cmds)!=141 or digest!=HIST:fail('26939 successful original 141 command historical regression changed '+str((len(cmds),digest)))
 required=(
  'verify_26904_v3_safety.py','verify_26904_v2_safety.py','test_26903_v3_archive_receipt.py',
  'build_26934_incremental.py seal','build_26935_incremental.py seal',
  'build_26936_incremental.py seal','build_26937_incremental.py seal',
  'build_26938_incremental.py seal','build_26939_incremental.py seal',
  'test_26939_shader_contract.py --payload','test_26939_highlight_math.py --payload',
  'test_26939_sealed_negatives.py','build_26940_incremental.py seal',
  'test_26940_source.py --payload','test_26940_cache_host.py --payload',
  'test_26940_patch_proof.py --payload','test_26940_sealed_negatives.py',
  'build_26940_incremental.py fetch','build_26940_incremental.py prepare',
  'test_26940_source.py --live','test_26940_cache_host.py --live',
  'test_26940_patch_proof.py --live','prepare_26940_lkr_from_successful_26939.py',
  'verify_26906_native_cache.py preflight','verify_26906_native_cache.py postflight',
  'compile_26904_shaders_v2.sh','verify_26904_v3_cmake_handoff.py --handoff',
  'compile_26939_shaders.sh','test_26931_native_integrity.py --native',
  'test_26931_native_integrity.py --cmake','test_26931_native_integrity.py --apk',
  'build_26940_incremental.py verify-compiled','build_26940_incremental.py finalize',
  'TRIGGER_26940.txt','IrisCamera-0.9726940-26940-iris-rawr-debug.apk',
  ':app:assembleDebug --stacktrace','actions/cache/restore@v4',
  'actions/cache/save@v4','actions/upload-artifact@v4')
 for k in required:
  if k not in s:fail('missing actual inherited/current runner reference '+k)
 for old in ('build_26939_incremental.py fetch','build_26939_incremental.py prepare',
             'build_26939_incremental.py finalize','build_26938_incremental.py fetch',
             'prepare_26939_lkr_from_successful_26938.py','releases/tags/2.2.86'):
  if old in s:fail('stale prior-version action '+old)
 if s.count('actions/upload-artifact@v4')!=1 or s.count('./gradlew --no-daemon --build-cache :app:assembleDebug --stacktrace')!=1:
  fail('must compile exact one real APK and publish one completed artifact')
 ordered=('build_26939_incremental.py seal','build_26940_incremental.py seal',
          'build_26940_incremental.py fetch','build_26940_incremental.py prepare',
          'test_26940_patch_proof.py --live','verify_26906_native_cache.py preflight',
          'compile_26904_shaders_v2.sh','verify_26904_v3_cmake_handoff.py --handoff',
          'prepare_26940_lkr_from_successful_26939.py','test_26931_native_integrity.py --native',
          'compile_26939_shaders.sh','build_26940_incremental.py verify-compiled',
          './gradlew --no-daemon --build-cache :app:assembleDebug --stacktrace',
          'test_26931_native_integrity.py --cmake','test_26931_native_integrity.py --apk',
          'build_26940_incremental.py finalize','actions/upload-artifact@v4')
 pos=0
 for k in ordered:
  i=s.find(k,pos)
  if i<0:fail('mandatory compiler/stage order invalid '+k)
  pos=i+len(k)
 names=re.findall(r'^\s+- name: (.+)$',s,re.M)
 if len(names)!=len(set(names)):fail('duplicate GitHub Actions stage name')
 refs=set(re.findall(r'python3 -S ([a-zA-Z0-9_]+\.py)',s))
 refs.update(re.findall(r'\bbash ([a-zA-Z0-9_]+\.sh)',s));refs.add('gradlew')
 expected=(R/'26940_EXPECTED_ACTION_EXECUTABLES.txt').read_text().splitlines()
 if expected!=sorted(set(expected)) or refs!=set(expected) or any('/' in x or '..' in x for x in expected):
  fail('stale, incorrect, unused or missing declared Actions executable reference '+str(sorted(refs^set(expected))))
 if '--on-actions' in sys.argv:
  for p in expected:
   if not (R/p).is_file():fail('mandatory referenced script absent from current checkout '+p)
 print('PASS original successful 26939 141 historical SHA-pinned commands, '+str(len(refs))+' exact referential source files, one full Android APK and sealed Actions graph')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
