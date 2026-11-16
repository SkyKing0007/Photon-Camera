#!/usr/bin/env python3
"""26944 original historical 141 command SHA, 26943 V5 seal and real full Android compiler graph."""
import hashlib,re,sys
from build_26944_incremental import R,fail
HIST='bce2979074eba73c9fa7defa4ee5657bb3ba619d705b2bb79334b1f901a7648b'
def main():
 wf=R/'.github/workflows/build-26944-change-aware.yml'
 s=wf.read_text()
 if len(s.splitlines())<380:fail('26944 workflow truncated')
 if s.count('      - TRIGGER_26944.txt')!=1 or '      - TRIGGER_26943.txt' in s:fail('incorrect 26944 trigger')
 a=s.index('      - name: Checkout intended experimental branch');b=s.index('      - name: Preserve successful 26934 visual-white')
 cmds=re.findall(r'^\s+(?:python3 -S|bash)\s+\S+(?:.*)$',s[a:b],re.M)
 digest=hashlib.sha256(('\n'.join(cmds)+'\n').encode()).hexdigest()
 if len(cmds)!=141 or digest!=HIST:fail('inherited exact 141 historical commands changed '+str((len(cmds),digest)))
 for needle in (
  'verify_26904_v3_safety.py','verify_26904_v2_safety.py',
  'test_26903_v3_archive_receipt.py','verify_26904_v3_cmake_handoff.py',
  'build_26939_incremental.py seal','build_26940_incremental.py seal',
  'build_26941_incremental.py seal','build_26942_incremental.py seal',
  'build_26943_incremental.py seal','test_26943_patch_proof.py --payload',
  'build_26944_incremental.py seal','test_26944_workflow_refs.py --on-actions',
  'test_26944_source.py --payload','test_26944_shader_contract.py --payload',
  'test_26944_motion_math.py --payload','test_26944_night_math.py --payload',
  'test_26944_java_contract.py --payload','test_26944_patch_proof.py --payload',
  'test_26944_sealed_negatives.py','build_26944_incremental.py fetch',
  'build_26944_incremental.py prepare','test_26944_source.py --live',
  'test_26944_patch_proof.py --live','test_26903_modes.py .',
  'verify_26906_native_cache.py preflight','verify_26906_native_cache.py postflight',
  'compile_26904_shaders_v2.sh','verify_26904_v3_cmake_handoff.py --handoff',
  'compile_26939_shaders.sh','compile_26941_shaders.sh',
  'compile_26942_shaders.sh','compile_26943_shaders.sh','compile_26944_shaders.sh',
  'prepare_26944_lkr_from_successful_26943.py',
  'test_26931_native_integrity.py --native',
  'test_26931_native_integrity.py --cmake',
  'test_26931_native_integrity.py --apk',
  'build_26944_incremental.py verify-compiled',
  'build_26944_incremental.py finalize',
  'actions/cache/restore@v4','actions/cache/save@v4',
  './gradlew --no-daemon --build-cache :app:assembleDebug --stacktrace',
  'actions/upload-artifact@v4'):
  if needle not in s:fail('missing mandatory original/current Actions stage '+needle)
 if s.count('./gradlew --no-daemon --build-cache :app:assembleDebug --stacktrace')!=1 or s.count('actions/upload-artifact@v4')!=1:fail('not exactly one real APK assemble+publication')
 order=('build_26943_incremental.py seal','build_26944_incremental.py seal',
 'build_26944_incremental.py fetch','build_26944_incremental.py prepare',
 'test_26944_source.py --live','verify_26906_native_cache.py preflight',
 'compile_26904_shaders_v2.sh','verify_26904_v3_cmake_handoff.py --handoff',
 'prepare_26944_lkr_from_successful_26943.py','test_26931_native_integrity.py --native',
 'compile_26939_shaders.sh','compile_26941_shaders.sh',
 'compile_26942_shaders.sh','compile_26943_shaders.sh','compile_26944_shaders.sh',
 'build_26944_incremental.py verify-compiled',
 './gradlew --no-daemon --build-cache :app:assembleDebug --stacktrace',
 'test_26931_native_integrity.py --cmake', 'test_26931_native_integrity.py --apk',
 'build_26944_incremental.py finalize','actions/upload-artifact@v4')
 pos=0
 for k in order:
  i=s.find(k,pos)
  if i<0:fail('wrong mandatory Actions execution ordering '+k)
  pos=i+len(k)
 names=re.findall(r'^\s+- name: (.+)$',s,re.M)
 if len(names)!=len(set(names)):fail('duplicate Actions step name')
 refs=set(re.findall(r'python3 -S ([a-zA-Z0-9_]+\.py)',s))
 refs.update(re.findall(r'\bbash ([a-zA-Z0-9_]+\.sh)',s));refs.add('gradlew')
 expected=(R/'26944_EXPECTED_ACTION_EXECUTABLES.txt').read_text().splitlines()
 if refs!=set(expected) or expected!=sorted(set(expected)) or any('/' in x or '..' in x for x in expected):fail('stale/missing/unused Actions executable refs '+str(sorted(refs^set(expected))))
 if len(refs)!=221:fail('26944 exhaustive executable reference count differs '+str(len(refs)))
 for bad in ('build_26943_incremental.py fetch','build_26943_incremental.py prepare','build_26943_incremental.py finalize',
             'prepare_26943_lkr_from_successful_26942.py','TRIGGER_26942.txt'):
  if bad in s:fail('stale previous version action '+bad)
 if '--on-actions' in sys.argv:
  for p in expected:
   if not (R/p).is_file():fail('Actions checkout executable missing '+p)
 print(f'PASS 26944 original historical 141 command SHA, {len(refs)} exact scripts, 26943 V5 prior seal, real 26944 dual ABI NDK shader Java Kotlin APK + publish')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
