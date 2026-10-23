#!/usr/bin/env python3
"""Preserve exact successful 26872 generated 17-stage mechanics and diff-audit 26873 scope.

The previous 26872 generator executes first on GitHub Actions; its exact SHA
must match successful run 40016268244. This generator only transforms the
known successful stage bodies and delegates every real compiler unchanged.
"""
from pathlib import Path
import hashlib,re,sys,difflib
root=Path(sys.argv[1]) if len(sys.argv)>1 else Path('.')
src=root/'build_26872_iris_rawr.sh';dst=root/'build_26873_iris_rawr.sh'
def sha(blob):return hashlib.sha256(blob).hexdigest()
assert sha(src.read_bytes())=='042f4550b60ba7efb8e363230a76931969e98c2ffacda3fa310895e98f40b7db', 'NOT successful exact 26872 generated build'
old=src.read_text()
stages=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','verify_candidate_patches','prebuild_safety','assemble','postbuild_proof','clean_extract_replay']
marks=list(re.finditer(r'(?m)^([a-z][a-z_0-9]*)\(\)\{',old));start=next(i for i,m in enumerate(marks) if m.group(1)=='verify_package');marks=marks[start:]
pre=old[:marks[0].start()];end_marker='\nverify_package\nverify_scope\nobtain_authority\nmake_candidate\nverify_successful_mechanics\n'
assert old.count(end_marker)==1
end=old.index(end_marker);body={}
for i,m in enumerate(marks):body[m.group(1)]=old[m.start():marks[i+1].start() if i+1<len(marks) else end]
# The successful 26872 script also has the authority-seeded canonical snapshot
# helper between GLSL compilation and live installation. It is not a new
# build stage and must be preserved byte-for-byte except version labels.
inherited_order=list(body)
assert [k for k in inherited_order if k in stages]==stages,('successful 17-stage order drift',inherited_order)
assert [k for k in inherited_order if k not in stages]==['snapshot_live_authority_seeded'],('inherited helper drift',inherited_order)
rename=lambda s:s.replace('26872_', '26873_').replace('build_26872', 'build_26873')
pre=rename(pre)
pre=pre.replace('Successful 26871 Actions compiled candidate is runtime authority.','Successful 26872 Actions compiled candidate is runtime authority.')
pre=pre.replace('Keep successful 26871 17-stage verification mechanics unchanged by default.','Keep successful 26872 17-stage verification mechanics unchanged by default.')
def change_line(key, value):
 global pre
 pre,n=re.subn(r'(?m)^'+re.escape(key)+r'=.*$',key+'='+value,pre)
 assert n==1,(key,'missing exact successful source assignment',n)
change_line('REPO_SCAFFOLD_BASE_COMMIT','"7007f9cdf0d3fb8f5662467f82d394f5b41e256e"')
change_line('RUNTIME_ARTIFACT_ID','"12528194015"; RUNTIME_ACTIONS_RUN="40016268244"')
change_line('RUNTIME_AUTHORITY_COMMIT','"7007f9cdf0d3fb8f5662467f82d394f5b41e256e"')
change_line('RUNTIME_ARTIFACT_SHA','"b5aa31aa25946f0f1376f8d0fdbead6446a0f119492b6bd7d8bd2fb602fdbb30"')
change_line('RUNTIME_TAR_SHA','"663cd8ebaf42adc7748efff3acbe5a9bf02e4d5b647911578df028579b908c4d"')
change_line('MECHANICS_GIT_BLOB','"08c6094dd0a9ef2f1373c58cade7690690e0ffc2"')
assert 'VERSION_NAME="0.9726872"; VERSION_BUILD="26872"' in pre
pre=pre.replace('VERSION_NAME="0.9726872"; VERSION_BUILD="26872"','VERSION_NAME="0.9726873"; VERSION_BUILD="26873"')
for k,a,b in [('ARTZIP','ARTZIP="$WORK/26871_artifact.zip"; ARTDIR="$WORK/artifact_26871"','ARTZIP="$WORK/26872_artifact.zip"; ARTDIR="$WORK/artifact_26872"'),('BASE','BASE="$WORK/exact_successful_26871_compiled_candidate"','BASE="$WORK/exact_successful_26872_compiled_candidate"'),('CAND','CAND="$WORK/candidate_26872"','CAND="$WORK/candidate_26873"')]:
 assert a in pre,k
 pre=pre.replace(a,b)
body={k:rename(v) for k,v in body.items()}
body['verify_package']=r'''verify_package(){
 sha256sum -c 26873_HANDOFF_HASHES.sha256 >/dev/null || fail 'sealed 26873 upload hashes drift'
 sha256sum -c 26873_GENERATED_BUILD_SHA256.txt >/dev/null || fail 'generated 26873 build script hash drift'
 bash -n build_26873_iris_rawr.sh || fail 'exact inherited guarded script shell syntax'
 python3 -S -m py_compile verify_26873_candidate.py verify_26873_patches.py regressions/26873_gpu_resident_owner.py
 rm -rf __pycache__ regressions/__pycache__
 for patch in 26873_FORWARD_FULL_INDEX.patch 26873_ROLLBACK_FULL_INDEX.patch;do
  ! grep -Eq '^(rename from|rename to|copy from|copy to) ' "$patch" || fail 'unexpected rename'
 done
 [[ $(find handoff_payload_26873 -type f | wc -l) -eq 6 ]] || fail 'six-file strict runtime upload scope'
 diff -u 26873_CHANGED_ALLOWLIST.txt <(find handoff_payload_26873 -type f | sed 's#^handoff_payload_26873/##' | LC_ALL=C sort) >/dev/null || fail 'strict runtime allowlist drift'
 sha256sum -c 26873_PAYLOAD_SHA256.txt >/dev/null || fail 'candidate payload hash drift'
 test -f TRIGGER_26873.txt && grep -Fx 'RUN_26873_B_GPU_RESIDENT' TRIGGER_26873.txt >/dev/null || fail 'wrong 26873 trigger'
 ! find . -type f -name '*.apk' | grep -q . || fail 'APK cannot be committed'
 pass '26873 exact sealed candidate-first six-file and inherited 26872 guarded package'
}
'''
body['verify_scope']=r'''verify_scope(){
 [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail 'wrong branch'
 git merge-base --is-ancestor "$RUNTIME_AUTHORITY_COMMIT" HEAD || fail '26872 authority not ancestor'
 [[ -z "$(git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD -- app/src app/version.properties)" ]] || fail 'live app altered before candidate-first install'
 [[ -z "$(git status --porcelain -- app/src app/version.properties)" ]] || fail 'uncommitted live source drift'
 [[ -z "$(git ls-files -- glsl_static)" ]] || fail 'generated shader file tracked'
 diff -u 26873_REPOSITORY_UPLOAD_ALLOWLIST.txt <(git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD | LC_ALL=C sort) >/dev/null || fail 'unexpected uploaded infrastructure/source file'
 [[ "$(git rev-parse "$RUNTIME_AUTHORITY_COMMIT:generate_26872_build.py")" == "$MECHANICS_GIT_BLOB" ]] || fail 'successful 26872 mechanics generator blob mismatch'
 [[ "$(sha build_26872_iris_rawr.sh)" == '042f4550b60ba7efb8e363230a76931969e98c2ffacda3fa310895e98f40b7db' ]] || fail 'successful 26872 17-stage source script drift'
 pass '26873 branch/HEAD, exact 26872 build and strict no-live-source/upload scope'
}
'''
body['obtain_authority']=r'''obtain_authority(){
 [[ -n "$TOKEN" ]] || fail 'GITHUB_TOKEN missing'
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' \
   "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/runs/${RUNTIME_ACTIONS_RUN}" -o "$WORK/26872_run.json"
 python3 -S - "$WORK/26872_run.json" "$RUNTIME_AUTHORITY_COMMIT" "$RUNTIME_ACTIONS_RUN" <<'PY_RUN'
import json,sys
x=json.load(open(sys.argv[1]));assert x['id']==int(sys.argv[3]) and x['conclusion']=='success' and x['head_sha']==sys.argv[2] and x['head_branch']=='experimental-clean-photon-rebuild'
print('PASS successful 26872 Actions run/HEAD/branch')
PY_RUN
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' \
   "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${RUNTIME_ARTIFACT_ID}" -o "$WORK/26872_artifact_metadata.json"
 python3 -S - "$WORK/26872_artifact_metadata.json" <<'PY_ART'
import json,sys
x=json.load(open(sys.argv[1]));assert x['id']==12528194015 and x['name']=='photon-26872-b-preview-stripe' and not x['expired'] and x['digest']=='sha256:b5aa31aa25946f0f1376f8d0fdbead6446a0f119492b6bd7d8bd2fb602fdbb30'
print('PASS successful 26872 artifact identity and digest')
PY_ART
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' \
  "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${RUNTIME_ARTIFACT_ID}/zip" -o "$ARTZIP"
 [[ "$(sha "$ARTZIP")" == "$RUNTIME_ARTIFACT_SHA" ]] || fail '26872 authority artifact hash drift'
 unzip -q "$ARTZIP" -d "$ARTDIR"
 local T="$ARTDIR/build_26872_iris_rawr_outputs/26872_candidate_app_source.tar.gz"
 [[ -f "$T" && "$(sha "$T")" == "$RUNTIME_TAR_SHA" ]] || fail 'exact successful 26872 compiled candidate TAR drift'
 local CS="$ARTDIR/build_26872_iris_rawr_outputs/26872_COMPILER_STATUS.txt"
 for proof in 'REAL GLSL COMPILE: PASS' 'REAL SPIR-V VALIDATION: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS';do
  grep -F "$proof" "$CS" >/dev/null || fail "26872 prior compiler authority missing $proof"
 done
 mkdir -p "$BASE";tar -xzf "$T" -C "$BASE"
 [[ "$(find "$BASE/app" -type f | wc -l)" -eq 1995 ]] || fail 'not successful 26872 compiled file universe'
 (cd "$BASE" && sha256sum -c "$ROOT/26873_BASE_26872_FULL_APP.sha256" >/dev/null) || fail '26872 authority manifest mismatch'
 cat > "$OUT/26873_RESOLVED_AUTHORITIES.txt" <<EOF_AUTH
runtime_commit=$RUNTIME_AUTHORITY_COMMIT
runtime_run=$RUNTIME_ACTIONS_RUN
runtime_artifact_id=$RUNTIME_ARTIFACT_ID
runtime_artifact_sha256=$RUNTIME_ARTIFACT_SHA
runtime_candidate_tar_sha256=$RUNTIME_TAR_SHA
mechanics_generator_blob_sha1=$MECHANICS_GIT_BLOB
mechanics_generated_script_sha256=042f4550b60ba7efb8e363230a76931969e98c2ffacda3fa310895e98f40b7db
EOF_AUTH
 pass 'real successful 26872 exact source universe/complete manifest/prior compilers'
}
'''
# Advance the proven real-artifact rollback chain by exactly one successful build.
mk=body['make_candidate']
assert 'cp -a "$BASE" "$H70"' in mk
mk=mk.replace('cp -a "$BASE" "$H70"','cp -a "$H71" "$H70"')
mk=mk.replace('cp -a "$H71" "$H70";git -C "$H70" init -q','cp -a "$H71" "$H70";rm -rf "$H70/.git";git -C "$H70" init -q')
mk=mk.replace('local H70="$WORK/historical_26870_from_26871"', '''local H71="$WORK/historical_26871_from_26872"
 cp -a "$BASE" "$H71";git -C "$H71" init -q
 (cd "$H71" && git apply --check --reverse "$ROOT/26872_FORWARD_FULL_INDEX.patch" &&
  git apply --reverse "$ROOT/26872_FORWARD_FULL_INDEX.patch" && sha256sum -c "$ROOT/26872_BASE_26871_FULL_APP.sha256" >/dev/null) || fail 'actual 26872->26871 rollback failed'
 local H70="$WORK/historical_26870_from_26871"''')
mk=mk.replace('"$ROOT/26873_BASE_26871_FULL_APP.sha256"','"$ROOT/26872_BASE_26871_FULL_APP.sha256"')
mk=mk.replace('"$BASE" && sha256sum -c "$ROOT/26872_BASE_26871_FULL_APP.sha256"','"$H71" && sha256sum -c "$ROOT/26872_BASE_26871_FULL_APP.sha256"')
mk=mk.replace('regressions/26871_b_shutter_group.py "$H70" "$BASE"','regressions/26871_b_shutter_group.py "$H70" "$H71"')
mk=mk.replace('regressions/26873_b_preview_only.py "$BASE" "$CAND"','regressions/26872_b_preview_only.py "$H71" "$BASE"\n python3 -S regressions/26873_gpu_resident_owner.py "$BASE" "$CAND"')
mk=mk.replace('verify_26873_runtime_shader.py','verify_26872_runtime_shader.py')
body['make_candidate']=mk
assert 'actual 26872->26871 rollback failed' in mk
assert '26873_gpu_resident_owner.py "$BASE" "$CAND"' in mk
# Every native vendor GLSL owner and real compiler remains unchanged.
compiler=body['compile_modified_runtime_shaders']
compiler=compiler.replace('verify_26873_runtime_shader.py','verify_26872_runtime_shader.py')
compiler=compiler.replace('regressions/26873_b_preview_only.py','regressions/26872_b_preview_only.py')
body['compile_modified_runtime_shaders']=compiler
body['verify_successful_mechanics']=r'''verify_successful_mechanics(){
 [[ "$(sha build_26872_iris_rawr.sh)" == '042f4550b60ba7efb8e363230a76931969e98c2ffacda3fa310895e98f40b7db' ]] || fail 'real successful 26872 generated mechanics drift'
 [[ "$(git rev-parse "$RUNTIME_AUTHORITY_COMMIT:generate_26872_build.py")" == "$MECHANICS_GIT_BLOB" ]] || fail 'successful 26872 generator blob drift'
 for validator in verify_26864_rawr_sources.py verify_26864_runtime_glsl.py verify_26864_semantics.py verify_26868_runtime_shader.py verify_26870_runtime_shader.py verify_26871_runtime_shader.py verify_26872_runtime_shader.py regressions/26868_direct_b_long_retire_ab.py regressions/26870_b_automatic_iq.py regressions/26871_b_shutter_group.py regressions/26872_b_preview_only.py;do
  local prior="$WORK/prior_$validator";mkdir -p "$(dirname "$prior")"
  git show "$RUNTIME_AUTHORITY_COMMIT:$validator" > "$prior"
  cmp -s "$prior" "$ROOT/$validator" || fail "successful 26872 validator differs $validator"
 done
 python3 -S - "$ROOT/build_26872_iris_rawr.sh" "$ROOT/build_26873_iris_rawr.sh" <<'PY_STAGES'
from pathlib import Path
import sys
stages=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','verify_candidate_patches','prebuild_safety','assemble','postbuild_proof','clean_extract_replay']
for name in sys.argv[1:]:
 txt=Path(name).read_text();pos=-1
 for stage in stages:
  nxt=txt.find('\n'+stage+'(){',pos+1);assert nxt>pos,(name,stage,'17-stage order deviation');pos=nxt
for cmd in ['./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'./gradlew :app:assembleDebug --stacktrace']:
 assert all(cmd in Path(name).read_text() for name in sys.argv[1:]),('real language/native/assemble command deviation',cmd)
print('PASS exact inherited successful 26872 17-stage compiler/NDK/assembly mechanics')
PY_STAGES
 pass 'actual successful 26872 verification mechanics unchanged; 26873 B-only native input diff audited'
}
'''
body['verify_candidate_patches']=r'''verify_candidate_patches(){
 python3 -S verify_26873_patches.py "$BASE" "$CAND" 26873_FORWARD_FULL_INDEX.patch 26873_ROLLBACK_FULL_INDEX.patch | tee "$OUT/26873_patch_validation.txt"
 pass 'exact 26873 6-file binary full-index 7/12/40 zero-fuzz forward and rollback'
}
'''
body['prebuild_safety']=r'''prebuild_safety(){
 snapshot_live_authority_seeded "$WORK/prebuild_live_snapshot"
 diff -qr "$CAND/app" "$WORK/prebuild_live_snapshot/app" >/dev/null || fail 'frozen compiled candidate versus canonical authority-seeded live mismatch'
 python3 -S verify_26873_candidate.py "$BASE" "$CAND" --root "$ROOT"
 (cd "$CAND" && sha256sum -c "$ROOT/26873_UNCHANGED_PROTECTED.sha256" >/dev/null) || fail 'protected DNG/vendor/preview/native file invariance failed'
 for k in 'REAL GLSL COMPILE: PASS' 'REAL SPIR-V VALIDATION: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS';do
  grep -F "$k" "$OUT/26873_COMPILER_STATUS.txt" >/dev/null || fail "mandatory prebuild compiler gate missing $k"
 done
 cat > "$OUT/26873_PREBUILD_SAFETY.txt" <<EOF_SAFETY
PRE-BUILD SAFETY PROOF PASSED
runtime_authority=successful 26872 $RUNTIME_AUTHORITY_COMMIT run $RUNTIME_ACTIONS_RUN artifact $RUNTIME_ARTIFACT_ID
verification_mechanics=exact successful 26872 inherited 17 stages, real compiler/NDK/assemble commands
runtime_changed_files=6, all B native RAW input ownership plus guarded version
infrastructure_delta=explicit 26873 workflow generator validators manifests and native-owner regression; compiler mechanics identical
prior_files=1995
candidate_files=1995
version_name=$VERSION_NAME
version_build=$VERSION_BUILD
real_compilers=GLSL+SPIR-V+Kotlin+Java+NDK 2 ABI PASS
patch_proof=full-index forward/rollback 7/12/40 fuzz 0 exact
protected_source=1989 files byte-identical to successful 26872; all GLSL/Java/AE/DNG/vendor untouched
EOF_SAFETY
 pass 'PRE-BUILD SAFETY PROOF PASSED'
}
'''
body['clean_extract_replay']=r'''clean_extract_replay(){
 local replay="$WORK/clean_replay_candidate" exp="$WORK/extracted_candidate_tar"
 rm -rf "$replay" "$exp";mkdir -p "$exp"
 sha256sum -c 26873_HANDOFF_HASHES.sha256 >/dev/null
 sha256sum -c 26873_GENERATED_BUILD_SHA256.txt >/dev/null
 bash -n build_26873_iris_rawr.sh
 python3 -S -m py_compile verify_26873_candidate.py verify_26873_patches.py regressions/26873_gpu_resident_owner.py
 rm -rf __pycache__ regressions/__pycache__
 python3 -S verify_26873_candidate.py "$BASE" "$replay" --root "$ROOT" --transform
 diff -qr "$CAND/app" "$replay/app" >/dev/null || fail 'final clean extracted transform not exact'
 sha256sum -c "$OUT/26873_candidate_app_source.tar.gz.sha256" >/dev/null
 tar -xzf "$OUT/26873_candidate_app_source.tar.gz" -C "$exp"
 diff -qr "$CAND/app" "$exp/app" >/dev/null || fail 'compiler-tested frozen candidate changed during assembly'
 python3 -S verify_26873_candidate.py "$BASE" "$exp" --root "$ROOT"
 python3 -S verify_26873_patches.py "$BASE" "$exp" 26873_FORWARD_FULL_INDEX.patch 26873_ROLLBACK_FULL_INDEX.patch > "$OUT/26873_final_patch_replay.txt"
 python3 -S verify_26864_runtime_glsl.py "$BASE" "$exp" --out "$OUT/26873_final_runtime_glsl" | tee "$OUT/26873_final_glsl_static.txt"
 python3 -S verify_26864_rawr_sources.py "$exp/app"
 python3 -S regressions/26864_glsl_reserved_identifiers.py "$exp/app"
 python3 -S regressions/26864_wronski_publisher.py "$WORK/historical_26867_from_26868/app"
 python3 -S verify_26864_semantics.py "$WORK/historical_26867_from_26868/app" --numeric
 python3 -S regressions/26865_b_lsc_owner.py "$exp/app"
 python3 -S regressions/26866_b_color_only.py "$WORK/historical_26866_from_26867/app"
 python3 -S regressions/26867_b_highlight_ab_retired.py "$WORK/historical_26867_from_26868/app"
 python3 -S regressions/26868_direct_b_long_retire_ab.py "$WORK/historical_26868_from_26870/app"
 python3 -S regressions/26870_b_automatic_iq.py "$WORK/historical_26868_from_26870/app" "$WORK/historical_26870_from_26871/app"
 python3 -S regressions/26871_b_shutter_group.py "$WORK/historical_26870_from_26871" "$WORK/historical_26871_from_26872"
 python3 -S regressions/26872_b_preview_only.py "$WORK/historical_26871_from_26872" "$BASE"
 python3 -S regressions/26873_gpu_resident_owner.py "$BASE" "$exp"
 python3 -S verify_26867_runtime_shader.py "$exp" --out "$OUT/26873_final_white_fade"
 python3 -S verify_26868_runtime_shader.py "$exp" --out "$OUT/26873_final_b_long"
 python3 -S verify_26871_runtime_shader.py "$exp" --out "$OUT/26873_final_prior_shader"
 python3 -S verify_26872_runtime_shader.py "$exp" --out "$OUT/26873_final_preview_shaders"
 grep -Fx 'VERSION_NAME=0.9726873' "$exp/app/version.properties" >/dev/null
 grep -Fx 'VERSION_BUILD=26873' "$exp/app/version.properties" >/dev/null
 for k in 'REAL GLSL COMPILE: PASS' 'REAL SPIR-V VALIDATION: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS';do
  grep -F "$k" "$OUT/26873_COMPILER_STATUS.txt" >/dev/null || fail "final successful compiler proof missing $k"
 done
 pass '26873 clean-extract source/protected/regressions/manifests/patches/version + real build'
}
'''
# Preserve inherited stages and exact original real compiler/NDK/assemble command order.
text=pre+''.join(body[k] for k in inherited_order)+rename(old[end:])
for k in stages:assert '\n'+k+'(){' in text
assert text.count(end_marker)==1
for cmd in ['./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'./gradlew :app:assembleDebug --stacktrace']:
 assert cmd in old and cmd in text,('inherited real compiler changed',cmd)
assert '# IRIS_26873_AUTHORITATIVE_ACTIONS_STAGE_ORDER' in text
assert 'RUNTIME_ARTIFACT_ID="12528194015"' in text
assert 'VERSION_NAME="0.9726873"' in text and 'VERSION_BUILD="26873"' in text
assert 'FULL ANDROID ASSEMBLE: NOT RUN YET' in text
# Current generated script is a deterministic function of two exact pinned
# prior generators; its checksum is sealed for every subsequent workflow stage.
dst.write_text(text)
diff=''.join(difflib.unified_diff(old.splitlines(keepends=True),text.splitlines(keepends=True),fromfile='exact_successful_26872_17_stages',tofile='26873_guarded_candidate_17_stages'))
(root/'26873_BUILD_INFRASTRUCTURE_DIFF.txt').write_text(diff)
(root/'26873_GENERATED_BUILD_SHA256.txt').write_text(f'{sha(text.encode())}  build_26873_iris_rawr.sh\n')
print('PASS 26873 exact successful 26872 17-stage chain, 3 real compilers+NDK+assemble order, explicit full infrastructure diff')
print('generated_sha256='+sha(text.encode()),'infrastructure_diff_sha256='+sha(diff.encode()))
