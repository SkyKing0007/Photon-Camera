#!/usr/bin/env python3
"""Fail-closed new 26912 wrapper around actual successful 26911 Actions mechanics.
Never modifies, replaces, or skips historical 26886/26887/26903/26904/26906-
26911 scripts. Requires exact runtime allowlist and immutable predecessor receipt.
"""
import hashlib,pathlib,re,sys
R=pathlib.Path(__file__).resolve().parent
PRIOR='f25eed1b82e1ddb952c2b11b313aed8d6dda49e33047405cdc7baeb52dfccd29'
ACTUAL_BUILDER='1032f0f32b60452e875524973de754f965103f76b51c6a1778beb77927f0c19f'
BASE_TAR='772681c677749a803a65d554b3ce1721157e1665ece40e7c6cc7ee0f7e9e931a'
ART_SHA='eb99c742fe9484e45f475264e753460b5c3b191c36eb033d313cfd876665ddc2'
TRIGGER=b'RUN_26912_NO_SHUTTER_GATES_PER_LENS_NOISE_ALT_HIGHLIGHT_V1\n'
def must(condition,explanation):
 if not condition:raise AssertionError('26912 blocked: '+explanation)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def manifest(p):
 d={}
 for line in (R/p).read_text().splitlines():
  h,name=line.split('  ',1)
  must(re.fullmatch('[0-9a-f]{64}',h)!=None and name.startswith('app/') and name not in d and '..' not in pathlib.PurePosixPath(name).parts,'manifest malformed')
  d[name]=h
 return d

def verify():
 wf='.github/workflows/build-26912-change-aware.yml'
 prevwf=R/'.github/workflows/build-26911-change-aware.yml'
 must(prevwf.is_file() and sha(prevwf)==PRIOR,'successful 26911 historical workflow was replaced or removed')
 list1=(R/'26912_STAGE1_PATHS.txt').read_text().splitlines()
 changed=(R/'26912_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines()
 added=(R/'26912_ADDED_RUNTIME_PATHS.txt').read_text().splitlines()
 must(len(list1)==len(set(list1)) and '26912_HANDOFF_HASHES.sha256' in list1,'invalid stage1 list')
 must(len(changed)==18 and len(set(changed))==18 and changed==sorted(changed),'wrong changed source allowlist')
 must(len(added)==2 and len(set(added))==2 and set(added).issubset(set(changed)),'wrong added source list')
 must({p for p in list1 if p.startswith('handoff_payload_26912/')} ==
      {'handoff_payload_26912/'+p for p in changed},'Stage1 source overlay not exact')
 want=set(list1)-{'26912_HANDOFF_HASHES.sha256'}|{wf,'TRIGGER_26912.txt'}
 seal={}
 for ln in (R/'26912_HANDOFF_HASHES.sha256').read_text().splitlines():
  h,path=ln.split('  ',1)
  must(path not in seal and re.fullmatch('[0-9a-f]{64}',h)!=None,'duplicate/invalid seal entry')
  seal[path]=h
 must(set(seal)==want,'SHA seal inventories did not exactly cover 3 stages')
 for path,h in seal.items():must((R/path).is_file() and sha(R/path)==h,'SHA seal mismatch '+path)
 must((R/'TRIGGER_26912.txt').read_bytes()==TRIGGER,'Stage3 trigger changed')
 base=manifest('26912_BASE_26911_FULL_APP.sha256');after=manifest('26912_PRECOMPILE_EXPECTED_FULL_APP.sha256')
 must(len(base)==2034 and len(after)==2036,'wrong source count')
 must(set(after)-set(base)==set(added) and not set(base)-set(after),'wrong source added/deleted')
 must({p for p in base if base[p]!=after[p]} == set(changed)-set(added),'unauthorized changed source')
 must(len(base)-len(changed)+len(added)==2018,'protected source mismatch')
 for p in changed:must(sha(R/'handoff_payload_26912'/p)==after[p],'nonfrozen payload '+p)
 for p in base:
  if p.startswith(('app/src/main/jniLibs/','app/src/main/assets/')):
   must(base[p]==after[p],'protected binary/vendor changed '+p)
 must(after['app/src/main/assets/iris26856/rawr/amaze/spv/amaze_export.spv']==
      '5853f1a0da12bab4b8c9489b6b298f3710f90fb6e51660204ed43f49963809f1',
      'pinned AMaZE binary drift')
 workflow=(R/wf).read_text()
 must('experimental-clean-photon-rebuild' in workflow and
      workflow.count('TRIGGER_26912.txt')==1,'branch/trigger')
 must(re.search(r'paths:\s*\n\s*- TRIGGER_26912.txt\s*\n\s*workflow_dispatch:',workflow)!=None,
      'unapproved additional workflow trigger path')
 must('dev' not in workflow.split('branches:')[1].split('paths:')[0], 'dev branch forbidden')
 must(workflow.count('./gradlew --no-daemon --build-cache :app:assembleDebug')==1,'real Gradle removed')
 for x in ['verify_26911_handoff.py','test_26906_native_cache.py',
     'verify_26904_v3_safety.py','verify_26904_v2_safety.py','build_26904_incremental.py seal',
     'verify_26906_native_cache.py preflight','compile_26904_shaders_v2.sh',
     'verify_26904_v3_cmake_handoff.py --handoff','compile_26906_tone_glsl.sh',
     'compile_26907_hue_glsl.sh','compile_26908_render_glsl.sh',
     'verify_26906_native_cache.py postflight']:
  must(x in workflow,'historical compiler/regression stage dropped '+x)
 for hist in ['test_26907_hue_source.py','test_26908_exposure_render.py',
              'test_26909_exposure.py','test_26910_capture_focus.py','test_26911_continuity.py']:
  must(workflow.count(hist)==2,'historical regression repetition weakened '+hist)
 must(workflow.count('test_26912_source.py')==3,'current source test missing pre/post action')
 must(workflow.count('python3 -S build_26912_incremental.py')==5,'successful 26911 builder sequence changed')
 original=(R/'build_26912_incremental.py').read_text()
 for pinned in ['RUN=42486914433',"COMMIT='671ffd1809f7a7312797327c1e8f9a0eb7bdd897'",
                'ART_ID=13620231358',ART_SHA,BASE_TAR,ACTUAL_BUILDER,PRIOR,
                "prefix='photon_26911_outputs/'", "get('26911_PREBUILD_SEALED_APP.sha256')",
                "get('ACTUAL_EXECUTED_build_26911_incremental.py')",
                "get('ACTUAL_EXECUTED_build-26911-change-aware.yml')",
                'source=2036 runtime_changed=18 protected=2018 added=2',
                '26908_RENDER_SHADER_REAL_COMPILER.txt','26907_HUE_SHADER_REAL_COMPILER.txt',
                '26906_TONE_SHADER_REAL_COMPILER.txt','26906_NATIVE_CACHE_PATCH_REPLAY.json',
                "'REAL PINNED GLSL COMPILE: PASS'","'REAL SPIR-V VALIDATION: PASS'",
                "'REAL KOTLIN COMPILE: PASS'","'REAL JAVA COMPILE: PASS'",
                "'NATIVE/NDK COMPILE: PASS'","'REAL ANDROID Gradle :app:assembleDebug: PASS'",
                "if len(apks)!=1",'26912_PREBUILD_SEALED_APP.sha256']:
  must(pinned in original,'actual successful 26911 authority/gate omitted '+pinned)
 order=['verify_26911_handoff.py','verify_26912_handoff.py','build_26912_incremental.py seal',
        'test_26906_native_cache.py','verify_26904_v3_safety.py',
        'verify_26904_v2_safety.py','build_26904_incremental.py seal',
        'build_26912_incremental.py fetch','build_26912_incremental.py prepare',
        'verify_26906_native_cache.py preflight','compile_26904_shaders_v2.sh',
        'verify_26904_v3_cmake_handoff.py --handoff','compile_26906_tone_glsl.sh',
        'compile_26907_hue_glsl.sh','compile_26908_render_glsl.sh',
        'build_26912_incremental.py verify-compiled',':app:assembleDebug',
        'verify_26906_native_cache.py postflight','build_26912_incremental.py finalize',
        'actions/upload-artifact@v4']
 must([workflow.index(x) for x in order]==sorted(workflow.index(x) for x in order),
      'original 17-stage order modified')
 must(workflow.index('id: native-cache')<workflow.index('verify_26906_native_cache.py preflight')
     <workflow.index('compile_26904_shaders_v2.sh'),'native cache ordering wrong')
 must(workflow.index(':app:assembleDebug')<workflow.index('verify_26906_native_cache.py postflight')
     <workflow.index('build_26912_incremental.py finalize'),'postflight/finalize ordering wrong')
 must('26912_APK.sha256' in original and '26912_ACTUAL_EXECUTED_BUILDER.sha256' in original,
      'missing 26912 final artifact provenance')
 print('PASS 26912 strict SHA-sealed three-stage package, 2034 authority, 2036 candidate, 18 changed, 2018 protected, 2 new, published 26911 Action identity and executed builder, historical 26886/87/26903/26904/26906-11 preserved, original pinned glslang/SPIRV/NDK/Kotlin/Java/Gradle gates')
if __name__=='__main__':
 try:verify()
 except Exception as e:print('26912 HANDOFF FAILED',e,file=sys.stderr);sys.exit(1)
