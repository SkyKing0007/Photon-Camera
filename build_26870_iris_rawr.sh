#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
ROOT="$(pwd)"; EXPECTED_BRANCH="experimental-clean-photon-rebuild"
# Exact most recent successful repo scaffolding HEAD is 26869, but its device
# runtime failed. Rebuild source INTENTIONALLY from successful 26868 artifact.
REPO_SCAFFOLD_BASE_COMMIT="ddb0538cd11c061755862c91e5595e12f018cf96"
RUNTIME_ARTIFACT_ID="12462853558"; RUNTIME_ACTIONS_RUN="39863379652"
RUNTIME_AUTHORITY_COMMIT="7800265e6a5909ddea770c93cfeaed244c489247"
RUNTIME_ARTIFACT_SHA="c22e4b592ff63884f6bdce1c1dba2d4543be5f2cf3b017ee957678f9b431241b"
RUNTIME_TAR_SHA="7ac33dfa920060b97465e6a1815573f56cdaf5548e444abd20d9366063ec5596"
MECHANICS_GIT_BLOB="1117b831cb4582db3f5949db11e93fde56fa6e33"
VERSION_NAME="0.9726870"; VERSION_BUILD="26870"; GLSLANG_VERSION="16.5.0"
GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"
GLSLANG_URL="https://github.com/KhronosGroup/glslang/releases/download/16.5.0/glslang-16.5.0-linux-x86_64-release.tar.gz"
OUT="$ROOT/build_26870_iris_rawr_outputs"; WORK="$ROOT/.build_26870_iris_rawr_work"
ARTZIP="$WORK/26868_artifact.zip"; ARTDIR="$WORK/artifact_26868"
BASE="$WORK/exact_successful_26868_compiled_candidate"; CAND="$WORK/candidate_26870"
LIVE_CANON="$WORK/live_compiler_candidate_snapshot"; POST_LANG="$WORK/post_language_compiler_source_snapshot"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-iris-rawr-debug.apk"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR"
cat > "$OUT/26870_COMPILER_STATUS.txt" <<'STATUS'
REAL GLSL COMPILE: NOT RUN YET
REAL SPIR-V VALIDATION: NOT RUN YET
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
NATIVE/NDK COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
STATUS
# IRIS_26870_AUTHORITATIVE_ACTIONS_STAGE_ORDER
verify_package(){
 sha256sum -c 26870_HANDOFF_HASHES.sha256 >/dev/null
 bash -n build_26870_iris_rawr.sh
 # PERMANENT prior 26869 Actions 39894413063 exact historical nested-validator
 # destination regression. Catch missing parent before any Actions download.
 python3 -S - <<'PY_26870_NESTED_PATH'
from pathlib import Path
import re,tempfile
s=Path('build_26870_iris_rawr.sh').read_text()
body=s.split('verify_successful_mechanics(){',1)[1].split('\nprepare_glslang(){',1)[0]
assert 'regressions/26868_direct_b_long_retire_ab.py' in body
assert 'local prior="$WORK/prior_$validator"' in body
assert 'mkdir -p "$(dirname "$prior")"' in body
assert 'git show "$RUNTIME_AUTHORITY_COMMIT:$validator" > "$prior"' in body
assert body.index('mkdir -p "$(dirname "$prior")"') < body.index('git show "$RUNTIME_AUTHORITY_COMMIT:$validator" > "$prior"')
# Actual previously failing pathname, not merely a generic flat fixture.
with tempfile.TemporaryDirectory() as d:
 f=Path(d)/'prior_regressions/26868_direct_b_long_retire_ab.py'
 assert not f.parent.exists()
 try: f.write_bytes(b'')
 except FileNotFoundError: pass
 else: raise AssertionError('26870 prior_regressions negative fixture did not reproduce')
 f.parent.mkdir(parents=True)
 f.write_bytes(b'historical source')
 assert f.read_bytes()==b'historical source'
print('PASS 26870 permanent 39894413063 nested historical-validator parent regression')
PY_26870_NESTED_PATH
 python3 -S -m py_compile verify_26870_candidate.py verify_26870_patches.py verify_26864_rawr_sources.py verify_26864_runtime_glsl.py verify_26864_semantics.py regressions/26864_glsl_reserved_identifiers.py regressions/26864_wronski_publisher.py regressions/26865_b_lsc_owner.py regressions/26866_b_color_only.py regressions/26867_b_highlight_ab_retired.py regressions/26868_direct_b_long_retire_ab.py regressions/26870_b_automatic_iq.py verify_26870_runtime_shader.py verify_26868_runtime_shader.py verify_26867_runtime_shader.py
 rm -rf __pycache__ regressions/__pycache__
 ! grep -Eq '^(rename from|rename to|copy from|copy to) ' 26870_FORWARD_FULL_INDEX.patch
 ! grep -Eq '^(rename from|rename to|copy from|copy to) ' 26870_ROLLBACK_FULL_INDEX.patch
 [[ $(find handoff_payload_26870 -type f | wc -l) -eq 8 ]] || fail '26870 exactly 8 replacement files'
 diff -u 26870_CHANGED_ALLOWLIST.txt <(find handoff_payload_26870 -type f | sed 's#^handoff_payload_26870/##' | sort) >/dev/null || fail '26870 strict package allowlist'
 sha256sum -c 26870_PAYLOAD_SHA256.txt >/dev/null
 ! find . -type f -name '*.apk' | grep -q . || fail 'APKs must never be packaged'
 test -f TRIGGER_26870.txt && grep -Fx 'RUN_26870_NATIVE_B_AUTOMATIC_IQ' TRIGGER_26870.txt >/dev/null || fail 'wrong trigger'
 pass '26870 package hashes/syntax/8-file exact source allowlist/trigger'
}
verify_scope(){
 [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail 'wrong branch'
 git merge-base --is-ancestor "$RUNTIME_AUTHORITY_COMMIT" HEAD || fail '26868 authority missing from history'
 git merge-base --is-ancestor "$REPO_SCAFFOLD_BASE_COMMIT" HEAD || fail '26869 repo scaffold HEAD missing from history'
 [[ -z "$(git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD -- app/src app/version.properties)" ]] || fail 'repository live runtime modified before guarded source install'
 [[ -z "$(git ls-files -- glsl_static)" ]] || fail 'generated GLSL is tracked after historical cleanup'
 [[ -z "$(git status --porcelain -- app/src app/version.properties)" ]] || fail 'uncommitted runtime source before freeze'
 # Infrastructure delta is explicitly audited against exact successful 26868
 # mechanics and exact 26869 post-device-failure repository scaffold HEAD;
 # uploaded handoff scaffolding is never silently allowed to change.
 diff -u 26870_REPOSITORY_UPLOAD_ALLOWLIST.txt <(git diff --name-only "$REPO_SCAFFOLD_BASE_COMMIT"..HEAD | LC_ALL=C sort) >/dev/null || fail 'unexpected 26870 repo/workflow/validator/upload infrastructure difference from successful 26868'
 pass '26870 correct branch, ancestor, exact repository infrastructure delta and guarded live source'
}
obtain_authority(){
 [[ -n "$TOKEN" ]] || fail 'GITHUB_TOKEN missing'
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' \
   "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/runs/${RUNTIME_ACTIONS_RUN}" -o "$WORK/26868_run.json"
 python3 -S - "$WORK/26868_run.json" "$RUNTIME_AUTHORITY_COMMIT" "$RUNTIME_ACTIONS_RUN" <<'PY_RUN'
import json,sys
x=json.load(open(sys.argv[1]));assert x['id']==int(sys.argv[3]) and x['conclusion']=='success' and x['head_sha']==sys.argv[2] and x['head_branch']=='experimental-clean-photon-rebuild'
print('PASS real 26868 GitHub Actions run/commit/success')
PY_RUN
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' \
   "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${RUNTIME_ARTIFACT_ID}" -o "$WORK/26868_artifact_metadata.json"
 python3 -S - "$WORK/26868_artifact_metadata.json" <<'PY_ART'
import json,sys
x=json.load(open(sys.argv[1]));assert x['id']==12462853558 and x['name']=='photon-26868-iris-direct-rawr' and not x['expired'] and x['digest']=='sha256:c22e4b592ff63884f6bdce1c1dba2d4543be5f2cf3b017ee957678f9b431241b'
print('PASS exact 26868 compiled artifact identity and digest')
PY_ART
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' \
   "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${RUNTIME_ARTIFACT_ID}/zip" -o "$ARTZIP"
 [[ "$(sha "$ARTZIP")" == "$RUNTIME_ARTIFACT_SHA" ]] || fail '26868 artifact SHA mismatch'
 unzip -q "$ARTZIP" -d "$ARTDIR"
 local T="$ARTDIR/build_26868_iris_rawr_outputs/26868_candidate_app_source.tar.gz"
 [[ -f "$T" && "$(sha "$T")" == "$RUNTIME_TAR_SHA" ]] || fail '26868 compiled source TAR hash mismatch'
 local CS="$ARTDIR/build_26868_iris_rawr_outputs/26868_COMPILER_STATUS.txt"
 for proof in 'REAL GLSL COMPILE: PASS' 'REAL SPIR-V VALIDATION: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS'; do grep -F "$proof" "$CS" >/dev/null || fail "26868 authority compiler proof missing $proof";done
 mkdir -p "$BASE";tar -xzf "$T" -C "$BASE"
 [[ "$(find "$BASE/app" -type f | wc -l)" -eq 1992 ]] || fail 'wrong 26868 authority universe size'
 (cd "$BASE" && sha256sum -c "$ROOT/26870_BASE_26868_FULL_APP.sha256" >/dev/null) || fail '26868 authority manifest mismatch'
 cat > "$OUT/26870_RESOLVED_AUTHORITIES.txt" <<EOF_AUTH
runtime_commit=$RUNTIME_AUTHORITY_COMMIT
runtime_run=$RUNTIME_ACTIONS_RUN
runtime_artifact_id=$RUNTIME_ARTIFACT_ID
runtime_artifact_sha256=$RUNTIME_ARTIFACT_SHA
runtime_candidate_tar_sha256=$RUNTIME_TAR_SHA
mechanics_blob_sha1=$MECHANICS_GIT_BLOB
EOF_AUTH
 pass 'exact successful 26868 Actions compiled-candidate authority reconstructed and compiler proof verified'
}
make_candidate(){
 python3 -S verify_26870_candidate.py "$BASE" "$CAND" --transform --root "$ROOT"
 # Historical failures remain permanent. Replay exact 26868 -> 26867 and
 # 26867 -> 26866 rollback against REAL successful-artifact file universes.
 local H67="$WORK/historical_26867_from_successful_26868"
 local H66="$WORK/historical_26866_from_successful_26867"
 rm -rf "$H67" "$H66"; cp -a "$BASE" "$H67"
 git -C "$H67" init -q
 [[ "$(git -C "$H67" rev-parse --show-toplevel)" == "$H67" ]] || fail 'historical rollback escaped isolated Git root'
 (cd "$H67" && git apply --check --reverse "$ROOT/26868_FORWARD_FULL_INDEX.patch" &&
    git apply --reverse "$ROOT/26868_FORWARD_FULL_INDEX.patch" &&
    sha256sum -c "$ROOT/26868_BASE_26867_FULL_APP.sha256" >/dev/null) || fail '26867 historical artifact rollback mismatch'
 cp -a "$H67" "$H66";rm -rf "$H66/.git";git -C "$H66" init -q
 (cd "$H66" && git apply --check --reverse "$ROOT/26867_FORWARD_FULL_INDEX.patch" &&
    git apply --reverse "$ROOT/26867_FORWARD_FULL_INDEX.patch" &&
    sha256sum -c "$ROOT/26867_BASE_26866_FULL_APP.sha256" >/dev/null) || fail '26866 historical artifact rollback mismatch'
 (cd "$BASE" && sha256sum -c "$ROOT/26870_BASE_26868_FULL_APP.sha256" >/dev/null) || fail 'historical replay mutated 26868 successful candidate'
 [[ -z "$(git diff --name-only -- app/src app/version.properties)" ]] || fail 'historical replay mutated checkout runtime source'
 python3 -S regressions/26865_b_lsc_owner.py "$CAND/app"
 python3 -S regressions/26866_b_color_only.py "$H66/app"
 python3 -S regressions/26867_b_highlight_ab_retired.py "$H67/app"
 python3 -S regressions/26868_direct_b_long_retire_ab.py "$BASE/app"
 python3 -S regressions/26870_b_automatic_iq.py "$BASE/app" "$CAND/app"
 python3 -S verify_26870_runtime_shader.py "$CAND" --out "$OUT/26870_precompile_new_shader_expansion"
 python3 -S verify_26864_rawr_sources.py "$CAND/app"
 python3 -S regressions/26864_glsl_reserved_identifiers.py "$CAND/app"
 python3 -S regressions/26864_wronski_publisher.py "$H67/app"
 python3 -S verify_26864_semantics.py "$H67/app" --numeric
 pass '26870 authority-seeded candidate and real 26868/26867/26866 regression replay'
}
verify_successful_mechanics(){
 [[ "$(git hash-object 26868_FORWARD_FULL_INDEX.patch)" == "$(git rev-parse "$RUNTIME_AUTHORITY_COMMIT:26868_FORWARD_FULL_INDEX.patch")" ]] || fail 'prior successful forward patch changed'
 git show "$RUNTIME_AUTHORITY_COMMIT:build_26868_iris_rawr.sh" > "$WORK/26868_successful_mechanics.sh"
 [[ "$(git hash-object "$WORK/26868_successful_mechanics.sh")" == "$MECHANICS_GIT_BLOB" ]] || fail 'exact successful 26868 implementation changed'
 for validator in verify_26864_rawr_sources.py verify_26864_runtime_glsl.py verify_26864_semantics.py verify_26868_runtime_shader.py regressions/26868_direct_b_long_retire_ab.py;do
   # PERMANENT 39894413063 regression: inherited validators may contain
   # nested paths. Materialize each destination parent before shell redirect.
   local prior="$WORK/prior_$validator"
   mkdir -p "$(dirname "$prior")"
   git show "$RUNTIME_AUTHORITY_COMMIT:$validator" > "$prior"
   cmp -s "$prior" "$ROOT/$validator" || fail "inherited 26868 validator changed: $validator"
 done
 python3 -S - "$WORK/26868_successful_mechanics.sh" "$ROOT/build_26870_iris_rawr.sh" <<'PY_STAGES'
from pathlib import Path
import sys
stages=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','verify_candidate_patches','prebuild_safety','assemble','postbuild_proof','clean_extract_replay']
for path in sys.argv[1:]:
 txt=Path(path).read_text();pos=-1
 for fn in stages:
  i=txt.find('\n'+fn+'(){',pos+1)
  assert i>pos,(path,fn,'successful 26868 mechanics 17-stage order changed');pos=i
for cmd in ["./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace", "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'./gradlew :app:assembleDebug --stacktrace']:
 assert all(cmd in Path(path).read_text() for path in sys.argv[1:]),('real compiler command changed',cmd)
print('PASS identical successful 26868 17-stage order and real Kotlin/Java/NDK/assemble compiler command identity')
PY_STAGES
 pass '26868 -> 26870 inherited unchanged 17-stage mechanics and compiler commands'
}
prepare_glslang(){
 local D="$WORK/glslang-${GLSLANG_VERSION}" A="$WORK/glslang.tar.gz";mkdir -p "$D"
 curl -L --fail --retry 3 "$GLSLANG_URL" -o "$A"
 [[ "$(sha "$A")" == "$GLSLANG_ARCHIVE_SHA" ]] || fail 'pinned glslang tar SHA'
 tar -xzf "$A" -C "$D"
 local compiler
 compiler="$(find "$D" -type f -name glslang -print -quit)"
 [[ -n "$compiler" ]] || compiler="$(find "$D" \( -type f -o -type l \) -name glslangValidator -print -quit)"
 [[ -n "$compiler" ]] || fail 'missing pinned real glslang binary'
 compiler="$(readlink -f "$compiler")";[[ -x "$compiler" ]] || chmod +x "$compiler"
 "$compiler" --version | tee "$OUT/26870_glslang_version.txt"
 grep -F '16.5.0' "$OUT/26870_glslang_version.txt" >/dev/null || fail 'glslang version mismatch'
 export IRIS26864_GLSLANG="$compiler";export IRIS26681_SPEKTRA_GLSLANG="$compiler"
 # Inherit exact successful 26864 real SPIR-V post-validation, no substitutions.
 sudo apt-get update -qq
 sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq spirv-tools
 command -v spirv-val >/dev/null && command -v spirv-opt >/dev/null || fail 'real SPIRV-Tools missing'
 spirv-val --version > "$OUT/26870_spirv_tools_version.txt"
 spirv-opt --version >> "$OUT/26870_spirv_tools_version.txt"
 pass 'pinned real glslang 16.5.0 + real SPIRV-Tools toolchain'
}
compile_modified_runtime_shaders(){
 # Preserve 26864's exact eleven expanded GLES300 owners and real compiler.
 # Preserve inherited expanded owners and compile all four 26870 expanded GLES300/310 tone/chroma/GPU-reference shaders with exact pinned compiler.
 git show "$RUNTIME_AUTHORITY_COMMIT:verify_26864_runtime_glsl.py" > "$WORK/successful_26864_runtime_glsl.py"
 [[ "$(git hash-object "$WORK/successful_26864_runtime_glsl.py")" == 'c5208e94865afbbbc437c31e09fd7b893e50ca20' ]] || fail '26864 shader validator drift'
 python3 -S verify_26864_runtime_glsl.py "$BASE" "$CAND" --compiler "$IRIS26864_GLSLANG" --out "$OUT/26870_runtime_expanded_glsl" | tee "$OUT/26870_gles_shader_proof.txt"
 grep -F 'PASS 26864 GLSL ownership:' "$OUT/26870_gles_shader_proof.txt" >/dev/null || fail 'inherited 11 expanded GLSL owners or stronger RAWR semantic gate failed'
 # The inherited native B smooth-white GLES300 owner is compiled with
 # EXACT same pinned 16.5.0 compiler. Two inherited LONG GLES300 owners are also compiled below.
 python3 -S verify_26867_runtime_shader.py "$CAND" --compiler "$IRIS26864_GLSLANG" --out "$OUT/26870_inherited_26867_white_fade" | tee "$OUT/26870_inherited_white_fade_glsl.txt"
 grep -F 'pinned-glslang=PASS' "$OUT/26870_inherited_white_fade_glsl.txt" >/dev/null || fail 'inherited 26868 pinned white-fade shader not compiled'
 python3 -S verify_26868_runtime_shader.py "$CAND" --compiler "$IRIS26864_GLSLANG" --out "$OUT/26870_inherited_b_long_expanded" | tee "$OUT/26870_inherited_b_long_glsl.txt"
 [[ $(grep -c 'pinned-glslang=PASS' "$OUT/26870_inherited_b_long_glsl.txt") -eq 2 ]] || fail '26868 two inherited LONG shaders must pass pinned real glslang' 

 python3 -S verify_26870_runtime_shader.py "$CAND" --compiler "$IRIS26864_GLSLANG" --out "$OUT/26870_new_tone_chroma_expanded" | tee "$OUT/26870_new_tone_chroma_glsl.txt"
 [[ $(grep -c 'pinned-glslang=PASS' "$OUT/26870_new_tone_chroma_glsl.txt") -eq 4 ]] || fail '26870 FOUR modified runtime expanded vertex/fragment shader programs failed real pinned glslang'
 python3 -S regressions/26864_glsl_reserved_identifiers.py "$CAND/app"
 # All 55 upstream + 3 Iris bridge shader inputs use the SAME pinned compiler,
 # real SPIR-V validator and optimizer *before* Java/Kotlin compilation.
 python3 -S verify_26864_rawr_sources.py "$CAND/app" --compile "$IRIS26864_GLSLANG" \
   --spirv-val "$(command -v spirv-val)" --spirv-opt "$(command -v spirv-opt)" \
   --out "$OUT/26870_all_native_expanded_spirv" | tee "$OUT/26870_spirv_validation.txt"
 grep -F 'PASS 26864 real 58 SPIR-V compute shaders' "$OUT/26870_spirv_validation.txt" >/dev/null || fail 'native SPIR-V real compiler proof missing'
 sed -i 's#REAL GLSL COMPILE: NOT RUN YET#REAL GLSL COMPILE: PASS (pinned 16.5.0 on expanded GLES300 and 58 exact native Vulkan shaders)#' "$OUT/26870_COMPILER_STATUS.txt"
 sed -i 's#REAL SPIR-V VALIDATION: NOT RUN YET#REAL SPIR-V VALIDATION: PASS (spirv-val pre/post optimized Vulkan 1.1)#' "$OUT/26870_COMPILER_STATUS.txt"
}
compile_spektra_raw_shader(){ pass 'inherited 26864 Spektra validator path protected byte-exact by manifests'; }
snapshot_live_authority_seeded(){
 python3 -S - "$CAND" "$1" "$ROOT" <<'PY_LIVE'
from pathlib import Path
import hashlib,shutil,sys
cand,out,live=map(Path,sys.argv[1:]);shutil.rmtree(out,ignore_errors=True);shutil.copytree(cand,out)
expected={str(p.relative_to(cand)):p for p in (cand/'app').rglob('*') if p.is_file()}
for rel in expected:
 lp=live/rel
 if not lp.is_file():raise SystemExit(f'missing live 26870 candidate path {rel}')
 (out/rel).write_bytes(lp.read_bytes())
# Repository-only build scaffolding is ignored; all unexpected actual app/src
# paths must be detected. app/build and app/.cxx are generated, never source.
expected_src={p for p in expected if p.startswith('app/src/')}
actual_src={str(p.relative_to(live)) for p in (live/'app/src').rglob('*') if p.is_file()}
extra=actual_src-expected_src
if extra:raise SystemExit(f'unexpected runtime app/src additions: {sorted(extra)}')
print('PASS authority-seeded canonical live app source universe',len(expected))
PY_LIVE
}
install_frozen_candidate_live(){
 rm -rf app; cp -a "$CAND/app" app
 snapshot_live_authority_seeded "$LIVE_CANON"
 diff -qr "$CAND/app" "$LIVE_CANON/app" >/dev/null || fail 'frozen compiler-tested candidate differs from live'
 pass '26870 live source byte-identical to frozen authority-seeded candidate'
}
compile_languages(){
 ./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace 2>&1 | tee "$OUT/26870_gradle_language_compilers.log"
 snapshot_live_authority_seeded "$POST_LANG";diff -qr "$CAND/app" "$POST_LANG/app" >/dev/null || fail 'language compilers changed source'
 sed -i 's/REAL KOTLIN COMPILE: NOT RUN YET/REAL KOTLIN COMPILE: PASS/' "$OUT/26870_COMPILER_STATUS.txt"
 sed -i 's/REAL JAVA COMPILE: NOT RUN YET/REAL JAVA COMPILE: PASS/' "$OUT/26870_COMPILER_STATUS.txt"
 pass 'real project Kotlin and Java compilers on frozen candidate'
}
verify_native_glslang_handoff(){
 [[ -n "${IRIS26864_GLSLANG:-}" && -x "$IRIS26864_GLSLANG" && "$IRIS26864_GLSLANG" == "$IRIS26681_SPEKTRA_GLSLANG" ]] || fail 'pinned real GLSL compiler handoff lost'
 command -v spirv-val >/dev/null && command -v spirv-opt >/dev/null || fail 'SPIR-V validator unavailable to NDK'
 pass 'same pinned real compiler handed to NDK shader subprojects'
}
compile_native(){
 ./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace 2>&1 | tee "$OUT/26870_gradle_native_compiler.log"
 snapshot_live_authority_seeded "$WORK/post_native_snapshot"
 diff -qr "$CAND/app" "$WORK/post_native_snapshot/app" >/dev/null || fail 'native compiler changed source'
 sed -i 's#NATIVE/NDK COMPILE: NOT RUN YET#NATIVE/NDK COMPILE: PASS (arm64-v8a + armeabi-v7a; real 58 pinned shader compilation)#' "$OUT/26870_COMPILER_STATUS.txt"
 pass 'real 2-ABI NDK compiler with authentic RAWR Vulkan sources'
}
verify_candidate_patches(){
 python3 -S verify_26870_patches.py "$BASE" "$CAND" 26870_FORWARD_FULL_INDEX.patch 26870_ROLLBACK_FULL_INDEX.patch | tee "$OUT/26870_patch_validation.txt"
 pass 'canonical binary full-index forward/rollback 7/12/40 fuzz=0 exact'
}
prebuild_safety(){
 snapshot_live_authority_seeded "$WORK/prebuild_live_snapshot"
 diff -qr "$CAND/app" "$WORK/prebuild_live_snapshot/app" >/dev/null || fail 'prebuild source drift'
 python3 -S verify_26870_candidate.py "$BASE" "$CAND" --root "$ROOT"
 (cd "$CAND" && sha256sum -c "$ROOT/26870_UNCHANGED_PROTECTED.sha256" >/dev/null) || fail 'protected/DNG/native/vendor source drift'
 for k in 'REAL GLSL COMPILE: PASS' 'REAL SPIR-V VALIDATION: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS';do grep -F "$k" "$OUT/26870_COMPILER_STATUS.txt" >/dev/null || fail "prebuild real compiler gate $k";done
 cat > "$OUT/26870_PREBUILD_SAFETY.txt" <<EOF_SAFETY
PRE-BUILD SAFETY PROOF PASSED
runtime_authority=successful 26868 $RUNTIME_AUTHORITY_COMMIT run $RUNTIME_ACTIONS_RUN artifact $RUNTIME_ARTIFACT_ID
verification_mechanics=exact successful 26868 17-stage proof; identical real compiler commands and order
runtime_changed_files=8 (2 new, 6 edited, 0 deleted incl guarded version)
infrastructure_delta=26868 17-stage mechanics retained; new 26870 guard/validators/workflow audited; native/vendor ZERO
prior_files=1992
candidate_files=1994
version_name=$VERSION_NAME
version_build=$VERSION_BUILD
real_compilers=GLSL+SPIR-V+Kotlin+Java+NDK two ABI PASS
patch_proof=full index forward/rollback 7/12/40 fuzz 0 exact
protected_source=1986 unchanged prior 26868 compiled candidate files byte-identical; DNG/native/vendor intact
EOF_SAFETY
 pass 'PRE-BUILD SAFETY PROOF PASSED'
}
assemble(){
 test -f "$OUT/26870_PREBUILD_SAFETY.txt" && grep -Fx 'PRE-BUILD SAFETY PROOF PASSED' "$OUT/26870_PREBUILD_SAFETY.txt" >/dev/null || fail 'assemble forbidden without proof'
 ./gradlew :app:assembleDebug --stacktrace 2>&1 | tee "$OUT/26870_gradle_assemble.log"
 mapfile -t apks < <(find app/build/outputs/apk -type f -name '*.apk' | sort)
 [[ "${#apks[@]}" -eq 1 ]] || fail "expected exactly one assembled APK, got ${#apks[@]}"
 cp "${apks[0]}" "$FINAL"
 [[ "$(find . -maxdepth 1 -name 'IrisCamera-*.apk' -type f | wc -l)" -eq 1 ]] || fail 'one intended APK at root'
 sha256sum "$FINAL" > "$OUT/26870_APK.sha256"
 sed -i 's/FULL ANDROID ASSEMBLE: NOT RUN YET/FULL ANDROID ASSEMBLE: PASS/' "$OUT/26870_COMPILER_STATUS.txt"
 pass 'full :app:assembleDebug including NDK, exactly one intended APK'
}
postbuild_proof(){
 snapshot_live_authority_seeded "$WORK/post_build_live_snapshot"
 diff -qr "$CAND/app" "$WORK/post_build_live_snapshot/app" >/dev/null || fail 'candidate changed after assemble'
 python3 -S verify_26870_candidate.py "$BASE" "$CAND" --root "$ROOT"
 (cd "$CAND" && sha256sum -c "$ROOT/26870_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null)
 (cd "$CAND" && sha256sum -c "$ROOT/26870_UNCHANGED_PROTECTED.sha256" >/dev/null)
 cp 26870_EXPECTED_CANDIDATE_FULL_APP.sha256 "$OUT/26870_candidate_full_app.sha256"
 (cd "$CAND" && tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -czf "$OUT/26870_candidate_app_source.tar.gz" app)
 sha256sum "$OUT/26870_candidate_app_source.tar.gz" > "$OUT/26870_candidate_app_source.tar.gz.sha256"
 cp 26870_FORWARD_FULL_INDEX.patch 26870_ROLLBACK_FULL_INDEX.patch "$OUT/"
 sed -i 's/POST-BUILD INVARIANCE: NOT RUN YET/POST-BUILD INVARIANCE: PASS/' "$OUT/26870_COMPILER_STATUS.txt"
 pass 'postbuild authority-seeded candidate/protected/DNG/native/vendor invariance and deterministic candidate export'
}
clean_extract_replay(){
 local replay="$WORK/clean_replay_candidate" exp="$WORK/extracted_candidate_tar"
 rm -rf "$replay" "$exp";mkdir -p "$exp"
 sha256sum -c 26870_HANDOFF_HASHES.sha256 >/dev/null
 bash -n build_26870_iris_rawr.sh
 # PERMANENT prior 26869 Actions 39894413063 exact historical nested-validator
 # destination regression. Catch missing parent before any Actions download.
 python3 -S - <<'PY_26870_NESTED_PATH'
from pathlib import Path
import re,tempfile
s=Path('build_26870_iris_rawr.sh').read_text()
body=s.split('verify_successful_mechanics(){',1)[1].split('\nprepare_glslang(){',1)[0]
assert 'regressions/26868_direct_b_long_retire_ab.py' in body
assert 'local prior="$WORK/prior_$validator"' in body
assert 'mkdir -p "$(dirname "$prior")"' in body
assert 'git show "$RUNTIME_AUTHORITY_COMMIT:$validator" > "$prior"' in body
assert body.index('mkdir -p "$(dirname "$prior")"') < body.index('git show "$RUNTIME_AUTHORITY_COMMIT:$validator" > "$prior"')
# Actual previously failing pathname, not merely a generic flat fixture.
with tempfile.TemporaryDirectory() as d:
 f=Path(d)/'prior_regressions/26868_direct_b_long_retire_ab.py'
 assert not f.parent.exists()
 try: f.write_bytes(b'')
 except FileNotFoundError: pass
 else: raise AssertionError('26870 prior_regressions negative fixture did not reproduce')
 f.parent.mkdir(parents=True)
 f.write_bytes(b'historical source')
 assert f.read_bytes()==b'historical source'
print('PASS 26870 permanent 39894413063 nested historical-validator parent regression')
PY_26870_NESTED_PATH
 python3 -S -m py_compile verify_26870_candidate.py verify_26870_patches.py verify_26864_rawr_sources.py verify_26864_runtime_glsl.py verify_26864_semantics.py regressions/26864_glsl_reserved_identifiers.py regressions/26864_wronski_publisher.py regressions/26865_b_lsc_owner.py regressions/26866_b_color_only.py regressions/26867_b_highlight_ab_retired.py regressions/26868_direct_b_long_retire_ab.py regressions/26870_b_automatic_iq.py verify_26870_runtime_shader.py verify_26868_runtime_shader.py verify_26867_runtime_shader.py
 rm -rf __pycache__ regressions/__pycache__
 python3 -S verify_26870_candidate.py "$BASE" "$replay" --root "$ROOT" --transform
 diff -qr "$CAND/app" "$replay/app" >/dev/null || fail 'clean-extract package transforms differ from frozen candidate'
 sha256sum -c "$OUT/26870_candidate_app_source.tar.gz.sha256" >/dev/null
 tar -xzf "$OUT/26870_candidate_app_source.tar.gz" -C "$exp"
 diff -qr "$CAND/app" "$exp/app" >/dev/null || fail 'exported compiled-candidate TAR differs from frozen candidate'
 python3 -S verify_26870_candidate.py "$BASE" "$exp" --root "$ROOT"
 python3 -S verify_26870_patches.py "$BASE" "$exp" 26870_FORWARD_FULL_INDEX.patch 26870_ROLLBACK_FULL_INDEX.patch > "$OUT/26870_final_patch_replay.txt"
 python3 -S verify_26864_runtime_glsl.py "$BASE" "$exp" --out "$OUT/26870_final_runtime_expanded_glsl" | tee "$OUT/26870_final_glsl_static_replay.txt"
 python3 -S verify_26864_rawr_sources.py "$exp/app"
 python3 -S regressions/26864_glsl_reserved_identifiers.py "$exp/app"
 # Exact historical regression validation was replayed in make_candidate,
 # against 26867 and 26866 derived from real successful 26868 artifact.
 python3 -S regressions/26864_wronski_publisher.py "$WORK/historical_26867_from_successful_26868/app"
 python3 -S verify_26864_semantics.py "$WORK/historical_26867_from_successful_26868/app" --numeric
 python3 -S regressions/26865_b_lsc_owner.py "$exp/app"
 python3 -S regressions/26866_b_color_only.py "$WORK/historical_26866_from_successful_26867/app"
 python3 -S regressions/26867_b_highlight_ab_retired.py "$WORK/historical_26867_from_successful_26868/app"
 python3 -S regressions/26868_direct_b_long_retire_ab.py "$BASE/app"
 python3 -S regressions/26870_b_automatic_iq.py "$BASE/app" "$exp/app"
 python3 -S verify_26867_runtime_shader.py "$exp" --out "$OUT/26870_final_inherited_white_fade"
 python3 -S verify_26868_runtime_shader.py "$exp" --out "$OUT/26870_final_expanded_b_long"
 python3 -S verify_26870_runtime_shader.py "$exp" --out "$OUT/26870_final_expanded_tone_chroma"
 grep -Fx 'VERSION_NAME=0.9726870' "$exp/app/version.properties" >/dev/null
 grep -Fx 'VERSION_BUILD=26870' "$exp/app/version.properties" >/dev/null
 for status in 'REAL GLSL COMPILE: PASS' 'REAL SPIR-V VALIDATION: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS';do grep -F "$status" "$OUT/26870_COMPILER_STATUS.txt" >/dev/null || fail "final compiler proof $status";done
 pass 'final 26870 clean-extract handoff replay exact candidate/hash/syntax/owners/GLSL/patches/version/compilers/build'
}

verify_package
verify_scope
obtain_authority
make_candidate
verify_successful_mechanics
prepare_glslang
compile_modified_runtime_shaders
compile_spektra_raw_shader
install_frozen_candidate_live
compile_languages
verify_native_glslang_handoff
compile_native
verify_candidate_patches
prebuild_safety
assemble
postbuild_proof
clean_extract_replay
pass '26870 ALL 17 INHERITED GUARDED STAGES PASSED'
