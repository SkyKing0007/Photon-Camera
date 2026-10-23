#!/usr/bin/env python3
"""Deterministically inherit EXACT successful 26871 17-stage build implementation.
Successful 26871 Actions generated script is reconstructed, SHA-sealed, and the
few version/authority/modified-shader owners are adapted explicitly. The compiler
commands and assembly ordering are never changed.
"""
from pathlib import Path
import hashlib,re,sys,difflib
root=Path(sys.argv[1]) if len(sys.argv)>1 else Path('.')
src=root/'build_26871_iris_rawr.sh';dst=root/'build_26872_iris_rawr.sh'
def sha(x):return hashlib.sha256(x).hexdigest()
assert sha(src.read_bytes())=='ca2d99d38c1de9a310205ba2c2af0fd7b49399f506e39a24fa94a6f15a338e0e','NOT exact successful 26871 Actions script'
old=src.read_text()
stages=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','verify_candidate_patches','prebuild_safety','assemble','postbuild_proof','clean_extract_replay']
marks=list(re.finditer(r'(?m)^([a-z][a-z_0-9]*)\(\)\{',old));start=next(i for i,m in enumerate(marks) if m.group(1)=='verify_package');marks=marks[start:]
pre=old[:marks[0].start()];end_marker='\nverify_package\nverify_scope\nobtain_authority\nmake_candidate\nverify_successful_mechanics\n';assert old.count(end_marker)==1
end=old.index(end_marker);body={}
for i,m in enumerate(marks):body[m.group(1)]=old[m.start():marks[i+1].start() if i+1<len(marks) else end]
assert set(stages).issubset(body)
# Rename only stage-local outputs. Do not touch inherited real compiler commands.
rename=lambda s:s.replace('26871_', '26872_').replace('build_26871', 'build_26872')
pre=rename(pre)
pre=pre.replace('Successful 26870 Actions compiled candidate is runtime authority.','Successful 26871 Actions compiled candidate is runtime authority.')
pre=pre.replace('Keep successful 26870 17-stage verification mechanics unchanged by default.','Keep successful 26871 17-stage verification mechanics unchanged by default.')
pre=re.sub(r'^REPO_SCAFFOLD_BASE_COMMIT=.*$', 'REPO_SCAFFOLD_BASE_COMMIT="ab638355f659b89b05b31cc318642b24aecb75fd"',pre,flags=re.M)
pre=re.sub(r'^RUNTIME_ARTIFACT_ID=.*$', 'RUNTIME_ARTIFACT_ID="12521581302"; RUNTIME_ACTIONS_RUN="39998422200"',pre,flags=re.M)
pre=re.sub(r'^RUNTIME_AUTHORITY_COMMIT=.*$', 'RUNTIME_AUTHORITY_COMMIT="ab638355f659b89b05b31cc318642b24aecb75fd"',pre,flags=re.M)
pre=re.sub(r'^RUNTIME_ARTIFACT_SHA=.*$', 'RUNTIME_ARTIFACT_SHA="25039054c7327596f0a928de00a91e6958996c08a757a38851f4688b25762077"',pre,flags=re.M)
pre=re.sub(r'^RUNTIME_TAR_SHA=.*$', 'RUNTIME_TAR_SHA="b7a0ff6b62117457101f2a0898694a4d4536dccbaaf6ed680c3a9e0f060b7db5"',pre,flags=re.M)
pre=re.sub(r'^MECHANICS_GIT_BLOB=.*$', 'MECHANICS_GIT_BLOB="71415dd61ca1f6be3ef81e5407afdd3625ade8e3"',pre,flags=re.M)
pre=pre.replace('VERSION_NAME="0.9726871"; VERSION_BUILD="26871"','VERSION_NAME="0.9726872"; VERSION_BUILD="26872"')
pre=pre.replace('ARTZIP="$WORK/26870_artifact.zip"; ARTDIR="$WORK/artifact_26870"','ARTZIP="$WORK/26871_artifact.zip"; ARTDIR="$WORK/artifact_26871"')
pre=pre.replace('BASE="$WORK/exact_successful_26870_compiled_candidate"','BASE="$WORK/exact_successful_26871_compiled_candidate"')
pre=pre.replace('CAND="$WORK/candidate_26871"','CAND="$WORK/candidate_26872"')
assert 'RUNTIME_ACTIONS_RUN="39998422200"' in pre
body={n:rename(x) for n,x in body.items()}
body['verify_package']=r'''verify_package(){
 sha256sum -c 26872_HANDOFF_HASHES.sha256 >/dev/null || fail 'sealed 26872 upload hashes drift'
 sha256sum -c 26872_GENERATED_BUILD_SHA256.txt >/dev/null || fail 'generated guard differs from proven package'
 bash -n build_26872_iris_rawr.sh || fail 'guarded build shell syntax'
 python3 -S -m py_compile verify_26872_candidate.py verify_26872_patches.py verify_26872_runtime_shader.py regressions/26872_b_preview_only.py
 rm -rf __pycache__ regressions/__pycache__
 for patch in 26872_FORWARD_FULL_INDEX.patch 26872_ROLLBACK_FULL_INDEX.patch;do
  ! grep -Eq '^(rename from|rename to|copy from|copy to) ' "$patch" || fail 'unexpected copy/rename'
 done
 [[ $(find handoff_payload_26872 -type f | wc -l) -eq 5 ]] || fail 'five-file strict payload'
 diff -u 26872_CHANGED_ALLOWLIST.txt <(find handoff_payload_26872 -type f | sed 's#^handoff_payload_26872/##' | LC_ALL=C sort) >/dev/null || fail 'runtime allowlist changed'
 sha256sum -c 26872_PAYLOAD_SHA256.txt >/dev/null || fail 'payload hashes fail'
 test -f TRIGGER_26872.txt && grep -Fx 'RUN_26872_B_PREVIEW_STRIPE' TRIGGER_26872.txt >/dev/null || fail 'wrong trigger'
 ! find . -type f -name '*.apk' | grep -q . || fail 'never package APK'
 pass '26872 exact sealed package, shader validator syntax, five-file runtime allowlist and trigger'
}
'''
body['verify_scope']=r'''verify_scope(){
 [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail 'wrong branch'
 git merge-base --is-ancestor "$RUNTIME_AUTHORITY_COMMIT" HEAD || fail '26871 authority not an ancestor'
 [[ -z "$(git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD -- app/src app/version.properties)" ]] || fail 'live app source changed before candidate-first install'
 [[ -z "$(git status --porcelain -- app/src app/version.properties)" ]] || fail 'uncommitted live source drift'
 [[ -z "$(git ls-files -- glsl_static)" ]] || fail 'generated shader file tracked'
 diff -u 26872_REPOSITORY_UPLOAD_ALLOWLIST.txt <(git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD | LC_ALL=C sort) >/dev/null || fail 'unexpected infrastructure/source file uploaded'
 [[ "$(git rev-parse "$RUNTIME_AUTHORITY_COMMIT:generate_26871_build.py")" == "$MECHANICS_GIT_BLOB" ]] || fail '26871 successful generator blob mismatch'
 [[ "$(sha build_26871_iris_rawr.sh)" == 'ca2d99d38c1de9a310205ba2c2af0fd7b49399f506e39a24fa94a6f15a338e0e' ]] || fail '26871 generated successful script differs'
 pass '26872 branch/ancestor, zero live runtime modifications, exact uploaded infrastructure delta and 26871 mechanics'
}
'''
body['obtain_authority']=r'''obtain_authority(){
 [[ -n "$TOKEN" ]] || fail 'GITHUB_TOKEN missing'
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' \
   "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/runs/${RUNTIME_ACTIONS_RUN}" -o "$WORK/26871_run.json"
 python3 -S - "$WORK/26871_run.json" "$RUNTIME_AUTHORITY_COMMIT" "$RUNTIME_ACTIONS_RUN" <<'PY_RUN'
import json,sys
x=json.load(open(sys.argv[1]));assert x['id']==int(sys.argv[3]) and x['conclusion']=='success' and x['head_sha']==sys.argv[2] and x['head_branch']=='experimental-clean-photon-rebuild'
print('PASS exact real successful 26871 Actions run/HEAD/branch')
PY_RUN
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' \
   "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${RUNTIME_ARTIFACT_ID}" -o "$WORK/26871_artifact_metadata.json"
 python3 -S - "$WORK/26871_artifact_metadata.json" <<'PY_ART'
import json,sys
x=json.load(open(sys.argv[1]));assert x['id']==12521581302 and x['name']=='photon-26871-b-exposure-flicker-chroma' and not x['expired'] and x['digest']=='sha256:25039054c7327596f0a928de00a91e6958996c08a757a38851f4688b25762077'
print('PASS exact successful 26871 artifact identity and digest')
PY_ART
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' \
  "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${RUNTIME_ARTIFACT_ID}/zip" -o "$ARTZIP"
 [[ "$(sha "$ARTZIP")" == "$RUNTIME_ARTIFACT_SHA" ]] || fail '26871 authority artifact SHA drift'
 unzip -q "$ARTZIP" -d "$ARTDIR"
 local T="$ARTDIR/build_26871_iris_rawr_outputs/26871_candidate_app_source.tar.gz"
 [[ -f "$T" && "$(sha "$T")" == "$RUNTIME_TAR_SHA" ]] || fail 'compiled 26871 candidate TAR drift'
 local CS="$ARTDIR/build_26871_iris_rawr_outputs/26871_COMPILER_STATUS.txt"
 for proof in 'REAL GLSL COMPILE: PASS' 'REAL SPIR-V VALIDATION: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS'; do
  grep -F "$proof" "$CS" >/dev/null || fail "successful 26871 prior compiler authority missing $proof"
 done
 mkdir -p "$BASE";tar -xzf "$T" -C "$BASE"
 [[ "$(find "$BASE/app" -type f | wc -l)" -eq 1994 ]] || fail 'not the exact 26871 source universe'
 (cd "$BASE" && sha256sum -c "$ROOT/26872_BASE_26871_FULL_APP.sha256" >/dev/null) || fail '26871 manifest mismatch'
 cat > "$OUT/26872_RESOLVED_AUTHORITIES.txt" <<EOF_AUTH
runtime_commit=$RUNTIME_AUTHORITY_COMMIT
runtime_run=$RUNTIME_ACTIONS_RUN
runtime_artifact_id=$RUNTIME_ARTIFACT_ID
runtime_artifact_sha256=$RUNTIME_ARTIFACT_SHA
runtime_candidate_tar_sha256=$RUNTIME_TAR_SHA
mechanics_generator_blob_sha1=$MECHANICS_GIT_BLOB
mechanics_generated_script_sha256=ca2d99d38c1de9a310205ba2c2af0fd7b49399f506e39a24fa94a6f15a338e0e
EOF_AUTH
 pass 'exact successful 26871 runtime+mechanics authority, complete candidate, verified real compiler receipt'
}
'''
body['make_candidate']=r'''make_candidate(){
 python3 -S verify_26872_candidate.py "$BASE" "$CAND" --transform --root "$ROOT"
 # Inherit real prior successful-universe rollback chain (no synthetic substitute).
 local H70="$WORK/historical_26870_from_26871" H68="$WORK/historical_26868_from_26870"
 local H67="$WORK/historical_26867_from_26868" H66="$WORK/historical_26866_from_26867"
 cp -a "$BASE" "$H70";git -C "$H70" init -q
 (cd "$H70" && git apply --check --reverse "$ROOT/26871_FORWARD_FULL_INDEX.patch" &&
  git apply --reverse "$ROOT/26871_FORWARD_FULL_INDEX.patch" && sha256sum -c "$ROOT/26871_BASE_26870_FULL_APP.sha256" >/dev/null) || fail 'actual 26871->26870 rollback failed'
 cp -a "$H70" "$H68";rm -rf "$H68/.git";git -C "$H68" init -q
 (cd "$H68" && git apply --check --reverse "$ROOT/26870_FORWARD_FULL_INDEX.patch" &&
  git apply --reverse "$ROOT/26870_FORWARD_FULL_INDEX.patch" && sha256sum -c "$ROOT/26870_BASE_26868_FULL_APP.sha256" >/dev/null) || fail '26870->26868 rollback failed'
 cp -a "$H68" "$H67";rm -rf "$H67/.git";git -C "$H67" init -q
 (cd "$H67" && git apply --check --reverse "$ROOT/26868_FORWARD_FULL_INDEX.patch" &&
  git apply --reverse "$ROOT/26868_FORWARD_FULL_INDEX.patch" && sha256sum -c "$ROOT/26868_BASE_26867_FULL_APP.sha256" >/dev/null) || fail '26868->26867 rollback failed'
 cp -a "$H67" "$H66";rm -rf "$H66/.git";git -C "$H66" init -q
 (cd "$H66" && git apply --check --reverse "$ROOT/26867_FORWARD_FULL_INDEX.patch" &&
  git apply --reverse "$ROOT/26867_FORWARD_FULL_INDEX.patch" && sha256sum -c "$ROOT/26867_BASE_26866_FULL_APP.sha256" >/dev/null) || fail '26867->26866 rollback failed'
 (cd "$BASE" && sha256sum -c "$ROOT/26872_BASE_26871_FULL_APP.sha256" >/dev/null) || fail 'historical replay mutated 26871 candidate'
 python3 -S regressions/26865_b_lsc_owner.py "$CAND/app"
 python3 -S regressions/26866_b_color_only.py "$H66/app"
 python3 -S regressions/26867_b_highlight_ab_retired.py "$H67/app"
 python3 -S regressions/26868_direct_b_long_retire_ab.py "$H68/app"
 python3 -S regressions/26870_b_automatic_iq.py "$H68/app" "$H70/app"
 python3 -S regressions/26871_b_shutter_group.py "$H70" "$BASE"
 python3 -S regressions/26872_b_preview_only.py "$BASE" "$CAND"
 python3 -S verify_26871_runtime_shader.py "$CAND" --out "$OUT/26872_inherited_26871_shader_expansion"
 python3 -S verify_26872_runtime_shader.py "$CAND" --out "$OUT/26872_precompile_preview_expansion"
 python3 -S verify_26864_rawr_sources.py "$CAND/app"
 python3 -S regressions/26864_glsl_reserved_identifiers.py "$CAND/app"
 python3 -S regressions/26864_wronski_publisher.py "$H67/app"
 python3 -S verify_26864_semantics.py "$H67/app" --numeric
 pass 'real 26871->26870->26868->26867->26866 historical universes and B-only preview detector regression'
}
'''
body['verify_successful_mechanics']=r'''verify_successful_mechanics(){
 [[ "$(sha build_26871_iris_rawr.sh)" == 'ca2d99d38c1de9a310205ba2c2af0fd7b49399f506e39a24fa94a6f15a338e0e' ]] || fail 'successfully generated 26871 mechanics drift'
 [[ "$(git rev-parse "$RUNTIME_AUTHORITY_COMMIT:generate_26871_build.py")" == "$MECHANICS_GIT_BLOB" ]] || fail 'successful 26871 generator source blob drift'
 for validator in verify_26864_rawr_sources.py verify_26864_runtime_glsl.py verify_26864_semantics.py verify_26868_runtime_shader.py verify_26870_runtime_shader.py verify_26871_runtime_shader.py regressions/26868_direct_b_long_retire_ab.py regressions/26870_b_automatic_iq.py regressions/26871_b_shutter_group.py;do
  local prior="$WORK/prior_$validator"
  mkdir -p "$(dirname "$prior")" # permanent nested-path historical regression
  git show "$RUNTIME_AUTHORITY_COMMIT:$validator" > "$prior"
  cmp -s "$prior" "$ROOT/$validator" || fail "successful 26871 validator changed: $validator"
 done
 python3 -S - "$ROOT/build_26871_iris_rawr.sh" "$ROOT/build_26872_iris_rawr.sh" <<'PY_STAGES'
from pathlib import Path
import sys
stages=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','verify_candidate_patches','prebuild_safety','assemble','postbuild_proof','clean_extract_replay']
for file in sys.argv[1:]:
 txt=Path(file).read_text();pos=-1
 for fn in stages:
  i=txt.find('\n'+fn+'(){',pos+1)
  assert i>pos,(file,fn,'successful 26871 17-stage order changed');pos=i
for cmd in ['./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'./gradlew :app:assembleDebug --stacktrace']:
 assert all(cmd in Path(file).read_text() for file in sys.argv[1:]),('compiler or NDK/assemble command deviation',cmd)
print('PASS exact inherited 26871 17 stages, real compiler commands and ordering')
PY_STAGES
 pass '26871 successful mechanics/validators intact and 26872 runtime scopes explicitly audited'
}
'''
body['compile_modified_runtime_shaders']=r'''compile_modified_runtime_shaders(){
 # Exact successful 26871 11 inherited GLES owners + native 58 SPIR-V owners.
 git show "$RUNTIME_AUTHORITY_COMMIT:verify_26864_runtime_glsl.py" > "$WORK/successful_26864_runtime_glsl.py"
 [[ "$(git hash-object "$WORK/successful_26864_runtime_glsl.py")" == 'c5208e94865afbbbc437c31e09fd7b893e50ca20' ]] || fail 'protected historical shader validator drift'
 python3 -S verify_26864_runtime_glsl.py "$BASE" "$CAND" --compiler "$IRIS26864_GLSLANG" --out "$OUT/26872_runtime_expanded_glsl" | tee "$OUT/26872_gles_shader_proof.txt"
 grep -F 'PASS 26864 GLSL ownership:' "$OUT/26872_gles_shader_proof.txt" >/dev/null || fail 'inherited expanded shader ownership failed'
 python3 -S verify_26867_runtime_shader.py "$CAND" --compiler "$IRIS26864_GLSLANG" --out "$OUT/26872_inherited_white_fade" | tee "$OUT/26872_white_fade_glsl.txt"
 grep -F 'pinned-glslang=PASS' "$OUT/26872_white_fade_glsl.txt" >/dev/null || fail 'inherited white fade real compiler missing'
 python3 -S verify_26868_runtime_shader.py "$CAND" --compiler "$IRIS26864_GLSLANG" --out "$OUT/26872_inherited_b_long" | tee "$OUT/26872_inherited_b_long_glsl.txt"
 [[ $(grep -c 'pinned-glslang=PASS' "$OUT/26872_inherited_b_long_glsl.txt") -eq 2 ]] || fail 'inherited two LONG shader compilers failed'
 python3 -S verify_26871_runtime_shader.py "$CAND" --compiler "$IRIS26864_GLSLANG" --out "$OUT/26872_inherited_26871_glsl" | tee "$OUT/26872_inherited_26871_glsl.txt"
 [[ $(grep -c 'pinned-glslang=PASS' "$OUT/26872_inherited_26871_glsl.txt") -eq 4 ]] || fail 'four inherited 26871 GLSL owners failed'
 python3 -S verify_26872_runtime_shader.py "$CAND" --compiler "$IRIS26864_GLSLANG" --out "$OUT/26872_preview_exact_expanded" | tee "$OUT/26872_new_preview_glsl.txt"
 [[ $(grep -c 'pinned-glslang=PASS' "$OUT/26872_new_preview_glsl.txt") -eq 4 ]] || fail 'four new exact runtime-expanded preview GL programs failed pinned compiler'
 python3 -S regressions/26864_glsl_reserved_identifiers.py "$CAND/app"
 python3 -S verify_26864_rawr_sources.py "$CAND/app" --compile "$IRIS26864_GLSLANG" \
  --spirv-val "$(command -v spirv-val)" --spirv-opt "$(command -v spirv-opt)" \
  --out "$OUT/26872_all_native_expanded_spirv" | tee "$OUT/26872_spirv_validation.txt"
 grep -F 'PASS 26864 real 58 SPIR-V compute shaders' "$OUT/26872_spirv_validation.txt" >/dev/null || fail 'real inherited native shader compiler proof missing'
 sed -i 's#REAL GLSL COMPILE: NOT RUN YET#REAL GLSL COMPILE: PASS (pinned 16.5.0 on expanded GLES300 and 58 exact native Vulkan shaders)#' "$OUT/26872_COMPILER_STATUS.txt"
 sed -i 's#REAL SPIR-V VALIDATION: NOT RUN YET#REAL SPIR-V VALIDATION: PASS (spirv-val pre/post optimized Vulkan 1.1)#' "$OUT/26872_COMPILER_STATUS.txt"
}
'''
body['verify_candidate_patches']=r'''verify_candidate_patches(){
 python3 -S verify_26872_patches.py "$BASE" "$CAND" 26872_FORWARD_FULL_INDEX.patch 26872_ROLLBACK_FULL_INDEX.patch | tee "$OUT/26872_patch_validation.txt"
 pass 'inherited full-index patch 7/12/40 fuzz=0 byte-exact rollback'
}
'''
body['prebuild_safety']=r'''prebuild_safety(){
 snapshot_live_authority_seeded "$WORK/prebuild_live_snapshot"
 diff -qr "$CAND/app" "$WORK/prebuild_live_snapshot/app" >/dev/null || fail 'frozen candidate/live source prebuild drift'
 python3 -S verify_26872_candidate.py "$BASE" "$CAND" --root "$ROOT"
 (cd "$CAND" && sha256sum -c "$ROOT/26872_UNCHANGED_PROTECTED.sha256" >/dev/null) || fail 'DNG/native/vendor/source protected drift'
 for k in 'REAL GLSL COMPILE: PASS' 'REAL SPIR-V VALIDATION: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS';do
  grep -F "$k" "$OUT/26872_COMPILER_STATUS.txt" >/dev/null || fail "prebuild compiler gate missing $k"
 done
 cat > "$OUT/26872_PREBUILD_SAFETY.txt" <<EOF_SAFETY
PRE-BUILD SAFETY PROOF PASSED
runtime_authority=successful 26871 $RUNTIME_AUTHORITY_COMMIT run $RUNTIME_ACTIONS_RUN artifact $RUNTIME_ARTIFACT_ID
verification_mechanics=exact successful 26871 17 stages and real compiler/NDK commands
runtime_changed_files=5 (1 new, 4 modified including guarded version)
infrastructure_delta=explicit 26872 workflow, build generator, validators, manifests and regression; previous mechanics and native/vendor ZERO
prior_files=1994
candidate_files=1995
version_name=$VERSION_NAME
version_build=$VERSION_BUILD
real_compilers=GLSL+SPIR-V+Kotlin+Java+NDK 2 ABI PASS
patch_proof=full-index forward/rollback 7/12/40 fuzz 0 exact
protected_source=1990 files byte-identical to successful 26871 candidate; DNG/native/vendor untouched
EOF_SAFETY
 pass 'PRE-BUILD SAFETY PROOF PASSED'
}
'''
body['clean_extract_replay']=r'''clean_extract_replay(){
 local replay="$WORK/clean_replay_candidate" exp="$WORK/extracted_candidate_tar"
 rm -rf "$replay" "$exp";mkdir -p "$exp"
 sha256sum -c 26872_HANDOFF_HASHES.sha256 >/dev/null
 sha256sum -c 26872_GENERATED_BUILD_SHA256.txt >/dev/null
 bash -n build_26872_iris_rawr.sh
 python3 -S -m py_compile verify_26872_candidate.py verify_26872_patches.py verify_26872_runtime_shader.py regressions/26872_b_preview_only.py
 rm -rf __pycache__ regressions/__pycache__
 python3 -S verify_26872_candidate.py "$BASE" "$replay" --root "$ROOT" --transform
 diff -qr "$CAND/app" "$replay/app" >/dev/null || fail 'clean-extract candidate transform mismatch'
 sha256sum -c "$OUT/26872_candidate_app_source.tar.gz.sha256" >/dev/null
 tar -xzf "$OUT/26872_candidate_app_source.tar.gz" -C "$exp"
 diff -qr "$CAND/app" "$exp/app" >/dev/null || fail 'exported compiler-tested candidate differs'
 python3 -S verify_26872_candidate.py "$BASE" "$exp" --root "$ROOT"
 python3 -S verify_26872_patches.py "$BASE" "$exp" 26872_FORWARD_FULL_INDEX.patch 26872_ROLLBACK_FULL_INDEX.patch > "$OUT/26872_final_patch_replay.txt"
 python3 -S verify_26864_runtime_glsl.py "$BASE" "$exp" --out "$OUT/26872_final_runtime_glsl" | tee "$OUT/26872_final_glsl_static.txt"
 python3 -S verify_26864_rawr_sources.py "$exp/app"
 python3 -S regressions/26864_glsl_reserved_identifiers.py "$exp/app"
 python3 -S regressions/26864_wronski_publisher.py "$WORK/historical_26867_from_26868/app"
 python3 -S verify_26864_semantics.py "$WORK/historical_26867_from_26868/app" --numeric
 python3 -S regressions/26865_b_lsc_owner.py "$exp/app"
 python3 -S regressions/26866_b_color_only.py "$WORK/historical_26866_from_26867/app"
 python3 -S regressions/26867_b_highlight_ab_retired.py "$WORK/historical_26867_from_26868/app"
 python3 -S regressions/26868_direct_b_long_retire_ab.py "$WORK/historical_26868_from_26870/app"
 python3 -S regressions/26870_b_automatic_iq.py "$WORK/historical_26868_from_26870/app" "$WORK/historical_26870_from_26871/app"
 python3 -S regressions/26871_b_shutter_group.py "$WORK/historical_26870_from_26871" "$BASE"
 python3 -S regressions/26872_b_preview_only.py "$BASE" "$exp"
 python3 -S verify_26867_runtime_shader.py "$exp" --out "$OUT/26872_final_white_fade"
 python3 -S verify_26868_runtime_shader.py "$exp" --out "$OUT/26872_final_b_long"
 python3 -S verify_26871_runtime_shader.py "$exp" --out "$OUT/26872_final_prior_shader"
 python3 -S verify_26872_runtime_shader.py "$exp" --out "$OUT/26872_final_preview_shaders"
 grep -Fx 'VERSION_NAME=0.9726872' "$exp/app/version.properties" >/dev/null
 grep -Fx 'VERSION_BUILD=26872' "$exp/app/version.properties" >/dev/null
 for k in 'REAL GLSL COMPILE: PASS' 'REAL SPIR-V VALIDATION: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS';do
  grep -F "$k" "$OUT/26872_COMPILER_STATUS.txt" >/dev/null || fail "final compiler proof missing $k"
 done
 pass '26872 final clean-extract hashes/source/shaders/regressions/manifests/patches/version and real compilers/build'
}
'''
# 'snapshot_live_authority_seeded' is intentionally inherited byte-for-byte aside
# from 26871 -> 26872 output labels. The 17 executable stage call order does not change.
text=pre+''.join(body[m.group(1)] for m in marks)+rename(old[end:])
for n in stages:assert '\n'+n+'(){' in text
for cmd in ['./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'./gradlew :app:assembleDebug --stacktrace']:
 assert cmd in text and cmd in old
for marker in ('# IRIS_26872_AUTHORITATIVE_ACTIONS_STAGE_ORDER',):assert marker in text
assert text.count('\nverify_package\nverify_scope\nobtain_authority\nmake_candidate\nverify_successful_mechanics\n')==1
assert 'RUNTIME_ARTIFACT_ID="12521581302"' in text
assert 'VERSION_NAME="0.9726872"' in text
assert 'FULL ANDROID ASSEMBLE: NOT RUN YET' in text
dst.write_text(text)
diff=''.join(difflib.unified_diff(old.splitlines(keepends=True),text.splitlines(keepends=True),fromfile='exact_successful_26871_generated',tofile='26872_guarded_upload_candidate'))
(root/'26872_BUILD_INFRASTRUCTURE_DIFF.txt').write_text(diff)
print('PASS exact 26871 successful mechanics SHA, inherited stage order/compiler command, complete explicit infrastructure diff')
print('generated_sha256',sha(text.encode()),'diff_sha256',sha(diff.encode()))
