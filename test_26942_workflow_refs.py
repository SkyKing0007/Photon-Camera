#!/usr/bin/env python3
"""Keep exact 26941 historical 141 executable commands and complete new 26942 build graph."""
import hashlib,re,sys
from build_26942_incremental import R,fail
HIST='bce2979074eba73c9fa7defa4ee5657bb3ba619d705b2bb79334b1f901a7648b'
def main():
 s=(R/'.github/workflows/build-26942-change-aware.yml').read_text()
 if len(s.splitlines())<365:fail('truncated 26942 Actions workflow')
 a=s.index('      - name: Checkout intended experimental branch')
 b=s.index('      - name: Preserve successful 26934 visual-white')
 cmds=re.findall(r'^\s+(?:python3 -S|bash)\s+\S+(?:.*)$',s[a:b],re.M)
 digest=hashlib.sha256(('\n'.join(cmds)+'\n').encode()).hexdigest()
 if len(cmds)!=141 or digest!=HIST:fail('successful original 141 historical command SHA changed '+str((len(cmds),digest)))
 required=(
 'verify_26904_v3_safety.py','verify_26904_v2_safety.py','test_26903_v3_archive_receipt.py',
 'build_26939_incremental.py seal','build_26940_incremental.py seal',
 'test_26940_cache_host.py --payload','test_26940_sealed_negatives.py',
 'build_26941_incremental.py seal','test_26941_workflow_refs.py --on-actions',
 'test_26941_source.py --payload','test_26941_native_host.py --payload',
 'test_26941_tone_math.py --payload','test_26941_shader_contract.py --payload',
 'test_26941_sealed_negatives.py',
 'build_26942_incremental.py seal','test_26942_workflow_refs.py --on-actions',
 'test_26942_shader_contract.py --payload','test_26941_tone_math.py --payload',
 'test_26942_source.py --live','test_26942_native_host.py --live',
 'test_26942_patch_proof.py --live','test_26942_sealed_negatives.py',
 'build_26942_incremental.py fetch','build_26942_incremental.py prepare',
 'prepare_26942_lkr_from_successful_26941.py',
 'compile_26904_shaders_v2.sh','verify_26904_v3_cmake_handoff.py --handoff',
 'compile_26939_shaders.sh','compile_26941_shaders.sh','compile_26942_shaders.sh',
 'test_26931_native_integrity.py --native','test_26931_native_integrity.py --cmake',
 'test_26931_native_integrity.py --apk',
 'verify_26906_native_cache.py preflight','verify_26906_native_cache.py postflight',
 'build_26942_incremental.py verify-compiled','build_26942_incremental.py finalize',
 'TRIGGER_26942.txt','IrisCamera-0.9726942-26942-iris-rawr-debug.apk',
 ':app:assembleDebug --stacktrace','actions/cache/restore@v4','actions/cache/save@v4',
 'actions/upload-artifact@v4')
 for k in required:
  if k not in s:fail('missing mandatory inherited/26942 executable '+k)
 for bad in ('build_26941_incremental.py fetch','build_26941_incremental.py prepare',
             'build_26941_incremental.py finalize',
             'prepare_26941_lkr_from_successful_26939.py',
             'releases/tags/2.2.86'):
  if bad in s:fail('stale/incorrect previous-version execution '+bad)
 if s.count('actions/upload-artifact@v4')!=1 or s.count('./gradlew --no-daemon --build-cache :app:assembleDebug --stacktrace')!=1:
  fail('new build must execute exactly one full :app:assembleDebug and publish exactly one artifact')
 ordered=('build_26939_incremental.py seal','build_26940_incremental.py seal','build_26941_incremental.py seal',
          'build_26942_incremental.py seal','build_26942_incremental.py fetch',
          'build_26942_incremental.py prepare','test_26942_patch_proof.py --live',
          'verify_26906_native_cache.py preflight',
          'compile_26904_shaders_v2.sh','verify_26904_v3_cmake_handoff.py --handoff',
          'prepare_26942_lkr_from_successful_26941.py',
          'test_26931_native_integrity.py --native','compile_26939_shaders.sh',
          'compile_26941_shaders.sh','compile_26942_shaders.sh','build_26942_incremental.py verify-compiled',
          './gradlew --no-daemon --build-cache :app:assembleDebug --stacktrace',
          'test_26931_native_integrity.py --cmake','test_26931_native_integrity.py --apk',
          'build_26942_incremental.py finalize','actions/upload-artifact@v4')
 pos=0
 for k in ordered:
  i=s.find(k,pos)
  if i<0:fail('actual Actions execution missing, wrong order, or stale '+k)
  pos=i+len(k)
 names=re.findall(r'^\s+- name: (.+)$',s,re.M)
 if len(names)!=len(set(names)):fail('duplicate Actions step name')
 refs=set(re.findall(r'python3 -S ([a-zA-Z0-9_]+\.py)',s))
 refs.update(re.findall(r'\bbash ([a-zA-Z0-9_]+\.sh)',s));refs.add('gradlew')
 expected=(R/'26942_EXPECTED_ACTION_EXECUTABLES.txt').read_text().splitlines()
 if expected!=sorted(set(expected)) or refs!=set(expected) or any('/' in x or '..' in x for x in expected):
  fail('incorrect/stale/unused/missing exact Actions executable names '+str(sorted(refs^set(expected))))
 if '--on-actions' in sys.argv:
  for x in expected:
   if not (R/x).is_file():fail('current checkout missing referenced Actions executable '+x)
 print('PASS 26942 original successful 141 historical commands SHA pinned, '+str(len(refs))+' exact current Actions executables, single full actual compile/publish')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
