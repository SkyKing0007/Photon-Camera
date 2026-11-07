#!/usr/bin/env python3
"""26908 three-stage exact-byte successful 26907 authority / native historical compiler gate."""
from pathlib import Path
import hashlib,re,sys
R=Path(__file__).resolve().parent
WF='.github/workflows/build-26908-change-aware.yml'
PARENTWF='.github/workflows/build-26907-change-aware.yml'
PARENTWF_SHA='2621fca6d0a6d48a0384fa16469132dca00d8131b924b7f5ed37a7ad5c141fb5'
TRIGGER=b'RUN_26908_CAPTURE_SHUTTER_FIRST_NIGHT_LIFT_SATURATION_V1\n'

def must(c,m):
 if not c:raise AssertionError('26908 HANDOFF BLOCKED '+m)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def parse(n):
 d={}
 for ln in (R/n).read_text().splitlines():
  h,p=ln.split('  ',1)
  must(re.fullmatch('[0-9a-f]{64}',h) is not None and p.startswith('app/') and '..' not in Path(p).parts and p not in d,'bad manifest '+p)
  d[p]=h
 return d

def verify():
 inventory=(R/'26908_STAGE1_PATHS.txt').read_text().splitlines()
 must(len(inventory)==len(set(inventory)) and '26908_HANDOFF_HASHES.sha256' in inventory,'Stage1 inventory wrong')
 changes=(R/'26908_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines()
 addition=(R/'26908_ADDED_RUNTIME_PATHS.txt').read_text().splitlines()
 must(len(changes)==6 and len(set(changes))==6 and changes[-1]=='app/version.properties','exact six-path allowlist wrong')
 must(len(addition)==1 and set(addition).issubset(changes),'one added file incorrect')
 must({p for p in inventory if p.startswith('handoff_payload_26908/')}=={'handoff_payload_26908/'+p for p in changes},'payload != allowlist')
 seals={}
 for line in (R/'26908_HANDOFF_HASHES.sha256').read_text().splitlines():
  h,p=line.split('  ',1)
  must(p not in seals and re.fullmatch('[0-9a-f]{64}',h) is not None,'duplicate/invalid SHA seal')
  seals[p]=h
 must(set(seals)==(set(inventory)-{'26908_HANDOFF_HASHES.sha256'})|{WF,'TRIGGER_26908.txt'},'staged SHA scope mismatch')
 for p,h in seals.items():must((R/p).is_file() and sha(R/p)==h,'SHA mismatch '+p)
 must((R/'TRIGGER_26908.txt').read_bytes()==TRIGGER,'stage3 bytes stale')
 before=parse('26908_BASE_26907_FULL_APP.sha256');after=parse('26908_PRECOMPILE_EXPECTED_FULL_APP.sha256')
 must(len(before)==2030 and len(after)==2031 and set(after)-set(before)==set(addition) and not(set(before)-set(after)),'source universe wrong')
 must({p for p in before if before[p]!=after[p]}==set(changes)-set(addition),'protected source modified')
 must(len(before)-len(changes)+len(addition)==2025,'protected count incorrect')
 for p in changes:must(sha(R/'handoff_payload_26908'/p)==after[p],'source payload incorrect '+p)
 for p in before:
  if p.startswith('app/src/main/cpp/') or p.startswith('app/src/main/jniLibs/'):
   must(before[p]==after[p],'native/vendor source modified '+p)
 must(after['app/src/main/assets/iris26856/rawr/amaze/spv/amaze_export.spv']==
      '5853f1a0da12bab4b8c9489b6b298f3710f90fb6e51660204ed43f49963809f1','pinned SPV modified')
 must((R/PARENTWF).is_file() and sha(R/PARENTWF)==PARENTWF_SHA,'previous successful 26907 workflow missing/drift')
 w=(R/WF).read_text()
 must('experimental-clean-photon-rebuild' in w and w.count('TRIGGER_26908.txt')==1 and 'dev' not in w.split('branches:')[1].split('paths:')[0],'wrong Actions branch')
 must(w.count('./gradlew --no-daemon --build-cache :app:assembleDebug')==1,'real Android assemble omitted/repeated')
 must(w.count('python3 -S build_26908_incremental.py')==5,'wrong current runner CLI count')
 must(w.count('test_26907_hue_source.py')==2 and w.count('test_26908_exposure_render.py')==2,'historical/current regression missing')
 stages=['build_26908_incremental.py seal','test_26906_native_cache.py','test_26907_hue_source.py','test_26908_exposure_render.py','verify_26904_v3_safety.py','verify_26904_v2_safety.py','build_26904_incremental.py seal',
         'build_26908_incremental.py fetch','build_26908_incremental.py prepare','verify_26906_native_cache.py preflight','compile_26904_shaders_v2.sh','verify_26904_v3_cmake_handoff.py --handoff','compile_26906_tone_glsl.sh','compile_26907_hue_glsl.sh','compile_26908_render_glsl.sh',
         'build_26908_incremental.py verify-compiled',':app:assembleDebug','verify_26906_native_cache.py postflight','build_26908_incremental.py finalize','actions/upload-artifact@v4']
 positions=[w.index(q) for q in stages];must(positions==sorted(positions),'original 26907 real compiler/build/native cache order drift')
 must(w.count('verify_26906_native_cache.py preflight')==1 and w.count('verify_26906_native_cache.py postflight')==1,'native cache V3 gate removed')
 must(w.index('id: native-cache')<w.index('verify_26906_native_cache.py preflight')<w.index('compile_26904_shaders_v2.sh'),'native cache ordering wrong')
 must(w.index(':app:assembleDebug')<w.index('verify_26906_native_cache.py postflight')<w.index('build_26908_incremental.py finalize'),'postflight wrong order')
 run=(R/'build_26908_incremental.py').read_text()
 for token in ['RUN=42391430919',"COMMIT='bdb362b77afb72d6dd3c972cf79fc9276354cdc3'",'ART_ID=13581474367',
  'd007eddb15c3056c432b661a66ce9488b45bf2855d425d740160981f659fa016','f9c0ab12efc3ffe6d8609cee887891fef04a27ccfcd2a39bb9465f549b024dd6',
  '08a447466919e684791cf8a71d37c3e3b39784aba17ceeb1cc65ff17028a37cf','2621fca6d0a6d48a0384fa16469132dca00d8131b924b7f5ed37a7ad5c141fb5',
  "prefix='photon_26907_outputs/'",'26907_PREBUILD_SEALED_APP.sha256','ACTUAL_EXECUTED_build_26907_incremental.py','ACTUAL_EXECUTED_build-26907-change-aware.yml',
  '2031 runtime_changed=6 protected=2025 added=1','26908_RENDER_SHADER_REAL_COMPILER.txt','26908_RENDER_SHADER_SPIRV_VALIDATED.txt',
  '26907_HUE_SHADER_REAL_COMPILER.txt','26906_TONE_SHADER_REAL_COMPILER.txt','26906_NATIVE_CACHE_PATCH_REPLAY.json',"if len(apks)!=1:"]:
  must(token in run,'new runner reference/guard missing '+token)
 compiler=(R/'compile_26908_render_glsl.sh').read_text()
 must('spirv-val --target-env opengl4.5' in compiler and 'spirv-opt --target-env=opengl4.5 -O' in compiler and 'app/src/main/assets/shaders/motionv2/render.glsl' in compiler and '16.5.0' in compiler,'new compiled shader real gate missing')
 print('PASS 26908 sealed Stage1/2/3, successful 26907 compiled source/builder/workflow, six scoped edits, 2025 protected, historical 26903/26904/26906/26907 regressions, pinned 26908 real compiler, Android build')
if __name__=='__main__':
 try:verify()
 except Exception as e:print('26908 HANDOFF FAIL',e,file=sys.stderr);sys.exit(1)
