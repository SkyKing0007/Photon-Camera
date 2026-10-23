#!/usr/bin/env python3
"""Derive 26871 guarded build from exact successful 26870 implementation.

The resulting stage ordering and real compiler commands are inherited unchanged.
Every method body that needs an authority/version/scope adaptation is enumerated.
This file MUST NOT alter repository app/src; it only creates the guarded script.
"""
from pathlib import Path
import hashlib,re,sys,difflib
repo=Path(sys.argv[1]) if len(sys.argv)>1 else Path('.')
root=(repo/'build_26870_iris_rawr.sh').resolve();dest=(repo/'build_26871_iris_rawr.sh').resolve()
source=root.read_bytes()
def git_blob(x):return hashlib.sha1(f'blob {len(x)}\0'.encode()+x).hexdigest()
assert git_blob(source)=='9d266c45e62ec3c8701acec6aaf1bf80b970a740','NOT exact successful 26870 mechanics source'
old=source.decode()
STAGES=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','verify_candidate_patches','prebuild_safety','assemble','postbuild_proof','clean_extract_replay']
# Shell functions use a whole-line declaration, and never a nested function declaration.
allmarks=list(re.finditer(r'(?m)^([a-z][a-z_0-9]*)\(\)\{',old))
stageindex=next(i for i,m in enumerate(allmarks) if m.group(1)=='verify_package')
marks=allmarks[stageindex:]
pre=old[:marks[0].start()]
trailer=old[marks[-1].start():]
# The last function terminates before the known exact 17-call sequence.
end_marker='\nverify_package\nverify_scope\nobtain_authority\nmake_candidate\nverify_successful_mechanics\n'
assert old.count(end_marker)==1
end=old.index(end_marker)
methods={}
for i,m in enumerate(marks):
 after=marks[i+1].start() if i+1<len(marks) else end
 methods[m.group(1)]=old[m.start():after]
assert set(STAGES).issubset(methods)
assert old[end:].count('\nverify_package\n')==1
# Simple filename and label migration, not a procedural change.
def rename_outputs(body):
 return body.replace('26870_', '26871_').replace('build_26870', 'build_26871')
# Prior authority changes are explicit, not a blind 26870->26871 replacement.
pre=pre.replace('''# Exact most recent successful repo scaffolding HEAD is 26869, but its device
# runtime failed. Rebuild source INTENTIONALLY from successful 26868 artifact.
''','''# Successful 26870 Actions compiled candidate is runtime authority.
# Keep successful 26870 17-stage verification mechanics unchanged by default.
''')
pre=re.sub(r'^REPO_SCAFFOLD_BASE_COMMIT=.*$', 'REPO_SCAFFOLD_BASE_COMMIT="5e567577a06053a1feb2a94bd40681c2731ce554"',pre,flags=re.M)
pre=re.sub(r'^RUNTIME_ARTIFACT_ID=.*$', 'RUNTIME_ARTIFACT_ID="12502775416"; RUNTIME_ACTIONS_RUN="39954786811"',pre,flags=re.M)
pre=re.sub(r'^RUNTIME_AUTHORITY_COMMIT=.*$', 'RUNTIME_AUTHORITY_COMMIT="5e567577a06053a1feb2a94bd40681c2731ce554"',pre,flags=re.M)
pre=re.sub(r'^RUNTIME_ARTIFACT_SHA=.*$', 'RUNTIME_ARTIFACT_SHA="432b88b36857d477272ed5db64411491ac99d899f3b4e03a90ca7de439377cd1"',pre,flags=re.M)
pre=re.sub(r'^RUNTIME_TAR_SHA=.*$', 'RUNTIME_TAR_SHA="47ac58d8817353148f6d8ab98f01d995750c69002b3b763c424022e70cd78211"',pre,flags=re.M)
pre=re.sub(r'^MECHANICS_GIT_BLOB=.*$', 'MECHANICS_GIT_BLOB="9d266c45e62ec3c8701acec6aaf1bf80b970a740"',pre,flags=re.M)
pre=pre.replace('VERSION_NAME="0.9726870"; VERSION_BUILD="26870"','VERSION_NAME="0.9726871"; VERSION_BUILD="26871"')
pre=rename_outputs(pre)
pre=pre.replace('ARTZIP="$WORK/26868_artifact.zip"; ARTDIR="$WORK/artifact_26868"','ARTZIP="$WORK/26870_artifact.zip"; ARTDIR="$WORK/artifact_26870"')
pre=pre.replace('BASE="$WORK/exact_successful_26868_compiled_candidate"','BASE="$WORK/exact_successful_26870_compiled_candidate"')
pre=pre.replace('CAND="$WORK/candidate_26870"','CAND="$WORK/candidate_26871"')
assert 'RUNTIME_ACTIONS_RUN="39954786811"' in pre
# The output file names change but the real project compiler and assembler commands do not.
methods={n:rename_outputs(b) for n,b in methods.items()}
methods['verify_package']=r'''verify_package(){
 sha256sum -c 26871_HANDOFF_HASHES.sha256 >/dev/null || fail 'sealed 26871 upload files drift'
 bash -n build_26871_iris_rawr.sh || fail '26871 guarded build syntax'
 python3 -S -m py_compile verify_26871_candidate.py verify_26871_patches.py verify_26871_runtime_shader.py regressions/26871_b_shutter_group.py
 rm -rf __pycache__ regressions/__pycache__
 for p in 26871_FORWARD_FULL_INDEX.patch 26871_ROLLBACK_FULL_INDEX.patch;do
   ! grep -Eq '^(rename from|rename to|copy from|copy to) ' "$p" || fail 'unexpected source rename/copy'
 done
 [[ $(find handoff_payload_26871 -type f | wc -l) -eq 3 ]] || fail 'strict 3-file payload'
 diff -u 26871_CHANGED_ALLOWLIST.txt <(find handoff_payload_26871 -type f | sed 's#^handoff_payload_26871/##' | LC_ALL=C sort) >/dev/null || fail 'payload allowlist mismatch'
 sha256sum -c 26871_PAYLOAD_SHA256.txt >/dev/null || fail 'payload byte drift'
 test -f TRIGGER_26871.txt && grep -Fx 'RUN_26871_B_EXPOSURE_FLICKER_CHROMA' TRIGGER_26871.txt >/dev/null || fail 'wrong workflow trigger'
 ! find . -type f -name '*.apk' | grep -q . || fail 'never upload APK'
 pass '26871 hashes + exact 3-file allowlist + trigger + syntax'
}
'''
methods['verify_scope']=r'''verify_scope(){
 [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail 'wrong branch'
 git merge-base --is-ancestor "$RUNTIME_AUTHORITY_COMMIT" HEAD || fail '26870 not prior ancestor'
 [[ -z "$(git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD -- app/src app/version.properties)" ]] || fail 'live app source modified; candidate-first only'
 [[ -z "$(git status --porcelain -- app/src app/version.properties)" ]] || fail 'uncommitted actual source drift'
 [[ -z "$(git ls-files -- glsl_static)" ]] || fail 'historical GLSL cleanup missing'
 diff -u 26871_REPOSITORY_UPLOAD_ALLOWLIST.txt <(git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD | LC_ALL=C sort) >/dev/null || fail '26871 repository upload infrastructure/unlisted file mismatch'
 [[ "$(git hash-object build_26870_iris_rawr.sh)" == "$MECHANICS_GIT_BLOB" ]] || fail 'last successful build mechanics drift'
 pass '26871 exact intended branch/source scope and explicit infrastructure diff'
}
'''
methods['obtain_authority']=r'''obtain_authority(){
 [[ -n "$TOKEN" ]] || fail 'GITHUB_TOKEN missing'
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' \
   "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/runs/${RUNTIME_ACTIONS_RUN}" -o "$WORK/26870_run.json"
 python3 -S - "$WORK/26870_run.json" "$RUNTIME_AUTHORITY_COMMIT" "$RUNTIME_ACTIONS_RUN" <<'PY_RUN'
import json,sys
x=json.load(open(sys.argv[1]));assert x['id']==int(sys.argv[3]) and x['conclusion']=='success' and x['head_sha']==sys.argv[2] and x['head_branch']=='experimental-clean-photon-rebuild'
print('PASS exact successful 26870 Actions run HEAD/branch/conclusion')
PY_RUN
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' \
   "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${RUNTIME_ARTIFACT_ID}" -o "$WORK/26870_artifact_metadata.json"
 python3 -S - "$WORK/26870_artifact_metadata.json" <<'PY_ART'
import json,sys
x=json.load(open(sys.argv[1]));assert x['id']==12502775416 and x['name']=='photon-26870-iris-rawr-automatic-iq' and not x['expired'] and x['digest']=='sha256:432b88b36857d477272ed5db64411491ac99d899f3b4e03a90ca7de439377cd1'
print('PASS exact 26870 artifact ID/name/digest')
PY_ART
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' \
   "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${RUNTIME_ARTIFACT_ID}/zip" -o "$ARTZIP"
 [[ "$(sha "$ARTZIP")" == "$RUNTIME_ARTIFACT_SHA" ]] || fail '26870 artifact ZIP SHA drift'
 unzip -q "$ARTZIP" -d "$ARTDIR"
 local T="$ARTDIR/build_26870_iris_rawr_outputs/26870_candidate_app_source.tar.gz"
 [[ -f "$T" && "$(sha "$T")" == "$RUNTIME_TAR_SHA" ]] || fail '26870 compiled candidate TAR mismatch'
 local CS="$ARTDIR/build_26870_iris_rawr_outputs/26870_COMPILER_STATUS.txt"
 for proof in 'REAL GLSL COMPILE: PASS' 'REAL SPIR-V VALIDATION: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS';do
   grep -F "$proof" "$CS" >/dev/null || fail "26870 real compiler proof missing $proof"
 done
 mkdir -p "$BASE";tar -xzf "$T" -C "$BASE"
 [[ "$(find "$BASE/app" -type f | wc -l)" -eq 1994 ]] || fail 'not exactly successful 26870 compiled 1994 files'
 (cd "$BASE" && sha256sum -c "$ROOT/26871_BASE_26870_FULL_APP.sha256" >/dev/null) || fail 'prior file-complete manifest mismatch'
 cat > "$OUT/26871_RESOLVED_AUTHORITIES.txt" <<EOF_AUTH
runtime_commit=$RUNTIME_AUTHORITY_COMMIT
runtime_run=$RUNTIME_ACTIONS_RUN
runtime_artifact_id=$RUNTIME_ARTIFACT_ID
runtime_artifact_sha256=$RUNTIME_ARTIFACT_SHA
runtime_candidate_tar_sha256=$RUNTIME_TAR_SHA
mechanics_blob_sha1=$MECHANICS_GIT_BLOB
EOF_AUTH
 pass 'exact 26870 compiled-candidate runtime and compiler authority'
}
'''
methods['make_candidate']=r'''make_candidate(){
 python3 -S verify_26871_candidate.py "$BASE" "$CAND" --transform --root "$ROOT"
 # Historical regression universes are derived from real successful 26870
 # compiler-tested candidate. Never compare live checkout app directly.
 local H68="$WORK/historical_26868_from_successful_26870"
 local H67="$WORK/historical_26867_from_successful_26868"
 local H66="$WORK/historical_26866_from_successful_26867"
 cp -a "$BASE" "$H68";git -C "$H68" init -q
 (cd "$H68" && git apply --check --reverse "$ROOT/26870_FORWARD_FULL_INDEX.patch" &&
   git apply --reverse "$ROOT/26870_FORWARD_FULL_INDEX.patch" &&
   sha256sum -c "$ROOT/26870_BASE_26868_FULL_APP.sha256" >/dev/null) || fail 'real 26870->26868 rollback failed'
 cp -a "$H68" "$H67";rm -rf "$H67/.git";git -C "$H67" init -q
 (cd "$H67" && git apply --check --reverse "$ROOT/26868_FORWARD_FULL_INDEX.patch" &&
   git apply --reverse "$ROOT/26868_FORWARD_FULL_INDEX.patch" &&
   sha256sum -c "$ROOT/26868_BASE_26867_FULL_APP.sha256" >/dev/null) || fail '26867 historical rollback mismatch'
 cp -a "$H67" "$H66";rm -rf "$H66/.git";git -C "$H66" init -q
 (cd "$H66" && git apply --check --reverse "$ROOT/26867_FORWARD_FULL_INDEX.patch" &&
   git apply --reverse "$ROOT/26867_FORWARD_FULL_INDEX.patch" &&
   sha256sum -c "$ROOT/26867_BASE_26866_FULL_APP.sha256" >/dev/null) || fail '26866 historical rollback mismatch'
 (cd "$BASE" && sha256sum -c "$ROOT/26871_BASE_26870_FULL_APP.sha256" >/dev/null) || fail 'historical proof altered frozen base'
 python3 -S regressions/26865_b_lsc_owner.py "$CAND/app"
 python3 -S regressions/26866_b_color_only.py "$H66/app"
 python3 -S regressions/26867_b_highlight_ab_retired.py "$H67/app"
 python3 -S regressions/26868_direct_b_long_retire_ab.py "$H68/app"
 python3 -S regressions/26870_b_automatic_iq.py "$H68/app" "$BASE/app"
 python3 -S regressions/26871_b_shutter_group.py "$BASE" "$CAND"
 python3 -S verify_26871_runtime_shader.py "$CAND" --out "$OUT/26871_precompile_expansion"
 python3 -S verify_26864_rawr_sources.py "$CAND/app"
 python3 -S regressions/26864_glsl_reserved_identifiers.py "$CAND/app"
 python3 -S regressions/26864_wronski_publisher.py "$H67/app"
 python3 -S verify_26864_semantics.py "$H67/app" --numeric
 pass '26871 candidate and exact real 26870/26868/26867/26866 historical regression replay'
}
'''
methods['verify_successful_mechanics']=r'''verify_successful_mechanics(){
 [[ "$(git hash-object build_26870_iris_rawr.sh)" == "$MECHANICS_GIT_BLOB" ]] || fail 'successful 26870 build mechanics script changed'
 [[ "$(git rev-parse "$RUNTIME_AUTHORITY_COMMIT:build_26870_iris_rawr.sh")" == "$MECHANICS_GIT_BLOB" ]] || fail '26870 mechanics blob not recorded in successful commit'
 for validator in verify_26864_rawr_sources.py verify_26864_runtime_glsl.py verify_26864_semantics.py verify_26868_runtime_shader.py verify_26870_runtime_shader.py regressions/26868_direct_b_long_retire_ab.py regressions/26870_b_automatic_iq.py;do
   local prior="$WORK/prior_$validator"
   # Permanent nested-path historical failure from Actions run 39894413063.
   mkdir -p "$(dirname "$prior")"
   git show "$RUNTIME_AUTHORITY_COMMIT:$validator" > "$prior"
   cmp -s "$prior" "$ROOT/$validator" || fail "successful 26870 validator changed: $validator"
 done
 python3 -S - "$ROOT/build_26870_iris_rawr.sh" "$ROOT/build_26871_iris_rawr.sh" <<'PY_STAGES'
from pathlib import Path
import sys,re
stages=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','verify_candidate_patches','prebuild_safety','assemble','postbuild_proof','clean_extract_replay']
for path in sys.argv[1:]:
 text=Path(path).read_text();pos=-1
 for fn in stages:
  i=text.find('\n'+fn+'(){',pos+1)
  assert i>pos,(path,fn,'17-stage verification order changed');pos=i
for cmd in ['./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'./gradlew :app:assembleDebug --stacktrace']:
 assert all(cmd in Path(path).read_text() for path in sys.argv[1:]),('real compiler sequence/command drift',cmd)
print('PASS inherited successful 26870 17-stage order, exact compiler commands, native and APK assembly')
PY_STAGES
 pass '26870 -> 26871 successful mechanics and inherited validators unmodified'
}
'''
# Preserve original expanded Kotlin/GLSL/native validation stage, upgrading only
# the changed shader's source validator to 26871. Other real compiler input and
# pinned glslang 16.5.0 remain the successful 26870 implementation.
shaderstage=methods['compile_modified_runtime_shaders']
assert shaderstage.count('verify_26871_runtime_shader.py')==1,shaderstage.count('verify_26871_runtime_shader.py')
methods['compile_modified_runtime_shaders']=shaderstage.replace('26870 FOUR modified runtime expanded','26871 FOUR runtime-expanded')
methods['verify_candidate_patches']=r'''verify_candidate_patches(){
 python3 -S verify_26871_patches.py "$BASE" "$CAND" 26871_FORWARD_FULL_INDEX.patch 26871_ROLLBACK_FULL_INDEX.patch | tee "$OUT/26871_patch_validation.txt"
 pass 'canonical binary full-index forward/rollback core.abbrev 7/12/40 and fuzz=0 exact'
}
'''
methods['prebuild_safety']=r'''prebuild_safety(){
 snapshot_live_authority_seeded "$WORK/prebuild_live_snapshot"
 diff -qr "$CAND/app" "$WORK/prebuild_live_snapshot/app" >/dev/null || fail 'prebuild source drift'
 python3 -S verify_26871_candidate.py "$BASE" "$CAND" --root "$ROOT"
 python3 -S regressions/26871_b_shutter_group.py "$BASE" "$CAND"
 (cd "$CAND" && sha256sum -c "$ROOT/26871_UNCHANGED_PROTECTED.sha256" >/dev/null) || fail '26871 protected/DNG/native/vendor drift'
 for k in 'REAL GLSL COMPILE: PASS' 'REAL SPIR-V VALIDATION: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS';do
   grep -F "$k" "$OUT/26871_COMPILER_STATUS.txt" >/dev/null || fail "prebuild real compiler gate $k"
 done
 cat > "$OUT/26871_PREBUILD_SAFETY.txt" <<EOF_SAFETY
PRE-BUILD SAFETY PROOF PASSED
runtime_authority=successful 26870 $RUNTIME_AUTHORITY_COMMIT run $RUNTIME_ACTIONS_RUN artifact $RUNTIME_ARTIFACT_ID
verification_mechanics=exact 26870 successful 17-stage order and real compiler commands
runtime_changed_files=3 (0 new, 3 modified including version)
infrastructure_delta=explicit 26871 upload list, build generator, validators, workflow; inherited native/vendor ZERO
prior_files=1994
candidate_files=1994
version_name=$VERSION_NAME
version_build=$VERSION_BUILD
real_compilers=GLSL+SPIR-V+Kotlin+Java+NDK 2 ABI PASS
patch_proof=full-index forward/rollback 7/12/40 fuzz=0 exact
protected_source=1991 byte-identical to successful 26870; DNG/native/vendor preserved
EOF_SAFETY
 pass 'PRE-BUILD SAFETY PROOF PASSED'
}
'''
methods['clean_extract_replay']=r'''clean_extract_replay(){
 local replay="$WORK/clean_replay_candidate" exp="$WORK/extracted_candidate_tar"
 rm -rf "$replay" "$exp";mkdir -p "$exp"
 sha256sum -c 26871_HANDOFF_HASHES.sha256 >/dev/null
 bash -n build_26871_iris_rawr.sh
 python3 -S -m py_compile verify_26871_candidate.py verify_26871_patches.py verify_26871_runtime_shader.py regressions/26871_b_shutter_group.py
 rm -rf __pycache__ regressions/__pycache__
 python3 -S verify_26871_candidate.py "$BASE" "$replay" --root "$ROOT" --transform
 diff -qr "$CAND/app" "$replay/app" >/dev/null || fail 'clean-extract candidate differs from frozen source'
 (cd "$OUT" && sha256sum -c 26871_candidate_app_source.tar.gz.sha256 >/dev/null)
 tar -xzf "$OUT/26871_candidate_app_source.tar.gz" -C "$exp"
 diff -qr "$CAND/app" "$exp/app" >/dev/null || fail 'exported compiled candidate TAR differs'
 python3 -S verify_26871_candidate.py "$BASE" "$exp" --root "$ROOT"
 python3 -S verify_26871_patches.py "$BASE" "$exp" 26871_FORWARD_FULL_INDEX.patch 26871_ROLLBACK_FULL_INDEX.patch > "$OUT/26871_final_patch_replay.txt"
 python3 -S verify_26864_runtime_glsl.py "$BASE" "$exp" --out "$OUT/26871_final_runtime_expanded_glsl" | tee "$OUT/26871_final_glsl_static_replay.txt"
 python3 -S verify_26864_rawr_sources.py "$exp/app"
 python3 -S regressions/26864_glsl_reserved_identifiers.py "$exp/app"
 python3 -S regressions/26864_wronski_publisher.py "$WORK/historical_26867_from_successful_26868/app"
 python3 -S verify_26864_semantics.py "$WORK/historical_26867_from_successful_26868/app" --numeric
 python3 -S regressions/26865_b_lsc_owner.py "$exp/app"
 python3 -S regressions/26866_b_color_only.py "$WORK/historical_26866_from_successful_26867/app"
 python3 -S regressions/26867_b_highlight_ab_retired.py "$WORK/historical_26867_from_successful_26868/app"
 python3 -S regressions/26868_direct_b_long_retire_ab.py "$WORK/historical_26868_from_successful_26870/app"
 python3 -S regressions/26870_b_automatic_iq.py "$WORK/historical_26868_from_successful_26870/app" "$BASE/app"
 python3 -S regressions/26871_b_shutter_group.py "$BASE" "$exp"
 python3 -S verify_26867_runtime_shader.py "$exp" --out "$OUT/26871_final_inherited_white_fade"
 python3 -S verify_26868_runtime_shader.py "$exp" --out "$OUT/26871_final_expanded_b_long"
 python3 -S verify_26871_runtime_shader.py "$exp" --out "$OUT/26871_final_expanded_tone_chroma"
 grep -Fx 'VERSION_NAME=0.9726871' "$exp/app/version.properties" >/dev/null
 grep -Fx 'VERSION_BUILD=26871' "$exp/app/version.properties" >/dev/null
 for status in 'REAL GLSL COMPILE: PASS' 'REAL SPIR-V VALIDATION: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS';do
   grep -F "$status" "$OUT/26871_COMPILER_STATUS.txt" >/dev/null || fail "final real compiler proof $status"
 done
 pass '26871 final clean-extract replay manifest/ownership/patches/regressions/real compilers'
}
'''
# Inherited unchanged functions (aside from output filenames) are not replaceable.
OVERRIDES={'verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','compile_modified_runtime_shaders','verify_candidate_patches','prebuild_safety','clean_extract_replay'}
for name in ('prepare_glslang','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','assemble','postbuild_proof'):
 assert methods[name]==rename_outputs(old[marks[[x.group(1) for x in marks].index(name)].start():(marks[[x.group(1) for x in marks].index(name)+1].start() if [x.group(1) for x in marks].index(name)+1<len(marks) else end)])
# Reconstruct in exactly the same function order, retaining the 17-call tail.
pieces=[pre]
for i,m in enumerate(marks):
 name=m.group(1)
 pieces.append(methods[name] if name in methods else rename_outputs(old[m.start():(marks[i+1].start() if i+1<len(marks) else end)]))
final=rename_outputs(old[end:]).replace("pass '26870 ALL 17", "pass '26871 ALL 17")
pieces.append(final)
script=''.join(pieces)
assert script.count('verify_package(){')==1 and script.count('\nverify_package\n')==1
for cmd in ('./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'./gradlew :app:assembleDebug --stacktrace'):
 assert cmd in script and cmd in old,(cmd,'real compiler command altered')
assert len(list(re.finditer(r'(?m)^[a-z_]+\(\)\{',script)))==len(allmarks)
assert 'RUNTIME_ARTIFACT_ID="12502775416"' in script
assert 'VERSION_BUILD="26871"' in script
assert '26871_BASE_26870_FULL_APP.sha256' in script
assert '26871_UNCHANGED_PROTECTED.sha256' in script
assert '26871_HANDOFF_HASHES.sha256' in script
assert 'verify_26871_runtime_shader.py' in script
assert 'IRIS_26871_B_SHUTTER_FLICKER_GROUP_GUARD' not in script  # runtime source only
assert hashlib.sha256(script.encode()).hexdigest() == 'ca2d99d38c1de9a310205ba2c2af0fd7b49399f506e39a24fa94a6f15a338e0e', 'guarded 26871 script drift from real successful 26870 diff audit'
# Deterministic byte output; stage-by-stage full infrastructure diff persisted.
assert not dest.exists() or dest.read_bytes()==script.encode(), 'non-deterministic generated build script'
dest.write_text(script)
output=repo/'26871_BUILD_INFRASTRUCTURE_DIFF.txt'
diff=''.join(difflib.unified_diff(old.splitlines(keepends=True),script.splitlines(keepends=True),fromfile='exact_successful_26870_build_script',tofile='26871_generated_build_script'))
assert hashlib.sha256(diff.encode()).hexdigest() == '36e8c0f108c49d0a2f45b9c47a579a596db385aa0851cf346933e753c0fcca20', 'exact successful 26870 mechanics delta drift'
output.write_text(diff)
print('PASS exact successful 26870 Git blob, inherited 17 stages and real compiler commands; explicit 26871 infrastructure diff')
print('generated_sha256',hashlib.sha256(script.encode()).hexdigest(),'diff_sha256',hashlib.sha256(diff.encode()).hexdigest())
