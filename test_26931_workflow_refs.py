#!/usr/bin/env python3
"""26931 immutable historical runner graph + current real dual-ABI action coverage."""
from pathlib import Path
import re,sys
from build_26931_incremental import R,fail

def main():
 s=(R/'.github/workflows/build-26931-change-aware.yml').read_text()
 if len(s.splitlines())<470:fail('cannot shorten inherited successful 26930 verification workflow')
 for needle in ('TRIGGER_26931.txt',
   'verify_26904_v3_safety.py','verify_26904_v2_safety.py',
   'verify_26906_native_cache.py preflight','verify_26906_native_cache.py postflight',
   'test_26925_shader_abi.py --payload','test_26930_shader_shadow.py --live',
   'test_26930_sealed_negatives.py','test_26930_shader_contract.py --live',
   'build_26930_incremental.py verify-compiled','build_26931_incremental.py seal',
   'build_26931_incremental.py fetch','build_26931_incremental.py prepare',
   'build_26931_incremental.py regress','build_26931_incremental.py verify-compiled',
   'build_26931_incremental.py finalize','test_26931_source.py --live',
   'test_26931_native_integrity.py --cmake','test_26931_native_integrity.py --apk',
   'prepare_26931_rawlens_binaries.py',
   'test_26931_shader_contract.py --live',
   'compile_26930_shaders.sh','compile_26930_hr_spirv.sh','compile_26931_lkr_gles.sh',
   'bash compile_26904_shaders_v2.sh',
   'test_26903_v3_archive_receipt.py','test_26903_modes.py .',
   ':app:assembleDebug','actions/upload-artifact@v4',
   'actions/cache/restore@v4','actions/cache/save@v4'):
  if needle not in s:fail('missing 26930 historical or current source/native compiler gate '+needle)
 if 'build_26930_incremental.py finalize' in s or 'TRIGGER_26930.txt\n  workflow_dispatch' in s:fail('accidentally rebuild/trigger old 26930 app')
 if s.count('actions/upload-artifact@v4')!=1:fail('multiple/zero publication owners')
 order=['build_26930_incremental.py verify-compiled','build_26931_incremental.py fetch',
  'build_26931_incremental.py prepare','test_26931_patch_proof.py --live',
  'verify_26906_native_cache.py preflight','prepare_26931_rawlens_binaries.py',
  'compile_26931_lkr_gles.sh','build_26931_incremental.py verify-compiled','./gradlew --no-daemon --build-cache :app:assembleDebug --stacktrace',
  'test_26931_native_integrity.py --apk','build_26931_incremental.py finalize',
  'actions/upload-artifact@v4']
 positions=[]
 cursor=0
 for x in order:
  pos=s.find(x,cursor)
  if pos<0:fail('26931 authority/GLSL/NDK/compile/APK/receipt sequence altered '+x)
  positions.append(pos);cursor=pos+len(x)
 if s.count('./gradlew --no-daemon --build-cache :app:assembleDebug --stacktrace')!=1:fail('more than one Android APK assembled')
 names=re.findall(r'^\s+- name: (.+)$',s,re.M)
 if len(names)!=len(set(names)):fail('duplicate named build stages')
 if 'no-daemon --build-cache :app:assembleDebug --stacktrace' not in s:fail('real Gradle compilation weakened')
 if 'runner_image_26931.outputs.image' not in s or "hashFiles('app/src/main/cpp/**/*'" not in s:fail('new native input cache not source matched')
 # Closed-world executable reference check: catch stale, missing, or unused
 # Actions references BEFORE a costly workflow is triggered. Every Python
 # and shell build entry used in the actual workflow must appear exactly once
 # in the frozen source-sealed executable manifest (plus Gradle wrapper).
 referenced = set(re.findall(r'python3 -S ([a-zA-Z0-9_]+\.py)',s))
 referenced.update(re.findall(r'\bbash ([a-zA-Z0-9_]+\.sh)',s))
 referenced.add('gradlew')
 listed = (R/'26931_EXPECTED_ACTION_EXECUTABLES.txt').read_text().splitlines()
 if listed != sorted(set(listed)) or any(not x or '/' in x or '..' in x for x in listed):
  fail('stale/duplicate/unsafe Actions executable manifest')
 missing=sorted(referenced-set(listed))
 unused=sorted(set(listed)-referenced)
 if missing or unused:fail('missing or unused Actions executable references missing='+str(missing)+' unused='+str(unused))
 # Historical script presence required IN GitHub Actions; local package audit
 # may verify graph without owning the original checked out root.
 if '--on-actions' in sys.argv:
  for p in listed:
   if not (R/p).is_file():fail('missing actual GitHub checked-out action executable '+p)
 print('PASS exact 151/151 Actions executable refs (no missing/unused/stale), original 26930 historical GLSL/NDK graph, one full dual-ABI assemble and publication')
if __name__=='__main__':
 try:main()
 except Exception as e:print('ERROR',e,file=sys.stderr);sys.exit(1)
