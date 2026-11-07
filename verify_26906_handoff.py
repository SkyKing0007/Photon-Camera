#!/usr/bin/env python3
"""Exact-byte 26906 clean-extracted staged source, verification, and workflow safety proof."""
from pathlib import Path
import hashlib,re,sys
R=Path(__file__).resolve().parent
OLDWF='.github/workflows/build-26905-change-aware.yml'
WF='.github/workflows/build-26906-change-aware.yml'
TRIGGER=b'RUN_26906_B_VISUAL_MIDTONE_TOE_NIGHT_EXPOSURE_V1\n'
CHANGED=['app/version.properties','app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java','app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java','app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/IrisNightExposureSelector.java','app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java','app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/assets/shaders/motionv2/gainmap.glsl','app/src/main/assets/shaders/iris26876/b_fused_final_p3_gain.frag']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def must(condition,why):
 if not condition:raise AssertionError('26906 HANDOFF BLOCKED: '+why)
def manifest(name):
 entries={}
 for line in (R/name).read_text().splitlines():
  h,path=line.split('  ',1)
  must(re.fullmatch('[0-9a-f]{64}',h) and path.startswith('app/') and '..' not in Path(path).parts and path not in entries,'invalid source SHA manifest row')
  entries[path]=h
 return entries
def check():
 paths=(R/'26906_STAGE1_PATHS.txt').read_text().splitlines()
 must(len(paths)==len(set(paths)) and '26906_HANDOFF_HASHES.sha256' in paths,'bad Stage1 inventory')
 must((R/'26906_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines()==CHANGED,'changed runtime allowlist mismatch')
 must({p for p in paths if p.startswith('handoff_payload_26906/')}=={'handoff_payload_26906/'+p for p in CHANGED},'missing/extra runtime payload')
 must((R/'TRIGGER_26906.txt').read_bytes()==TRIGGER,'trigger byte mismatch')
 seals={}
 for line in (R/'26906_HANDOFF_HASHES.sha256').read_text().splitlines():
  h,p=line.split('  ',1)
  must(p not in seals and re.fullmatch('[0-9a-f]{64}',h),'invalid seal entry')
  seals[p]=h
 must(set(seals)==set(paths)-{'26906_HANDOFF_HASHES.sha256'}|{WF,'TRIGGER_26906.txt'},'seal paths wrong')
 for p,h in seals.items():must((R/p).is_file() and sha(R/p)==h,'sealed bytes mismatch '+p)
 before=manifest('26906_BASE_26905_FULL_APP.sha256');after=manifest('26906_PRECOMPILE_EXPECTED_FULL_APP.sha256')
 must(before.keys()==after.keys() and len(before)==2027,'successful source universe changed')
 must({p for p in before if before[p]!=after[p]}==set(CHANGED),'unlisted source change')
 for p in CHANGED:must(sha(R/'handoff_payload_26906'/p)==after[p],'changed runtime bytes differ '+p)
 must(before['app/src/main/assets/iris26856/rawr/amaze/spv/amaze_export.spv']==after['app/src/main/assets/iris26856/rawr/amaze/spv/amaze_export.spv'],'original compiled AMaZE SPV changed')
 must((R/OLDWF).is_file() and sha(R/OLDWF)=='fc57c6abf04dfb62b0cba69061009101175f97237aafdcb5e8c69a71e6e0c2da','exact successfully executed 26905 parent workflow changed')
 w=(R/WF).read_text()
 must(w.count('TRIGGER_26906.txt')==1 and 'experimental-clean-photon-rebuild' in w,'trigger/branch mismatch')
 must(w.count('./gradlew --no-daemon --build-cache :app:assembleDebug')==1,'full Android assemble not once')
 must(w.count('python3 -S build_26906_incremental.py')==5,'builder CLI count wrong')
 cmds=['build_26906_incremental.py fetch','build_26906_incremental.py prepare','compile_26904_shaders_v2.sh','verify_26904_v3_cmake_handoff.py --handoff','compile_26906_tone_glsl.sh','build_26906_incremental.py verify-compiled',':app:assembleDebug','build_26906_incremental.py finalize','actions/upload-artifact@v4']
 positions=[w.index(x) for x in cmds]
 must(positions==sorted(positions),'toolchain build stage command order changed')
 must('26906_TONE_SHADER_REAL_COMPILER.txt' in (R/'build_26906_incremental.py').read_text(),'missing real modified shader compiler gate')
 must('ACTUAL_EXECUTED_build_26906_incremental.py' in (R/'build_26906_incremental.py').read_text(),'missing actual executed script archival')
 must('26905_success.zip' in (R/'build_26906_incremental.py').read_text(),'missing exact prior published archive fetch')
 print('PASS exact 26906 3-stage seal, 2027 source and 2018 protected files, pinned 26905 workflow, real shader/native/Java/Kotlin and one Android assemble sequence')
if __name__=='__main__':
 try:check()
 except Exception as e: print('26906 HANDOFF FAIL',e,file=sys.stderr);sys.exit(1)
