#!/usr/bin/env python3
"""26943 V2 R1: validate active workflow identity, sealed executable manifest and historical graph.
The original 26943 workflow regression is preserved in the full check below.
"""
import hashlib,re,sys
from build_26943_incremental import R,fail
HIST='bce2979074eba73c9fa7defa4ee5657bb3ba619d705b2bb79334b1f901a7648b'
def main():
 wf=R/'.github/workflows/build-26943-change-aware.yml'
 s=wf.read_text()
 if not s.startswith('name: Photon 26943 V2 R1 -') or s.count('name: photon-26943-v2-r1-b-off-gpu-zsl-motion-reconstruction') != 1:
  fail('stale V1 or wrong V2 R1 workflow/artifact identity')
 if len(s.splitlines())<375:fail('truncated mandatory Actions workflow')
 if 'TRIGGER_26943.txt' not in s or '\n      - TRIGGER_26942.txt' in s:fail('wrong 26943 trigger')
 a=s.index('      - name: Checkout intended experimental branch');b=s.index('      - name: Preserve successful 26934 visual-white')
 cmds=re.findall(r'^\s+(?:python3 -S|bash)\s+\S+(?:.*)$',s[a:b],re.M)
 digest=hashlib.sha256(('\n'.join(cmds)+'\n').encode()).hexdigest()
 if len(cmds)!=141 or digest!=HIST:fail('inherited 141 historical executable commands changed '+str((len(cmds),digest)))
 required=(
 'verify_26904_v3_safety.py','verify_26904_v2_safety.py',
 'test_26903_v3_archive_receipt.py','verify_26904_v3_cmake_handoff.py',
 'build_26940_incremental.py seal','build_26941_incremental.py seal',
 'build_26942_incremental.py seal','test_26942_workflow_refs.py --on-actions',
 'test_26942_native_host.py --payload','test_26942_shader_contract.py --payload',
 'test_26942_sealed_negatives.py',
 'build_26943_incremental.py seal','test_26943_workflow_refs.py --on-actions',
 'test_26943_source.py --payload','test_26943_native_host.py --payload',
 'test_26943_shader_contract.py --payload','test_26943_java_contract.py --payload',
 'test_26943_patch_proof.py --payload','test_26943_sealed_negatives.py',
 'build_26943_incremental.py fetch','build_26943_incremental.py prepare',
 'test_26943_source.py --live','test_26943_java_contract.py --live',
 'test_26943_native_host.py --live','test_26943_patch_proof.py --live',
 'prepare_26943_lkr_from_successful_26942.py',
 'compile_26904_shaders_v2.sh','verify_26904_v3_cmake_handoff.py --handoff',
 'compile_26939_shaders.sh','compile_26941_shaders.sh','compile_26942_shaders.sh','compile_26943_shaders.sh',
 'verify_26906_native_cache.py preflight','verify_26906_native_cache.py postflight',
 'test_26931_native_integrity.py --native','test_26931_native_integrity.py --cmake',
 'test_26931_native_integrity.py --apk',
 'build_26943_incremental.py verify-compiled','build_26943_incremental.py finalize',
 'IrisCamera-0.9726943-26943-iris-rawr-debug.apk',
 ':app:assembleDebug --stacktrace','actions/cache/restore@v4',
 'actions/cache/save@v4','actions/upload-artifact@v4')
 for k in required:
  if k not in s:fail('missing mandatory Actions stage/reference '+k)
 if s.count('./gradlew --no-daemon --build-cache :app:assembleDebug --stacktrace')!=1 or s.count('actions/upload-artifact@v4')!=1:
  fail('exactly one full Android :app:assembleDebug and only one published artifact')
 order=('build_26942_incremental.py seal','build_26943_incremental.py seal',
        'build_26943_incremental.py fetch','build_26943_incremental.py prepare',
        'test_26943_source.py --live','verify_26906_native_cache.py preflight',
        'compile_26904_shaders_v2.sh','verify_26904_v3_cmake_handoff.py --handoff',
        'prepare_26943_lkr_from_successful_26942.py','test_26931_native_integrity.py --native',
        'compile_26939_shaders.sh','compile_26941_shaders.sh','compile_26942_shaders.sh','compile_26943_shaders.sh',
        'build_26943_incremental.py verify-compiled',
        './gradlew --no-daemon --build-cache :app:assembleDebug --stacktrace',
        'test_26931_native_integrity.py --cmake','test_26931_native_integrity.py --apk',
        'build_26943_incremental.py finalize','actions/upload-artifact@v4')
 pos=0
 for k in order:
  i=s.find(k,pos)
  if i<0:fail('incorrect required Actions stage order, missing '+k)
  pos=i+len(k)
 names=re.findall(r'^\s+- name: (.+)$',s,re.M)
 if len(names)!=len(set(names)):fail('duplicate Actions step name')
 refs=set(re.findall(r'python3 -S ([a-zA-Z0-9_]+\.py)',s))
 refs.update(re.findall(r'\bbash ([a-zA-Z0-9_]+\.sh)',s));refs.add('gradlew')
 expected=(R/'26943_EXPECTED_ACTION_EXECUTABLES.txt').read_text().splitlines()
 if refs!=set(expected) or expected!=sorted(set(expected)) or any('/' in x or '..' in x for x in expected):
  fail('stale unused extra or missing Actions executable refs '+str(sorted(refs^set(expected))))
 for obsolete in ('build_26942_incremental.py fetch','build_26942_incremental.py prepare',
                  'build_26942_incremental.py finalize','prepare_26942_lkr_from_successful_26941.py',
                  'compile_26942_shaders.sh\n          bash compile_26942_shaders.sh'):
  if obsolete in s:fail('stale previous-version execution '+obsolete)
 if '--on-actions' in sys.argv:
  for p in expected:
   if not (R/p).is_file():fail('Actions checkout executable missing '+p)
 print(f'PASS 26943 V2 R1 workflow identity, historical 141 command SHA, {len(refs)} executable refs, real unchanged 26942 build gates, mandatory full Android compile+publish')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
