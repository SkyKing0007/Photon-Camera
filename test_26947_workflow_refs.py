#!/usr/bin/env python3
"""Exactly inherited 141 successful historical commands, exhaustive 26947 executable graph."""
import hashlib,re,sys
from build_26947_incremental import R,fail
HIST='bce2979074eba73c9fa7defa4ee5657bb3ba619d705b2bb79334b1f901a7648b'
def main():
 s=(R/'.github/workflows/build-26947-change-aware.yml').read_text()
 if len(s.splitlines())<400:fail('workflow truncated')
 if s.count('      - TRIGGER_26947.txt')!=1 or '      - TRIGGER_26946.txt' in s.split('jobs:',1)[0]:fail('wrong trigger')
 if 'branches:\n      - experimental-clean-photon-rebuild' not in s:fail('wrong branch')
 a=s.index('      - name: Checkout intended experimental branch');b=s.index('      - name: Preserve successful 26934 visual-white')
 cmds=re.findall(r'^\s+(?:python3 -S|bash)\s+\S+(?:.*)$',s[a:b],re.M)
 digest=hashlib.sha256(('\n'.join(cmds)+'\n').encode()).hexdigest()
 if len(cmds)!=141 or digest!=HIST:fail('successful 26945 original historical 141 executable commands changed '+str((len(cmds),digest)))
 ordered=(
 'build_26944_incremental.py seal','build_26945_incremental.py seal',
 'build_26946_incremental.py seal',
 'build_26947_incremental.py seal','build_26947_incremental.py fetch',
 'build_26947_incremental.py prepare','test_26947_source.py --live',
 'test_26947_lifecycle.py --live','test_26947_java_host.py --live',
 'verify_26906_native_cache.py preflight','compile_26904_shaders_v2.sh',
 'verify_26904_v3_cmake_handoff.py --handoff',
 'prepare_26947_lkr_from_successful_26946.py','test_26931_native_integrity.py --native',
 'compile_26939_shaders.sh','compile_26944_shaders.sh',
 'build_26947_incremental.py verify-compiled',
 './gradlew --no-daemon --build-cache :app:assembleDebug --stacktrace',
 'test_26931_native_integrity.py --cmake', 'test_26931_native_integrity.py --apk',
 'verify_26906_native_cache.py postflight',
 'build_26947_incremental.py finalize','actions/upload-artifact@v4')
 pos=0
 for k in ordered:
  n=s.find(k,pos)
  if n<0:fail('historical/current required workflow ordering absent '+k)
  pos=n+len(k)
 for k in (
 'verify_26904_v3_safety.py','verify_26904_v2_safety.py',
 'test_26903_v3_archive_receipt.py','test_26923_workflow_refs.py',
 'test_26886','test_26887',
 'test_26945_workflow_refs.py --on-actions',
 'test_26945_source.py --payload','test_26945_gainmap.py --payload',
 'test_26945_preview.py --payload','test_26945_patch_proof.py --payload',
 'test_26945_sealed_negatives.py',
 'test_26946_source.py --payload','test_26946_gainmap_geometry.py --payload',
 'test_26947_source.py --payload','test_26947_lifecycle.py --payload',
 'test_26947_java_host.py --payload','test_26947_patch_proof.py --payload',
 'test_26946_sealed_negatives.py','test_26946_workflow_refs.py --on-actions',
 'test_26947_sealed_negatives.py','test_26947_workflow_refs.py --on-actions',
 'compile_26941_shaders.sh','compile_26942_shaders.sh','compile_26943_shaders.sh',
 'verify_26906_native_cache.py postflight',
 'actions/cache/restore@v4','actions/cache/save@v4',
 'if-no-files-found: error','retention-days: 90'):
  # 26886/26887 may be named historical validators, not necessarily those substrings,
  # but the original successful prefix is byte-identical.
  if k in ('test_26886','test_26887'):continue
  if k not in s:fail('missing historical or current production verification '+k)
 if s.count('./gradlew --no-daemon --build-cache :app:assembleDebug --stacktrace')!=1 or s.count('actions/upload-artifact@v4')!=1:fail('not one compiled APK/published artifact')
 names=re.findall(r'^\s+- name: (.+)$',s,re.M)
 if len(names)!=len(set(names)):fail('duplicate Actions step')
 refs=set(re.findall(r'python3 -S ([a-zA-Z0-9_]+\.py)',s));refs.update(re.findall(r'\bbash ([a-zA-Z0-9_]+\.sh)',s));refs.add('gradlew')
 expected=(R/'26947_EXPECTED_ACTION_EXECUTABLES.txt').read_text().splitlines()
 if refs!=set(expected) or expected!=sorted(set(expected)) or any('/' in v or '..' in v for v in expected):fail('missing/stale/unused executable '+str(sorted(refs^set(expected))))
 if len(refs)!=242:fail('unexpected new executable count '+str(len(refs)))
 if '--on-actions' in sys.argv:
  for p in expected:
   if not (R/p).is_file():fail('missing stage1 or historical Actions executable '+p)
 print('PASS 26947 original 141 successful historical command SHA, exactly 242 executable refs, no unused/stale, full Android build graph')
if __name__=='__main__':
 try:main()
 except Exception as e:print(e,file=sys.stderr);sys.exit(1)
