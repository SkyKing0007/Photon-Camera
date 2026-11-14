#!/usr/bin/env python3
"""Closed-world current+historical Actions executable references and single APK owner."""
from pathlib import Path
import re,sys
from build_26932_incremental import R,fail

def main():
 s=(R/'.github/workflows/build-26932-change-aware.yml').read_text()
 if len(s.splitlines())<550:fail('inherited 26930->26931 17+ stage workflow was weakened')
 needed=('TRIGGER_26932.txt','verify_26904_v3_safety.py','verify_26904_v2_safety.py',
  'test_26903_v3_archive_receipt.py','test_26925_shader_abi.py --payload',
  'test_26930_shader_contract.py --live','test_26931_native_integrity.py --apk',
  'build_26931_incremental.py verify-compiled','compile_26931_lkr_gles.sh',
  'prepare_26931_rawlens_binaries.py','build_26932_incremental.py seal',
  'build_26932_incremental.py fetch','build_26932_incremental.py prepare',
  'test_26932_patch_proof.py --live','test_26932_shader_contract.py --live',
  'test_26932_math.py --live','compile_26932_shaders.sh',
  'build_26932_incremental.py verify-compiled','verify_26906_native_cache.py postflight',
  'build_26932_incremental.py finalize',':app:assembleDebug','actions/cache/restore@v4',
  'actions/cache/save@v4','actions/upload-artifact@v4')
 for token in needed:
  if token not in s:fail('missing required historical or current executable '+token)
 if s.count('actions/upload-artifact@v4')!=1 or s.count('./gradlew --no-daemon --build-cache :app:assembleDebug --stacktrace')!=1:fail('more than one APK build or publisher')
 for bad in ('build_26931_incremental.py finalize','build_26930_incremental.py finalize','TRIGGER_26931.txt\n  workflow_dispatch'):
  if bad in s:fail('26932 accidentally builds old APK '+bad)
 order=('build_26931_incremental.py verify-compiled','build_26932_incremental.py seal',
  'build_26932_incremental.py fetch','build_26932_incremental.py prepare',
  'test_26932_patch_proof.py --live','verify_26906_native_cache.py preflight',
  'compile_26932_shaders.sh','build_26932_incremental.py verify-compiled',
  './gradlew --no-daemon --build-cache :app:assembleDebug --stacktrace',
  'test_26931_native_integrity.py --apk','build_26932_incremental.py finalize',
  'actions/upload-artifact@v4')
 cursor=0
 for x in order:
  pos=s.find(x,cursor)
  if pos<0:fail('incorrect seeded authority real shader build order '+x)
  cursor=pos+len(x)
 names=re.findall(r'^\s+- name: (.+)$',s,re.M)
 if len(names)!=len(set(names)):fail('duplicate workflow stage name')
 referenced=set(re.findall(r'python3 -S ([a-zA-Z0-9_]+\.py)',s))
 referenced.update(re.findall(r'\bbash ([a-zA-Z0-9_]+\.sh)',s));referenced.add('gradlew')
 listed=(R/'26932_EXPECTED_ACTION_EXECUTABLES.txt').read_text().splitlines()
 if sorted(set(listed))!=listed or any('/' in k or '..' in k for k in listed):fail('stale/noncanonical executable list')
 missing=sorted(referenced-set(listed));unused=sorted(set(listed)-referenced)
 if missing or unused:fail('missing/unused 26932 executable refs: missing='+str(missing)+' unused='+str(unused))
 if '--on-actions' in sys.argv:
  for p in listed:
   if not (R/p).is_file():fail('required historical/current executable absent from GitHub checkout '+p)
 print('PASS full 26932 '+str(len(listed))+'/'+str(len(listed))+' closed-world executable refs, historical 26931 GLSL and native paths, 1 APK')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
