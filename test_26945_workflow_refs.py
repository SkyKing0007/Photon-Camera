#!/usr/bin/env python3
"""26945 exact historical 26944 gates, current Actions runtime graph, executable refs."""
import hashlib,pathlib,re,sys
from build_26945_incremental import R,REQUIRED,scope,fail,sha
HIST='bce2979074eba73c9fa7defa4ee5657bb3ba619d705b2bb79334b1f901a7648b'

def main():
 s=(R/'.github/workflows/build-26945-change-aware.yml').read_text()
 if len(s.splitlines())<400:fail('26945 Actions job truncated')
 if s.count('      - TRIGGER_26945.txt')!=1 or '      - TRIGGER_26944.txt' in s:fail('stale trigger')
 if 'branches:\n      - experimental-clean-photon-rebuild' not in s:fail('wrong experimental branch')
 a=s.index('      - name: Checkout intended experimental branch');b=s.index('      - name: Preserve successful 26934 visual-white')
 cmds=re.findall(r'^\s+(?:python3 -S|bash)\s+\S+(?:.*)$',s[a:b],re.M)
 digest=hashlib.sha256(('\n'.join(cmds)+'\n').encode()).hexdigest()
 if len(cmds)!=141 or digest!=HIST:fail('inherited 26944 historical 141 commands no longer byte identical '+str((len(cmds),digest)))
 for needle in ('verify_26904_v3_safety.py','verify_26904_v2_safety.py','test_26903_v3_archive_receipt.py',
   'build_26940_incremental.py seal','build_26941_incremental.py seal',
   'build_26942_incremental.py seal','build_26943_incremental.py seal',
   'build_26944_incremental.py seal','test_26944_workflow_refs.py --on-actions',
   'test_26944_source.py --payload','test_26944_motion_math.py --payload',
   'test_26944_night_math.py --payload','test_26944_java_contract.py --payload',
   'test_26944_patch_proof.py --payload','test_26944_sealed_negatives.py',
   'build_26945_incremental.py seal','test_26945_sealed_negatives.py',
   'build_26945_incremental.py fetch','build_26945_incremental.py prepare',
   'test_26945_source.py --live','test_26945_gainmap.py --live',
   'test_26945_preview.py --live','test_26945_patch_proof.py --live',
   'build_26945_incremental.py regress',
   'verify_26906_native_cache.py preflight','verify_26906_native_cache.py postflight',
   'compile_26904_shaders_v2.sh','verify_26904_v3_cmake_handoff.py --handoff',
   'compile_26939_shaders.sh','compile_26941_shaders.sh','compile_26942_shaders.sh',
   'compile_26943_shaders.sh','compile_26944_shaders.sh',
   'prepare_26945_lkr_from_successful_26944.py',
   'test_26931_native_integrity.py --native','test_26931_native_integrity.py --cmake',
   'test_26931_native_integrity.py --apk',
   'build_26945_incremental.py verify-compiled','build_26945_incremental.py finalize',
   './gradlew --no-daemon --build-cache :app:assembleDebug --stacktrace',
   'actions/cache/restore@v4','actions/cache/save@v4','actions/upload-artifact@v4'):
  if needle not in s:fail('mandatory prior/current check missing '+needle)
 if s.count('actions/upload-artifact@v4')!=1 or s.count('./gradlew --no-daemon --build-cache :app:assembleDebug --stacktrace')!=1:fail('duplicate build or publication')
 if 'if-no-files-found: error' not in s or 'retention-days: 90' not in s:fail('artifact publication guard missing')
 for needle in ('build_26944_incremental.py seal','build_26945_incremental.py seal',
   'build_26945_incremental.py fetch','build_26945_incremental.py prepare',
   'test_26945_source.py --live','verify_26906_native_cache.py preflight',
   'compile_26904_shaders_v2.sh','prepare_26945_lkr_from_successful_26944.py',
   'compile_26939_shaders.sh','compile_26944_shaders.sh',
   'build_26945_incremental.py verify-compiled',
   './gradlew --no-daemon --build-cache :app:assembleDebug --stacktrace',
   'test_26931_native_integrity.py --cmake',
   'test_26931_native_integrity.py --apk',
   'build_26945_incremental.py finalize','actions/upload-artifact@v4'):
  if s.find(needle)<0:fail('missing workflow order member '+needle)
 positions=[s.index(k) for k in ('build_26944_incremental.py seal','build_26945_incremental.py seal',
   'build_26945_incremental.py fetch','build_26945_incremental.py prepare',
   'test_26945_source.py --live','verify_26906_native_cache.py preflight',
   'compile_26904_shaders_v2.sh','prepare_26945_lkr_from_successful_26944.py',
   'compile_26939_shaders.sh','compile_26944_shaders.sh',
   'build_26945_incremental.py verify-compiled',
   './gradlew --no-daemon --build-cache :app:assembleDebug --stacktrace',
   'test_26931_native_integrity.py --cmake',
   'test_26931_native_integrity.py --apk',
   'build_26945_incremental.py finalize','actions/upload-artifact@v4')]
 if positions!=sorted(positions):fail('unapproved verification ordering')
 names=re.findall(r'^\s+- name: (.+)$',s,re.M)
 if len(names)!=len(set(names)):fail('duplicate Actions step')
 refs=set(re.findall(r'python3 -S ([a-zA-Z0-9_]+\.py)',s));refs.update(re.findall(r'\bbash ([a-zA-Z0-9_]+\.sh)',s));refs.add('gradlew')
 expected=(R/'26945_EXPECTED_ACTION_EXECUTABLES.txt').read_text().splitlines()
 if refs!=set(expected) or expected!=sorted(set(expected)) or any('/' in v or '..' in v for v in expected):fail('exact executable reference set changed '+str(sorted(refs^set(expected))))
 if '--on-actions' in sys.argv:
  for p in expected:
   if not (R/p).is_file():fail('missing existing/added Actions executable '+p)
 print('PASS 26945 inherited 141 historical SHA, '+str(len(expected))+' required scripts, front/rear-only scope, one real full Android build')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
