#!/usr/bin/env python3
"""26889 strict successor of ACTUAL SUCCESSFUL 26888 guarded 17-stage runner."""
from pathlib import Path
import hashlib,re,sys
R=(Path(sys.argv[1]) if len(sys.argv)>1 else Path('.')).resolve()
parent=R/'build_26888_iris_rawr.sh'
assert parent.is_file(),'actual executed 26888 runner must be generated first'
assert hashlib.sha256(parent.read_bytes()).hexdigest()=='5e9bc28287ba38099390b9cad99168c314e3058473e9924137aaf2f02d7f4753','26888 verified runner SHA mismatch'
original=parent.read_text();body=original
STAGES=('verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','verify_candidate_patches','prebuild_safety','assemble','postbuild_proof','clean_extract_replay')
regex=re.compile(r'\n([a-z_]+)\(\)\{')
assert tuple(n for n in regex.findall(body) if n in STAGES)==STAGES

def stage(s,n):
 a=s.index('\n'+n+'(){')+1;b=s.index('\n}',a)+2
 return s[a:b]
def edit(n,fn):
 global body
 old=stage(body,n);new=fn(old)
 assert new.startswith(n+'(){') and new.endswith('}') and new!=old
 body=body.replace(old,new,1)
def append(s,addition):
 assert s.endswith('\n}')
 return s[:-2]+'\n'+addition.strip('\n')+'\n}'
def once(a,b):
 global body
 assert body.count(a)==1,(a,body.count(a))
 body=body.replace(a,b,1)

# Identity and real successful authority, untouched historical 17-stage order.
for a,b in (
 ('# Successful 26887 V4 Actions compiled candidate is runtime authority.', '# Successful 26888 Actions compiled candidate is runtime authority.'),
 ('REPO_SCAFFOLD_BASE_COMMIT="de478c5c3ce85de56ac74be3cbd885c128ebd833"','REPO_SCAFFOLD_BASE_COMMIT="762f5531def4a880d46e144a0e204eebb5ad1d28"'),
 ('RUNTIME_ARTIFACT_ID="12870194123"; RUNTIME_ACTIONS_RUN="40810858529"','RUNTIME_ARTIFACT_ID="12933881423"; RUNTIME_ACTIONS_RUN="40954102038"'),
 ('RUNTIME_AUTHORITY_COMMIT="de478c5c3ce85de56ac74be3cbd885c128ebd833"','RUNTIME_AUTHORITY_COMMIT="762f5531def4a880d46e144a0e204eebb5ad1d28"'),
 ('RUNTIME_ARTIFACT_SHA="70d2ac2780485a5d845fcca02f0cb7c20a7c262249432b633100d4f369365d41"','RUNTIME_ARTIFACT_SHA="68b368663476be9369e72fc305cbdd571d18e7e1b9df3afb0666859be1400d73"'),
 ('RUNTIME_TAR_SHA="864312c1fa31b03cf0dd208014f35e8749cbeb21de7be64278c683a69acc8912"','RUNTIME_TAR_SHA="22f0679109f38c2ec749b1e403dede337464eecfe3049620f445a73881171bfb"'),
 ('VERSION_NAME="0.9726888"; VERSION_BUILD="26888"','VERSION_NAME="0.9726889"; VERSION_BUILD="26889"'),
 ('OUT="$ROOT/build_26888_iris_rawr_outputs"; WORK="$ROOT/.build_26888_iris_rawr_work"','OUT="$ROOT/build_26889_iris_rawr_outputs"; WORK="$ROOT/.build_26889_iris_rawr_work"'),
 ('ARTZIP="$WORK/26887_artifact.zip"; ARTDIR="$WORK/artifact_26887"','ARTZIP="$WORK/26888_artifact.zip"; ARTDIR="$WORK/artifact_26888"'),
 ('BASE="$WORK/exact_successful_26887_compiled_candidate"; CAND="$WORK/candidate_26888"','BASE="$WORK/exact_successful_26888_compiled_candidate"; CAND="$WORK/candidate_26889"'),
 ('# IRIS_26888_AUTHORITATIVE_ACTIONS_STAGE_ORDER','# IRIS_26889_AUTHORITATIVE_ACTIONS_STAGE_ORDER'),
):once(a,b)
body=body.replace('$OUT/26888_COMPILER_STATUS.txt','$OUT/26889_COMPILER_STATUS.txt')
# Exact package stage remains and its entire historical contents execute first.
edit('verify_package',lambda s:append(s,'''
 test -f TRIGGER_26889.txt && grep -Fx 'RUN_26889_B_OFF_SHUTTER_ADJACENT_MOTION_LONG_V1' TRIGGER_26889.txt >/dev/null || fail 'immutable 26889 trigger changed'
 python3 -S stage_26889_root.py
 sha256sum -c 26889_HANDOFF_HASHES.sha256 >/dev/null || fail '26889 sealed staged bytes tampered'
 python3 -S -m py_compile generate_26889_build.py verify_26889_candidate.py verify_26889_semantics.py verify_26889_patches.py verify_26889_expanded_glsl.py stage_26889_root.py test_26889_negative_tamper.py verify_26889_compiled_push_abi.py
 (cd "$ROOT" && test "$(find handoff_payload_26889 -type f | wc -l)" -eq 10) || fail '26889 9 modified + 1 new B-OFF source scope drift'
'''))
edit('verify_scope',lambda s:'''verify_scope(){
 [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail 'wrong branch'
 git merge-base --is-ancestor "$RUNTIME_AUTHORITY_COMMIT" HEAD || fail 'successful 26888 authority not ancestor'
 [[ -z "$(git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD -- app/src app/version.properties)" ]] || fail 'unintended committed live source delta'
 [[ -z "$(git status --porcelain -- app/src app/version.properties)" ]] || fail 'uncommitted app source delta'
 diff -u 26889_REPOSITORY_UPLOAD_ALLOWLIST.txt <(git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD | LC_ALL=C sort) >/dev/null || fail 'unexpected repository infrastructure changed paths'
 [[ "$(sha build_26888_iris_rawr.sh)" == '5e9bc28287ba38099390b9cad99168c314e3058473e9924137aaf2f02d7f4753' ]] || fail 'actual successful 26888 runner mismatch'
 [[ "$(git rev-parse "$RUNTIME_AUTHORITY_COMMIT:generate_26888_build.py")" == '35f5739773be225b1ce0c6626cdc719f8bd537b8' ]] || fail 'actual successful 26888 generator Git blob mismatch'
 pass '26889 strict repository scope and successful 26888 generated-runner identity'
}''')
edit('obtain_authority',lambda s:'''obtain_authority(){
 [[ -n "$TOKEN" ]] || fail 'GITHUB_TOKEN missing'
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' \\
   "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/runs/${RUNTIME_ACTIONS_RUN}" -o "$WORK/26888_run.json"
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' \\
   "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${RUNTIME_ARTIFACT_ID}" -o "$WORK/26888_artifact_metadata.json"
 python3 -S - "$WORK/26888_run.json" "$WORK/26888_artifact_metadata.json" <<'PY_AUTH_89'
import json,sys
run=json.load(open(sys.argv[1]));art=json.load(open(sys.argv[2]))
assert run['id']==40954102038 and run['conclusion']=='success' and run['head_sha']=='762f5531def4a880d46e144a0e204eebb5ad1d28' and run['head_branch']=='experimental-clean-photon-rebuild'
assert art['id']==12933881423 and art.get('expired') is False and art.get('digest')=='sha256:68b368663476be9369e72fc305cbdd571d18e7e1b9df3afb0666859be1400d73'
print('PASS exact successful 26888 run and artifact')
PY_AUTH_89
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' \\
  "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${RUNTIME_ARTIFACT_ID}/zip" -o "$ARTZIP"
 [[ "$(sha "$ARTZIP")" == "$RUNTIME_ARTIFACT_SHA" ]] || fail '26888 archive drift'
 unzip -q "$ARTZIP" -d "$ARTDIR"
 local T="$ARTDIR/build_26888_iris_rawr_outputs/26888_candidate_app_source.tar.gz"
 [[ -f "$T" && "$(sha "$T")" == "$RUNTIME_TAR_SHA" ]] || fail '26888 exact compiled TAR drift'
 local EXEC="$ARTDIR/build_26888_iris_rawr_outputs/exact_generated_runner/build_26888_iris_rawr.sh"
 [[ -f "$EXEC" && "$(sha "$EXEC")" == '5e9bc28287ba38099390b9cad99168c314e3058473e9924137aaf2f02d7f4753' ]] || fail 'actual executed 26888 runner archive mismatch'
 cmp -s "$EXEC" "$ROOT/build_26888_iris_rawr.sh" || fail 'generated 26888 runner not identical to executed 26888 Actions runner'
 local CS="$ARTDIR/build_26888_iris_rawr_outputs/26888_COMPILER_STATUS.txt"
 for k in 'REAL GLSL COMPILE: PASS' 'REAL SPIR-V VALIDATION: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS';do
  grep -F "$k" "$CS" >/dev/null || fail "26888 successful real compiler receipt missing: $k"
 done
 mkdir -p "$BASE";tar -xzf "$T" -C "$BASE"
 [[ "$(find "$BASE/app" -type f | wc -l)" -eq 2024 ]] || fail 'exact 26888 compiled file count drift'
 (cd "$BASE" && sha256sum -c "$ROOT/26889_BASE_FULL_APP.sha256" >/dev/null) || fail '26888 manifest mismatch'
 cmp -s "$ARTDIR/build_26888_iris_rawr_outputs/26888_candidate_full_app.sha256" "$ROOT/26889_BASE_FULL_APP.sha256" || fail '26888 original compiler manifest differs'
 pass 'actual successful 26888 compiled TAR 2024/2024, runner and real compiler receipts'
}''')
# Preserve ENTIRE original 26888 successful historical replay mechanism byte-exact.
original_make=stage(body,'make_candidate')
body=body.replace(original_make,original_make.replace('make_candidate(){','historical_26888_make_candidate(){',1),1)
insert='''\nmake_candidate(){
 local H87="$WORK/historical_26887_from_26888" H88="$WORK/historical_26888_replayed"
 cp -a "$BASE" "$H87"; git -C "$H87" init -q
 (cd "$H87" && git apply --check --reverse "$ROOT/26888_FORWARD_FULL_INDEX.patch" && \\
  git apply --reverse "$ROOT/26888_FORWARD_FULL_INDEX.patch" && \\
  sha256sum -c "$ROOT/26888_BASE_26887_FULL_APP.sha256" >/dev/null) || fail '26888 exact original source rollback failed'
 ( local BASE="$H87" CAND="$H88"; historical_26888_make_candidate )
 diff -qr "$H88/app" "$BASE/app" >/dev/null || fail 'original 26888 successful historical generated candidate mismatches actual compiled source'
 python3 -S verify_26888_candidate.py "$H87" "$BASE"
 python3 -S verify_26888_semantics.py "$H87" "$BASE"
 python3 -S verify_26888_patches.py "$H87" "$BASE" 26888_FORWARD_FULL_INDEX.patch 26888_ROLLBACK_FULL_INDEX.patch
 python3 -S verify_26889_candidate.py "$BASE" "$CAND" --transform
 python3 -S verify_26889_semantics.py "$BASE" "$CAND"
 python3 -S verify_26889_expanded_glsl.py "$CAND"
}
'''
body=body.replace('\nverify_successful_mechanics(){',insert+'\nverify_successful_mechanics(){',1)
assert tuple(n for n in regex.findall(body) if n in STAGES)==STAGES
edit('verify_successful_mechanics',lambda s:append(s,'''
 [[ "$(sha build_26888_iris_rawr.sh)" == '5e9bc28287ba38099390b9cad99168c314e3058473e9924137aaf2f02d7f4753' ]] || fail 'successful actual 26888 17-stage executable runner drift'
 python3 -S verify_26889_candidate.py "$BASE" "$CAND"
 python3 -S verify_26889_semantics.py "$BASE" "$CAND"
 python3 -S verify_26889_compiled_push_abi.py "$ARTDIR/build_26888_iris_rawr_outputs/26888_modified_shader_spirv/Iris26887BOffHdrqMerge_prod.spv" "$BASE" "$CAND"
'''))
def shaders(s):
 assert s.count('verify_26888_expanded_glsl.py "$CAND"')==1
 s=s.replace('verify_26888_expanded_glsl.py "$CAND"','verify_26888_expanded_glsl.py "$WORK/historical_26888_replayed"',1)
 # The original 26868 validator asserts exactly one original LONG shader
 # consumer, which is deliberately not true of the B-OFF-only 26889 addition.
 # Execute it on its own exact successful historical 26868 candidate.
 s=s.replace('verify_26868_runtime_shader.py "$CAND"','verify_26868_runtime_shader.py "$WORK/historical_26868_from_26870"')
 return append(s,'''
 python3 -S verify_26889_expanded_glsl.py "$CAND" --compiler "$IRIS26864_GLSLANG" --spirv-val "$(command -v spirv-val)" --spirv-opt "$(command -v spirv-opt)" --out "$OUT/26889_modified_shader_spirv" | tee "$OUT/26889_real_shader_compile_receipt.txt"
 test -s "$OUT/26889_modified_shader_spirv/26889_REAL_COMPILED_SHADER_SHA256.txt" || fail '26889 real compiled SPIR-V receipts missing'
 sed -i 's/REAL GLSL COMPILE: NOT RUN YET/REAL GLSL COMPILE: PASS/' "$OUT/26889_COMPILER_STATUS.txt"
 sed -i 's/REAL SPIR-V VALIDATION: NOT RUN YET/REAL SPIR-V VALIDATION: PASS/' "$OUT/26889_COMPILER_STATUS.txt"
''')
edit('compile_modified_runtime_shaders',shaders)
for name in ('compile_languages','compile_native'):
 edit(name,lambda s:s.replace('26888_gradle','26889_gradle'))
edit('verify_candidate_patches',lambda s:'''verify_candidate_patches(){
 python3 -S verify_26889_candidate.py "$BASE" "$CAND"
 python3 -S verify_26889_semantics.py "$BASE" "$CAND"
 python3 -S verify_26889_patches.py "$BASE" "$CAND" 26889_FORWARD_FULL_INDEX.patch 26889_ROLLBACK_FULL_INDEX.patch | tee "$OUT/26889_patch_validation.txt"
 python3 -S test_26889_negative_tamper.py "$BASE" "$CAND"
 pass 'exact 26889 10 source paths and 2015 protected, full-index forward/rollback 7/12/40 and negative tamper'
}''')
def safety(s):
 s=s.replace('26888_','26889_').replace('verify_26888_candidate.py','verify_26889_candidate.py').replace('2015 protected','2015 protected')
 s=s.replace('runtime_authority=successful 26887','runtime_authority=successful 26888').replace('prior_files=2020','prior_files=2024').replace('candidate_files=2024','candidate_files=2025').replace('9 (5 modified existing including version, 4 B-OFF private additions)','10 (9 modified existing including version, 1 B-OFF private addition)')
 s=s.replace('verification_mechanics=exact successful 26887 inherited 17 stages','verification_mechanics=exact successful 26888 inherited 17 stages')
 s=s.replace('infrastructure_delta=26888 strict successor','infrastructure_delta=26889 strict successor').replace('successful 26887 compiled candidate','successful 26888 compiled candidate')
 return s
edit('prebuild_safety',safety)
edit('assemble',lambda s:s.replace('26888_','26889_'))
edit('postbuild_proof',lambda s:s.replace('26888_','26889_').replace('verify_26888_candidate.py','verify_26889_candidate.py'))
def replay(s):
 s=s.replace('26888_HANDOFF_HASHES.sha256','26889_HANDOFF_HASHES.sha256').replace('26888_GENERATED_BUILD_SHA256.txt','26889_GENERATED_BUILD_SHA256.txt').replace('build_26888_iris_rawr.sh','build_26889_iris_rawr.sh')
 s=s.replace('verify_26888_candidate.py "$BASE" "$replay" --root "$ROOT" --transform','verify_26889_candidate.py "$BASE" "$replay" --transform')
 # Every application of the previous-successful 26888 validator to the CURRENT
 # 26889 candidate must use the new validator; other historic sources untouched.
 for what in ('verify_26888_candidate.py "$BASE" "$exp"','verify_26888_semantics.py "$BASE" "$exp"','verify_26888_expanded_glsl.py "$exp"','verify_26888_patches.py "$BASE" "$exp"'):
  new=what.replace('26888_','26889_')
  s=s.replace(what,new)
 s=s.replace('26888_candidate_app_source.tar.gz','26889_candidate_app_source.tar.gz').replace('26888_final_patch_replay.txt','26889_final_patch_replay.txt')
 s=s.replace('26888_FORWARD_FULL_INDEX.patch 26888_ROLLBACK_FULL_INDEX.patch','26889_FORWARD_FULL_INDEX.patch 26889_ROLLBACK_FULL_INDEX.patch')
 s=s.replace('26888_candidate_full_app.sha256','26889_candidate_full_app.sha256')
 # Historical 26868 source-domain validator is for the original shader's exact
 # trustedShadowGain call cardinality; the added 26889 private shader changes it.
 s=s.replace('verify_26868_runtime_shader.py "$exp"','verify_26868_runtime_shader.py "$WORK/historical_26868_from_26870"')
 s=s.replace('VERSION_NAME=0.9726888','VERSION_NAME=0.9726889').replace('VERSION_BUILD=26888','VERSION_BUILD=26889')
 s=s.replace('26888_COMPILER_STATUS.txt','26889_COMPILER_STATUS.txt')
 # Preserve historical 26888 tests on restored 26887/26888 universes.
 return append(s,'''
 python3 -S verify_26888_candidate.py "$WORK/historical_26887_from_26888" "$WORK/historical_26888_replayed"
 python3 -S verify_26888_semantics.py "$WORK/historical_26887_from_26888" "$WORK/historical_26888_replayed"
 python3 -S verify_26888_expanded_glsl.py "$WORK/historical_26888_replayed"
 python3 -S verify_26888_patches.py "$WORK/historical_26887_from_26888" "$WORK/historical_26888_replayed" 26888_FORWARD_FULL_INDEX.patch 26888_ROLLBACK_FULL_INDEX.patch
 python3 -S verify_26889_candidate.py "$BASE" "$exp"
 python3 -S verify_26889_semantics.py "$BASE" "$exp"
 python3 -S verify_26889_expanded_glsl.py "$exp"
 python3 -S verify_26889_patches.py "$BASE" "$exp" 26889_FORWARD_FULL_INDEX.patch 26889_ROLLBACK_FULL_INDEX.patch
''')
edit('clean_extract_replay',replay)
assert tuple(n for n in regex.findall(body) if n in STAGES)==STAGES
for cmd in ('./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'./gradlew :app:assembleDebug --stacktrace'):
 assert cmd in body,cmd
# Replace initial compiler status file path only, all historical stage commands remain literal.
body=body.replace('26888_COMPILER_STATUS.txt','26889_COMPILER_STATUS.txt')
# The 26888 archived parent compiler receipt path is historical identity;
# restore it after successor-wide compiler status substitutions.
body=body.replace('build_26888_iris_rawr_outputs/26889_COMPILER_STATUS.txt',
                  'build_26888_iris_rawr_outputs/26888_COMPILER_STATUS.txt')
# The new verifier has strict positional base/candidate operands and one
# optional --transform: prohibit inherited 26888 --root operands.
for name in ('CAND','exp'):
 body=body.replace('verify_26889_candidate.py "$BASE" "$'+name+'" --root "$ROOT"',
                   'verify_26889_candidate.py "$BASE" "$'+name+'"')
assert 'verify_26889_candidate.py "$BASE" "$CAND" --root' not in body
assert 'verify_26889_candidate.py "$BASE" "$exp" --root' not in body
dest=R/'build_26889_iris_rawr.sh';dest.write_text(body)
sha=hashlib.sha256(dest.read_bytes()).hexdigest()
(R/'26889_GENERATED_BUILD_SHA256.txt').write_text(f'{sha}  build_26889_iris_rawr.sh\n')
print('PASS generated exact 26888-derived guarded 17-stage 26889 runner SHA256',sha)
