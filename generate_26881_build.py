#!/usr/bin/env python3
"""Deterministically extend EXACT successful 26880 attempt-4 17-stage runner.
Compiler commands, original historical validators, ordering and freeze inherited.
New 26881 checks execute on real 26880 candidate; 26880-only regressions
execute on historical 26879->26880 objects, never revised 26881 bytes.
"""
from pathlib import Path
import hashlib,re,difflib,sys
P=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path('.').resolve()
prior=(P/'build_26880_iris_rawr.sh').read_text()
PARENT='312bc023047ea13752efc46c6ad030e34d63441c807f55873266417fa113c21a'
assert hashlib.sha256(prior.encode()).hexdigest()==PARENT,'Not exact successful 26880 attempt-4 guarded runner'
body=prior.replace('26880','26881').replace('0.9726880','0.9726881')
# Exact successful 26880 validators and historical regression mechanics are
# inherited as original named files, not silently renamed into nonexistent 26881 copies.
for historical in ('verify_26880_native_shaders.py','verify_26880_spektra_abi.py',
                   'verify_26880_rawr_shader_universe.py','verify_26880_runtime_glsl_scope.py',
                   'verify_26880_highlight_runtime_shader.py','regressions/26880_runtime_ownership_spektra.py',
                   'regressions/26880_wr_no_fit_optional_wavelet.py'):
 body=body.replace(historical.replace('26880','26881'),historical)
def edit(stage,fn):
 global body
 start=body.index('\n'+stage+'(){')+1;end=body.index('\n}',start)+2
 old=body[start:end];new=fn(old)
 assert old!=new,stage
 if not new.rstrip().endswith('}'):
  i=new.rfind('\n}')
  assert i>=0,('stage ending missing',stage)
  new=new[:i]+new[i+2:]+ '\n}'
 body=body[:start]+new+body[end:]
def one(old,new):
 global body
 assert body.count(old)==1,(old,body.count(old));body=body.replace(old,new,1)
for old,new in [
 ('REPO_SCAFFOLD_BASE_COMMIT="7b5dcab60f290a61ecc7e0af8a82398ac4c124ab"','REPO_SCAFFOLD_BASE_COMMIT="6dd572d3d7b33ba4309eed87edbd9884624410de"'),
 ('RUNTIME_AUTHORITY_COMMIT="7b5dcab60f290a61ecc7e0af8a82398ac4c124ab"','RUNTIME_AUTHORITY_COMMIT="6dd572d3d7b33ba4309eed87edbd9884624410de"'),
 ('RUNTIME_ARTIFACT_ID="12600241817"; RUNTIME_ACTIONS_RUN="40195876708"','RUNTIME_ARTIFACT_ID="12658293287"; RUNTIME_ACTIONS_RUN="40324502022"'),
 ('RUNTIME_ARTIFACT_SHA="bf060a690ee8792e0d3ab4fd58d25cabb2c0a2d35d6ffcd8a186508bb7132930"','RUNTIME_ARTIFACT_SHA="5516d6deffd486de6d5dd18a51ebeb6d216883b7a4df325cc70ad09d80bee455"'),
 ('RUNTIME_TAR_SHA="2775f4f35139709d6521a8e6a9d6d91d1fd9a46a5c2a2997d6d24f2e10a2e44b"','RUNTIME_TAR_SHA="913ffd7dcdfe791b734b47199ed20c69ebad25e23b4b6c83c3ff54c37ea5baca"'),
 ('MECHANICS_GIT_BLOB="e354c0c6971de8809c0c0211623164208c1a1dff"','MECHANICS_GIT_BLOB="249a47f13f7ce618fcd63eff6d5bfa5ab326f8c7"'),
 ('ARTZIP="$WORK/26879_artifact.zip"; ARTDIR="$WORK/artifact_26879"','ARTZIP="$WORK/26880_artifact.zip"; ARTDIR="$WORK/artifact_26880"'),
 ('BASE="$WORK/exact_successful_26879_compiled_candidate"','BASE="$WORK/exact_successful_26880_compiled_candidate"'),
]:one(old,new)
def package(s):
 s=s.replace('[[ $(find handoff_payload_26881 -type f | wc -l) -eq 34 ]]','[[ $(find handoff_payload_26881 -type f | wc -l) -eq 12 ]]')
 s=s.replace('34-file exact runtime upload scope','18-path exact runtime scope including six deletions')
 s=s.replace('34-file','18-path')
 # The six deleted 1.2.5-only files are an EXACT part of the runtime change
 # scope but have no replacement payload. Do not weaken allowlist equality.
 s=s.replace('diff -u 26881_CHANGED_ALLOWLIST.txt <(find handoff_payload_26881 -type f',
             'diff -u <(grep -vxf 26881_DELETIONS.txt 26881_CHANGED_ALLOWLIST.txt) <(find handoff_payload_26881 -type f')
 s=s.replace('RUN_26881_ORIGINAL_125_WRONSKI_WAVELET_HIGHLIGHT_V1','RUN_26881_SPEKTRA112_FOV_CHROMA_HIGHLIGHT_R6')
 # 26880 packed SO proof is historical; new native is exact 26692 and verified by 26881 candidate validator.
 s=s.replace(' sha256sum -c 26881_ORIGINAL_NATIVE_ZLIB_SHA256.txt >/dev/null || fail \'original native compressed source drift\'','')
 s=s.replace(' sha256sum -c 26881_FLAT_SOURCE_SHA256.txt >/dev/null || fail \'flat source staging drift\'','')
 return s+'''
 python3 -S -m py_compile verify_26881_candidate.py verify_26881_patches.py verify_26881_expanded_glsl.py regressions/26881_spektra_chroma_clip.py regressions/26881_actual_generator_artifact_identity.py stage_26881_root.py
 python3 -S stage_26881_root.py --verify-only
 python3 -S regressions/26881_actual_generator_artifact_identity.py build_26881_iris_rawr.sh
'''
edit('verify_package',package)
def scope(s):
 s=s.replace('generate_26879_build.py','generate_26880_build.py').replace('build_26879_iris_rawr.sh','build_26880_iris_rawr.sh')
 s=s.replace('985e5f03c620deef3a42b0b50424776e6208e85b62ff5d26e16a7579940d0c19',PARENT)
 return s
edit('verify_scope',scope)
def authority(s):
 # Permanent regression from failed Actions 40392745967 / job 121817713609:
 # prior source identifiers have already undergone the historic 26879->26880
 # stage-local substitution when we update the *artifact name*. A silent
 # missed .replace() caused an assertion before any real compiler ran.
 historical_name="photon-26880-b-50mp-neon-spektra-fov"
 actual_name="photon-26880-original-spektra125-rawwavelet-highlights"
 assert s.count("12600241817")==1, ('old successful artifact ID not unique',s.count("12600241817"))
 assert s.count('sha256:bf060a690ee8792e0d3ab4fd58d25cabb2c0a2d35d6ffcd8a186508bb7132930')==1, 'old artifact digest missing/duplicated'
 # This operation must run BEFORE verifying the artifact-name anchor: the
 # previous successful 26880 runner references the prior 26879 artifact.
 s=s.replace('26879','26880')
 assert s.count(historical_name)==1, ('successful 26879 artifact name anchor missing',s.count(historical_name))
 assert actual_name not in s, 'current artifact name was already present before targeted migration'
 s=s.replace(historical_name,actual_name,1)
 s=s.replace("12600241817","12658293287",1)
 s=s.replace('sha256:bf060a690ee8792e0d3ab4fd58d25cabb2c0a2d35d6ffcd8a186508bb7132930','sha256:5516d6deffd486de6d5dd18a51ebeb6d216883b7a4df325cc70ad09d80bee455',1)
 assert s.count(actual_name)==1 and s.count("12658293287")==1, 'exact current successful artifact metadata was not installed'
 assert historical_name not in s, 'stale previous artifact name left behind'
 # Successful 26880 attempt 4 added 14 source files: unlike 26879's 2001,
 # exact 26880 artifact authority contains 2015 files. This is distinct from
 # the candidate's final 2009 count and must not be conflated.
 old_universe=' -eq 2001 ]]'
 assert s.count(old_universe)==1,('unexpected 26880 authority-count gate',s.count(old_universe))
 s=s.replace(old_universe,' -eq 2015 ]]',1)
 s=s.replace('mechanics_generated_script_sha256=985e5f03c620deef3a42b0b50424776e6208e85b62ff5d26e16a7579940d0c19','mechanics_generated_script_sha256='+PARENT)
 # 26880 successful attempt 4 checked out 6dd572..., while original event SHA is 675d282...
 # Do NOT compare original run head_sha with the later actual checkout commit.
 target="x['head_sha']==sys.argv[2]"
 assert target in s,'original run head SHA check not found'
 s=s.replace(target,"x['head_sha']=='675d28299d9264baad1a549946661c57388e5cf8' and x.get('run_attempt',0)>=4",1)
 assert '12658293287' in s and 'photon-26880-original-spektra125-rawwavelet-highlights' in s
 return s
edit('obtain_authority',authority)
def candidate(s):
 # Prior runner first rolled back successful 26879 -> 26878; now first roll back 26880 -> 26879.
 marker='local H78="$WORK/historical_26878_from_26879"'
 assert marker in s
 header='''local H79="$WORK/historical_26879_from_26880"
 cp -a "$BASE" "$H79";git -C "$H79" init -q
 (cd "$H79" && git apply --check --reverse "$ROOT/26880_FORWARD_FULL_INDEX.patch" &&
  git apply --reverse "$ROOT/26880_FORWARD_FULL_INDEX.patch" &&
  sha256sum -c "$ROOT/26880_BASE_26879_FULL_APP.sha256" >/dev/null) || fail '26880->26879 real compiled historical rollback failed'
 '''
 s=s.replace(marker,header+marker,1)
 s=s.replace('cp -a "$BASE" "$H78"','cp -a "$H79" "$H78"',1)
 # The 26880 regression is pinned to 26879->26880 historical bytes, not the 26881 edited native library.
 s=s.replace('regressions/26880_runtime_ownership_spektra.py "$BASE" "$CAND"',
 '''regressions/26880_runtime_ownership_spektra.py "$H79" "$BASE"
 python3 -S regressions/26881_spektra_chroma_clip.py "$BASE" "$CAND"''')
 s=s.replace('regressions/26879_runtime_ownership_spektra.py "$H78" "$BASE"','regressions/26879_runtime_ownership_spektra.py "$H78" "$H79"')
 s=s.replace('verify_26880_spektra_abi.py "$CAND/app"','verify_26880_spektra_abi.py "$BASE/app"')
 s=s.replace('verify_26881_spektra_abi.py "$CAND/app"','verify_26880_spektra_abi.py "$BASE/app"')
 s=s.replace('verify_26880_highlight_runtime_shader.py "$CAND"','verify_26880_highlight_runtime_shader.py "$BASE"')
 s=s.replace('verify_26880_runtime_glsl_scope.py "$BASE" "$CAND"','verify_26880_runtime_glsl_scope.py "$H79" "$BASE"')
 s+='''
 python3 -S verify_26881_expanded_glsl.py "$CAND" --out "$OUT/26881_new_shader_preflight"
'''
 return s
edit('make_candidate',candidate)
def mechanics(s):
 return s.replace('build_26879_iris_rawr.sh','build_26880_iris_rawr.sh').replace('generate_26879_build.py','generate_26880_build.py').replace('985e5f03c620deef3a42b0b50424776e6208e85b62ff5d26e16a7579940d0c19',PARENT)
edit('verify_successful_mechanics',mechanics)
def shaders(s):
 # Replay the successful 26880 highlight proof on its actual compiled candidate.
 s=s.replace('verify_26880_highlight_runtime_shader.py "$CAND"','verify_26880_highlight_runtime_shader.py "$BASE"')
 s=s.replace('verify_26880_runtime_glsl_scope.py "$BASE" "$CAND"','verify_26880_runtime_glsl_scope.py "$WORK/historical_26879_from_26880" "$BASE"')
 # This success stdout is produced by byte-unchanged successful 26880
 # validators. Global version migration changes the current runner's output
 # paths, NOT the historical validators' printed success strings.
 hist=(
  ("grep -Fx 'PASS REAL 26881 FIVE ORIGINAL RAWR WAVELET SPIR-V COMPILERS'",
   "grep -Fx 'PASS REAL 26880 FIVE ORIGINAL RAWR WAVELET SPIR-V COMPILERS'"),
  ("grep -Fx 'PASS 26881 THREE CURRENT HIGHROOM/SMOOTH-WHITE SHADERS REAL GLSL'",
   "grep -Fx 'PASS 26880 THREE CURRENT HIGHROOM/SMOOTH-WHITE SHADERS REAL GLSL'"),
 )
 for stale,historical in hist:
  assert s.count(stale)==1,('missing or duplicated stale generated output check',stale,s.count(stale))
  s=s.replace(stale,historical,1)
  assert s.count(historical)==1,('historical immutable validator output contract absent',historical)
 # H79 is local to make_candidate; later stages use the persisted WORK path.
 # Historical 26880 exact-original shader proof uses its own expected marker unchanged.
 s+='''
 python3 -S verify_26881_expanded_glsl.py "$CAND" --compiler "$IRIS26864_GLSLANG" --out "$OUT/26881_real_current_glsl" | tee "$OUT/26881_shader_compiler_proof.txt"
 grep -Fx 'PASS 26881 BOTH MODIFIED RUNTIME GLES300 PROGRAMS REAL PINNED GLSL' "$OUT/26881_shader_compiler_proof.txt" >/dev/null || fail '26881 required real changed GLSL compiler proof missing'
'''
 return s
edit('compile_modified_runtime_shaders',shaders)
def patch(s):return s.replace('34-file binary','18-path binary including deletions')
edit('verify_candidate_patches',patch)
def safety(s):
 s=s.replace('runtime_changed_files=34','runtime_changed_files=18 (12 replacements + 6 deletions)')
 s=s.replace('candidate_files=2015','candidate_files=2009')
 s=s.replace('protected_source=1981','protected_source=1997')
 s=s.replace('original UnspektrAwesome 1.2.5 arm64 native+Camera2+RAW/preview/capture, original RAWR B 7-scale chroma and ON/OFF highlight+version','restored compiled 26692 Vulkan/JNI; full-view portrait/landscape + bounded B multiscale chroma + sensor-clipped-white+version')
 return s
edit('prebuild_safety',safety)
def replay(s):
 s=s.replace('regressions/26880_runtime_ownership_spektra.py "$BASE" "$exp"',
 '''regressions/26880_runtime_ownership_spektra.py "$WORK/historical_26879_from_26880" "$BASE"
 python3 -S regressions/26881_spektra_chroma_clip.py "$BASE" "$exp"''')
 s=s.replace('regressions/26879_runtime_ownership_spektra.py "$WORK/historical_26878_from_26879" "$BASE"',
 'regressions/26879_runtime_ownership_spektra.py "$WORK/historical_26878_from_26879" "$WORK/historical_26879_from_26880"')
 # The successful 26880 original 1.2.5 JNI validator must run on its
 # original compiled candidate, not on restored 26692 JNI ABI in 26881.
 assert s.count('verify_26880_spektra_abi.py "$exp/app"')==1,'missing exact successful 26880 final Spektra ABI validator'
 s=s.replace('verify_26880_spektra_abi.py "$exp/app"','verify_26880_spektra_abi.py "$BASE/app"')
 s=s.replace('verify_26880_highlight_runtime_shader.py "$exp"','verify_26880_highlight_runtime_shader.py "$BASE"')
 s=s.replace('verify_26880_runtime_glsl_scope.py "$BASE" "$exp"','verify_26880_runtime_glsl_scope.py "$WORK/historical_26879_from_26880" "$BASE"')
 s+='''
 python3 -S verify_26881_expanded_glsl.py "$exp" --out "$OUT/26881_clean_extract_shader_preflight"
'''
 return s
edit('clean_extract_replay',replay)
STAGES=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','verify_candidate_patches','prebuild_safety','assemble','postbuild_proof','clean_extract_replay']
fn=lambda s:[m.group(1) for m in re.finditer(r'\n([a-z_]+)\(\)\{',s)]
assert fn(prior)==fn(body) and [n for n in fn(body) if n in STAGES]==STAGES
for cmd in ('./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'./gradlew :app:assembleDebug --stacktrace'):
 assert cmd in prior and cmd in body,cmd
assert 'GLSLANG_VERSION="16.5.0"' in prior and 'GLSLANG_VERSION="16.5.0"' in body
assert 'PRE-BUILD SAFETY PROOF PASSED' in body and 'snapshot_live_authority_seeded' in body
assert 'regressions/26877_superres_ownership.py' not in body
(P/'build_26881_iris_rawr.sh').write_text(body)
(P/'26881_BUILD_INFRASTRUCTURE_DIFF.txt').write_text(''.join(difflib.unified_diff(prior.splitlines(True),body.splitlines(True),fromfile='exact_successful_26880_17_stage_runner_attempt4',tofile='26881_inherited_17_stage_runner')))
(P/'26881_GENERATED_BUILD_SHA256.txt').write_text(hashlib.sha256(body.encode()).hexdigest()+'  build_26881_iris_rawr.sh\n')
print('PASS 26881 inherited 17 ordered stages and real compiler commands from SHA-pinned successful 26880',hashlib.sha256(body.encode()).hexdigest())
