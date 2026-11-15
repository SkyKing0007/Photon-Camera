#!/usr/bin/env python3
"""All 141 immutable successful historical commands and closed-world 26937 real-compile graph."""
import sys,hashlib,re
from build_26937_incremental import R,fail
HIST='bce2979074eba73c9fa7defa4ee5657bb3ba619d705b2bb79334b1f901a7648b'

def main():
 s=(R/'.github/workflows/build-26937-change-aware.yml').read_text()
 if len(s.splitlines())<318:fail('truncated successful procedure')
 a=s.index('      - name: Checkout intended experimental branch')
 b=s.index('      - name: Preserve successful 26934 visual-white')
 cmds=re.findall(r'^\s+(?:python3 -S|bash)\s+\S+(?:.*)$',s[a:b],re.M)
 if len(cmds)!=141 or hashlib.sha256(('\n'.join(cmds)+'\n').encode()).hexdigest()!=HIST:
  fail('original 141 historical commands changed; 26886/26887 26903 26904 V1/V2/V3 compilation failures must replay')
 required=(
  'verify_26904_v3_safety.py','verify_26904_v2_safety.py','test_26903_v3_archive_receipt.py',
  'build_26934_incremental.py seal','build_26935_incremental.py seal','build_26936_incremental.py seal',
  'test_26936_guard_host.py --payload','test_26936_highlight_math.py --payload',
  'build_26937_incremental.py seal','test_26937_source.py --payload',
  'test_26937_highlight_math.py --payload','test_26937_shader_contract.py --payload',
  'test_26937_sealed_negatives.py','build_26937_incremental.py fetch',
  'build_26937_incremental.py prepare','test_26937_source.py --live',
  'test_26937_highlight_math.py --live','test_26937_shader_contract.py --live',
  'test_26937_patch_proof.py --live','prepare_26937_lkr_from_successful_26936.py',
  'test_26931_native_integrity.py --native','test_26931_native_integrity.py --cmake',
  'test_26931_native_integrity.py --apk','compile_26904_shaders_v2.sh',
  'verify_26904_v3_cmake_handoff.py --handoff','compile_26937_shaders.sh',
  'build_26937_incremental.py verify-compiled','build_26937_incremental.py finalize',
  'TRIGGER_26937.txt','IrisCamera-0.9726937-26937-iris-rawr-debug.apk',
  ':app:assembleDebug --stacktrace','actions/cache/restore@v4','actions/cache/save@v4','actions/upload-artifact@v4',
 )
 for k in required:
  if k not in s:fail('missing real build/historical/provenance reference '+k)
 banned=('build_26936_incremental.py fetch','build_26936_incremental.py prepare',
  'build_26936_incremental.py finalize','build_26935_incremental.py fetch',
  'build_26935_incremental.py prepare','build_26935_incremental.py finalize',
  'prepare_26937_lkr_from_successful_26935.py','releases/tags/2.2.86',
  'prepare_26931_rawlens_binaries.py')
 for k in banned:
  if k in s:fail('stale prior build/download reference '+k)
 if s.count('actions/upload-artifact@v4')!=1 or s.count('./gradlew --no-daemon --build-cache :app:assembleDebug --stacktrace')!=1:
  fail('one authentic assemble and one artifact publisher only')
 pos=0
 ordered=('build_26934_incremental.py seal','build_26935_incremental.py seal',
  'build_26936_incremental.py seal','build_26937_incremental.py seal',
  'build_26937_incremental.py fetch','build_26937_incremental.py prepare',
  'test_26937_source.py --live','test_26937_patch_proof.py --live',
  'verify_26906_native_cache.py preflight','compile_26904_shaders_v2.sh',
  'verify_26904_v3_cmake_handoff.py --handoff','prepare_26937_lkr_from_successful_26936.py',
  'test_26931_native_integrity.py --native','compile_26937_shaders.sh',
  'build_26937_incremental.py verify-compiled',
  './gradlew --no-daemon --build-cache :app:assembleDebug --stacktrace',
  'test_26931_native_integrity.py --cmake','test_26931_native_integrity.py --apk',
  'build_26937_incremental.py finalize','actions/upload-artifact@v4')
 for k in ordered:
  i=s.find(k,pos)
  if i<0:fail('stage ordering altered or missing '+k)
  pos=i+len(k)
 stages=re.findall(r'^\s+- name: (.+)$',s,re.M)
 if len(stages)!=len(set(stages)):fail('duplicate Actions stage names')
 refs=set(re.findall(r'python3 -S ([a-zA-Z0-9_]+\.py)',s))
 refs.update(re.findall(r'\bbash ([a-zA-Z0-9_]+\.sh)',s));refs.add('gradlew')
 expected=(R/'26937_EXPECTED_ACTION_EXECUTABLES.txt').read_text().splitlines()
 if not expected or expected!=sorted(set(expected)) or any('/' in x or '..' in x for x in expected):fail('wrong executable manifest format')
 if set(expected)!=refs:fail('wrong missing/stale executable references '+str(sorted(set(expected)^refs)))
 if '--on-actions' in sys.argv:
  for k in expected:
   if not (R/k).is_file():fail('missing exact executable in Actions checkout '+k)
 print('PASS immutable 141 historical commands, '+str(len(refs))+' current/historical closed-world executable refs, verified full Android compile/assemble/artifact order')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
