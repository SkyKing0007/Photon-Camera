#!/usr/bin/env python3
"""Generate Photon 26883 ONLY from exact successful 26882 compiled 17-stage runner.
Inherit freeze, Kotlin/Java/NDK/assemble, archive/rollback, and provenance order.
Historical verifiers run against their own real compiled successful source universes.
"""
from pathlib import Path
import re,hashlib,difflib,sys
P=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path('.').resolve()
prior=(P/'build_26882_iris_rawr.sh').read_text()
PARENT='8bbdf3738e8a8b17f236db6c43f8273b2a24e164b847963aa9c749da7707251c'
assert hashlib.sha256(prior.encode()).hexdigest()==PARENT,'not the exact successful 26882 17-stage runner'
body=prior.replace('26882','26883').replace('0.9726882','0.9726883')
# Version-name transformation must retain older historical validator identity.
for old in ('verify_26882_candidate.py','verify_26882_patches.py','verify_26882_semantics.py','verify_26882_expanded_glsl.py','stage_26882_root.py','regressions/26882_actual_successor_contract.py'):
 # Never change the old successful validator's namespace where it is still required.
 pass

def edit(name,fn):
 global body
 a=body.index('\n'+name+'(){')+1;b=body.index('\n}',a)+2
 old=body[a:b];new=fn(old)
 assert old!=new,('unexpected noop for inherited stage',name)
 body=body[:a]+new+body[b:]
def once(old,new):
 global body
 assert body.count(old)==1,('unexpected replacement cardinality',old,body.count(old))
 body=body.replace(old,new,1)

# Only successful 26882 runtime authority and its SHA-pinned verification generator change.
for old,new in [
 ('REPO_SCAFFOLD_BASE_COMMIT="c28269f36b5754bded0623c104b9dcc1244b15d3"','REPO_SCAFFOLD_BASE_COMMIT="694bdc8b03b93131b17d753c60f92bef21404e22"'),
 ('RUNTIME_AUTHORITY_COMMIT="c28269f36b5754bded0623c104b9dcc1244b15d3"','RUNTIME_AUTHORITY_COMMIT="694bdc8b03b93131b17d753c60f92bef21404e22"'),
 ('RUNTIME_ARTIFACT_ID="12695143651"; RUNTIME_ACTIONS_RUN="40415858178"','RUNTIME_ARTIFACT_ID="12705612602"; RUNTIME_ACTIONS_RUN="40439262910"'),
 ('RUNTIME_ARTIFACT_SHA="b83eb47da7da71fc75a82aa1bb562acb6169379e65ee483f60ee92702cb790da"','RUNTIME_ARTIFACT_SHA="41dda5bb2484f5f26f87856325a4d70aeafc227811b946e5ae9eae35f1f43497"'),
 ('RUNTIME_TAR_SHA="5cd951c92e7782bf12812cb5f6e9adb76aabd7255515512e5196e7688f2a3e87"','RUNTIME_TAR_SHA="ed756212e83d96ae0ad474c3ca84fd947bcabce4a5fbb45c7c2ed5a81b37d5a6"'),
 ('MECHANICS_GIT_BLOB="2a503622fd337a7355385fbf82706c4b089de777"','MECHANICS_GIT_BLOB="18ed8d5b0b78a1f3e6676c73f50346bdb503dc1c"'),
 ('ARTZIP="$WORK/26881_artifact.zip"; ARTDIR="$WORK/artifact_26881"','ARTZIP="$WORK/26882_artifact.zip"; ARTDIR="$WORK/artifact_26882"'),
 ('BASE="$WORK/exact_successful_26881_compiled_candidate"','BASE="$WORK/exact_successful_26882_compiled_candidate"'),
]:once(old,new)
TRIGGER='RUN_26883_SPEKTRA_FULL_FOV_1920_B_EARLY_WHITE_ON_OFF_V1'

# Inherit every historical source validator, replacing only current-version inputs.
def package(s):
 s=s.replace('[[ $(find handoff_payload_26883 -type f | wc -l) -eq 3 ]]','[[ $(find handoff_payload_26883 -type f | wc -l) -eq 4 ]]')
 s=s.replace('3-file exact runtime correction scope','4-file exact runtime correction scope')
 s=s.replace('RUN_26883_SPEKTRA_ROTATED_RAW_B_WHITE_OFF_V1',TRIGGER)
 # Existing 26882 validators must continue to test the EXACT SUCCESSFUL 26882
 # compiled universe, not the transformed 26883 one.
 s=s.replace('verify_26883_expanded_glsl.py regressions/26881_spektra_chroma_clip.py',
             'verify_26881_expanded_glsl.py regressions/26881_spektra_chroma_clip.py')
 s=s.replace('regressions/26881_actual_generator_artifact_identity.py build_26881_iris_rawr.sh',
             'regressions/26881_actual_generator_artifact_identity.py build_26881_iris_rawr.sh')
 # Old 26882 root verification is historical; the new stage root follows it.
 s=s.replace('stage_26883_root.py --verify-only','stage_26882_root.py --verify-only')
 s=s.replace('stage_26883_root.py\n','stage_26882_root.py\n')
 s=s.replace('verify_26883_candidate.py verify_26883_patches.py verify_26883_expanded_glsl.py verify_26883_semantics.py stage_26882_root.py',
             'verify_26882_candidate.py verify_26882_patches.py verify_26882_expanded_glsl.py verify_26882_semantics.py stage_26882_root.py')
 # New source checks are ADDITIVE to every inherited historical package check.
 s=s[:-2]+''' python3 -S -m py_compile verify_26883_candidate.py verify_26883_patches.py verify_26883_expanded_glsl.py verify_26883_semantics.py regressions/26883_successor_contract.py stage_26883_root.py
 python3 -S regressions/26883_successor_contract.py
 python3 -S stage_26883_root.py
'''+ '\n}'
 return s
edit('verify_package',package)

def scope(s):
 s=s.replace('generate_26881_build.py','generate_26882_build.py').replace('build_26881_iris_rawr.sh','build_26882_iris_rawr.sh')
 s=s.replace('8e9d44d66e4c955c105d136a1c380206ae93b671b9e57806412c2c991a791fc5',PARENT)
 return s
edit('verify_scope',scope)

def authority(s):
 s=s.replace('26881','26882')
 s=s.replace("x['head_sha']=='c28269f36b5754bded0623c104b9dcc1244b15d3'", "x['head_sha']=='694bdc8b03b93131b17d753c60f92bef21404e22'")
 s=s.replace("'id':12695143651", "'id':12705612602")
 s=s.replace("'name':'photon-26882-spektra-fov-b-halo-clipped-highlights'", "'name':'photon-26882-spektra-orientation-b-white-off'")
 s=s.replace('sha256:b83eb47da7da71fc75a82aa1bb562acb6169379e65ee483f60ee92702cb790da', 'sha256:41dda5bb2484f5f26f87856325a4d70aeafc227811b946e5ae9eae35f1f43497')
 s=s.replace('mechanics_generated_script_sha256=8e9d44d66e4c955c105d136a1c380206ae93b671b9e57806412c2c991a791fc5', 'mechanics_generated_script_sha256='+PARENT)
 assert '12705612602' in s and 'photon-26882-spektra-orientation-b-white-off' in s, s[:2600]
 return s
edit('obtain_authority',authority)

def candidate(s):
 # Step backward through actual 26882 -> 26881 compiled source BEFORE any
 # historical 26881/26880 tests; the 26883 candidate remains authority-seeded.
 mark=' local H80="$WORK/historical_26880_from_26881"';assert mark in s
 intro=''' local H81="$WORK/historical_26881_from_26882"
 cp -a "$BASE" "$H81";git -C "$H81" init -q
 (cd "$H81" && git apply --check --reverse "$ROOT/26882_FORWARD_FULL_INDEX.patch" &&
  git apply --reverse "$ROOT/26882_FORWARD_FULL_INDEX.patch" &&
  sha256sum -c "$ROOT/26882_BASE_26881_FULL_APP.sha256" >/dev/null) || fail 'real successful 26882->26881 compiled candidate rollback failed'
'''
 s=s.replace(mark,intro+mark,1)
 s=s.replace('cp -a "$BASE" "$H80"','cp -a "$H81" "$H80"',1)
 s=s.replace('regressions/26881_spektra_chroma_clip.py "$H80" "$BASE"','regressions/26881_spektra_chroma_clip.py "$H80" "$H81"')
 s=s.replace('verify_26881_expanded_glsl.py "$BASE"','verify_26881_expanded_glsl.py "$H81"')
 s=s.replace('verify_26883_semantics.py "$BASE" "$CAND"','verify_26882_semantics.py "$H81" "$BASE"')
 s=s.replace('verify_26883_expanded_glsl.py "$CAND" --out "$OUT/26883_current_white_source_preflight"','verify_26882_expanded_glsl.py "$BASE" --out "$OUT/26883_successful_26882_white_preflight"')
 return s[:-2]+''' python3 -S verify_26882_candidate.py "$H81" "$BASE"
 python3 -S verify_26883_semantics.py "$BASE" "$CAND"
 python3 -S verify_26883_expanded_glsl.py "$CAND" --out "$OUT/26883_current_shared_white_preflight"
'''+ '\n}'
edit('make_candidate',candidate)

def mechanics(s):
 s=s.replace('build_26881_iris_rawr.sh','build_26882_iris_rawr.sh').replace('generate_26881_build.py','generate_26882_build.py')
 s=s.replace('8e9d44d66e4c955c105d136a1c380206ae93b671b9e57806412c2c991a791fc5',PARENT)
 return s
edit('verify_successful_mechanics',mechanics)

def shaders(s):
 # 26882 shader validator must stay attached to exact compiled 26882 bytes;
 # the new 26883 owner gets its own expanded reserved/real compiler gate.
 s=s.replace('verify_26883_expanded_glsl.py "$CAND"','verify_26882_expanded_glsl.py "$BASE"')
 s=s.replace('verify_26881_expanded_glsl.py "$BASE"','verify_26881_expanded_glsl.py "$WORK/historical_26881_from_26882"')
 s=s.replace('PASS 26882 modified runtime-expanded GLES300', 'PASS 26882 modified runtime-expanded GLES300')
 # Historical output has new 26883 logfile paths, but historical validator is 26882.
 return s[:-2]+''' python3 -S verify_26883_expanded_glsl.py "$CAND" --compiler "$IRIS26864_GLSLANG" --out "$OUT/26883_real_shared_white" | tee "$OUT/26883_shared_white_pinned_glsl.txt"
 grep -F 'pinned-glslang=PASS' "$OUT/26883_shared_white_pinned_glsl.txt" >/dev/null || fail '26883 modified expanded shared HDRq/Wronski B highlight shader not compiled by pinned real glslang'
'''+ '\n}'
edit('compile_modified_runtime_shaders',shaders)

def patch_stage(s):
 return s.replace('3-file full-index binary','4-file full-index binary')
edit('verify_candidate_patches',patch_stage)

def safety(s):
 s=s.replace('runtime_authority=successful 26881','runtime_authority=successful 26882')
 s=s.replace('verification_mechanics=exact successful 26881 inherited','verification_mechanics=exact successful 26882 inherited')
 line=next((x for x in s.splitlines() if x.startswith('runtime_changed_files=')),None)
 assert line
 s=s.replace(line,'runtime_changed_files=4 (3 localized owners + version); Spektra uncropped 1920x1440 GPU preview, shared HDRq/Wronski B early smooth-white with pre-Lab RGB evidence and unchanged binary mask; 0 additions/deletions; native/vendor/DNG unchanged')
 line=next((x for x in s.splitlines() if x.startswith('protected_source=')),None)
 assert line
 s=s.replace(line,'protected_source=2005 files byte-identical to successful 26882 compiled candidate; DNG/native/vendor/Experiment A/Motion/Night/LONG protected')
 s=s.replace('runtime_changed_files=3','runtime_changed_files=4')
 return s
edit('prebuild_safety',safety)

def replay(s):
 # Inherit unchanged historical validators, each against the correct earlier
 # compiled source, and separately rerun current source and compiler receipts.
 s=s.replace('regressions/26881_spektra_chroma_clip.py "$WORK/historical_26880_from_26881" "$BASE"',
             'regressions/26881_spektra_chroma_clip.py "$WORK/historical_26880_from_26881" "$WORK/historical_26881_from_26882"')
 s=s.replace('verify_26881_expanded_glsl.py "$BASE"', 'verify_26881_expanded_glsl.py "$WORK/historical_26881_from_26882"')
 # Prior 26882 validator must use successful 26881 versus 26882.
 s=s.replace('verify_26883_semantics.py "$BASE" "$exp"',
             'verify_26882_semantics.py "$WORK/historical_26881_from_26882" "$BASE"')
 s=s.replace('verify_26883_expanded_glsl.py "$exp"', 'verify_26882_expanded_glsl.py "$BASE"')
 return s[:-2]+''' python3 -S verify_26882_candidate.py "$WORK/historical_26881_from_26882" "$BASE"
 python3 -S verify_26883_semantics.py "$BASE" "$exp"
 python3 -S verify_26883_expanded_glsl.py "$exp" --out "$OUT/26883_final_shared_white_expanded_source"
'''+ '\n}'
edit('clean_extract_replay',replay)

STAGES=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','verify_candidate_patches','prebuild_safety','assemble','postbuild_proof','clean_extract_replay']
fn=lambda s:[m.group(1) for m in re.finditer(r'\n([a-z_]+)\(\)\{',s)]
assert fn(body)==fn(prior) and [x for x in fn(body) if x in STAGES]==STAGES
# UNMODIFIED compiler, freeze, native, and full assembly stages, except release
# version naming and inherited script-output identifiers.
for name in ['prepare_glslang','compile_spektra_raw_shader','snapshot_live_authority_seeded','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','assemble','postbuild_proof']:
 def stage(s,n):
  a=s.index('\n'+n+'(){')+1;b=s.index('\n}',a)+2;return s[a:b]
 assert stage(body,name)==stage(prior.replace('26882','26883').replace('0.9726882','0.9726883'),name),name
for cmd in ['./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'./gradlew :app:assembleDebug --stacktrace']:
 assert cmd in prior and cmd in body,cmd
assert 'GLSLANG_VERSION="16.5.0"' in body and 'PRE-BUILD SAFETY PROOF PASSED' in body and 'snapshot_live_authority_seeded' in body
assert 'regressions/26877_superres_ownership.py' not in body
(P/'build_26883_iris_rawr.sh').write_text(body)
(P/'26883_BUILD_INFRASTRUCTURE_DIFF.txt').write_text(''.join(difflib.unified_diff(prior.splitlines(True),body.splitlines(True),fromfile='SHA_PINNED_EXACT_SUCCESSFUL_26882_17_STAGE',tofile='26883_INHERITED_17_STAGE')))
(P/'26883_GENERATED_BUILD_SHA256.txt').write_text(hashlib.sha256(body.encode()).hexdigest()+'  build_26883_iris_rawr.sh\n')
print('PASS 26883 exact 26882 inherited 17 stages and compiler/freeze/assembly commands; generated SHA-256',hashlib.sha256(body.encode()).hexdigest())
