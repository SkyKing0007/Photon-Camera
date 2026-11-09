#!/usr/bin/env python3
"""Photon 26915 fail-closed, three-stage, source/runner/workflow validator.
The older successful 26914 V2 runner remains historical build mechanics authority.
"""
from pathlib import Path
import hashlib,re
R=Path(__file__).resolve().parent
WF='.github/workflows/build-26915-change-aware.yml'
PREV_WF='.github/workflows/build-26914-v2-change-aware.yml'
PREV_WF_SHA='5f5af7aab0a46fdf71abc2c89e4bfb3803321fd93424723ce2a6717b5c90cc84'
PREV_BUILDER_SHA='0cc4c6c6d4829f89fe5a7e8d22f5585ada746b36a66893470dc1351cae374376'
TRIGGER=b'RUN_26915_B_TRUE2X_FULL_NORMAL_TELE_STRIDE_PAIR_V1\n'
def need(v,m):
 if not v:raise AssertionError('26915 BLOCKED '+m)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def manifest(p):
 d={}
 for line in (R/p).read_text().splitlines():
  h,k=line.split('  ',1)
  need(re.fullmatch('[a-f0-9]{64}',h) is not None and k.startswith('app/') and k not in d and '..' not in Path(k).parts,'bad manifest')
  d[k]=h
 return d

def verify():
 stage=(R/'26915_STAGE1_PATHS.txt').read_text().splitlines()
 need(len(stage)==len(set(stage)) and len(stage)>12 and '26915_HANDOFF_HASHES.sha256' in stage,'wrong stage1 inventory')
 need(not any(p.startswith('/') or '..' in Path(p).parts for p in stage),'unsafe stage path')
 receipts={}
 for line in (R/'26915_HANDOFF_HASHES.sha256').read_text().splitlines():
  h,p=line.split('  ',1)
  need(re.fullmatch('[a-f0-9]{64}',h) is not None and p not in receipts,'duplicate/invalid seal')
  receipts[p]=h
 need(set(receipts)==(set(stage)-{'26915_HANDOFF_HASHES.sha256'})|{WF,'TRIGGER_26915.txt'},'wrong SHA inventory')
 for path,h in receipts.items():
  f=R/path
  need(f.is_file() and not f.is_symlink() and sha(f)==h,'changed/missing SHA sealed '+path)
 need((R/'TRIGGER_26915.txt').read_bytes()==TRIGGER,'wrong last trigger')
 need((R/'26915_FULL_INDEX_FORWARD.patch').read_bytes().count(b'diff --git ')==7,'not seven full-index patch files')
 need((R/PREV_WF).is_file() and sha(R/PREV_WF)==PREV_WF_SHA,'26914 V2 actual successful workflow differs')
 need((R/'build_26914_v2_incremental.py').is_file()
      and sha(R/'build_26914_v2_incremental.py')==PREV_BUILDER_SHA,'26914 V2 actual successful builder differs')
 base=manifest('26915_BASE_26914_V2_FULL_APP.sha256');after=manifest('26915_PRECOMPILE_EXPECTED_FULL_APP.sha256')
 changed=(R/'26915_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines()
 added=(R/'26915_ADDED_RUNTIME_PATHS.txt').read_text().splitlines()
 deleted=(R/'26915_DELETED_RUNTIME_PATHS.txt').read_text().splitlines()
 need(len(base)==2035 and len(after)==2036 and len(changed)==7
      and len(set(changed))==len(changed) and len(added)==1 and not deleted
      and set(added).issubset(set(changed)),'wrong source universe/change count')
 need(set(after)-set(base)==set(added) and not (set(base)-set(after))
      and {p for p in base if base[p]!=after[p]}==set(changed)-set(added),
      'unapproved source changes')
 need(len(base)-len(changed)+len(added)==2029,'protected count mismatch')
 need({p for p in stage if p.startswith('handoff_payload_26915/')}==
      {'handoff_payload_26915/'+p for p in changed},'overlay Stage1 does not match allowlist')
 for p in changed:need(sha(R/'handoff_payload_26915'/p)==after[p],'overlay hash does not match expected '+p)
 for p in base:
  if p.startswith(('app/src/main/assets/','app/src/main/jniLibs/','app/src/main/cpp/iris26864/')):
   need(base[p]==after[p],'protected vendor/NDK/Amaze changed '+p)
 need(after['app/src/main/assets/iris26856/rawr/amaze/spv/amaze_export.spv']==
      '5853f1a0da12bab4b8c9489b6b298f3710f90fb6e51660204ed43f49963809f1','pinned AMaZE binary changed')
 need((R/'handoff_payload_26915/app/version.properties').read_text().count('VERSION_BUILD=26915')==1,'wrong version')
 builder=(R/'build_26915_incremental.py').read_text();wf=(R/WF).read_text()
 for term in ["RUN=42679211318", "COMMIT='dddbf99a1a6977fc02e973fce1631195e822f264'",
              'ART_ID=13703245819','09cf9bf689eb1c2111aa75c8837f733a094e0c8d546653fe4f852eaea6ecaa15',
              'bf735dc2c49730d65f11c1272e7443a5c41215c1964b2e3cffcf97e135b39631',
              PREV_BUILDER_SHA,PREV_WF_SHA,
              "get('26914_V2_PREBUILD_SEALED_APP.sha256')",
              "get('ACTUAL_EXECUTED_build_26914_v2_incremental.py')",
              "get('ACTUAL_EXECUTED_build-26914-v2-change-aware.yml')",
              'source=2036 runtime_changed=7 protected=2029 added=1 deleted=0',
              "'REAL KOTLIN COMPILE: PASS'", "'REAL JAVA COMPILE: PASS'", "'NATIVE/NDK COMPILE: PASS'",
              'if len(apks)!=1:',"OUT/'26915_COMPILER_STATUS.txt'", "OUT/'26915_PREBUILD_SEALED_APP.sha256'",
              "OUT/'26915_candidate_app_source.tar.gz'", "OUT/'ACTUAL_EXECUTED_build_26915_incremental.py'",
              "OUT/'ACTUAL_EXECUTED_build-26915-change-aware.yml'"]:
  need(term in builder,'builder incorrect authority/receipt '+term)
 need('photon_26913_outputs/' not in builder and 'build_26913_incremental.py seal' not in builder,'stale builder predecessor')
 need('experimental-clean-photon-rebuild' in wf and wf.count('TRIGGER_26915.txt')==1,'wrong workflow trigger')
 need('TRIGGER_26914_V2.txt' not in wf and 'TRIGGER_26914.txt' not in wf,'stale workflow trigger')
 need(wf.count('build_26915_incremental.py')==5,'incorrect five builder invocations')
 need(wf.count('./gradlew --no-daemon --build-cache :app:assembleDebug')==1
      and wf.count('actions/upload-artifact@v4')==1,'real Android assembly/artifact omitted')
 for k in ['verify_26914_v2_handoff.py','test_26914_v2_source.py --payload',
           'test_26914_kotlin_owner.py handoff_payload_26914/',
           'test_26914_kotlin_owner.py handoff_payload_26914_v2/',
           'test_26915_source.py --payload','test_26915_source.py --live',
           'test_26915_native_guide.py --payload','test_26915_native_guide.py --live',
           'test_26915_capture.py --payload','test_26915_capture.py --live',
           'test_26915_java_carrier.py --payload','test_26915_java_carrier.py --live',
           'test_26915_patch_proof.py --live',
           'test_26915_kotlin_consumer.py --static-only --live',
           'test_26915_sealed_negatives.py',
           'verify_26906_native_cache.py preflight','verify_26906_native_cache.py postflight',
           'compile_26904_shaders_v2.sh','verify_26904_v3_cmake_handoff.py --handoff',
           'compile_26906_tone_glsl.sh','compile_26907_hue_glsl.sh','compile_26908_render_glsl.sh',
           'verify_26904_v3_safety.py','verify_26904_v2_safety.py',
           'build_26904_incremental.py seal','test_26904_changeaware.py . --with-javac']:
  need(k in wf,'missing historical/current compiler or regression '+k)
 seq=['verify_26915_handoff.py', 'build_26915_incremental.py seal',
      'test_26906_native_cache.py', 'test_26907_hue_source.py',
      'verify_26904_v3_safety.py', 'verify_26904_v2_safety.py',
      'build_26904_incremental.py seal', 'build_26915_incremental.py fetch',
      'build_26915_incremental.py prepare', 'verify_26906_native_cache.py preflight',
      'compile_26904_shaders_v2.sh', 'verify_26904_v3_cmake_handoff.py --handoff',
      'compile_26906_tone_glsl.sh', 'compile_26907_hue_glsl.sh', 'compile_26908_render_glsl.sh',
      'build_26915_incremental.py verify-compiled',
      ':app:assembleDebug', 'verify_26906_native_cache.py postflight',
      'build_26915_incremental.py finalize', 'actions/upload-artifact@v4']
 indices=[wf.index(k) for k in seq]
 need(indices==sorted(indices),'guarded inherited stage ordering changed')
 need(wf.index('id: native-cache')<wf.index('verify_26906_native_cache.py preflight')
      <wf.index('compile_26904_shaders_v2.sh'),'native-cache guard ordering wrong')
 need(wf.index('test_26915_source.py --live')<wf.index(':app:assembleDebug'),'new live source regression after assembly')
 for term in ['photon_26914_v2_outputs/','26914_v2_gradle_assemble.log','TRIGGER_26913.txt','build_26914_v2_incremental.py seal']:
  need(term not in wf,'stale workflow output/trigger '+term)
 print('PASS 26915 new sealed SHA inventory; 2035->2036 exact source; 7 allowlisted/2029 protected; unchanged successful 26914 V2 17-stage shader/Kotlin/Java/NDK/assemble/caches/patch receipts')
if __name__=='__main__':verify()
