#!/usr/bin/env python3
"""Fail-closed historical 26912 authority and 26913 exact-three-path scope."""
import hashlib,pathlib,re,sys
R=pathlib.Path(__file__).resolve().parent
PRIOR='85a170e64fcde083211297e90f5d2658ff9fb34996c1cdfcb1bfd56392d6a8fb'
ACTUAL_BUILDER='af2e5020239ca2f5edecd749747fafa9104354b838a31e988677a9a99a4b32ce'
BASE_TAR='caaba90c8aa3f66c00c50ad52090d41476dd064b435a39d1f48a73367ebb1c4c'
ART_SHA='dfd561dc3dcef030091361016635cf37f8e4a5da2db9bbff06befb2ada8d03d1'
TRIGGER=b'RUN_26913_BRIGHTNESS_LOW_ISO_SHUTTER_V1\n'
def must(ok,why):
 if not ok:raise AssertionError('26913 BLOCKED '+why)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def manifest(p):
 d={}
 for line in (R/p).read_text().splitlines():
  h,f=line.split('  ',1)
  must(bool(re.fullmatch('[0-9a-f]{64}',h)) and f.startswith('app/') and f not in d and '..' not in pathlib.PurePosixPath(f).parts,'bad manifest')
  d[f]=h
 return d
def verify():
 wf='.github/workflows/build-26913-change-aware.yml'
 prev=R/'.github/workflows/build-26912-change-aware.yml'
 must(prev.is_file() and sha(prev)==PRIOR,'successful 26912 workflow mutated/missing')
 paths=(R/'26913_STAGE1_PATHS.txt').read_text().splitlines()
 changed=(R/'26913_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines()
 added=(R/'26913_ADDED_RUNTIME_PATHS.txt').read_text().splitlines()
 must(len(paths)==len(set(paths)) and '26913_HANDOFF_HASHES.sha256' in paths,'bad stage inventory')
 must(len(changed)==3 and len(set(changed))==3 and changed==sorted(changed) and not added,'wrong exactly three-source scope')
 must({p for p in paths if p.startswith('handoff_payload_26913/')}=={'handoff_payload_26913/'+p for p in changed},'extra/missing overlay')
 want=set(paths)-{'26913_HANDOFF_HASHES.sha256'}|{wf,'TRIGGER_26913.txt'}
 entries={}
 for line in (R/'26913_HANDOFF_HASHES.sha256').read_text().splitlines():
  h,p=line.split('  ',1)
  must(p not in entries and bool(re.fullmatch('[0-9a-f]{64}',h)),'duplicate seal')
  entries[p]=h
 must(set(entries)==want,'seal incomplete/extra')
 for p,h in entries.items():must((R/p).is_file() and sha(R/p)==h,'tamper '+p)
 must((R/'TRIGGER_26913.txt').read_bytes()==TRIGGER,'trigger bytes')
 before=manifest('26913_BASE_26912_FULL_APP.sha256');after=manifest('26913_PRECOMPILE_EXPECTED_FULL_APP.sha256')
 must(len(before)==len(after)==2036 and set(before)==set(after),'not exact 26912 source universe')
 must({p for p in before if before[p]!=after[p]}==set(changed),'unexpected runtime change')
 must(sum(1 for p in before if p not in changed)==2033,'protected count')
 for p in changed:must(sha(R/'handoff_payload_26913'/p)==after[p],'payload wrong '+p)
 for p in before:
  if p.startswith(('app/src/main/cpp/','app/src/main/jniLibs/','app/src/main/assets/')):
   must(before[p]==after[p],'native/vendor drift')
 must(after['app/src/main/assets/iris26856/rawr/amaze/spv/amaze_export.spv']=='5853f1a0da12bab4b8c9489b6b298f3710f90fb6e51660204ed43f49963809f1','AMaZE SPV drift')
 w=(R/wf).read_text();runner=(R/'build_26913_incremental.py').read_text()
 must('experimental-clean-photon-rebuild' in w and w.count('TRIGGER_26913.txt')==1,'wrong branch/trigger')
 must(bool(re.search(r'paths:\s*\n\s*- TRIGGER_26913.txt\s*\n\s*workflow_dispatch:',w)),'new unauthorized workflow trigger')
 must('dev' not in w.split('branches:')[1].split('paths:')[0],'dev forbidden')
 must(w.count('./gradlew --no-daemon --build-cache :app:assembleDebug')==1,'Gradle compile disabled')
 for p in ['verify_26912_handoff.py','verify_26913_handoff.py','test_26912_sealed_negatives.py',
           'test_26913_sealed_negatives.py','test_26913_brightness.py --payload','test_26913_brightness.py --live',
           'test_26906_native_cache.py','verify_26904_v3_safety.py','verify_26904_v2_safety.py',
           'build_26904_incremental.py seal','verify_26906_native_cache.py preflight',
           'compile_26904_shaders_v2.sh','verify_26904_v3_cmake_handoff.py --handoff',
           'compile_26906_tone_glsl.sh','compile_26907_hue_glsl.sh','compile_26908_render_glsl.sh',
           'verify_26906_native_cache.py postflight','actions/upload-artifact@v4']:
  must(p in w,'historical real gate removed '+p)
 for p in ['test_26907_hue_source.py','test_26908_exposure_render.py','test_26909_exposure.py',
           'test_26910_capture_focus.py','test_26911_continuity.py','test_26912_source.py --payload']:
  must(w.count(p)>=2,'historical regressions dropped '+p)
 must(w.count('python3 -S build_26913_incremental.py')==5,'runner original five phases changed')
 for s in ['RUN=42534139279',"COMMIT='cf2421d624f70cae72ed20d5750c37577d6c1352'",'ART_ID=13639020850',
           ART_SHA,BASE_TAR,ACTUAL_BUILDER,PRIOR,"prefix='photon_26912_outputs/'",
           "get('26912_PREBUILD_SEALED_APP.sha256')","get('ACTUAL_EXECUTED_build_26912_incremental.py')",
           "get('ACTUAL_EXECUTED_build-26912-change-aware.yml')",
           'source=2036 runtime_changed=3 protected=2033 added=0','26908_RENDER_SHADER_REAL_COMPILER.txt',
           '26907_HUE_SHADER_REAL_COMPILER.txt','26906_TONE_SHADER_REAL_COMPILER.txt',
           "'REAL PINNED GLSL COMPILE: PASS'","'REAL SPIR-V VALIDATION: PASS'",
           "'REAL KOTLIN COMPILE: PASS'","'REAL JAVA COMPILE: PASS'",
           "'NATIVE/NDK COMPILE: PASS'","'REAL ANDROID Gradle :app:assembleDebug: PASS'",
           'if len(apks)!=1','26913_PREBUILD_SEALED_APP.sha256']:
  must(s in runner,'unverifiable authority/compilation gate '+s)
 order=['verify_26912_handoff.py','verify_26913_handoff.py','build_26913_incremental.py seal',
        'test_26906_native_cache.py','verify_26904_v3_safety.py','verify_26904_v2_safety.py',
        'build_26904_incremental.py seal','build_26913_incremental.py fetch','build_26913_incremental.py prepare',
        'verify_26906_native_cache.py preflight','compile_26904_shaders_v2.sh',
        'verify_26904_v3_cmake_handoff.py --handoff','compile_26906_tone_glsl.sh',
        'compile_26907_hue_glsl.sh','compile_26908_render_glsl.sh',
        'build_26913_incremental.py verify-compiled',':app:assembleDebug',
        'verify_26906_native_cache.py postflight','build_26913_incremental.py finalize','actions/upload-artifact@v4']
 must([w.index(p) for p in order]==sorted(w.index(p) for p in order),'inherited seventeen-stage order changed')
 must(w.index('id: native-cache')<w.index('verify_26906_native_cache.py preflight')<w.index('compile_26904_shaders_v2.sh'),'native order')
 must(w.index(':app:assembleDebug')<w.index('verify_26906_native_cache.py postflight')<w.index('build_26913_incremental.py finalize'),'postbuild order')
 print('PASS 26913 SHA-sealed original mechanics, successful 26912 authority, 2036 source, three changed, 2033 protected, historic 26886/26887/26903/26904-26912 retained')
if __name__=='__main__':
 try:verify()
 except Exception as e:print('26913 HANDOFF FAILED',e,file=sys.stderr);sys.exit(1)
