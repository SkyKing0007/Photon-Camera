#!/usr/bin/env python3
"""26882: inherit SHA-pinned successfully COMPILED 26881 17-stage runner.

Do not invent a second handoff/build authority. All compiler and assemble
commands and the exact successful candidate-first/freeze sequence are inherited.
Historical 26880/26881 validators must run on their own compiled sources.
"""
from pathlib import Path
import sys,hashlib,re,difflib
P=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path('.').resolve()
prior=(P/'build_26881_iris_rawr.sh').read_text()
PARENT='8e9d44d66e4c955c105d136a1c380206ae93b671b9e57806412c2c991a791fc5'
assert hashlib.sha256(prior.encode()).hexdigest()==PARENT,'Not exact successful 26881 17-stage compiler runner'
body=prior.replace('26881','26882').replace('0.9726881','0.9726882')
# These historical verifiers are not renamed by a successor's source scope.
for rel in ('verify_26881_expanded_glsl.py','regressions/26881_spektra_chroma_clip.py',
 'regressions/26881_actual_generator_artifact_identity.py','regressions/26881_no_crossstage_local.py',
 'regressions/26881_trigger_contract.py','regressions/26881_historical_output_contract.py'):
 body=body.replace(rel.replace('26881','26882'),rel)
def edit(name,fn):
 global body
 i=body.index('\n'+name+'(){')+1;j=body.index('\n}',i)+2
 old=body[i:j];new=fn(old)
 assert new!=old,('stage no-op',name)
 if not new.rstrip().endswith('}'):
  k=new.rfind('\n}')
  assert k>0,('stage terminator lost',name)
  new=new[:k]+new[k+2:]+'\n}'
 body=body[:i]+new+body[j:]
def once(old,new):
 global body
 assert body.count(old)==1,(old,body.count(old))
 body=body.replace(old,new,1)
# The compiled 26881 checkout, not repository app/src, becomes runtime authority.
for a,b in [
 ('REPO_SCAFFOLD_BASE_COMMIT="6dd572d3d7b33ba4309eed87edbd9884624410de"', 'REPO_SCAFFOLD_BASE_COMMIT="c28269f36b5754bded0623c104b9dcc1244b15d3"'),
 ('RUNTIME_AUTHORITY_COMMIT="6dd572d3d7b33ba4309eed87edbd9884624410de"', 'RUNTIME_AUTHORITY_COMMIT="c28269f36b5754bded0623c104b9dcc1244b15d3"'),
 ('RUNTIME_ARTIFACT_ID="12658293287"; RUNTIME_ACTIONS_RUN="40324502022"','RUNTIME_ARTIFACT_ID="12695143651"; RUNTIME_ACTIONS_RUN="40415858178"'),
 ('RUNTIME_ARTIFACT_SHA="5516d6deffd486de6d5dd18a51ebeb6d216883b7a4df325cc70ad09d80bee455"','RUNTIME_ARTIFACT_SHA="b83eb47da7da71fc75a82aa1bb562acb6169379e65ee483f60ee92702cb790da"'),
 ('RUNTIME_TAR_SHA="913ffd7dcdfe791b734b47199ed20c69ebad25e23b4b6c83c3ff54c37ea5baca"','RUNTIME_TAR_SHA="5cd951c92e7782bf12812cb5f6e9adb76aabd7255515512e5196e7688f2a3e87"'),
 ('MECHANICS_GIT_BLOB="249a47f13f7ce618fcd63eff6d5bfa5ab326f8c7"','MECHANICS_GIT_BLOB="2a503622fd337a7355385fbf82706c4b089de777"'),
 ('ARTZIP="$WORK/26880_artifact.zip"; ARTDIR="$WORK/artifact_26880"','ARTZIP="$WORK/26881_artifact.zip"; ARTDIR="$WORK/artifact_26881"'),
 ('BASE="$WORK/exact_successful_26880_compiled_candidate"','BASE="$WORK/exact_successful_26881_compiled_candidate"'),
]:once(a,b)

def package(s):
 # Inherits all previous hash, compiler command, GLSL, scope and trigger gates.
 s=s.replace('[[ $(find handoff_payload_26882 -type f | wc -l) -eq 12 ]]',
             '[[ $(find handoff_payload_26882 -type f | wc -l) -eq 3 ]]')
 s=s.replace('18-path exact runtime scope including six deletions','3-file exact runtime correction scope')
 s=s.replace('18-path','3-file')
 # 26882 has zero source deletions; use straightforward strict allowlist equality.
 s=s.replace('diff -u <(grep -vxf 26882_DELETIONS.txt 26882_CHANGED_ALLOWLIST.txt)',
             'diff -u 26882_CHANGED_ALLOWLIST.txt')
 s=s.replace('RUN_26882_SPEKTRA112_FOV_CHROMA_HIGHLIGHT_R6','RUN_26882_SPEKTRA_ROTATED_RAW_B_WHITE_OFF_V1')
 # Previous 26881 generator and its historical regressions retain their
 # exact original 26881 names, and execute only against that prior runner.
 s=s.replace('regressions/26881_actual_generator_artifact_identity.py build_26882_iris_rawr.sh',
             'regressions/26881_actual_generator_artifact_identity.py build_26881_iris_rawr.sh')
 insert='''
 python3 -S -m py_compile verify_26882_candidate.py verify_26882_patches.py verify_26882_expanded_glsl.py verify_26882_semantics.py stage_26882_root.py
 python3 -S stage_26882_root.py
'''
 return s[:-2]+insert+'\n}'
edit('verify_package',package)

def scope(s):
 return s.replace('generate_26880_build.py','generate_26881_build.py').replace('build_26880_iris_rawr.sh','build_26881_iris_rawr.sh').replace('312bc023047ea13752efc46c6ad030e34d63441c807f55873266417fa113c21a',PARENT)
edit('verify_scope',scope)

def authority(s):
 # Previous successful 26881 runner acquired 26880, not its own 26881 ZIP.
 s=s.replace('26880','26881')
 a='12658293287';b='12695143651'
 assert a in s; s=s.replace(a,b)
 a='photon-26881-original-spektra125-rawwavelet-highlights';b='photon-26881-spektra-fov-b-halo-clipped-highlights'
 assert a in s,s[-1900:];s=s.replace(a,b)
 a='sha256:5516d6deffd486de6d5dd18a51ebeb6d216883b7a4df325cc70ad09d80bee455';b='sha256:b83eb47da7da71fc75a82aa1bb562acb6169379e65ee483f60ee92702cb790da'
 assert a in s;s=s.replace(a,b)
 s=s.replace(' -eq 2015 ]]',' -eq 2009 ]]')
 s=s.replace("x['head_sha']=='675d28299d9264baad1a549946661c57388e5cf8' and x.get('run_attempt',0)>=4",
             "x['head_sha']=='c28269f36b5754bded0623c104b9dcc1244b15d3' and x.get('run_attempt',0)==1")
 s=s.replace('mechanics_generated_script_sha256=312bc023047ea13752efc46c6ad030e34d63441c807f55873266417fa113c21a',
             'mechanics_generated_script_sha256='+PARENT)
 assert '12695143651' in s and ' -eq 2009 ]]' in s
 return s
edit('obtain_authority',authority)

def candidate(s):
 # Reconstruct REAL compiled 26880 from the REAL compiled 26881 artifact.
 # The old 26881 historical rollback sequence then operates on its own
 # byte-identical successful ancestor, never on the new 26882 candidate.
 mark='local H79="$WORK/historical_26879_from_26880"';assert mark in s
 source='''local H80="$WORK/historical_26880_from_26881"
 cp -a "$BASE" "$H80";git -C "$H80" init -q
 (cd "$H80" && git apply --check --reverse "$ROOT/26881_FORWARD_FULL_INDEX.patch" &&
  git apply --reverse "$ROOT/26881_FORWARD_FULL_INDEX.patch" &&
  sha256sum -c "$ROOT/26881_BASE_26880_FULL_APP.sha256" >/dev/null) || fail '26881->26880 actual compiled candidate rollback failed'
 '''
 s=s.replace(mark,source+mark,1)
 assert 'cp -a "$BASE" "$H79"' in s
 s=s.replace('cp -a "$BASE" "$H79"','cp -a "$H80" "$H79"',1)
 # Historical checks preserve their old source domain, native JNI and output.
 s=s.replace('regressions/26880_runtime_ownership_spektra.py "$H79" "$BASE"','regressions/26880_runtime_ownership_spektra.py "$H79" "$H80"')
 s=s.replace('regressions/26881_spektra_chroma_clip.py "$BASE" "$CAND"',
             'regressions/26881_spektra_chroma_clip.py "$H80" "$BASE"')
 s=s.replace('verify_26880_spektra_abi.py "$BASE/app"','verify_26880_spektra_abi.py "$H80/app"')
 s=s.replace('verify_26880_highlight_runtime_shader.py "$BASE"','verify_26880_highlight_runtime_shader.py "$H80"')
 s=s.replace('verify_26880_native_shaders.py "$BASE"','verify_26880_native_shaders.py "$H80"')
 s=s.replace('verify_26880_runtime_glsl_scope.py "$H79" "$BASE"','verify_26880_runtime_glsl_scope.py "$H79" "$H80"')
 s=s.replace('verify_26881_expanded_glsl.py "$CAND"','verify_26881_expanded_glsl.py "$BASE"')
 # In R6 this call might already be renamed by generic version transformation.
 s=s.replace('verify_26882_expanded_glsl.py "$CAND"','verify_26881_expanded_glsl.py "$BASE"')
 return s[:-2]+'''
 python3 -S verify_26882_semantics.py "$BASE" "$CAND"
 python3 -S verify_26882_expanded_glsl.py "$CAND" --out "$OUT/26882_current_white_source_preflight"
'''+ '\n}'
edit('make_candidate',candidate)

def mechanics(s):
 return s.replace('build_26880_iris_rawr.sh','build_26881_iris_rawr.sh').replace('generate_26880_build.py','generate_26881_build.py').replace('312bc023047ea13752efc46c6ad030e34d63441c807f55873266417fa113c21a',PARENT)
edit('verify_successful_mechanics',mechanics)

def shaders(s):
 # Original 26880 checks run on unchanged 26880; original 26881 checks
 # on unchanged 26881. The ONLY edited runtime shader is recompiled below.
 s=s.replace('verify_26880_highlight_runtime_shader.py "$BASE"','verify_26880_highlight_runtime_shader.py "$WORK/historical_26880_from_26881"')
 s=s.replace('verify_26880_native_shaders.py "$BASE"','verify_26880_native_shaders.py "$WORK/historical_26880_from_26881"')
 s=s.replace('verify_26880_runtime_glsl_scope.py "$WORK/historical_26879_from_26880" "$BASE"',
             'verify_26880_runtime_glsl_scope.py "$WORK/historical_26879_from_26880" "$WORK/historical_26880_from_26881"')
 s=s.replace('verify_26882_expanded_glsl.py "$CAND"','verify_26881_expanded_glsl.py "$BASE"')
 s=s.replace('verify_26881_expanded_glsl.py "$CAND"','verify_26881_expanded_glsl.py "$BASE"')
 s=s.replace("grep -Fx 'PASS 26882 BOTH MODIFIED RUNTIME GLES300 PROGRAMS REAL PINNED GLSL'",
             "grep -Fx 'PASS 26881 BOTH MODIFIED RUNTIME GLES300 PROGRAMS REAL PINNED GLSL'")
 return s[:-2]+'''
 python3 -S verify_26882_expanded_glsl.py "$CAND" --compiler "$IRIS26864_GLSLANG" --out "$OUT/26882_real_expanded_white" | tee "$OUT/26882_modified_white_glsl.txt"
 grep -F 'pinned-glslang=PASS' "$OUT/26882_modified_white_glsl.txt" >/dev/null || fail '26882 exact modified native white shader not compiled by pinned real GLSL'
'''+ '\n}'
edit('compile_modified_runtime_shaders',shaders)

def patches_stage(s):
 return s.replace('18-path binary including deletions','3-file full-index binary forward/rollback')
edit('verify_candidate_patches',patches_stage)

def safety(s):
 # Names in prior 26881's report are historical, never runtime authorities.
 s=s.replace('runtime_authority=successful 26879','runtime_authority=successful 26881')
 s=s.replace('verification_mechanics=exact successful 26879 inherited',
             'verification_mechanics=exact successful 26881 inherited')
 s=s.replace('prior_files=2001','prior_files=2009')
 s=s.replace('runtime_changed_files=18 (12 replacements + 6 deletions)','runtime_changed_files=3 (2 localized fixes + version)')
 s=s.replace('candidate_files=2009','candidate_files=2009')
 s=s.replace('protected_source=1997','protected_source=2006')
 s=s.replace('restored compiled 26692 Vulkan/JNI; full-view portrait/landscape + bounded B multiscale chroma + sensor-clipped-white+version',
             '26882 orientation-aware Spektra RAW dimension guard + B shared HDRq/Wronski clipped-white fade + version; no native/vendor/DNG/routing changes')
 return s
edit('prebuild_safety',safety)

def replay(s):
 s=s.replace('regressions/26881_spektra_chroma_clip.py "$BASE" "$exp"',
             'regressions/26881_spektra_chroma_clip.py "$WORK/historical_26880_from_26881" "$BASE"')
 s=s.replace('regressions/26880_runtime_ownership_spektra.py "$WORK/historical_26879_from_26880" "$BASE"',
             'regressions/26880_runtime_ownership_spektra.py "$WORK/historical_26879_from_26880" "$WORK/historical_26880_from_26881"')
 s=s.replace('verify_26880_spektra_abi.py "$BASE/app"','verify_26880_spektra_abi.py "$WORK/historical_26880_from_26881/app"')
 s=s.replace('verify_26880_highlight_runtime_shader.py "$BASE"','verify_26880_highlight_runtime_shader.py "$WORK/historical_26880_from_26881"')
 s=s.replace('verify_26880_native_shaders.py "$BASE"','verify_26880_native_shaders.py "$WORK/historical_26880_from_26881"')
 s=s.replace('verify_26880_runtime_glsl_scope.py "$WORK/historical_26879_from_26880" "$BASE"',
             'verify_26880_runtime_glsl_scope.py "$WORK/historical_26879_from_26880" "$WORK/historical_26880_from_26881"')
 s=s.replace('verify_26882_expanded_glsl.py "$exp"','verify_26881_expanded_glsl.py "$BASE"')
 s=s.replace('verify_26881_expanded_glsl.py "$exp"','verify_26881_expanded_glsl.py "$BASE"')
 return s[:-2]+'''
 python3 -S verify_26882_semantics.py "$BASE" "$exp"
 python3 -S verify_26882_expanded_glsl.py "$exp" --out "$OUT/26882_final_white_shader_source"
'''+ '\n}'
edit('clean_extract_replay',replay)
STAGES=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','verify_candidate_patches','prebuild_safety','assemble','postbuild_proof','clean_extract_replay']
fn=lambda s:[m.group(1) for m in re.finditer(r'\n([a-z_]+)\(\)\{',s)]
assert fn(body)==fn(prior) and [x for x in fn(body) if x in STAGES]==STAGES
for cmd in ['./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'./gradlew :app:assembleDebug --stacktrace']:
 assert cmd in prior and cmd in body,cmd
assert 'GLSLANG_VERSION="16.5.0"' in body and 'PRE-BUILD SAFETY PROOF PASSED' in body
assert 'snapshot_live_authority_seeded' in prior and 'snapshot_live_authority_seeded' in body
assert 'regressions/26877_superres_ownership.py' not in body
(P/'build_26882_iris_rawr.sh').write_text(body)
(P/'26882_BUILD_INFRASTRUCTURE_DIFF.txt').write_text(''.join(difflib.unified_diff(prior.splitlines(True),body.splitlines(True),fromfile='SHA_pinned_successful_26881_17_stage_runner',tofile='26882_successor_17_stage_runner')))
(P/'26882_GENERATED_BUILD_SHA256.txt').write_text(hashlib.sha256(body.encode()).hexdigest()+'  build_26882_iris_rawr.sh\n')
print('PASS 26882 generated 17 unchanged ordered stages / compiler commands, SHA-pinned actual successful 26881 parent',hashlib.sha256(body.encode()).hexdigest())
