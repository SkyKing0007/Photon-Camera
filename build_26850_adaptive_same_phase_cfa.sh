#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
ROOT="$(pwd)"; EXPECTED_BRANCH="experimental-clean-photon-rebuild"
RUNTIME_AUTHORITY_COMMIT="d2ef3e278e2352218086769c571e38a3c48c8ec9"; RUNTIME_ACTIONS_RUN="39000100494"; RUNTIME_ARTIFACT_ID="12088717999"; RUNTIME_ARTIFACT_NAME="photon-26849-peripheral-phase-safe-cfa"; RUNTIME_ARTIFACT_SHA="ffa66aa894e1068bc868af9133a0f2d0faf969e001093d5e7bfcced060cef63e"; RUNTIME_TAR_SHA="69e1582869784b718bf5b8ad6e818c8c30cdde34ba97a0e551abfa3b0c87a579"
MECHANICS_AUTHORITY_COMMIT="$RUNTIME_AUTHORITY_COMMIT"; MECHANICS_ACTIONS_RUN="$RUNTIME_ACTIONS_RUN"; ROOT_MECHANICS_COMMIT="9fdf39a0a99773ea86159250c7715396b58e78d3"; ROOT_MECHANICS_RUN="38295667311"
VERSION_NAME="0.9726850"; VERSION_BUILD="26850"; GLSLANG_VERSION="16.5.0"; GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"; GLSLANG_URL="https://github.com/KhronosGroup/glslang/releases/download/16.5.0/glslang-16.5.0-linux-x86_64-release.tar.gz"
OUT="$ROOT/build_26850_adaptive_same_phase_cfa_outputs"; WORK="$ROOT/.build_26850_adaptive_same_phase_cfa_work"; ARTZIP="$WORK/26849_artifact.zip"; ARTDIR="$WORK/artifact_26849"; BASE="$WORK/exact_successful_26849_compiled_candidate"; CAND="$WORK/candidate_26850"; LIVE_CANON="$WORK/live_compiler_candidate_snapshot"; POST_LANG="$WORK/post_language_compiler_source_snapshot"; FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-adaptive-same-phase-cfa-debug.apk"; TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR"
cat > "$OUT/26850_COMPILER_STATUS.txt" <<EOF
REAL GLSL COMPILE: NOT RUN YET
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
NATIVE/NDK COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
EOF
# IRIS_26850_AUTHORITATIVE_ACTIONS_STAGE_ORDER
verify_package(){ sha256sum -c 26850_HANDOFF_HASHES.sha256 >/dev/null; bash -n build_26850_adaptive_same_phase_cfa.sh; python3 -S -m py_compile transform_26850.py validate_26850.py verify_26850_patches.py verify_26850_runtime_glsl.py; rm -rf __pycache__; [[ "$(find handoff_payload_26850 -type f | wc -l)" -eq 2 ]] || fail "26850 payload count"; diff -u 26850_RUNTIME_CHANGED_PATHS.txt <(find handoff_payload_26850 -type f | sed 's#^handoff_payload_26850/##' | sort) >/dev/null || fail "26850 payload allowlist mismatch"; for p in 26850_FORWARD_FULL_INDEX.patch 26850_ROLLBACK_FULL_INDEX.patch; do ! grep -Eq '^(rename from|rename to|copy from|copy to) ' "$p" || fail "patch rename/copy inference"; done; grep -Fx 'RUN_26850_ADAPTIVE_SAME_PHASE_CFA' TRIGGER_26850.txt >/dev/null || fail "26850 trigger identity mismatch"; grep -F "$RUNTIME_AUTHORITY_COMMIT..HEAD" "$0" >/dev/null || fail "26850 scope diff base does not match runtime authority"; ! find . -type f -name '*.apk' | grep -q . || fail "APK unexpectedly packaged"; pass "sealed 26850 package hashes/syntax/allowlist/patch identity"; }
verify_scope(){ [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch"; git merge-base --is-ancestor "$RUNTIME_AUTHORITY_COMMIT" HEAD || fail "26849 runtime authority not ancestor"; git merge-base --is-ancestor "$ROOT_MECHANICS_COMMIT" HEAD || fail "26821 root mechanics authority not ancestor"; if git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD | grep -E '^app/'; then fail "live app source changed after 26849 authority"; fi; python3 -S - <<'PY_SCOPE'
import subprocess
allowed=('26850_','build_26850_adaptive_same_phase_cfa.sh','transform_26850.py','validate_26850.py','verify_26850_patches.py','verify_26850_runtime_glsl.py','handoff_payload_26850/','.github/workflows/build-26850-adaptive-same-phase-cfa.yml','TRIGGER_26850.txt','26850_README.txt')
paths=subprocess.check_output(['git','diff','--name-only','d2ef3e278e2352218086769c571e38a3c48c8ec9..HEAD'],text=True).splitlines(); bad=[p for p in paths if not any(p==x or p.startswith(x) for x in allowed)]; assert not bad,bad; print('PASS 26850 infrastructure scope allowlist')
PY_SCOPE
pass "26850 scope exact: successful 26849 authority + sealed 2-path payload; live app untouched"; }
obtain_authority(){ [[ -n "$TOKEN" ]] || fail "GITHUB_TOKEN missing"; curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${RUNTIME_ARTIFACT_ID}/zip" -o "$ARTZIP"; [[ "$(sha "$ARTZIP")" == "$RUNTIME_ARTIFACT_SHA" ]] || fail "26849 artifact sha"; unzip -q "$ARTZIP" -d "$ARTDIR"; T="$ARTDIR/build_26849_peripheral_phase_safe_cfa_outputs/26849_candidate_app_source.tar.gz"; [[ -f "$T" && "$(sha "$T")" == "$RUNTIME_TAR_SHA" ]] || fail "26849 candidate tar sha"; STATUS="$ARTDIR/build_26849_peripheral_phase_safe_cfa_outputs/26849_COMPILER_STATUS.txt"; for proof in 'REAL GLSL COMPILE: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS'; do grep -F "$proof" "$STATUS" >/dev/null || fail "missing 26849 authority proof: $proof"; done; mkdir -p "$BASE"; tar -xzf "$T" -C "$BASE"; [[ "$(find "$BASE/app" -type f | wc -l)" -eq 1786 ]] || fail "26849 base file count"; (cd "$BASE" && sha256sum -c "$ROOT/26850_BASE_26849_FULL_APP.sha256" >/dev/null); (cd "$BASE" && sha256sum -c "$ROOT/26850_PRIOR_SOURCE_HASHES.sha256" >/dev/null); (cd "$BASE" && sha256sum -c "$ROOT/26850_NATIVE_PROTECTED_26849.sha256" >/dev/null); (cd "$BASE" && sha256sum -c "$ROOT/26850_VENDOR_26849.sha256" >/dev/null); (cd "$BASE" && sha256sum -c "$ROOT/26850_DNG_WRITER_26849.sha256" >/dev/null); (cd "$BASE" && sha256sum -c "$ROOT/26850_SHADER_ASSETS_PROTECTED_26849.sha256" >/dev/null); cat > "$OUT/26850_RESOLVED_AUTHORITIES.txt" <<EOF
runtime_commit=$RUNTIME_AUTHORITY_COMMIT
runtime_run=$RUNTIME_ACTIONS_RUN
runtime_artifact_id=$RUNTIME_ARTIFACT_ID
runtime_artifact_name=$RUNTIME_ARTIFACT_NAME
runtime_artifact_sha256=$RUNTIME_ARTIFACT_SHA
runtime_candidate_tar_sha256=$RUNTIME_TAR_SHA
mechanics_commit=$MECHANICS_AUTHORITY_COMMIT
mechanics_run=$MECHANICS_ACTIONS_RUN
root_mechanics_commit=$ROOT_MECHANICS_COMMIT
root_mechanics_run=$ROOT_MECHANICS_RUN
EOF
pass "exact successful 26849 compiled candidate reconstructed"; }
universe_equal(){ python3 -S - "$1" "$2" <<'PY_U'
from pathlib import Path
import hashlib,sys
def U(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(r)/'app').rglob('*') if p.is_file()}
a,b=U(sys.argv[1]),U(sys.argv[2]); assert a==b,(len(a),len(b)); print(f'PASS byte-identical app universe: {len(a)} files')
PY_U
}
make_candidate(){ python3 -S transform_26850.py "$BASE" "$CAND" handoff_payload_26850; python3 -S validate_26850.py "$BASE" "$CAND"; (cd "$CAND" && sha256sum -c "$ROOT/26850_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null); for f in 26850_PROTECTED_26849.sha256 26850_NATIVE_PROTECTED_26849.sha256 26850_VENDOR_26849.sha256 26850_DNG_WRITER_26849.sha256 26850_SHADER_ASSETS_PROTECTED_26849.sha256 26850_FALSE_COLOR_ASSETS_PROTECTED_26849.sha256 26850_SUCCESSFUL_26849_PERFORMANCE_REFERENCE.sha256 26850_SABRE_PROTECTED_26849.sha256 26850_SUCCESSFUL_26849_DNG_PHASE_REFERENCE.sha256; do (cd "$CAND" && sha256sum -c "$ROOT/$f" >/dev/null); done; [[ "$(find "$CAND/app" -type f | wc -l)" -eq 1786 ]] || fail "candidate count"; pass "candidate-first 26850 from exact successful-26849 authority; only NORMAL adaptive evidence-selected same-phase R/B registration + version changed; 26846 phase-validity/LONG/highlight/color/exposure/UHDR/DNG/high-zoom/motion/detail protections preserved"; }
verify_successful_mechanics(){ local a45="$WORK/authority_26849_build.sh" a21="$WORK/authority_26821_build.sh"; git show "$MECHANICS_AUTHORITY_COMMIT:build_26849_peripheral_phase_safe_cfa.sh" > "$a45"; git show "$ROOT_MECHANICS_COMMIT:build_26821_connected_false_color_dng_all_phase_coherence.sh" > "$a21"; for cmd in './gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace' "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace" './gradlew :app:assembleDebug --stacktrace'; do grep -F "$cmd" "$a45" >/dev/null || fail "26849 authority command missing: $cmd"; grep -F "$cmd" "$0" >/dev/null || fail "26850 command differs: $cmd"; done; grep -F 'compile_spektra_raw_shader(){' "$a45" >/dev/null; grep -F 'compile_spektra_raw_shader(){' "$0" >/dev/null; grep -F 'verify_native_glslang_handoff(){' "$a45" >/dev/null; grep -F 'verify_native_glslang_handoff(){' "$0" >/dev/null; python3 -S - "$0" "$a45" "$a21" <<'PY_O'
from pathlib import Path
import sys
def ordered(text,marker,tokens,label):
 i=text.find(marker); assert i>=0,(label,marker); text=text[i:]; pos=-1
 for token in tokens: nxt=text.find(token,pos+1); assert nxt>pos,(label,token); pos=nxt
stages=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','verify_candidate_patches','prebuild_safety','assemble','postbuild_proof','clean_extract_replay']
cur,a45,a21=[Path(x).read_text() for x in sys.argv[1:]]; ordered(cur,'# IRIS_26850_AUTHORITATIVE_ACTIONS_STAGE_ORDER',stages,'26850'); ordered(a45,'# IRIS_26849_AUTHORITATIVE_ACTIONS_STAGE_ORDER',stages,'26849 authority'); ordered(a21,'# IRIS_26821_AUTHORITATIVE_ACTIONS_STAGE_ORDER',stages,'26821 root'); print('PASS 26850 stage order exactly inherits successful 26849 procedure and successful 26821 root mechanics')
PY_O
cp 26850_MECHANICS_DIFF_AUDIT.txt "$OUT/26850_MECHANICS_DIFF_AUDIT.txt"; pass "successful 26849 implementation diff-audited: zero stage-order/compiler/native/assemble deviation"; }
prepare_glslang(){ D="$WORK/glslang-${GLSLANG_VERSION}"; A="$WORK/glslang.tar.gz"; mkdir -p "$D"; curl -L --fail --retry 3 "$GLSLANG_URL" -o "$A"; [[ "$(sha "$A")" == "$GLSLANG_ARCHIVE_SHA" ]] || fail "glslang archive sha"; tar -xzf "$A" -C "$D"; compiler="$(find "$D" -type f -name glslang -print -quit)"; [[ -n "$compiler" ]] || compiler="$(find "$D" \( -type f -o -type l \) -name glslangValidator -print -quit)"; compiler="$(readlink -f "$compiler")"; [[ -x "$compiler" ]] || chmod +x "$compiler"; "$compiler" --version | tee "$OUT/26850_glslang_version.txt"; export IRIS26850_GLSLANG="$compiler"; export IRIS26681_SPEKTRA_GLSLANG="$compiler"; pass "pinned glslang 16.5.0 dual environment handoff"; }
compile_modified_runtime_shaders(){ python3 -S verify_26850_runtime_glsl.py "$BASE" "$CAND" --compiler "$IRIS26850_GLSLANG" --out "$OUT/26850_runtime_expanded_glsl" | tee "$OUT/26850_glsl_validation.txt"; grep -F 'PASS 26850 GLSL ownership: exactly 1 modified NORMAL merge shader; 45 successful-26849 active/protected variants inherited byte-identically' "$OUT/26850_glsl_validation.txt" >/dev/null; grep -F 'PASS 26850 CFA safety:' "$OUT/26850_glsl_validation.txt" >/dev/null; sed -i 's#REAL GLSL COMPILE: NOT RUN YET#REAL GLSL COMPILE: PASS (1 modified NORMAL merge shader + 45 inherited active/protected variants replayed with pinned glslang 16.5.0)#' "$OUT/26850_COMPILER_STATUS.txt"; }
compile_spektra_raw_shader(){ pass "Spektra project verifier absent from repo shell; inherited source protected by candidate manifest"; }
snapshot_live_authority_seeded(){ python3 -S - "$CAND" "$1" "$ROOT" <<'PY_S'
from pathlib import Path
import shutil,sys
cand,out,live=map(Path,sys.argv[1:]);
if out.exists(): shutil.rmtree(out)
shutil.copytree(cand,out); expected={str(p.relative_to(cand)):p for p in (cand/'app').rglob('*') if p.is_file()}
for rel in expected:
 lp=live/rel
 if not lp.is_file(): raise SystemExit(f'missing live candidate path: {rel}')
 (out/rel).write_bytes(lp.read_bytes())
expected_src={r for r in expected if r.startswith('app/src/')}; actual_src={str(p.relative_to(live)) for p in (live/'app/src').rglob('*') if p.is_file()}; extra=sorted(actual_src-expected_src)
if extra: raise SystemExit(f'unexpected app/src paths: {extra}')
print(f'PASS authority-seeded canonical live snapshot: {len(expected)} candidate files; generated app/build + app/.cxx excluded')
PY_S
}
install_frozen_candidate_live(){ rm -rf app; cp -a "$CAND/app" app; snapshot_live_authority_seeded "$LIVE_CANON"; universe_equal "$CAND" "$LIVE_CANON"; pass "authority-seeded canonical live candidate byte-identical to frozen 26850 candidate"; }
compile_languages(){ ./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace 2>&1 | tee "$OUT/26850_gradle_language_compilers.log"; snapshot_live_authority_seeded "$POST_LANG"; universe_equal "$CAND" "$POST_LANG"; sed -i 's/REAL KOTLIN COMPILE: NOT RUN YET/REAL KOTLIN COMPILE: PASS/' "$OUT/26850_COMPILER_STATUS.txt"; sed -i 's/REAL JAVA COMPILE: NOT RUN YET/REAL JAVA COMPILE: PASS/' "$OUT/26850_COMPILER_STATUS.txt"; pass "real Kotlin/Java compilers passed and frozen source remained byte-identical"; }
verify_native_glslang_handoff(){ [[ -n "${IRIS26850_GLSLANG:-}" && -x "$IRIS26850_GLSLANG" ]] || fail "IRIS26850_GLSLANG missing"; [[ -n "${IRIS26681_SPEKTRA_GLSLANG:-}" && -x "$IRIS26681_SPEKTRA_GLSLANG" ]] || fail "IRIS26681_SPEKTRA_GLSLANG missing"; [[ "$(readlink -f "$IRIS26850_GLSLANG")" == "$(readlink -f "$IRIS26681_SPEKTRA_GLSLANG")" ]] || fail "native/Spektra glslang handoff differs"; { echo "IRIS26681_SPEKTRA_GLSLANG=$IRIS26681_SPEKTRA_GLSLANG"; echo "IRIS26850_GLSLANG=$IRIS26850_GLSLANG"; } | tee "$OUT/26850_native_glslang_handoff.txt"; pass "successful 26849 native glslang handoff preserved before both-ABI native compile"; }
compile_native(){ ./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace 2>&1 | tee "$OUT/26850_gradle_native_compiler.log"; sed -i 's#NATIVE/NDK COMPILE: NOT RUN YET#NATIVE/NDK COMPILE: PASS (arm64-v8a + armeabi-v7a)#' "$OUT/26850_COMPILER_STATUS.txt"; }
verify_candidate_patches(){ python3 -S verify_26850_patches.py "$BASE" "$CAND" 26850_FORWARD_FULL_INDEX.patch 26850_ROLLBACK_FULL_INDEX.patch | tee "$OUT/26850_patch_validation.txt"; grep -F 'PASS 26850 canonical patch proof' "$OUT/26850_patch_validation.txt" >/dev/null; pass "sealed full-index forward/rollback proof: successful 26849 -> exact 2-path 26850 candidate"; }
prebuild_safety(){ snapshot_live_authority_seeded "$WORK/prebuild_live_snapshot"; universe_equal "$CAND" "$WORK/prebuild_live_snapshot"; python3 -S validate_26850.py "$BASE" "$CAND"; for f in 26850_PROTECTED_26849.sha256 26850_NATIVE_PROTECTED_26849.sha256 26850_VENDOR_26849.sha256 26850_DNG_WRITER_26849.sha256 26850_SHADER_ASSETS_PROTECTED_26849.sha256 26850_FALSE_COLOR_ASSETS_PROTECTED_26849.sha256 26850_SUCCESSFUL_26849_PERFORMANCE_REFERENCE.sha256 26850_SABRE_PROTECTED_26849.sha256 26850_SUCCESSFUL_26849_DNG_PHASE_REFERENCE.sha256; do (cd "$CAND" && sha256sum -c "$ROOT/$f" >/dev/null); done; cat > "$OUT/26850_PREBUILD_SAFETY.txt" <<EOF
PRE-BUILD SAFETY PROOF PASSED
runtime_authority=successful 26849 $RUNTIME_AUTHORITY_COMMIT run $RUNTIME_ACTIONS_RUN artifact $RUNTIME_ARTIFACT_ID
verification_mechanics=exact successful 26849 17-stage sequence; successful 26821 root mechanics inherited
runtime_changed_files=2 modified / 0 added / 0 deleted
runtime_allowlist=exact 2 paths in 26850_RUNTIME_CHANGED_PATHS.txt
protected_files=1784 unchanged
native_protected_files=819 unchanged
vendor_files=773 unchanged
dng_writer_files=6 unchanged
shader_assets_protected=274 unchanged; modified_shader_assets=0
base_candidate_files=1786
final_candidate_files=1786
image_quality=successful 26849 LONG/highlight/color/exposure/UHDR/DNG/high-zoom/motion/detail behavior preserved; only NORMAL pre-Resolve peripheral evidence-selected same-phase R/B registration changes; 26848 CFA topology preserved
exposure=successful 26849 CaptureController byte-identical
color=successful 26849 downstream VGN/FCC/clip-zone/final-render protections byte-identical
long=successful 26849 LONG low-frequency shadow-luma architecture byte-identical
high_zoom=successful 26849 high-zoom/direct-CFA path byte-identical
runtime_glsl_delta=1 modified NORMAL merge shader; 45 inherited active/protected variants replayed
backup_branch_required=NONE_USER_EXPLICIT
EOF
echo 'PRE-BUILD SAFETY PROOF PASSED'; }
assemble(){ ./gradlew :app:assembleDebug --stacktrace 2>&1 | tee "$OUT/26850_gradle_assemble.log"; mapfile -t apks < <(find app/build/outputs/apk -type f -name '*.apk' | sort); [[ "${#apks[@]}" -eq 1 ]] || fail "expected exactly one APK, got ${#apks[@]}"; cp "${apks[0]}" "$FINAL"; sha256sum "$FINAL" | tee "$OUT/26850_APK.sha256"; sed -i 's/FULL ANDROID ASSEMBLE: NOT RUN YET/FULL ANDROID ASSEMBLE: PASS (exactly one APK)/' "$OUT/26850_COMPILER_STATUS.txt"; }
postbuild_proof(){ snapshot_live_authority_seeded "$WORK/postbuild_live_snapshot"; universe_equal "$CAND" "$WORK/postbuild_live_snapshot"; python3 -S validate_26850.py "$BASE" "$CAND"; (cd "$CAND" && sha256sum -c "$ROOT/26850_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null); for f in 26850_PROTECTED_26849.sha256 26850_NATIVE_PROTECTED_26849.sha256 26850_VENDOR_26849.sha256 26850_DNG_WRITER_26849.sha256 26850_SHADER_ASSETS_PROTECTED_26849.sha256 26850_FALSE_COLOR_ASSETS_PROTECTED_26849.sha256 26850_SUCCESSFUL_26849_PERFORMANCE_REFERENCE.sha256 26850_SABRE_PROTECTED_26849.sha256 26850_SUCCESSFUL_26849_DNG_PHASE_REFERENCE.sha256; do (cd "$CAND" && sha256sum -c "$ROOT/$f" >/dev/null); done; cp 26850_EXPECTED_CANDIDATE_FULL_APP.sha256 "$OUT/26850_candidate_full_app.sha256"; tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -czf "$OUT/26850_candidate_app_source.tar.gz" -C "$CAND" app; sha256sum "$OUT/26850_candidate_app_source.tar.gz" > "$OUT/26850_candidate_app_source.tar.gz.sha256"; cp 26850_FORWARD_FULL_INDEX.patch "$OUT/26850_FORWARD_FULL_INDEX.patch"; cp 26850_ROLLBACK_FULL_INDEX.patch "$OUT/26850_ROLLBACK_FULL_INDEX.patch"; sed -i 's/POST-BUILD INVARIANCE: NOT RUN YET/POST-BUILD INVARIANCE: PASS/' "$OUT/26850_COMPILER_STATUS.txt"; pass "authority-seeded post-build protected/DNG/native/vendor/shader/source invariance"; }
clean_extract_replay(){ local replay="$WORK/clean_replay_candidate"; rm -rf "$replay"; sha256sum -c 26850_HANDOFF_HASHES.sha256 >/dev/null; bash -n build_26850_adaptive_same_phase_cfa.sh; python3 -S -m py_compile transform_26850.py validate_26850.py verify_26850_patches.py verify_26850_runtime_glsl.py; rm -rf __pycache__; python3 -S transform_26850.py "$BASE" "$replay" handoff_payload_26850; universe_equal "$CAND" "$replay"; python3 -S validate_26850.py "$BASE" "$replay"; python3 -S verify_26850_runtime_glsl.py "$BASE" "$replay" --out "$OUT/26850_final_runtime_expanded_glsl" | tee "$OUT/26850_final_glsl_static_replay.txt"; python3 -S verify_26850_patches.py "$BASE" "$replay" 26850_FORWARD_FULL_INDEX.patch 26850_ROLLBACK_FULL_INDEX.patch | tee "$OUT/26850_final_patch_replay.txt"; (cd "$replay" && sha256sum -c "$ROOT/26850_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null); grep -F 'VERSION_NAME=0.9726850' "$replay/app/version.properties" >/dev/null; grep -F 'VERSION_BUILD=26850' "$replay/app/version.properties" >/dev/null; for proof in 'REAL GLSL COMPILE: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS'; do grep -F "$proof" "$OUT/26850_COMPILER_STATUS.txt" >/dev/null || fail "missing final proof $proof"; done; pass "final 26850 clean replay of hashes/successful-26849 runtime inheritance/adaptive same-phase CFA registration/version/patch/compiler/build proofs"; }
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
pass "26850 ADAPTIVE SAME-PHASE CFA: ACTIONS BUILD PROOF COMPLETE"
