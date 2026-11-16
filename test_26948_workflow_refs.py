#!/usr/bin/env python3
"""Exact successful 26947 historical 141 commands and exhaustive changed 26948 action graph."""
import hashlib,re,sys
from build_26948_incremental import R,fail
HIST='bce2979074eba73c9fa7defa4ee5657bb3ba619d705b2bb79334b1f901a7648b'
def main():
 s=(R/'.github/workflows/build-26948-change-aware.yml').read_text()
 if len(s.splitlines())<400 or s.count('      - TRIGGER_26948.txt')!=1 or '      - TRIGGER_26947.txt' in s.split('jobs:',1)[0]:fail('truncated/old trigger')
 if 'branches:\n      - experimental-clean-photon-rebuild' not in s:fail('nonexperimental branch')
 a=s.index('      - name: Checkout intended experimental branch');b=s.index('      - name: Preserve successful 26934 visual-white')
 cmds=re.findall(r'^\s+(?:python3 -S|bash)\s+\S+(?:.*)$',s[a:b],re.M)
 digest=hashlib.sha256(('\n'.join(cmds)+'\n').encode()).hexdigest()
 if len(cmds)!=141 or digest!=HIST:fail('inherited 141 exact commands differ '+str((len(cmds),digest)))
 ordered=('build_26944_incremental.py seal','build_26945_incremental.py seal','build_26946_incremental.py seal','build_26947_incremental.py seal','build_26948_incremental.py seal','build_26948_incremental.py fetch','build_26948_incremental.py prepare','test_26948_source.py --live','test_26948_sdr_hdr_math.py --live','test_26948_flicker_host.py --live','test_26948_gpu_row.py --live','test_26948_patch_proof.py --live','verify_26906_native_cache.py preflight','compile_26904_shaders_v2.sh','verify_26904_v3_cmake_handoff.py --handoff','prepare_26948_lkr_from_successful_26947.py','test_26931_native_integrity.py --native','compile_26939_shaders.sh','compile_26944_shaders.sh','compile_26948_shaders.sh','build_26948_incremental.py verify-compiled','./gradlew --no-daemon --build-cache :app:assembleDebug --stacktrace','test_26931_native_integrity.py --cmake','test_26931_native_integrity.py --apk','verify_26906_native_cache.py postflight','build_26948_incremental.py finalize','actions/upload-artifact@v4')
 pos=0
 for k in ordered:
  j=s.find(k,pos)
  if j<0:fail('missing/incorrect ordering '+k)
  pos=j+len(k)
 for required in ('verify_26904_v3_safety.py','verify_26904_v2_safety.py','test_26903_v3_archive_receipt.py','test_26925_source.py','test_26945_gainmap.py --payload','test_26946_gainmap_geometry.py --payload','test_26947_lifecycle.py --payload','test_26947_java_host.py --payload','test_26947_sealed_negatives.py','test_26948_sealed_negatives.py','test_26948_patch_proof.py --payload','test_26948_flicker_host.py --payload','test_26948_gpu_row.py --payload','test_26948_v2_shader_compat.py --payload --on-actions','test_26948_v2_shader_compat.py --live --on-actions','compile_26941_shaders.sh','compile_26942_shaders.sh','compile_26943_shaders.sh','actions/cache/restore@v4','actions/cache/save@v4','if-no-files-found: error','retention-days: 90'):
  if required not in s:fail('missing historical/current gate '+required)
 if s.count('./gradlew --no-daemon --build-cache :app:assembleDebug --stacktrace')!=1 or s.count('actions/upload-artifact@v4')!=1:fail('duplicate or absent full real APK/Artifact')
 steps=re.findall(r'^\s+- name: (.+)$',s,re.M)
 if len(steps)!=len(set(steps)):fail('duplicate stage names')
 refs=set(re.findall(r'python3 -S ([a-zA-Z0-9_]+\.py)',s))|set(re.findall(r'\bbash ([a-zA-Z0-9_]+\.sh)',s))|{'gradlew'}
 want=(R/'26948_EXPECTED_ACTION_EXECUTABLES.txt').read_text().splitlines()
 if sorted(refs)!=want or len(refs)!=252 or any('/' in x or '..' in x for x in want):fail('unused/stale/missing refs '+str(sorted(set(want)^refs)))
 if '--on-actions' in sys.argv:
  for p in want:
   if not (R/p).is_file():fail('missing in real GitHub checkout '+p)
 print('PASS 26948 preserved exact 141 original successful commands SHA, 252 referenced executables no missing/unused/stale, one pinned shader/NDK/Kotlin/Java/assemble APK')
if __name__=='__main__':
 try:main()
 except Exception as e:print(e,file=sys.stderr);sys.exit(1)
