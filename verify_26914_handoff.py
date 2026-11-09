#!/usr/bin/env python3
"""Validate complete 26914 three-stage SHA seal, source scope and historic real gates."""
from pathlib import Path
import hashlib,ast,re,sys
R=Path(__file__).resolve().parent
WF='.github/workflows/build-26914-change-aware.yml';BLD='build_26914_incremental.py'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def need(x,why):
 if not x:raise AssertionError('26914 BLOCKED '+why)
def manifest(p):
 d={}
 for row in (R/p).read_text().splitlines():
  h,k=row.split('  ',1);need(k.startswith('app/') and k not in d and bool(re.fullmatch('[a-f0-9]{64}',h)),'invalid manifest row');d[k]=h
 return d
def verify():
 old=manifest('26914_BASE_26913_FULL_APP.sha256');new=manifest('26914_PRECOMPILE_EXPECTED_FULL_APP.sha256')
 changed=(R/'26914_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines()
 added=(R/'26914_ADDED_RUNTIME_PATHS.txt').read_text().splitlines();deleted=(R/'26914_DELETED_RUNTIME_PATHS.txt').read_text().splitlines()
 need(len(old)==2036 and len(new)==2035 and len(changed)==len(set(changed))==14 and not added and len(deleted)==1,'bad source universe or scope')
 need(deleted==['app/src/main/java/com/particlesdevs/photoncamera/ui/settings/custompreferences/Iris26912PerLensHighlightSwitch.java'],'unexpected deletion')
 need(set(old)-set(new)==set(deleted) and not set(new)-set(old),'unexpected added/deleted file')
 need({p for p in old if p in new and old[p]!=new[p]}==set(changed)-set(deleted) and len(set(old)-set(changed))==2022,'unapproved runtime mutation')
 for p in old:
  if p.startswith(('app/src/main/assets/','app/src/main/jniLibs/','app/src/main/cpp/iris26864/vendor/')):need(new.get(p)==old[p],'native vendor or shader changed '+p)
 for p in changed:
  f=R/'handoff_payload_26914'/p
  if p in deleted:need(not f.exists(),'deleted path included')
  else:need(f.is_file() and sha(f)==new[p],'altered candidate overlay '+p)
 paths=(R/'26914_STAGE1_PATHS.txt').read_text().splitlines()
 need(len(paths)==len(set(paths)) and '26914_HANDOFF_HASHES.sha256' in paths,'stage1 inventory duplicate or missing seal')
 need(set(x for x in paths if x.startswith('handoff_payload_26914/'))=={'handoff_payload_26914/'+p for p in changed if p not in deleted},'wrong stage1 runtime payload')
 receipts={}
 for row in (R/'26914_HANDOFF_HASHES.sha256').read_text().splitlines():
  h,p=row.split('  ',1);need(p not in receipts and re.fullmatch('[a-f0-9]{64}',h) is not None,'invalid seal row');receipts[p]=h
 need(set(receipts)==set(paths)-{'26914_HANDOFF_HASHES.sha256'}|{WF,'TRIGGER_26914.txt'},'stage inventory/seal disagreement')
 for p,h in receipts.items():
  f=R/p;need(f.is_file() and not f.is_symlink() and sha(f)==h,'SHA tamper '+p)
 need((R/'TRIGGER_26914.txt').read_bytes()==b'RUN_26914_UNIFIED_B_NOISE_ALWAYS_HIGHLIGHT_SETTINGS_V1\n','wrong trigger')
 b=(R/BLD).read_text();w=(R/WF).read_text();ast.parse(b)
 need('experimental-clean-photon-rebuild' in w and w.count('TRIGGER_26914.txt')==1,'wrong branch/trigger')
 need('  pull_request:' not in w and '  pull_request_target:' not in w and '  schedule:' not in w,'extra unsafe workflow trigger')
 need(w.count('build_26914_incremental.py')==5 and w.count('./gradlew --no-daemon --build-cache :app:assembleDebug')==1,'compiled workflow weakened')
 need('build_26913_incremental.py' not in w and 'photon_26913_outputs/' not in w,'stale workflow references')
 for s in ['RUN=42543642399',"COMMIT='b14f6dda1eae08677469e67cff8cab18f6bf96a6'",'ART_ID=13642374414',
   'ed00774f8f3e29a6134ba5cfcaf2f47d828034ff5ffa2967b741e8c9117b9c5a',
   '9b6fe38e3a337c0a2f834d459777340330ae339eb0ae834c095da4573f6e710d',
   '8ebd0be6412264bca09cacd530dca2b5f31e382252a73ee5af2b2ef3dbfc7c78',
   'e748c678008c7a09ddefec122fafda55bff4df3679ca855b36f3c298e188b4ca',
   "get('26913_PREBUILD_SEALED_APP.sha256')", "get('ACTUAL_EXECUTED_build_26913_incremental.py')",
   'if len(apks)!=1:', 'source=2035 runtime_changed=14 protected=2022 added=0 deleted=1',
   'REAL KOTLIN COMPILE: PASS','REAL JAVA COMPILE: PASS','NATIVE/NDK COMPILE: PASS','REAL PINNED GLSL COMPILE: PASS',
   'REAL SPIR-V VALIDATION: PASS','REAL ANDROID Gradle :app:assembleDebug: PASS',
   '26914_DELETED_RUNTIME_PATHS.txt',':app:buildCMakeDebug[arm64-v8a]',':app:buildCMakeDebug[armeabi-v7a]']:
  need(s in b,'required prior/run/compilation gate absent '+s)
 for s in ['verify_26911_handoff.py','verify_26912_handoff.py','verify_26913_handoff.py','verify_26914_handoff.py',
   'test_26912_sealed_negatives.py','test_26913_sealed_negatives.py','test_26914_sealed_negatives.py',
   'test_26907_hue_source.py','test_26908_exposure_render.py','test_26909_exposure.py','test_26910_capture_focus.py',
   'test_26911_continuity.py','test_26913_brightness.py --payload','test_26914_source.py --live',
   'verify_26904_v3_safety.py','verify_26904_v2_safety.py','build_26904_incremental.py seal',
   'verify_26906_native_cache.py preflight','compile_26904_shaders_v2.sh',
   'verify_26904_v3_cmake_handoff.py --handoff','compile_26906_tone_glsl.sh',
   'compile_26907_hue_glsl.sh','compile_26908_render_glsl.sh',
   'verify_26906_native_cache.py postflight','actions/upload-artifact@v4']:
  need(s in w,'removed historical regression/gate '+s)
 sequence=['verify_26914_handoff.py','test_26914_sealed_negatives.py','build_26914_incremental.py seal',
   'verify_26904_v3_safety.py','verify_26904_v2_safety.py','build_26914_incremental.py fetch',
   'build_26914_incremental.py prepare','test_26914_source.py --live','verify_26906_native_cache.py preflight',
   'compile_26904_shaders_v2.sh','verify_26904_v3_cmake_handoff.py --handoff','compile_26906_tone_glsl.sh',
   'compile_26907_hue_glsl.sh','compile_26908_render_glsl.sh',
   'build_26914_incremental.py verify-compiled',':app:assembleDebug','verify_26906_native_cache.py postflight',
   'build_26914_incremental.py finalize','actions/upload-artifact@v4']
 need([w.index(x) for x in sequence]==sorted(w.index(x) for x in sequence),'successful guarded stage ordering modified')
 print('PASS 26914 exact compiled 26913 authority, strict 3-stage seal, 14 changes, 2022 protected and historical regression/real compilation gates')
if __name__=='__main__':
 try:verify()
 except Exception as e:print('FAIL',e,file=sys.stderr);sys.exit(1)
