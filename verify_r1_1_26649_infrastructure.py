#!/usr/bin/env python3
from pathlib import Path
import re,subprocess,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_r1_1_26649_infrastructure.py BUILD_SCRIPT WORKFLOW')
bs=Path(sys.argv[1]); wf=Path(sys.argv[2]); b=bs.read_text(); w=wf.read_text()
# Exact authorities.
SUCCESS='3b46a176d4d018613b17912bce30ebdb6e2fd7e7'
FAILED='fd0e9f9de32f976c6dcf7f3449f02d3c457354d2'
PINS={
 (SUCCESS,'build_r1_2_26648_universal_fusion_heic_ui.sh'):'940320d3b7b6d60cdb9bb8f0f2e9dc61b7d932f7',
 (SUCCESS,'.github/workflows/build-r1-2-26648-apk-artifact-repair.yml'):'ef04fa514a63464d71cc4db630dcf72c8f040283',
 (FAILED,'build_26649_r1_photon_highlight_compression.sh'):'a0a6e7e4b90c7ca21542a67ca30e197654f29b4b',
 (FAILED,'verify_26649_shaders.py'):'5fc7d6b71c90dd71d7e03214916736117bd8431c',
 (FAILED,'.github/workflows/build-26649-r1-photon-highlight-compression.yml'):'f336c2f41ad1666fcae4ffbf7a042c7da03a910e'}
if Path('.git').exists():
 for (commit,path),want in PINS.items():
  got=subprocess.check_output(['git','rev-parse',f'{commit}:{path}'],text=True).strip()
  if got!=want: raise SystemExit(f'FAIL authority blob {commit}:{path} {got} != {want}')
# The successful ordering must stay unchanged.
order=['verify_package','verify_scope','obtain_authority','make_candidate','verify_shaders','verify_successful_26648_mechanics','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]'",'verify_candidate_patches','PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug','postbuild_proof']
pos=-1
for tok in order:
 p=b.find(tok,pos+1)
 if p<0: raise SystemExit(f'FAIL missing/order token {tok}')
 pos=p
# Permanent regression for the exact Actions failure.
if 'verify_r1_1_26649_shaders.py' not in b: raise SystemExit('FAIL corrected shader verifier not wired')
if 'R1_1_26649_RUNTIME_EXPANDED_SHADERS.sha256' not in b: raise SystemExit('FAIL corrected expanded pin not wired')
sv=Path('verify_r1_1_26649_shaders.py').read_text()
for tok in ['runtime_expand(raw,assetroot)','#version 310 es','GLInterface.readProgram','p.write_text(expanded)']:
 if tok not in sv: raise SystemExit(f'FAIL corrected runtime expansion token {tok}')
if 'p.write_text(src)' in sv or "out.write_text(src)" in sv: raise SystemExit('FAIL raw asset compiler shortcut survived')
# Workflow must be disjoint from failed R1 trigger and package exact repaired APK.
expected='IrisCamera-0.9726649-26649-r1-1-photon-highlight-compression-debug.apk'
if w.count(expected)!=3: raise SystemExit('FAIL exact repaired APK basename contract')
if 'if-no-files-found: error' not in w or 'test -f '+expected not in w: raise SystemExit('FAIL pre-upload APK existence gate')
for forbidden in ["'R1_26649_*'","'verify_26649_*.py'","'handoff_payload_26649/**'","'build_26649_r1_photon_highlight_compression.sh'"]:
 if forbidden in w: raise SystemExit(f'FAIL overlapping failed-R1 trigger {forbidden}')
print('PASS 26649 R1.1 infrastructure: successful-26648 order exact; failed-R1 raw GLSL compile defect permanently removed; workflow trigger disjoint')
