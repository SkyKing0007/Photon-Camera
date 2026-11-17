#!/usr/bin/env python3
"""Full 26953 Actions executable, actual successful 26952 prefix, missing/stale/duplicate references and historical failures audit."""
import hashlib,re,subprocess,sys
from pathlib import Path
from build_26953_incremental import R,fail,scope,WORKFLOW_SHA,BUILDER_SHA,TAR_SHA,RUN,ART_ID,COMMIT,ART_SHA

old=(R/'26952_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml').read_text()
new=(R/'.github/workflows/build-26953-change-aware.yml').read_text()
if hashlib.sha256(old.encode()).hexdigest()!=WORKFLOW_SHA:fail('not exact actually executed successful 26952 V4 workflow')
oldmark='      - name: Verify sealed 26952 payload and byte-exact successful 26951 source authority'
newmark='      # The 26952 V4 historical handoff is checked against its OWN frozen'
if old.count(oldmark)!=1 or new.count(newmark)!=1:fail('successful workflow and current inserted stage anchors missing')
oldprefix=old.split(oldmark,1)[0]
newprefix=new.split(newmark,1)[0]
oldprefix=oldprefix.replace('name: Photon 26952 - successful 26951 LKR color parity, 3x2 preserved and SDR halo guard','name: Photon 26953 - 26940 no-halo B SDR with global UHDR-body brightness and Night/high zoom')
oldprefix=oldprefix.replace('      - TRIGGER_26952.txt\n','      - TRIGGER_26953.txt\n')
if oldprefix!=newprefix:fail('old successful V4 31-step build/historical preflight graph changed or omitted')
if new.count('TRIGGER_26953.txt')!=1 or 'TRIGGER_26952.txt' in new.split('jobs:',1)[0]:fail('stale/double staged trigger')
if new.count('runs-on: ubuntu-24.04')!=1 or new.count('timeout-minutes: 120')!=1:fail('changed runner environment')
if new.count('    branches:\n      - experimental-clean-photon-rebuild')!=1 or re.search(r'(?m)^\s*[- ]*dev\s*$',new):fail('dev target not allowed')
if new.count('permissions:\n  contents: read\n  actions: read')!=1:fail('actual artifact retrieval permissions changed')
if new.count(':app:assembleDebug --stacktrace')!=1 or new.count('actions/upload-artifact@v4')!=1:fail('full Android assembly/publication weakened')
if 'if-no-files-found: error' not in new or 'retention-days: 30' not in new:fail('publication not fail-closed')
if 'actions/cache/restore@v4' not in new or 'verify_26906_native_cache.py preflight' not in new or 'verify_26906_native_cache.py postflight' not in new:fail('source-addressed native cache protections omitted')
if new.count('compile_26904_shaders_v2.sh')!=1 or new.count('verify_26904_v3_cmake_handoff.py --handoff')!=1:fail('26886/26904 SPIR-V or CMake regression bypassed')
if 'test_26903_v3_archive_receipt.py' not in new or 'test_26925_sealed_negatives.py' not in new:fail('historical 26903, 26886/26887 or 26925 regression removed')
# Required deterministic sequence: previous success restored and ALL old shader compilers
# before 26953 runtime overwrite, then current real compilers and NDK/Javac/Kotlin/assemble.
ordered=(
 'build_26953_incremental.py seal',
 'build_26953_incremental.py fetch',
 'build_26953_incremental.py prepare-base',
 'test_26952_source.py --live',
 'compile_26904_shaders_v2.sh',
 'verify_26904_v3_cmake_handoff.py --handoff',
 'replay_26952_current_legacy_glsl.py 39',
 'replay_26952_current_legacy_glsl.py 41',
 'replay_26952_current_legacy_glsl.py 42',
 'replay_26952_inherited_glsl.py 43',
 'replay_26952_inherited_glsl.py 44',
 'replay_26952_inherited_glsl.py 48',
 'replay_26952_inherited_glsl.py 49',
 'bash compile_26952_shaders.sh',
 'build_26953_incremental.py install',
 'verify_26906_native_cache.py preflight',
 'prepare_26953_native.py from-success',
 'bash compile_26953_shaders.sh',
 'build_26953_incremental.py verify-compiled',
 ':app:assembleDebug --stacktrace',
 'test_26953_native.py --cmake',
 'test_26953_native.py --apk',
 'verify_26906_native_cache.py postflight',
 'build_26953_incremental.py finalize',
 'actions/upload-artifact@v4',
)
pos=-1
for needle in ordered:
 where=new.find(needle,pos+1)
 if where<0:fail('missing/stale/unordered actual future executable '+needle)
 pos=where
for needle in ('python3 -S build_26952_incremental.py seal','python3 -S test_26952_workflow_refs.py --on-actions','python3 -S test_26952_patches.py --payload','python3 -S build_26953_incremental.py regress','python3 -S test_26953_source.py --payload','python3 -S test_26953_patches.py --payload','python3 -S test_26953_tone_math.py --payload','python3 -S test_26953_native.py --native','python3 -S test_26953_native.py --cmake','python3 -S test_26953_native.py --apk'):
 if needle not in new:fail('missing mandatory versioned executable '+needle)
for stale in ('build_26952_incremental.py fetch','build_26952_incremental.py prepare','prepare_26952_native.py original','prepare_26952_native.py official','photon_26952_outputs/26952_gradle_assemble.log','IrisCamera-0.9726952-26952-iris-rawr-debug.apk'):
 if stale in new:fail('older version re-fetched/reconstructed/rebuilt or published '+stale)
if new.count('photon-26953-b-off-night-uhdr-body-global-no-halo')!=1:fail('incorrect new published artifact name')
# Check every direct command. This list is closed and stable against stale missing tools.
pattern=r'\b(?:python3\s+-S\s+|bash\s+|\./)([\w.-]+\.(?:py|sh))\b'
oldinv=set(re.findall(pattern,old));newinv=set(re.findall(pattern,new))
expected=(R/'26953_EXPECTED_ACTION_EXECUTABLES.txt').read_text().splitlines()
if sorted(newinv)!=expected or len(expected)!=len(set(expected)):fail('incomplete/unreferenced current workflow executable inventory '+str(sorted(newinv^set(expected))[:10]))
if '--on-actions' in sys.argv:
 for file in expected:
  if not (R/file).is_file():fail('actual GitHub Actions executable absent '+file)
# Compiler bodies genuinely compile and optimize, fail closed on original 26904 incorrect CLI.
shell=(R/'compile_26953_shaders.sh').read_text()
for anchor in ('"$COMPILER" -S frag', '"$COMPILER" -G --auto-map-locations --auto-map-bindings', '"$COMPILER" -V --target-env vulkan1.1', 'spirv-val --target-env opengl4.5', 'spirv-opt --target-env=opengl4.5 -O','spirv-opt --target-env=vulkan1.1 -O'):
 if anchor not in shell:fail('real current GLES/SPIR-V compilation omitted '+anchor)
if 'spirv-opt --target-env opengl4.5' in shell:fail('26904 V2 improper optimizer CLI regression')
if subprocess.run(['bash','-n',str(R/'compile_26953_shaders.sh')],capture_output=True).returncode:fail('real current compile shell syntax invalid')
if subprocess.run([sys.executable,'-S','-m','py_compile',str(R/'build_26953_incremental.py')],capture_output=True).returncode:fail('current build python syntax invalid')
# Only 26952 *published* ZIP is used for source; earlier source remains in receipt-only tests.
builder=(R/'build_26953_incremental.py').read_text()
fetch=builder.split('def fetch():',1)[1].split('def safe_tar(',1)[0]
if fetch.count("subprocess.run(['curl','--fail','--location','--retry','3','--silent','--show-error',")!=1 or "'-H','Authorization: Bearer '+token" not in fetch:fail('26952 V1 HTTP401 regression: altered proven authenticated redirect downloader')
if 'with urllib.request.urlopen(req,timeout=180)' in fetch:fail('stale unauthorized 401 artifact download returned')
for value in (TAR_SHA,ART_SHA,COMMIT,str(RUN),str(ART_ID)):
 if value not in builder:fail('latest successful 26952 artifact identity missing')
if 'NPROTECTED=2051' not in builder or 'NCHANGE=4' not in builder:fail('source scope incorrectly represented')
if 'REAL GLSL/SPIR-V' in new and 'NOT RUN' in new:fail('workflow claims no real GLSL')
# Current real shader clip is a genuine primary/denominator mirror, not source-based brightness uplift.
render=(R/'handoff_payload_26953/app/src/main/assets/shaders/motionv2/render.glsl').read_text()
gain=(R/'handoff_payload_26953/app/src/main/assets/shaders/motionv2/gainmap.glsl').read_text()
for code in (render,gain):
 if re.search(r'\bfloat\s+(?:flat|coherent|restrict)\b',re.sub(r'/\*.*?\*/|//[^\n]*','',code,flags=re.S)):
  fail('prior actual glslang unexpected FLAT / coherent regression returned')
if 'iris26953BOffNightSafeBody' not in gain or 'iris26953BOffNightSafeBody' not in render:fail('SDR and UHDR physical tone match omitted')
print('PASS complete successful 26952 V4 historic executable prefix, 26953 exact current shader/native/Gradle/zip stages, no missing/stale/unused refs, original 26904 compiler failures checked')
