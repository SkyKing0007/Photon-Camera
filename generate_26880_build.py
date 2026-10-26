#!/usr/bin/env python3
"""Generate 26880 from exact successful 26879 17-stage runner without reordering.
The new scoped proofs are additions inside inherited stages; compiler/assemble
command lines, shader pin, candidate-freeze mechanics remain byte-identical.
"""
from pathlib import Path
import hashlib,re,difflib,sys
P=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path('.').resolve()
prior=(P/'build_26879_iris_rawr.sh').read_text()
PARENT='985e5f03c620deef3a42b0b50424776e6208e85b62ff5d26e16a7579940d0c19'
assert hashlib.sha256(prior.encode()).hexdigest()==PARENT
body=prior.replace('26879','26880').replace('0.9726879','0.9726880')
def one(old,new):
 global body
 assert body.count(old)==1,(old,body.count(old))
 body=body.replace(old,new,1)
def edit(name,fn):
 global body
 a=body.index('\n'+name+'(){')+1;b=body.index('\n}',a)+2
 old=body[a:b];new=fn(old)
 assert old!=new,name
 body=body[:a]+new+body[b:]
# Only authority metadata changes: strictly last successful GitHub Actions compiled candidate.
for old,new in [
 ('REPO_SCAFFOLD_BASE_COMMIT="9318391f2da8a8a2ab92a3e85e3c01cb6533a55f"','REPO_SCAFFOLD_BASE_COMMIT="7b5dcab60f290a61ecc7e0af8a82398ac4c124ab"'),
 ('RUNTIME_AUTHORITY_COMMIT="9318391f2da8a8a2ab92a3e85e3c01cb6533a55f"','RUNTIME_AUTHORITY_COMMIT="7b5dcab60f290a61ecc7e0af8a82398ac4c124ab"'),
 ('RUNTIME_ARTIFACT_ID="12586138690"; RUNTIME_ACTIONS_RUN="40160908258"','RUNTIME_ARTIFACT_ID="12600241817"; RUNTIME_ACTIONS_RUN="40195876708"'),
 ('RUNTIME_ARTIFACT_SHA="254c63008636c721005dae80b4e4b9fffaf6252ac67a32f87f3238a1a0cec29d"','RUNTIME_ARTIFACT_SHA="bf060a690ee8792e0d3ab4fd58d25cabb2c0a2d35d6ffcd8a186508bb7132930"'),
 ('RUNTIME_TAR_SHA="e3337188adc91ef89741dbe96f8384049304144cc9a358e8146631934149e849"','RUNTIME_TAR_SHA="2775f4f35139709d6521a8e6a9d6d91d1fd9a46a5c2a2997d6d24f2e10a2e44b"'),
 ('MECHANICS_GIT_BLOB="567d6e22d2100aac80e7bfd2c992340323958354"','MECHANICS_GIT_BLOB="e354c0c6971de8809c0c0211623164208c1a1dff"'),
 ('ARTZIP="$WORK/26878_artifact.zip"; ARTDIR="$WORK/artifact_26878"','ARTZIP="$WORK/26879_artifact.zip"; ARTDIR="$WORK/artifact_26879"'),
 ('BASE="$WORK/exact_successful_26878_compiled_candidate"','BASE="$WORK/exact_successful_26879_compiled_candidate"'),
 ]:one(old,new)
# Stage 1 explicit source/domain exactness, regressions all original, including new true failure.
def package(s):
 s=s.replace('regressions/26880_runtime_ownership_spektra.py regressions/26878_runtime_ownership_spektra.py regressions/26877_runtime_ownership_spektra.py',
             'regressions/26880_runtime_ownership_spektra.py regressions/26879_runtime_ownership_spektra.py regressions/26878_runtime_ownership_spektra.py regressions/26877_runtime_ownership_spektra.py regressions/26880_wr_no_fit_optional_wavelet.py')
 s=s.replace('[[ $(find handoff_payload_26880 -type f | wc -l) -eq 5 ]]', '[[ $(find handoff_payload_26880 -type f | wc -l) -eq 34 ]]')
 s=s.replace('five-file strict runtime upload scope','34-file exact runtime upload scope')
 s=s.replace('26880 exact sealed candidate-first five-file','26880 exact sealed candidate-first 34-file')
 s=s.replace('RUN_26880_B_50MP_NEON_SPEKTRA_FOV_V1','RUN_26880_ORIGINAL_125_WRONSKI_WAVELET_HIGHLIGHT_V1')
 s=s.replace(" sha256sum -c 26880_PAYLOAD_SHA256.txt >/dev/null || fail 'candidate payload hash drift'", """ sha256sum -c 26880_PAYLOAD_SHA256.txt >/dev/null || fail 'candidate payload hash drift'
 sha256sum -c 26880_ORIGINAL_NATIVE_ZLIB_SHA256.txt >/dev/null || fail 'original native compressed source drift'
 sha256sum -c 26880_FLAT_SOURCE_SHA256.txt >/dev/null || fail 'flat source staging drift'""")
 return s
edit('verify_package',package)
def scope(s):
 s=s.replace('generate_26878_build.py','generate_26879_build.py').replace('build_26878_iris_rawr.sh','build_26879_iris_rawr.sh')
 s=s.replace('53e570e4cc92ef5050f5f15953dd0fba88ec41cc2707c5eb79f1bc5994a531bb',PARENT)
 return s
edit('verify_scope',scope)
def authority(s):
 # Historical authority references ONLY in this stage refer to last 26879.
 s=s.replace('26878','26879')
 s=s.replace("'id':12586138690","'id':12600241817")
 s=s.replace("'name':'photon-26879-b-sr-guide-spektra-full-active'","'name':'photon-26879-b-50mp-neon-spektra-fov'")
 s=s.replace('sha256:254c63008636c721005dae80b4e4b9fffaf6252ac67a32f87f3238a1a0cec29d','sha256:bf060a690ee8792e0d3ab4fd58d25cabb2c0a2d35d6ffcd8a186508bb7132930')
 s=s.replace('mechanics_generated_script_sha256=53e570e4cc92ef5050f5f15953dd0fba88ec41cc2707c5eb79f1bc5994a531bb', 'mechanics_generated_script_sha256='+PARENT)
 assert '12600241817' in s and 'photon-26879-b-50mp-neon-spektra-fov' in s
 return s
edit('obtain_authority',authority)
def candidate(s):
 marker=' local H77="$WORK/historical_26877_from_26878"'
 assert marker in s
 header=''' local H78="$WORK/historical_26878_from_26879"
 cp -a "$BASE" "$H78";git -C "$H78" init -q
 (cd "$H78" && git apply --check --reverse "$ROOT/26879_FORWARD_FULL_INDEX.patch" &&
  git apply --reverse "$ROOT/26879_FORWARD_FULL_INDEX.patch" &&
  sha256sum -c "$ROOT/26879_BASE_26878_FULL_APP.sha256" >/dev/null) || fail 'real 26879->26878 successful candidate rollback failed'
'''
 s=s.replace(marker,header+marker,1)
 s=s.replace(' cp -a "$BASE" "$H77"',' cp -a "$H78" "$H77"',1)
 s=s.replace('regressions/26878_runtime_ownership_spektra.py "$H77" "$BASE"',
             'regressions/26878_runtime_ownership_spektra.py "$H77" "$H78"')
 s=s.replace('regressions/26880_runtime_ownership_spektra.py "$BASE" "$CAND"',
 '''regressions/26879_runtime_ownership_spektra.py "$H78" "$BASE"
 python3 -S regressions/26880_runtime_ownership_spektra.py "$BASE" "$CAND"
 python3 -S regressions/26880_wr_no_fit_optional_wavelet.py "$CAND/app/src/main/cpp/iris26864/Iris26864JniGpuInteropImpl.inc"
 python3 -S verify_26880_spektra_abi.py "$CAND/app"
 python3 -S verify_26880_native_shaders.py "$CAND"''')
 assert 'regressions/26879_runtime_ownership_spektra.py "$H78" "$BASE"' in s
 return s
edit('make_candidate',candidate)
def mechanics(s):
 s=s.replace('build_26878_iris_rawr.sh','build_26879_iris_rawr.sh').replace('generate_26878_build.py','generate_26879_build.py')
 s=s.replace('53e570e4cc92ef5050f5f15953dd0fba88ec41cc2707c5eb79f1bc5994a531bb',PARENT)
 return s
edit('verify_successful_mechanics',mechanics)
def shader(s):
 anchor=" sed -i 's#REAL GLSL COMPILE: NOT RUN YET#"
 assert anchor in s
 s=s.replace(anchor,''' python3 -S verify_26880_native_shaders.py "$CAND" --compiler "$IRIS26864_GLSLANG" \\
  --spirv-val "$(command -v spirv-val)" --spirv-opt "$(command -v spirv-opt)" \\
  --out "$OUT/26880_original_rawwavelet_spirv" | tee "$OUT/26880_original_rawwavelet_shader_proof.txt"
 grep -Fx 'PASS REAL 26880 FIVE ORIGINAL RAWR WAVELET SPIR-V COMPILERS' "$OUT/26880_original_rawwavelet_shader_proof.txt" >/dev/null || fail '26880 pinned original wavelet shader proof absent'
'''+anchor)
 return s
edit('compile_modified_runtime_shaders',shader)
def native(s):
 s=s.replace('real 58 pinned shader compilation','real 58 inherited + 5 original RAWR wavelet pinned shader compilation')
 return s
edit('compile_native',native)
def patch(s):return s.replace('5-file binary','34-file binary')
edit('verify_candidate_patches',patch)
def safety(s):
 s=s.replace('runtime_changed_files=5, B 50MP GPU intent + B neon sensor clipping + Spektra capture-matched RAW and FULL-quality + version',
 '''runtime_changed_files=34, 14 additions/20 modified; original UnspektrAwesome 1.2.5 arm64 native+Camera2+RAW/preview/capture, original RAWR B 7-scale chroma and ON/OFF highlight+version''')
 s=s.replace('candidate_files=2001','candidate_files=2015')
 s=s.replace('protected_source=1996 files byte-identical to successful 26878; GLSL/AE/DNG/vendor/old native JPEG unchanged',
             'protected_source=1981 files byte-identical to successful 26879, DNG/LONG/Motion/Night/Experiment A protected; original Spektra native explicitly changed')
 s=s.replace('successful 26878','successful 26879')
 return s
edit('prebuild_safety',safety)
def replay(s):
 s=s.replace('regressions/26878_runtime_ownership_spektra.py "$WORK/historical_26877_from_26878" "$BASE"',
             'regressions/26878_runtime_ownership_spektra.py "$WORK/historical_26877_from_26878" "$WORK/historical_26878_from_26879"')
 s=s.replace('regressions/26880_runtime_ownership_spektra.py "$BASE" "$exp"',
 '''regressions/26879_runtime_ownership_spektra.py "$WORK/historical_26878_from_26879" "$BASE"
 python3 -S regressions/26880_runtime_ownership_spektra.py "$BASE" "$exp"
 python3 -S regressions/26880_wr_no_fit_optional_wavelet.py "$exp/app/src/main/cpp/iris26864/Iris26864JniGpuInteropImpl.inc"
 python3 -S verify_26880_spektra_abi.py "$exp/app"
 python3 -S verify_26880_native_shaders.py "$exp"''')
 s=s.replace('regressions/26878_runtime_ownership_spektra.py regressions/26880_runtime_ownership_spektra.py',
             'regressions/26878_runtime_ownership_spektra.py regressions/26879_runtime_ownership_spektra.py regressions/26880_runtime_ownership_spektra.py regressions/26880_wr_no_fit_optional_wavelet.py')
 return s
edit('clean_extract_replay',replay)
# 40324502022: The original 55-shader RAWR validator must stay identical to
# successful 26879. On the expanded 26880 candidate, invoke a candidate-specific
# wrapper that runs the unchanged validator on a read-only original-domain view
# and enforces all four new wavelet shader hashes/counts separately. Never
# weaken or edit the historical file, nor bypass its real GLSL compilation.
for _stage in ('make_candidate','compile_modified_runtime_shaders','clean_extract_replay'):
 def _fix_candidate_shader_scope(old):
  before='python3 -S verify_26864_rawr_sources.py '
  after='python3 -S verify_26880_rawr_shader_universe.py '
  assert old.count(before)==1, (_stage,'unexpected original source verifier call count',old.count(before))
  return old.replace(before,after,1)
 edit(_stage,_fix_candidate_shader_scope)
def _compile_new_scope(s):
 needle='python3 -S -m py_compile verify_26880_candidate.py verify_26880_patches.py '
 assert needle in s
 return s.replace(needle,needle+'verify_26880_rawr_shader_universe.py ',1)
edit('verify_package',_compile_new_scope)
def _compile_final_scope(s):
 needle='python3 -S -m py_compile verify_26880_candidate.py verify_26880_patches.py '
 assert needle in s
 return s.replace(needle,needle+'verify_26880_rawr_shader_universe.py ',1)
edit('clean_extract_replay',_compile_final_scope)

# EXACT failures of Actions 40324502022 attempt 2 and its next stale
# highlight validator: original 26864/26867 historical scripts SHA-PINNED.
# Revalidate current exact 26880 shader owners with real glslang separately.
def _repair_script_preflight(s):
 target='verify_26880_rawr_shader_universe.py '
 assert s.count(target)==1,('preflight py_compile',s.count(target))
 return s.replace(target,target+'verify_26880_runtime_glsl_scope.py verify_26880_highlight_runtime_shader.py ',1)
edit('verify_package',_repair_script_preflight)

def _repair_candidate_source(s):
 needle=' python3 -S verify_26880_rawr_shader_universe.py "$CAND/app"'
 assert s.count(needle)==1,('make candidate shader scope call',s.count(needle))
 return s.replace(needle,needle+'''
 python3 -S verify_26880_runtime_glsl_scope.py "$BASE" "$CAND" --out "$OUT/26880_inherited11_current_shader_preflight"
 python3 -S verify_26880_highlight_runtime_shader.py "$CAND" --out "$OUT/26880_current_highlight_preflight"''',1)
edit('make_candidate',_repair_candidate_source)

def _repair_compile_stage(s):
 before='python3 -S verify_26864_runtime_glsl.py "$BASE" "$CAND"'
 assert s.count(before)==1
 s=s.replace(before,'python3 -S verify_26880_runtime_glsl_scope.py "$BASE" "$CAND"',1)
 before='python3 -S verify_26867_runtime_shader.py "$CAND"'
 assert s.count(before)==1
 s=s.replace(before,'python3 -S verify_26867_runtime_shader.py "$WORK/historical_26867_from_26868"',1)
 marker=""" grep -F 'pinned-glslang=PASS' "$OUT/26880_white_fade_glsl.txt" >/dev/null || fail 'inherited white fade real compiler missing'"""
 assert s.count(marker)==1
 after='''
 # The historical 26867 proof is replayed on EXACT 26867 bytes, while the
 # changed 26880 source is separately PINNED-COMPILED (not a static substitute).
 python3 -S verify_26880_highlight_runtime_shader.py "$CAND" --compiler "$IRIS26864_GLSLANG" --out "$OUT/26880_current_highlight_compiled" | tee "$OUT/26880_current_highlight_glsl.txt"
 grep -Fx 'PASS 26880 THREE CURRENT HIGHROOM/SMOOTH-WHITE SHADERS REAL GLSL' "$OUT/26880_current_highlight_glsl.txt" >/dev/null || fail 'three changed highlight owners not really compiled'
'''
 return s.replace(marker,marker+after,1)
edit('compile_modified_runtime_shaders',_repair_compile_stage)

def _repair_final_replay(s):
 target='python3 -S -m py_compile verify_26880_candidate.py verify_26880_patches.py verify_26880_rawr_shader_universe.py '
 assert s.count(target)==1
 s=s.replace(target,target+'verify_26880_runtime_glsl_scope.py verify_26880_highlight_runtime_shader.py ',1)
 before='python3 -S verify_26864_runtime_glsl.py "$BASE" "$exp"'
 assert s.count(before)==1
 s=s.replace(before,'python3 -S verify_26880_runtime_glsl_scope.py "$BASE" "$exp"',1)
 before='python3 -S verify_26867_runtime_shader.py "$exp"'
 assert s.count(before)==1
 s=s.replace(before,'python3 -S verify_26867_runtime_shader.py "$WORK/historical_26867_from_26868"',1)
 marker=' python3 -S verify_26880_rawr_shader_universe.py "$exp/app"'
 assert s.count(marker)==1
 s=s.replace(marker,marker+'''
 python3 -S verify_26880_highlight_runtime_shader.py "$exp" --out "$OUT/26880_final_highlight_preflight"''',1)
 return s
edit('clean_extract_replay',_repair_final_replay)

stages=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','verify_candidate_patches','prebuild_safety','assemble','postbuild_proof','clean_extract_replay']
def names(s):return [m.group(1) for m in re.finditer(r'\n([a-z_]+)\(\)\{',s)]
assert names(prior)==names(body) and [x for x in names(body) if x in stages]==stages
for cmd in ('./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'./gradlew :app:assembleDebug --stacktrace'):
 assert cmd in prior and cmd in body,cmd
for required in ('GLSLANG_VERSION="16.5.0"','PRE-BUILD SAFETY PROOF PASSED','snapshot_live_authority_seeded','RUNTIME_ARTIFACT_ID="12600241817"','runtime_changed_files=34','real successful 26879','26880_PREBUILD_SAFETY.txt'):
 assert required in body,required
assert 'regressions/26877_superres_ownership.py' not in body
# Preserve all historical regression validators. Local staging duplicates only the latest.
for rel in {'verify_26880_candidate.py','verify_26880_patches.py','verify_26880_native_shaders.py','verify_26880_spektra_abi.py','regressions/26880_runtime_ownership_spektra.py','regressions/26880_wr_no_fit_optional_wavelet.py','verify_26880_rawr_shader_universe.py','verify_26880_runtime_glsl_scope.py','verify_26880_highlight_runtime_shader.py','regressions/26879_runtime_ownership_spektra.py','regressions/26878_runtime_ownership_spektra.py','regressions/26877_runtime_ownership_spektra.py'}:
 assert (P/rel).is_file(),rel
(P/'build_26880_iris_rawr.sh').write_text(body)
(P/'26880_BUILD_INFRASTRUCTURE_DIFF.txt').write_text(''.join(difflib.unified_diff(prior.splitlines(True),body.splitlines(True),fromfile='exact_successful_26879_guarded_17_stage_runner',tofile='26880_inherited_17_stage_runner')))
(P/'26880_GENERATED_BUILD_SHA256.txt').write_text(hashlib.sha256(body.encode()).hexdigest()+'  build_26880_iris_rawr.sh\n')
print('PASS 26880 generated 17 stages',hashlib.sha256(body.encode()).hexdigest())
