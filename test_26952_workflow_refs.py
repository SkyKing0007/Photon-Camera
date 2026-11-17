#!/usr/bin/env python3
"""Exact 26951 successful historical workflow prefix, correct new Actions refs,
real shader/NDK/compiler and release gates, no unused/obsolete executable refs.
"""
import hashlib,re,subprocess,sys
from pathlib import Path
from build_26952_incremental import R,fail,STAGE1_FILES,sha
PREV_SHA='40980c9badbe157fab569971f063966360ca9f0b6020792df1f1dd2be069966b'
OLD=R/'26951_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml'
NEW=R/'.github/workflows/build-26952-change-aware.yml'
if sha(OLD)!=PREV_SHA:fail('original successful 26951 executed workflow reference modified')
old=OLD.read_text();new=NEW.read_text();cut='      - name: Fetch SUCCESSFUL 26949 Actions run'
if old.count(cut)!=1:fail('old workflow anchor missing')
prefix=old[:old.index(cut)].replace('name: Photon 26951 - successful 26949 RAWR HDRQ compatibility and matched SDR','name: Photon 26952 - successful 26951 LKR color parity, 3x2 preserved and SDR halo guard',1).replace('      - TRIGGER_26951.txt','      - TRIGGER_26952.txt',1)
if not new.startswith(prefix):fail('actual successful 26951 historical verification steps/command graph weakened')
if new.count('      - name: Fetch exact successful 26951 run')!=1 or new.count('actions/upload-artifact@v4')!=1:fail('wrong actual historical provenance/artifact output')
if new.count('./gradlew --no-daemon --build-cache :app:assembleDebug --stacktrace')!=1:fail('actual real full Android compile omitted/duplicated')
for p in ('test_26903_v3_archive_receipt.py','test_26925_sealed_negatives.py','compile_26904_shaders_v2.sh','verify_26904_v3_cmake_handoff.py','verify_26906_native_cache.py','test_26931_native_integrity.py','replay_26952_inherited_glsl.py','replay_26952_26943_contract.py','compile_26952_shaders.sh','build_26952_incremental.py','prepare_26952_native.py','test_26952_native.py','test_26952_source.py','test_26952_chroma.py','test_26952_halo.py','test_26952_patches.py','test_26952_sealed_negatives.py'):
 if p not in new and p!='replay_26952_26943_contract.py':fail('mandatory historical/current executable missing '+p)
for p in ('python3 -S prepare_26952_native.py original','python3 -S test_26931_native_integrity.py --native','python3 -S prepare_26952_native.py official','python3 -S test_26952_native.py --native','python3 -S test_26952_native.py --cmake','python3 -S test_26952_native.py --apk','python3 -S build_26952_incremental.py verify-compiled','python3 -S build_26952_incremental.py finalize','python3 -S build_26952_incremental.py fetch','python3 -S build_26952_incremental.py prepare','bash compile_26952_shaders.sh'):
 if new.count(p)!=1:fail('missing or duplicated required action '+p)
if new.find('prepare_26952_native.py original')>new.find('prepare_26952_native.py official') or new.find('prepare_26952_native.py official')>new.find('compile_26952_shaders.sh'):fail('historical/new native verification order broken')
if new.find('verify-compiled')>new.find(':app:assembleDebug --stacktrace'):fail('compiler proofs run after assemble')
if 'photon_26951_outputs/26951_gradle_assemble.log' in new or 'TRIGGER_26951.txt' in new.split('jobs:',1)[0] or new.find('26952-SUCCESSFUL')>=0:fail('stale root workflow or invented success')
if new.count('photon-26952-rawlens-2394-two-radius-3x2-sdr-rim')!=1:fail('wrong publication name')
# Actual GitHub checkout already contains old 26951 files and all historical scripts.
# Only newly introduced scripts/stage files need be in the handoff.
oldinv=set(re.findall(r'\b(?:python3\s+-S\s+|bash\s+|\./)([\w.-]+\.(?:py|sh))\b',old))
newinv=set(re.findall(r'\b(?:python3\s+-S\s+|bash\s+|\./)([\w.-]+\.(?:py|sh))\b',new))
if not oldinv<=newinv|{'build_26951_incremental.py','test_26951_source.py','test_26951_highlight.py','test_26951_descriptor_abi.py','test_26951_patch_proof.py','test_26951_math.py','replay_26951_inherited_26949_glsl.py','replay_26951_inherited_26948_glsl.py','replay_26951_inherited_26943_glsl.py','replay_26951_inherited_26944_glsl.py','compile_26951_shaders.sh','compile_26951_sdr_shaders.sh','prepare_26951_lkr_from_successful_26949.py'}:fail('historical execution unexpectedly removed')
listed=(R/'26952_EXPECTED_ACTION_EXECUTABLES.txt').read_text().splitlines()
if listed!=sorted(newinv) or len(listed)!=len(set(listed)):fail('missing/unused executable list '+repr(sorted(newinv^set(listed))[:20]))
if '--on-actions' in sys.argv:
 for script in listed:
  if not (R/script).is_file():fail('missing actual GitHub Actions executable '+script)
# The known 26950 V3 SPIR-V optimizer CLI regression must FAIL, including if
# source text is resealed, and both current and inherited real compiler gates exist.
shell=(R/'compile_26952_shaders.sh').read_text()
if shell.count('spirv-opt --target-env=opengl4.5 -O')!=1 or 'spirv-opt --target-env opengl4.5' in shell:fail('26904 V2/26950 V3 malformed optimizer CLI')
if not re.search(r'^\s*spirv-val --target-env opengl4.5',shell,re.M):fail('real validator absent')
for name in ('compile_26952_shaders.sh',):
 ret=subprocess.run(['bash','-n',str(R/name)],capture_output=True,text=True)
 if ret.returncode:fail('real shader bash syntax invalid '+ret.stderr)
negative=shell.replace('--target-env=opengl4.5','--target-env opengl4.5',1)
if negative==shell or 'spirv-opt --target-env opengl4.5' not in negative:fail('historical SPIR-V negative malformed')
print('PASS 26952 successful 26951 historical graph unchanged, exact live executable manifest, original 26904 V2/V3 regressions and full real compile + two ABI native gates')
