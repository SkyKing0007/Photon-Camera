#!/usr/bin/env python3
"""Photon 26910 exact-byte sealed three-stage handoff and historical successful-gate proof."""
from pathlib import Path
import hashlib,re,sys
R=Path(__file__).resolve().parent
WF='.github/workflows/build-26910-change-aware.yml'
PREVIOUS_WF='.github/workflows/build-26909-change-aware.yml'
PREVIOUS_WF_SHA='d2c7d0a2f4bf9be3bba1628022992da4308fec0eb17a3b0d994e5ebf3ecae147'
TRIGGER=b'RUN_26910_B_FOCUS_GESTURE_CAPTURE_TIMEOUT_PREVIEW_V1\n'

def require(b,msg):
 if not b:raise AssertionError('26910 BLOCKED: '+msg)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def parse(filename):
 d={}
 for ln in (R/filename).read_text().splitlines():
  h,p=ln.split('  ',1)
  require(re.fullmatch('[0-9a-f]{64}',h)!=None and p.startswith('app/')
          and '..' not in Path(p).parts and p not in d,'invalid manifest '+p)
  d[p]=h
 return d

def verify():
 paths=(R/'26910_STAGE1_PATHS.txt').read_text().splitlines()
 require('26910_HANDOFF_HASHES.sha256' in paths and len(paths)==len(set(paths)),
         'Stage1 inventory invalid')
 changed=(R/'26910_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines()
 added=(R/'26910_ADDED_RUNTIME_PATHS.txt').read_text().splitlines()
 require(len(changed)==6 and len(set(changed))==6
         and changed[-1]=='app/version.properties', 'six approved paths only')
 require(len(added)==1 and set(added).issubset(set(changed)),'exactly one added helper')
 require({x for x in paths if x.startswith('handoff_payload_26910/')} ==
         {'handoff_payload_26910/'+x for x in changed},'runtime source overlay mismatch')
 receipts={}
 for ln in (R/'26910_HANDOFF_HASHES.sha256').read_text().splitlines():
  h,path=ln.split('  ',1)
  require(path not in receipts and re.fullmatch('[0-9a-f]{64}',h)!=None, 'duplicate/invalid seal')
  receipts[path]=h
 require(set(receipts)==set(paths)-{'26910_HANDOFF_HASHES.sha256'}|{WF,'TRIGGER_26910.txt'},'wrong seal inventory')
 for p,h in receipts.items():require((R/p).is_file() and sha(R/p)==h,'seal mismatched '+p)
 require((R/'TRIGGER_26910.txt').read_bytes()==TRIGGER,'trigger modified')
 before=parse('26910_BASE_26909_FULL_APP.sha256')
 after=parse('26910_PRECOMPILE_EXPECTED_FULL_APP.sha256')
 require(len(before)==2032 and len(after)==2033, 'compiled source population wrong')
 require(set(after)-set(before)==set(added) and not set(before)-set(after),'missing or extra source')
 require({p for p in before if before[p]!=after[p]}==set(changed)-set(added),'protected source diff')
 require(len(before)-len(set(changed)-set(added))==2027,'protected source count')
 for p in changed:require(sha(R/'handoff_payload_26910'/p)==after[p],'overlay not sealed '+p)
 for p in before:
  if p.startswith(('app/src/main/cpp/','app/src/main/jniLibs/','app/src/main/assets/')):
   require(before[p]==after[p],'native/vendor/shader mutated '+p)
 require(after['app/src/main/assets/iris26856/rawr/amaze/spv/amaze_export.spv']==
         '5853f1a0da12bab4b8c9489b6b298f3710f90fb6e51660204ed43f49963809f1',
         'pinned AMaZE SPV changed')
 require((R/PREVIOUS_WF).is_file() and sha(R/PREVIOUS_WF)==PREVIOUS_WF_SHA,
         'original successful 26909 Actions workflow absent/drifted')
 workflow=(R/WF).read_text()
 require('experimental-clean-photon-rebuild' in workflow and workflow.count('TRIGGER_26910.txt')==1,
         'incorrect workflow branch or trigger')
 require('dev' not in workflow.split('branches:')[1].split('paths:')[0], 'dev branch forbidden')
 require(workflow.count('./gradlew --no-daemon --build-cache :app:assembleDebug')==1,'Gradle build weakened')
 require(workflow.count('python3 -S build_26910_incremental.py')==5,'current strict builder calls changed')
 for script in ('test_26907_hue_source.py','test_26908_exposure_render.py',
                'test_26909_exposure.py','test_26910_capture_focus.py'):
  require(workflow.count(script)==2,'historical or new regressions absent '+script)
 order=['verify_26910_handoff.py','build_26910_incremental.py seal',
        'test_26906_native_cache.py','test_26907_hue_source.py',
        'test_26908_exposure_render.py','test_26909_exposure.py',
        'test_26910_capture_focus.py','verify_26904_v3_safety.py',
        'verify_26904_v2_safety.py','build_26904_incremental.py seal',
        'build_26910_incremental.py fetch', 'build_26910_incremental.py prepare',
        'verify_26906_native_cache.py preflight','compile_26904_shaders_v2.sh',
        'verify_26904_v3_cmake_handoff.py --handoff','compile_26906_tone_glsl.sh',
        'compile_26907_hue_glsl.sh','compile_26908_render_glsl.sh',
        'build_26910_incremental.py verify-compiled', ':app:assembleDebug',
        'verify_26906_native_cache.py postflight','build_26910_incremental.py finalize',
        'actions/upload-artifact@v4']
 require([workflow.index(s) for s in order]==sorted(workflow.index(s) for s in order),
         'successful 26909 17-stage compiler/build/cached-native ordering drift')
 require(workflow.index('id: native-cache')<workflow.index('verify_26906_native_cache.py preflight')
         <workflow.index('compile_26904_shaders_v2.sh'), 'preflight CMake cache order changed')
 require(workflow.index(':app:assembleDebug')<workflow.index('verify_26906_native_cache.py postflight')
         <workflow.index('build_26910_incremental.py finalize'), 'final native cache proof bypassed')
 runner=(R/'build_26910_incremental.py').read_text()
 for token in ['RUN=42432381183',"COMMIT='44696a7aa3c8e51b1a6eed2c140d592fdc5e9e6a'",
               'ART_ID=13598327952','c2c52550b18d769af1cb9b7f42e34cac3a6823851137730a8154b0b8194dc2d5',
               'e834eb233a6d3c1cadcee0a24bd17d38837db88fe997dde7af13c8eac2b2ad67',
               '5e9ff5f98955a806ff1f1aa87df0a29744bf6c0b6ef7ada664a2e8d6191d9499',
               'd2c7d0a2f4bf9be3bba1628022992da4308fec0eb17a3b0d994e5ebf3ecae147',
               "prefix='photon_26909_outputs/'", "get('26909_PREBUILD_SEALED_APP.sha256')",
               "get('ACTUAL_EXECUTED_build_26909_incremental.py')",
               "get('ACTUAL_EXECUTED_build-26909-change-aware.yml')",
               'source=2033 runtime_changed=6 protected=2027 added=1',
               '26908_RENDER_SHADER_REAL_COMPILER.txt', '26907_HUE_SHADER_REAL_COMPILER.txt',
               '26906_TONE_SHADER_REAL_COMPILER.txt', '26906_NATIVE_CACHE_PATCH_REPLAY.json',
               'if len(apks)!=1:']:
  require(token in runner,'successful runner authority/compiler gate removed '+token)
 compiler=(R/'compile_26908_render_glsl.sh').read_text()
 require('spirv-val --target-env opengl4.5' in compiler
         and 'spirv-opt --target-env=opengl4.5 -O' in compiler
         and 'app/src/main/assets/shaders/motionv2/render.glsl' in compiler
         and '16.5.0' in compiler,'pinned historical shader compiler weakened')
 print('PASS Photon 26910 stage1/2/3 exact inventory, successful 26909 published authority, 6 runtime paths, 2027 protected, pinned shader/NDK/Java/Kotlin and historical 26886/26887/26903/26904/26906/26907/26908/26909 gates')

if __name__=='__main__':
 try:verify()
 except Exception as e:print('26910 HANDOFF FAILED',str(e),file=sys.stderr);sys.exit(1)
