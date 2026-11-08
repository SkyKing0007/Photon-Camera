#!/usr/bin/env python3
"""Exact-source sealed three-stage validator with successful 26910 verification authority."""
from pathlib import Path
import hashlib,re,sys
R=Path(__file__).resolve().parent
WF='.github/workflows/build-26911-change-aware.yml'
PRIOR_WF='.github/workflows/build-26910-change-aware.yml'
PRIOR_WORKFLOW_SHA='ac0be9aa36067752d36c9545e57c5ab06cd379c43f0897a0ea690d705f44a898'
TRIGGER=b'RUN_26911_B_PREVIEW_CAPTURE_EXPOSURE_CONTINUITY_V1\n'

def must(condition,message):
 if not condition:raise AssertionError('26911 BLOCKED '+message)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def manifest(filename):
 result={}
 for line in (R/filename).read_text().splitlines():
  h,p=line.split('  ',1)
  must(re.fullmatch('[0-9a-f]{64}',h) is not None and p.startswith('app/')
       and p not in result and '..' not in Path(p).parts,'invalid/duplicate source manifest row')
  result[p]=h
 return result

def verify():
 paths=(R/'26911_STAGE1_PATHS.txt').read_text().splitlines()
 changed=(R/'26911_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines()
 added=(R/'26911_ADDED_RUNTIME_PATHS.txt').read_text().splitlines()
 must(len(paths)==len(set(paths)) and '26911_HANDOFF_HASHES.sha256' in paths,'invalid Stage1 inventory')
 must(len(changed)==4 and len(set(changed))==4 and changed[-1]=='app/version.properties','wrong four-file allowlist')
 must(len(added)==1 and set(added).issubset(set(changed)),'one source helper added only')
 must({p for p in paths if p.startswith('handoff_payload_26911/')}=={'handoff_payload_26911/'+p for p in changed},'payload scope')
 receipts={}
 for line in (R/'26911_HANDOFF_HASHES.sha256').read_text().splitlines():
  h,path=line.split('  ',1)
  must(path not in receipts and re.fullmatch('[0-9a-f]{64}',h) is not None,'seal duplicate')
  receipts[path]=h
 must(set(receipts)==set(paths)-{'26911_HANDOFF_HASHES.sha256'}|{WF,'TRIGGER_26911.txt'},'wrong seal inventory')
 for path,h in receipts.items():must((R/path).is_file() and sha(R/path)==h,'seal mismatch '+path)
 must((R/'TRIGGER_26911.txt').read_bytes()==TRIGGER,'altered last trigger')
 before=manifest('26911_BASE_26910_FULL_APP.sha256')
 after=manifest('26911_PRECOMPILE_EXPECTED_FULL_APP.sha256')
 must(len(before)==2033 and len(after)==2034,'unexpected source universe')
 must(set(after)-set(before)==set(added) and not set(before)-set(after),'added/deleted scope')
 must({p for p in before if before[p]!=after[p]}==set(changed)-set(added),'unapproved source modification')
 must(len(before)-len(changed)+len(added)==2030,'protected count changed')
 for p in changed:must(sha(R/'handoff_payload_26911'/p)==after[p],'wrong candidate overlay '+p)
 for p in before:
  if p.startswith(('app/src/main/cpp/','app/src/main/jniLibs/','app/src/main/assets/')):
   must(before[p]==after[p],'native/vendor/shader mutation '+p)
 must(after['app/src/main/assets/iris26856/rawr/amaze/spv/amaze_export.spv']==
       '5853f1a0da12bab4b8c9489b6b298f3710f90fb6e51660204ed43f49963809f1','pinned AMaZE binary')
 must((R/PRIOR_WF).is_file() and sha(R/PRIOR_WF)==PRIOR_WORKFLOW_SHA,'successfully executed 26910 workflow missing')
 workflow=(R/WF).read_text()
 must('experimental-clean-photon-rebuild' in workflow and workflow.count('TRIGGER_26911.txt')==1,'wrong branch/trigger')
 must('dev' not in workflow.split('branches:')[1].split('paths:')[0],'dev forbidden')
 must(workflow.count('./gradlew --no-daemon --build-cache :app:assembleDebug')==1,'real Gradle disabled')
 must(workflow.count('python3 -S build_26911_incremental.py')==5,'guarded builder invocation changed')
 for script in ['test_26907_hue_source.py','test_26908_exposure_render.py',
                'test_26909_exposure.py','test_26910_capture_focus.py','test_26911_continuity.py']:
  must(workflow.count(script)==2,'regression missing '+script)
 sequence=['verify_26911_handoff.py','build_26911_incremental.py seal',
    'test_26906_native_cache.py','test_26907_hue_source.py','test_26908_exposure_render.py',
    'test_26909_exposure.py','test_26910_capture_focus.py','test_26911_continuity.py',
    'verify_26904_v3_safety.py','verify_26904_v2_safety.py',
    'build_26904_incremental.py seal','build_26911_incremental.py fetch',
    'build_26911_incremental.py prepare','verify_26906_native_cache.py preflight',
    'compile_26904_shaders_v2.sh','verify_26904_v3_cmake_handoff.py --handoff',
    'compile_26906_tone_glsl.sh','compile_26907_hue_glsl.sh',
    'compile_26908_render_glsl.sh','build_26911_incremental.py verify-compiled',
    ':app:assembleDebug','verify_26906_native_cache.py postflight',
    'build_26911_incremental.py finalize','actions/upload-artifact@v4']
 must([workflow.index(x) for x in sequence]==sorted(workflow.index(x) for x in sequence),'17-stage ordering not preserved')
 must(workflow.index('id: native-cache')<workflow.index('verify_26906_native_cache.py preflight')
       <workflow.index('compile_26904_shaders_v2.sh'),'native cache/shader ordering violated')
 must(workflow.index(':app:assembleDebug')<workflow.index('verify_26906_native_cache.py postflight')
       <workflow.index('build_26911_incremental.py finalize'),'postflight/finalize ordering violated')
 runner=(R/'build_26911_incremental.py').read_text()
 for x in ['RUN=42450831835',"COMMIT='92e7e46f64b2a40e717d6bbb3711ff2ea296b987'",
           'ART_ID=13606221070','c317801800fbcfc1f8461a308ad1aa03860c37ab916ec2de4d3306531e174e9d',
           '76c0b817d29757a7f9120563f1081d04d2750c8609f782c8f283c511e70ac626',
           '3dce3646266759f35062f9974b4eb2842fd7d79f6d7342c849cf277e3277f063',
           PRIOR_WORKFLOW_SHA,"prefix='photon_26910_outputs/'", "get('26910_PREBUILD_SEALED_APP.sha256')",
           "get('ACTUAL_EXECUTED_build_26910_incremental.py')", "get('ACTUAL_EXECUTED_build-26910-change-aware.yml')",
           'source=2034 runtime_changed=4 protected=2030 added=1',
           '26908_RENDER_SHADER_REAL_COMPILER.txt','26907_HUE_SHADER_REAL_COMPILER.txt',
           '26906_TONE_SHADER_REAL_COMPILER.txt','26906_NATIVE_CACHE_PATCH_REPLAY.json',
           'if len(apks)!=1:','if len(changed)!=4 or',
           "'REAL PINNED GLSL COMPILE: PASS'","'REAL SPIR-V VALIDATION: PASS'",
           "'REAL KOTLIN COMPILE: PASS'","'REAL JAVA COMPILE: PASS'",
           "'NATIVE/NDK COMPILE: PASS'", "'REAL ANDROID Gradle :app:assembleDebug: PASS'",]:
  must(x in runner,'builder gate/authority absent '+x)
 shader=(R/'compile_26908_render_glsl.sh').read_text()
 must('spirv-val --target-env opengl4.5' in shader and 'spirv-opt --target-env=opengl4.5 -O' in shader
      and '16.5.0' in shader,'historical pinned SPIR-V verification weakened')
 must(sha(R/'compile_26908_render_glsl.sh')=='c85b3fceaa7c99e7ef974e8fbc38d194560fbc2df4a63fc03ff0bf2e724e8776',
      'successful unchanged 26908 shader compiler script SHA mismatch')
 print('PASS 26911 3-stage exact source, successful 26910 run/artifact/builder/workflow authority, 4 changed paths, 2030 protected, original 17-stage NDK/GLSL/SPIRV/Kotlin/Java/assemble/cached-native/26886/26887/26903/26904/26906/26907/26908/26909/26910 gates retained')
if __name__=='__main__':
 try:verify()
 except Exception as e:print('26911 HANDOFF FAILED',e,file=sys.stderr);sys.exit(1)
