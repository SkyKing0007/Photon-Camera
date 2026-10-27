#!/usr/bin/env python3
"""26884 successor of EXACT successful 26883 compiled 17-stage runner.
All proven compiler, freeze, native/NDK, full assemble and post-build mechanics
remain unchanged (except versioned identifiers). Current shader is the fused
pre-Lab RAWR Highlight Reconstruction OFF owner shared by native HDRq/Wronski.
Historical validators replay only against their own successful artifacts.
"""
from pathlib import Path
import hashlib,re,difflib,sys
P=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path('.').resolve()
prior=(P/'build_26883_iris_rawr.sh').read_text()
PARENT='7799509f64c7f84c2223f7014dac925b2f6f31ed96667d754d0b1c0df29e979f'
assert hashlib.sha256(prior.encode()).hexdigest()==PARENT,'not exact successful 26883 17-stage runner'
body=prior.replace('26883','26884').replace('0.9726883','0.9726884')
def edit(stage,fn):
 global body
 a=body.index('\n'+stage+'(){')+1;b=body.index('\n}',a)+2
 before=body[a:b];after=fn(before)
 assert before!=after,('stage no-op',stage)
 assert after.rstrip().endswith('}'),('broken stage terminator',stage)
 body=body[:a]+after+body[b:]
def once(before,after):
 global body
 assert body.count(before)==1,(before,body.count(before))
 body=body.replace(before,after,1)
for old,new in [
 ('REPO_SCAFFOLD_BASE_COMMIT="694bdc8b03b93131b17d753c60f92bef21404e22"','REPO_SCAFFOLD_BASE_COMMIT="28823b94be2cc636983f01a99dfc2f0840f5a05b"'),
 ('RUNTIME_AUTHORITY_COMMIT="694bdc8b03b93131b17d753c60f92bef21404e22"','RUNTIME_AUTHORITY_COMMIT="28823b94be2cc636983f01a99dfc2f0840f5a05b"'),
 ('RUNTIME_ARTIFACT_ID="12705612602"; RUNTIME_ACTIONS_RUN="40439262910"','RUNTIME_ARTIFACT_ID="12734144623"; RUNTIME_ACTIONS_RUN="40505011172"'),
 ('RUNTIME_ARTIFACT_SHA="41dda5bb2484f5f26f87856325a4d70aeafc227811b946e5ae9eae35f1f43497"','RUNTIME_ARTIFACT_SHA="e1ffb9c7c826d5504d39b496134aeea141a4b8e2661f30496ecbacc3ff997071"'),
 ('RUNTIME_TAR_SHA="ed756212e83d96ae0ad474c3ca84fd947bcabce4a5fbb45c7c2ed5a81b37d5a6"','RUNTIME_TAR_SHA="729c9ad909c3444bec1028e17a4a4803b1ebda3fe73d0c541b466b825a93e1f7"'),
 ('MECHANICS_GIT_BLOB="18ed8d5b0b78a1f3e6676c73f50346bdb503dc1c"','MECHANICS_GIT_BLOB="2db9740d5fbe7baa0d7054c1132f158cbfbfb499"'),
 ('ARTZIP="$WORK/26882_artifact.zip"; ARTDIR="$WORK/artifact_26882"','ARTZIP="$WORK/26883_artifact.zip"; ARTDIR="$WORK/artifact_26883"'),
 ('BASE="$WORK/exact_successful_26882_compiled_candidate"','BASE="$WORK/exact_successful_26883_compiled_candidate"'),
]:once(old,new)
TRIGGER='RUN_26884_RAWR_HIGHLIGHT_OFF_SHARED_B_V1'
def package(s):
 # Pure inherited history remains 26883's successful validation; it must not
 # be renamed as though 26883 had tested the new 26884 compiled candidate.
 s=s.replace('[[ $(find handoff_payload_26884 -type f | wc -l) -eq 4 ]]','[[ $(find handoff_payload_26884 -type f | wc -l) -eq 3 ]]')
 s=s.replace('4-file exact runtime correction scope','3-file exact B-only runtime correction scope')
 s=s.replace('RUN_26884_SPEKTRA_FULL_FOV_1920_B_EARLY_WHITE_ON_OFF_V1',TRIGGER)
 s=s.replace('verify_26884_candidate.py verify_26884_patches.py verify_26884_expanded_glsl.py verify_26884_semantics.py regressions/26884_successor_contract.py stage_26884_root.py',
             'verify_26883_candidate.py verify_26883_patches.py verify_26883_expanded_glsl.py verify_26883_semantics.py regressions/26883_successor_contract.py stage_26883_root.py')
 s=s.replace('python3 -S regressions/26884_successor_contract.py','python3 -S regressions/26883_successor_contract.py')
 s=s.replace('python3 -S stage_26884_root.py\n','python3 -S stage_26883_root.py\n')
 s=s[:-2]+''' python3 -S -m py_compile verify_26884_candidate.py verify_26884_patches.py verify_26884_expanded_glsl.py verify_26884_semantics.py regressions/26884_successor_contract.py regressions/26884_rawr_off_math.py stage_26884_root.py
 python3 -S regressions/26884_successor_contract.py
 python3 -S stage_26884_root.py
'''+ '\n}'
 return s
edit('verify_package',package)
def scope(s):
 return s.replace('generate_26882_build.py','generate_26883_build.py').replace('build_26882_iris_rawr.sh','build_26883_iris_rawr.sh').replace('8bbdf3738e8a8b17f236db6c43f8273b2a24e164b847963aa9c749da7707251c',PARENT)
edit('verify_scope',scope)
def authority(s):
 # Only last successful artifact IDs are updated; historical version names
 # inside older local-source validation are unaffected.
 s=s.replace('26882','26883')
 s=s.replace("x['head_sha']=='694bdc8b03b93131b17d753c60f92bef21404e22'", "x['head_sha']=='28823b94be2cc636983f01a99dfc2f0840f5a05b'")
 s=s.replace("'id':12705612602","'id':12734144623")
 s=s.replace("'name':'photon-26883-spektra-orientation-b-white-off'", "'name':'photon-26883-spektra-full-fov-b-early-white-both'")
 s=s.replace('sha256:41dda5bb2484f5f26f87856325a4d70aeafc227811b946e5ae9eae35f1f43497','sha256:e1ffb9c7c826d5504d39b496134aeea141a4b8e2661f30496ecbacc3ff997071')
 s=s.replace('mechanics_generated_script_sha256=8bbdf3738e8a8b17f236db6c43f8273b2a24e164b847963aa9c749da7707251c','mechanics_generated_script_sha256='+PARENT)
 assert '12734144623' in s and 'photon-26883-spektra-full-fov-b-early-white-both' in s
 return s
edit('obtain_authority',authority)
def candidate(s):
 marker=' local H81="$WORK/historical_26881_from_26882"';assert s.count(marker)==1
 intro=''' local H82="$WORK/historical_26882_from_26883"
 cp -a "$BASE" "$H82";git -C "$H82" init -q
 (cd "$H82" && git apply --check --reverse "$ROOT/26883_FORWARD_FULL_INDEX.patch" &&
  git apply --reverse "$ROOT/26883_FORWARD_FULL_INDEX.patch" &&
  sha256sum -c "$ROOT/26883_BASE_26882_FULL_APP.sha256" >/dev/null) || fail '26883->26882 REAL successful compiled candidate rollback failed'
'''
 s=s.replace(marker,intro+marker,1)
 s=s.replace('cp -a "$BASE" "$H81"','cp -a "$H82" "$H81"',1)
 s=s.replace('verify_26882_semantics.py "$H81" "$BASE"','verify_26882_semantics.py "$H81" "$H82"')
 s=s.replace('verify_26882_expanded_glsl.py "$BASE"','verify_26882_expanded_glsl.py "$H82"')
 s=s.replace('verify_26882_candidate.py "$H81" "$BASE"','verify_26882_candidate.py "$H81" "$H82"')
 # Current shared B source and preserved prior white are different owners.
 s=s.replace('verify_26884_semantics.py "$BASE" "$CAND"','verify_26883_semantics.py "$H82" "$BASE"')
 s=s.replace('verify_26884_expanded_glsl.py "$CAND" --out "$OUT/26884_current_shared_white_preflight"',
             'verify_26883_expanded_glsl.py "$BASE" --out "$OUT/26884_prior_shared_white_preflight"')
 return s[:-2]+''' python3 -S verify_26883_candidate.py "$H82" "$BASE"
 python3 -S verify_26884_semantics.py "$BASE" "$CAND"
 python3 -S regressions/26884_rawr_off_math.py "$CAND"
 python3 -S verify_26884_expanded_glsl.py "$CAND" --out "$OUT/26884_current_rawr_off_source_preflight"
'''+ '\n}'
edit('make_candidate',candidate)
def mechanics(s):
 return s.replace('build_26882_iris_rawr.sh','build_26883_iris_rawr.sh').replace('generate_26882_build.py','generate_26883_build.py').replace('8bbdf3738e8a8b17f236db6c43f8273b2a24e164b847963aa9c749da7707251c',PARENT)
edit('verify_successful_mechanics',mechanics)
def shaders(s):
 # The original 26883 smooth-white compiler proof runs against the EXACT
 # successful 26883 source, not the changed 26884 native B domain.
 s=s.replace('verify_26882_expanded_glsl.py "$BASE"','verify_26882_expanded_glsl.py "$WORK/historical_26882_from_26883"')
 s=s.replace('verify_26884_expanded_glsl.py "$CAND" --compiler', 'verify_26883_expanded_glsl.py "$BASE" --compiler')
 return s[:-2]+''' python3 -S verify_26884_expanded_glsl.py "$CAND" --compiler "$IRIS26864_GLSLANG" --out "$OUT/26884_real_rawr_off_fused_wb" | tee "$OUT/26884_rawr_off_pinned_glsl.txt"
 grep -F 'pinned-glslang=PASS' "$OUT/26884_rawr_off_pinned_glsl.txt" >/dev/null || fail '26884 original RAWR OFF fused WB GLSL not compiled by pinned real glslang'
'''+ '\n}'
edit('compile_modified_runtime_shaders',shaders)
def patch(s):return s.replace('4-file full-index binary','3-file full-index binary').replace('4-file','3-file')
edit('verify_candidate_patches',patch)
def safety(s):
 s=s.replace('runtime_authority=successful 26882','runtime_authority=successful 26883')
 s=s.replace('verification_mechanics=exact successful 26882 inherited','verification_mechanics=exact successful 26883 inherited')
 line=next((t for t in s.splitlines() if t.startswith('runtime_changed_files=')),None);assert line
 s=s.replace(line,'runtime_changed_files=3 (2 shared Experiment B POST-AMaZE owners + version); exact RAWR OFF fused WB shared ceiling before Lab/FCC; no Spektra change; 0 source additions/deletions; native/vendor/DNG unchanged')
 line=next((t for t in s.splitlines() if t.startswith('protected_source=')),None);assert line
 s=s.replace(line,'protected_source=2006 files byte-identical to successful 26883 compiled candidate; Spektra/DNG/native/vendor/Experiment A/Motion/Night/LONG preserved')
 return s
edit('prebuild_safety',safety)
def replay(s):
 s=s.replace('verify_26882_semantics.py "$WORK/historical_26881_from_26882" "$BASE"',
             'verify_26882_semantics.py "$WORK/historical_26881_from_26882" "$WORK/historical_26882_from_26883"')
 s=s.replace('verify_26882_expanded_glsl.py "$BASE"', 'verify_26882_expanded_glsl.py "$WORK/historical_26882_from_26883"')
 s=s.replace('verify_26882_candidate.py "$WORK/historical_26881_from_26882" "$BASE"',
             'verify_26882_candidate.py "$WORK/historical_26881_from_26882" "$WORK/historical_26882_from_26883"')
 s=s.replace('verify_26884_semantics.py "$BASE" "$exp"','verify_26883_semantics.py "$WORK/historical_26882_from_26883" "$BASE"')
 s=s.replace('verify_26884_expanded_glsl.py "$exp"','verify_26883_expanded_glsl.py "$BASE"')
 return s[:-2]+''' python3 -S verify_26883_candidate.py "$WORK/historical_26882_from_26883" "$BASE"
 python3 -S verify_26884_semantics.py "$BASE" "$exp"
 python3 -S regressions/26884_rawr_off_math.py "$exp"
 python3 -S verify_26884_expanded_glsl.py "$exp" --out "$OUT/26884_final_rawr_off_fused_wb_source"
'''+ '\n}'
edit('clean_extract_replay',replay)
STAGES=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','verify_candidate_patches','prebuild_safety','assemble','postbuild_proof','clean_extract_replay']
fn=lambda s:[m.group(1) for m in re.finditer(r'\n([a-z_]+)\(\)\{',s)]
assert fn(body)==fn(prior) and [x for x in fn(body) if x in STAGES]==STAGES
for name in ('prepare_glslang','compile_spektra_raw_shader','snapshot_live_authority_seeded','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','assemble','postbuild_proof'):
 def stage(s,n):
  a=s.index('\n'+n+'(){')+1;b=s.index('\n}',a)+2;return s[a:b]
 assert stage(body,name)==stage(prior.replace('26883','26884').replace('0.9726883','0.9726884'),name),name
for cmd in ('./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'./gradlew :app:assembleDebug --stacktrace'):
 assert cmd in prior and cmd in body,cmd
assert 'GLSLANG_VERSION="16.5.0"' in body and 'PRE-BUILD SAFETY PROOF PASSED' in body
assert 'snapshot_live_authority_seeded' in body and 'regressions/26877_superres_ownership.py' not in body
(P/'build_26884_iris_rawr.sh').write_text(body)
(P/'26884_BUILD_INFRASTRUCTURE_DIFF.txt').write_text(''.join(difflib.unified_diff(prior.splitlines(True),body.splitlines(True),fromfile='SHA_PINNED_SUCCESSFUL_26883_17_STAGE',tofile='26884_INHERITED_17_STAGE')))
(P/'26884_GENERATED_BUILD_SHA256.txt').write_text(hashlib.sha256(body.encode()).hexdigest()+'  build_26884_iris_rawr.sh\n')
print('PASS 26884 exact successful 26883 17-stage ordering, freeze/compiler/NDK/assemble commands; runner SHA-256',hashlib.sha256(body.encode()).hexdigest())
