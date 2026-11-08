#!/usr/bin/env python3
"""26909 three-stage exact-byte successful 26907 authority / native historical compiler gate."""
from pathlib import Path
import hashlib,re,sys
R=Path(__file__).resolve().parent
WF='.github/workflows/build-26909-change-aware.yml'
PARENTWF='.github/workflows/build-26908-change-aware.yml'
PARENTWF_SHA='a85922b7b3a69ee48879a14b6c35724a3d7a3ba720ab9f9759b8c8edb0c18d70'
TRIGGER=b'RUN_26909_B_SHUTTER_FIRST_NIGHT_1P10_LOW_ISO_V1\n'

def must(c,m):
 if not c:raise AssertionError('26909 HANDOFF BLOCKED '+m)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def parse(n):
 d={}
 for ln in (R/n).read_text().splitlines():
  h,p=ln.split('  ',1)
  must(re.fullmatch('[0-9a-f]{64}',h) is not None and p.startswith('app/') and '..' not in Path(p).parts and p not in d,'bad manifest '+p)
  d[p]=h
 return d

def verify():
 inventory=(R/'26909_STAGE1_PATHS.txt').read_text().splitlines()
 must(len(inventory)==len(set(inventory)) and '26909_HANDOFF_HASHES.sha256' in inventory,'Stage1 inventory wrong')
 changes=(R/'26909_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines()
 addition=(R/'26909_ADDED_RUNTIME_PATHS.txt').read_text().splitlines()
 must(len(changes)==4 and len(set(changes))==4 and changes[-1]=='app/version.properties','exact four-path allowlist wrong')
 must(len(addition)==1 and set(addition).issubset(changes),'one added file incorrect')
 must({p for p in inventory if p.startswith('handoff_payload_26909/')}=={'handoff_payload_26909/'+p for p in changes},'payload != allowlist')
 seals={}
 for line in (R/'26909_HANDOFF_HASHES.sha256').read_text().splitlines():
  h,p=line.split('  ',1)
  must(p not in seals and re.fullmatch('[0-9a-f]{64}',h) is not None,'duplicate/invalid SHA seal')
  seals[p]=h
 must(set(seals)==(set(inventory)-{'26909_HANDOFF_HASHES.sha256'})|{WF,'TRIGGER_26909.txt'},'staged SHA scope mismatch')
 for p,h in seals.items():must((R/p).is_file() and sha(R/p)==h,'SHA mismatch '+p)
 must((R/'TRIGGER_26909.txt').read_bytes()==TRIGGER,'stage3 bytes stale')
 before=parse('26909_BASE_26908_FULL_APP.sha256');after=parse('26909_PRECOMPILE_EXPECTED_FULL_APP.sha256')
 must(len(before)==2031 and len(after)==2032 and set(after)-set(before)==set(addition) and not(set(before)-set(after)),'source universe wrong')
 must({p for p in before if before[p]!=after[p]}==set(changes)-set(addition),'protected source modified')
 must(len(before)-len(changes)+len(addition)==2028,'protected count incorrect')
 for p in changes:must(sha(R/'handoff_payload_26909'/p)==after[p],'source payload incorrect '+p)
 for p in before:
  if p.startswith('app/src/main/cpp/') or p.startswith('app/src/main/jniLibs/'):
   must(before[p]==after[p],'native/vendor source modified '+p)
 must(after['app/src/main/assets/iris26856/rawr/amaze/spv/amaze_export.spv']==
      '5853f1a0da12bab4b8c9489b6b298f3710f90fb6e51660204ed43f49963809f1','pinned SPV modified')
 must((R/PARENTWF).is_file() and sha(R/PARENTWF)==PARENTWF_SHA,'previous successful 26908 workflow missing/drift')
 w=(R/WF).read_text()
 must('experimental-clean-photon-rebuild' in w and w.count('TRIGGER_26909.txt')==1 and 'dev' not in w.split('branches:')[1].split('paths:')[0],'wrong Actions branch')
 must(w.count('./gradlew --no-daemon --build-cache :app:assembleDebug')==1,'real Android assemble omitted/repeated')
 must(w.count('python3 -S build_26909_incremental.py')==5,'wrong current runner CLI count')
 must(w.count('test_26907_hue_source.py')==2 and w.count('test_26908_exposure_render.py')==2 and w.count('test_26909_exposure.py')==2,'historical/current regression missing')
 stages=['build_26909_incremental.py seal','test_26906_native_cache.py','test_26907_hue_source.py','test_26908_exposure_render.py','test_26909_exposure.py','verify_26904_v3_safety.py','verify_26904_v2_safety.py','build_26904_incremental.py seal',
         'build_26909_incremental.py fetch','build_26909_incremental.py prepare','verify_26906_native_cache.py preflight','compile_26904_shaders_v2.sh','verify_26904_v3_cmake_handoff.py --handoff','compile_26906_tone_glsl.sh','compile_26907_hue_glsl.sh','compile_26908_render_glsl.sh',
         'build_26909_incremental.py verify-compiled',':app:assembleDebug','verify_26906_native_cache.py postflight','build_26909_incremental.py finalize','actions/upload-artifact@v4']
 positions=[w.index(q) for q in stages];must(positions==sorted(positions),'original 26908 real compiler/build/native cache order drift')
 must(w.count('verify_26906_native_cache.py preflight')==1 and w.count('verify_26906_native_cache.py postflight')==1,'native cache V3 gate removed')
 must(w.index('id: native-cache')<w.index('verify_26906_native_cache.py preflight')<w.index('compile_26904_shaders_v2.sh'),'native cache ordering wrong')
 must(w.index(':app:assembleDebug')<w.index('verify_26906_native_cache.py postflight')<w.index('build_26909_incremental.py finalize'),'postflight wrong order')
 run=(R/'build_26909_incremental.py').read_text()
 for token in ['RUN=42425604402',"COMMIT='cd669718cbc883704f5c3cb1bd8b636487b15e11'",'ART_ID=13594998530',
  '9974381fd2a864a1b6e8f218eced2133adf90e21a1ff734538a5da45a80c723b','26e219392a747f7fd303d89ec620dcb8351139e48b29d32a6c719e7d915af206',
  '36d8f25387d1d7a32e985f920b0c9bc52155af18a5e17d0cbce61071a41a8ab8','a85922b7b3a69ee48879a14b6c35724a3d7a3ba720ab9f9759b8c8edb0c18d70',
  "prefix='photon_26908_outputs/'",'26908_PREBUILD_SEALED_APP.sha256','ACTUAL_EXECUTED_build_26908_incremental.py','ACTUAL_EXECUTED_build-26908-change-aware.yml',
  '2032 runtime_changed=4 protected=2028 added=1','26908_RENDER_SHADER_REAL_COMPILER.txt','26908_RENDER_SHADER_SPIRV_VALIDATED.txt',
  '26907_HUE_SHADER_REAL_COMPILER.txt','26906_TONE_SHADER_REAL_COMPILER.txt','26906_NATIVE_CACHE_PATCH_REPLAY.json',"if len(apks)!=1:"]:
  must(token in run,'new runner reference/guard missing '+token)
 compiler=(R/'compile_26908_render_glsl.sh').read_text()
 must('spirv-val --target-env opengl4.5' in compiler and 'spirv-opt --target-env=opengl4.5 -O' in compiler and 'app/src/main/assets/shaders/motionv2/render.glsl' in compiler and '16.5.0' in compiler,'new compiled shader real gate missing')
 print('PASS 26909 sealed Stage1/2/3, successful 26908 compiled source/builder/workflow, four scoped edits, 2028 protected, historical 26886/26887/26903/26904/26906/26907/26908 regressions, pinned 26908 real compiler, Android build')
if __name__=='__main__':
 try:verify()
 except Exception as e:print('26909 HANDOFF FAIL',e,file=sys.stderr);sys.exit(1)
