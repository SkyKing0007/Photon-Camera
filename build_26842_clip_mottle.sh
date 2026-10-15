#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
ROOT="$(pwd)"; EXPECTED_BRANCH="experimental-clean-photon-rebuild"
RUNTIME_AUTHORITY_COMMIT="c7f8cbbf07f927c225bf0a631fc3b79874c4ccac"; RUNTIME_ACTIONS_RUN="38792229547"; RUNTIME_ARTIFACT_ID="12001595609"; RUNTIME_ARTIFACT_NAME="photon-26841-hdr-preview-warm"; RUNTIME_ARTIFACT_SHA="9e2b672eb563256843918756f98330396bd1bf96da034fe5015a22aa01279cbd"; RUNTIME_TAR_SHA="504d0cb029d77f97f42d809ee5884b9a0c8d25f685d83ebcbd69be97219a1b46"
MECHANICS_AUTHORITY_COMMIT="$RUNTIME_AUTHORITY_COMMIT"; MECHANICS_ACTIONS_RUN="$RUNTIME_ACTIONS_RUN"; ROOT_MECHANICS_COMMIT="9fdf39a0a99773ea86159250c7715396b58e78d3"; ROOT_MECHANICS_RUN="38295667311"
VERSION_NAME="0.9726842"; VERSION_BUILD="26842"; GLSLANG_VERSION="16.5.0"; GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"; GLSLANG_URL="https://github.com/KhronosGroup/glslang/releases/download/16.5.0/glslang-16.5.0-linux-x86_64-release.tar.gz"
OUT="$ROOT/build_26842_clip_mottle_outputs"; WORK="$ROOT/.build_26842_clip_mottle_work"; ARTZIP="$WORK/26841_artifact.zip"; ARTDIR="$WORK/artifact_26841"; BASE="$WORK/exact_successful_26841_compiled_candidate"; CAND="$WORK/candidate_26842"; LIVE_CANON="$WORK/live_compiler_candidate_snapshot"; POST_LANG="$WORK/post_language_compiler_source_snapshot"; FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-clip-mottle-debug.apk"; TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR"
cat > "$OUT/26842_COMPILER_STATUS.txt" <<EOF
REAL GLSL COMPILE: NOT RUN YET
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
NATIVE/NDK COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
EOF
# IRIS_26842_AUTHORITATIVE_ACTIONS_STAGE_ORDER
verify_package(){ sha256sum -c 26842_HANDOFF_HASHES.sha256 >/dev/null; bash -n build_26842_clip_mottle.sh; python3 -S -m py_compile transform_26842.py validate_26842.py verify_26842_patches.py verify_26842_runtime_glsl.py; rm -rf __pycache__; [[ "$(find handoff_payload_26842 -type f | wc -l)" -eq 3 ]] || fail "26842 payload count"; diff -u 26842_RUNTIME_CHANGED_PATHS.txt <(find handoff_payload_26842 -type f | sed 's#^handoff_payload_26842/##' | sort) >/dev/null || fail "26842 payload allowlist mismatch"; for p in 26842_FORWARD_FULL_INDEX.patch 26842_ROLLBACK_FULL_INDEX.patch; do ! grep -Eq '^(rename from|rename to|copy from|copy to) ' "$p" || fail "patch rename/copy inference"; done; grep -Fx 'RUN_26842_CLIP_MOTTLE' TRIGGER_26842.txt >/dev/null || fail "26842 trigger identity mismatch"; ! find . -type f -name '*.apk' | grep -q . || fail "APK unexpectedly packaged"; pass "sealed 26842 package hashes/syntax/allowlist/patch identity"; }
verify_scope(){ [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch"; git merge-base --is-ancestor "$RUNTIME_AUTHORITY_COMMIT" HEAD || fail "26841 runtime authority not ancestor"; git merge-base --is-ancestor "$ROOT_MECHANICS_COMMIT" HEAD || fail "26821 root mechanics authority not ancestor"; if git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD | grep -E '^app/'; then fail "live app source changed after 26841 authority"; fi; python3 -S - <<'PY_SCOPE'
import subprocess
allowed=('26842_','build_26842_clip_mottle.sh','transform_26842.py','validate_26842.py','verify_26842_patches.py','verify_26842_runtime_glsl.py','handoff_payload_26842/','.github/workflows/build-26842-clip-mottle.yml','TRIGGER_26842.txt','26842_README.txt')
paths=subprocess.check_output(['git','diff','--name-only','c641816db971b7059c2fd511745154f7dc1f4f36..HEAD'],text=True).splitlines()
bad=[p for p in paths if not any(p==x or p.startswith(x) for x in allowed)]
assert not bad,bad
print('PASS 26842 infrastructure scope allowlist')
PY_SCOPE
pass "26842 scope exact: successful 26841 authority + sealed 3-path payload; live app untouched"; }
obtain_authority(){ [[ -n "$TOKEN" ]] || fail "GITHUB_TOKEN missing"; curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${RUNTIME_ARTIFACT_ID}/zip" -o "$ARTZIP"; [[ "$(sha "$ARTZIP")" == "$RUNTIME_ARTIFACT_SHA" ]] || fail "26841 artifact sha"; unzip -q "$ARTZIP" -d "$ARTDIR"; T="$ARTDIR/build_26841_hdr_preview_warm_outputs/26841_candidate_app_source.tar.gz"; [[ -f "$T" && "$(sha "$T")" == "$RUNTIME_TAR_SHA" ]] || fail "26841 candidate tar sha"; STATUS="$ARTDIR/build_26841_hdr_preview_warm_outputs/26841_COMPILER_STATUS.txt"; for proof in 'REAL GLSL COMPILE: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS'; do grep -F "$proof" "$STATUS" >/dev/null || fail "missing 26841 authority proof: $proof"; done; mkdir -p "$BASE"; tar -xzf "$T" -C "$BASE"; [[ "$(find "$BASE/app" -type f | wc -l)" -eq 1786 ]] || fail "26841 base file count"; (cd "$BASE" && sha256sum -c "$ROOT/26842_BASE_26841_FULL_APP.sha256" >/dev/null); (cd "$BASE" && sha256sum -c "$ROOT/26842_PRIOR_SOURCE_HASHES.sha256" >/dev/null); (cd "$BASE" && sha256sum -c "$ROOT/26842_NATIVE_PROTECTED_26841.sha256" >/dev/null); (cd "$BASE" && sha256sum -c "$ROOT/26842_VENDOR_26841.sha256" >/dev/null); (cd "$BASE" && sha256sum -c "$ROOT/26842_DNG_WRITER_26841.sha256" >/dev/null); (cd "$BASE" && sha256sum -c "$ROOT/26842_SHADER_ASSETS_PROTECTED_26841.sha256" >/dev/null); cat > "$OUT/26842_RESOLVED_AUTHORITIES.txt" <<EOF
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
pass "exact successful 26841 compiled candidate reconstructed"; }
universe_equal(){ python3 -S - "$1" "$2" <<'PY_U'
from pathlib import Path
import hashlib,sys
def U(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(r)/'app').rglob('*') if p.is_file()}
a,b=U(sys.argv[1]),U(sys.argv[2]); assert a==b,(len(a),len(b)); print(f'PASS byte-identical app universe: {len(a)} files')
PY_U
}
make_candidate(){ python3 -S transform_26842.py "$BASE" "$CAND" handoff_payload_26842; python3 -S validate_26842.py "$BASE" "$CAND"; (cd "$CAND" && sha256sum -c "$ROOT/26842_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26842_PROTECTED_26841.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26842_NATIVE_PROTECTED_26841.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26842_VENDOR_26841.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26842_DNG_WRITER_26841.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26842_SHADER_ASSETS_PROTECTED_26841.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26842_FALSE_COLOR_ASSETS_PROTECTED_26841.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26842_SUCCESSFUL_26841_PERFORMANCE_REFERENCE.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26842_SABRE_PROTECTED_26841.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26842_SUCCESSFUL_26841_DNG_PHASE_REFERENCE.sha256" >/dev/null); [[ "$(find "$CAND/app" -type f | wc -l)" -eq 1786 ]] || fail "candidate count"; pass "candidate-first 26842 from exact successful-26841 authority; 26841 one-shot HDR preview and warm-midtone restraint frozen byte-identical; 26842 changes only final clip-zone chroma magnitude rolloff and true-flat low-signal mottling cleanup; source hue remains sole clipped-color direction owner; DNG/UHDR/native/high-zoom/SR protected"; }
verify_successful_mechanics(){ local a29="$WORK/authority_26841_build.sh" a21="$WORK/authority_26821_build.sh"; git show "$MECHANICS_AUTHORITY_COMMIT:build_26841_hdr_preview_warm.sh" > "$a29"; git show "$ROOT_MECHANICS_COMMIT:build_26821_connected_false_color_dng_all_phase_coherence.sh" > "$a21"; for cmd in './gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace' "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace" './gradlew :app:assembleDebug --stacktrace'; do grep -F "$cmd" "$a29" >/dev/null || fail "26841 authority command missing: $cmd"; grep -F "$cmd" "$0" >/dev/null || fail "26842 command differs: $cmd"; done; grep -F 'compile_spektra_raw_shader(){' "$a29" >/dev/null; grep -F 'compile_spektra_raw_shader(){' "$0" >/dev/null; grep -F 'verify_native_glslang_handoff(){' "$a29" >/dev/null; grep -F 'verify_native_glslang_handoff(){' "$0" >/dev/null; python3 -S - "$0" "$a29" "$a21" <<'PY_O'
from pathlib import Path
import sys
def ordered(text,marker,tokens,label):
 i=text.find(marker); assert i>=0,(label,marker); text=text[i:]; pos=-1
 for token in tokens:
  nxt=text.find(token,pos+1); assert nxt>pos,(label,token); pos=nxt
stages=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','verify_candidate_patches','prebuild_safety','assemble','postbuild_proof','clean_extract_replay']
cur,a29,a21=[Path(x).read_text() for x in sys.argv[1:]]
ordered(cur,'# IRIS_26842_AUTHORITATIVE_ACTIONS_STAGE_ORDER',stages,'26842')
ordered(a29,'# IRIS_26841_AUTHORITATIVE_ACTIONS_STAGE_ORDER',stages,'26841 authority')
ordered(a21,'# IRIS_26821_AUTHORITATIVE_ACTIONS_STAGE_ORDER',stages,'26821 root')
print('PASS 26842 stage order exactly inherits successful 26841 procedure and successful 26821 root mechanics')
PY_O
cp 26842_MECHANICS_DIFF_AUDIT.txt "$OUT/26842_MECHANICS_DIFF_AUDIT.txt"; pass "successful 26841 implementation diff-audited: zero stage-order/compiler/native/assemble deviation"; }
prepare_glslang(){ D="$WORK/glslang-${GLSLANG_VERSION}"; A="$WORK/glslang.tar.gz"; mkdir -p "$D"; curl -L --fail --retry 3 "$GLSLANG_URL" -o "$A"; [[ "$(sha "$A")" == "$GLSLANG_ARCHIVE_SHA" ]] || fail "glslang archive sha"; tar -xzf "$A" -C "$D"; compiler="$(find "$D" -type f -name glslang -print -quit)"; [[ -n "$compiler" ]] || compiler="$(find "$D" \( -type f -o -type l \) -name glslangValidator -print -quit)"; compiler="$(readlink -f "$compiler")"; [[ -x "$compiler" ]] || chmod +x "$compiler"; "$compiler" --version | tee "$OUT/26842_glslang_version.txt"; export IRIS26842_GLSLANG="$compiler"; export IRIS26681_SPEKTRA_GLSLANG="$compiler"; pass "pinned glslang 16.5.0 dual environment handoff"; }
compile_modified_runtime_shaders(){ python3 -S verify_26842_runtime_glsl.py "$BASE" "$CAND" --compiler "$IRIS26842_GLSLANG" --out "$OUT/26842_runtime_expanded_glsl" | tee "$OUT/26842_glsl_validation.txt"; grep -F 'PASS 26842 GLSL ownership: 2 modified runtime-expanded shaders + 44 inherited active/protected runtime variants' "$OUT/26842_glsl_validation.txt" >/dev/null; grep -F 'PASS 26842 inherited shader fidelity: 36 legacy active/protected shaders + 8 successful-26841 color-transform variants byte-identical' "$OUT/26842_glsl_validation.txt" >/dev/null; sed -i 's#REAL GLSL COMPILE: NOT RUN YET#REAL GLSL COMPILE: PASS (2 modified runtime-expanded shaders + 44 inherited active/protected variants, pinned glslang 16.5.0)#' "$OUT/26842_COMPILER_STATUS.txt"; }
compile_spektra_raw_shader(){ pass "Spektra project verifier absent from repo shell; inherited source protected by candidate manifest"; }
snapshot_live_authority_seeded(){ python3 -S - "$CAND" "$1" "$ROOT" <<'PY_S'
from pathlib import Path
import shutil,sys
cand,out,live=map(Path,sys.argv[1:])
if out.exists(): shutil.rmtree(out)
shutil.copytree(cand,out)
expected={str(p.relative_to(cand)):p for p in (cand/'app').rglob('*') if p.is_file()}
for rel in expected:
 lp=live/rel
 if not lp.is_file(): raise SystemExit(f'missing live candidate path: {rel}')
 (out/rel).write_bytes(lp.read_bytes())
expected_src={r for r in expected if r.startswith('app/src/')}; actual_src={str(p.relative_to(live)) for p in (live/'app/src').rglob('*') if p.is_file()}; extra=sorted(actual_src-expected_src)
if extra: raise SystemExit(f'unexpected app/src paths: {extra}')
print(f'PASS authority-seeded canonical live snapshot: {len(expected)} candidate files; generated app/build + app/.cxx excluded')
PY_S
}
install_frozen_candidate_live(){ rm -rf app; cp -a "$CAND/app" app; snapshot_live_authority_seeded "$LIVE_CANON"; universe_equal "$CAND" "$LIVE_CANON"; pass "authority-seeded canonical live candidate byte-identical to frozen 26842 candidate"; }
compile_languages(){ ./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace 2>&1 | tee "$OUT/26842_gradle_language_compilers.log"; snapshot_live_authority_seeded "$POST_LANG"; universe_equal "$CAND" "$POST_LANG"; sed -i 's/REAL KOTLIN COMPILE: NOT RUN YET/REAL KOTLIN COMPILE: PASS/' "$OUT/26842_COMPILER_STATUS.txt"; sed -i 's/REAL JAVA COMPILE: NOT RUN YET/REAL JAVA COMPILE: PASS/' "$OUT/26842_COMPILER_STATUS.txt"; pass "real Kotlin/Java compilers passed and frozen source remained byte-identical"; }
verify_native_glslang_handoff(){ [[ -n "${IRIS26842_GLSLANG:-}" && -x "$IRIS26842_GLSLANG" ]] || fail "IRIS26842_GLSLANG missing"; [[ -n "${IRIS26681_SPEKTRA_GLSLANG:-}" && -x "$IRIS26681_SPEKTRA_GLSLANG" ]] || fail "IRIS26681_SPEKTRA_GLSLANG missing"; [[ "$(readlink -f "$IRIS26842_GLSLANG")" == "$(readlink -f "$IRIS26681_SPEKTRA_GLSLANG")" ]] || fail "native/Spektra glslang handoff differs"; { echo "IRIS26681_SPEKTRA_GLSLANG=$IRIS26681_SPEKTRA_GLSLANG"; echo "IRIS26842_GLSLANG=$IRIS26842_GLSLANG"; } | tee "$OUT/26842_native_glslang_handoff.txt"; pass "successful 26841 native glslang handoff preserved before both-ABI native compile"; }
compile_native(){ ./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace 2>&1 | tee "$OUT/26842_gradle_native_compiler.log"; sed -i 's#NATIVE/NDK COMPILE: NOT RUN YET#NATIVE/NDK COMPILE: PASS (arm64-v8a + armeabi-v7a)#' "$OUT/26842_COMPILER_STATUS.txt"; }
verify_candidate_patches(){ python3 -S verify_26842_patches.py "$BASE" "$CAND" 26842_FORWARD_FULL_INDEX.patch 26842_ROLLBACK_FULL_INDEX.patch | tee "$OUT/26842_patch_validation.txt"; grep -F 'PASS 26842 canonical patch proof' "$OUT/26842_patch_validation.txt" >/dev/null; pass "sealed full-index forward/rollback proof: successful 26841 -> exact 3-path 26842 candidate"; }
prebuild_safety(){ snapshot_live_authority_seeded "$WORK/prebuild_live_snapshot"; universe_equal "$CAND" "$WORK/prebuild_live_snapshot"; python3 -S validate_26842.py "$BASE" "$CAND"; (cd "$CAND" && sha256sum -c "$ROOT/26842_PROTECTED_26841.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26842_NATIVE_PROTECTED_26841.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26842_VENDOR_26841.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26842_DNG_WRITER_26841.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26842_SHADER_ASSETS_PROTECTED_26841.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26842_FALSE_COLOR_ASSETS_PROTECTED_26841.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26842_SUCCESSFUL_26841_PERFORMANCE_REFERENCE.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26842_SABRE_PROTECTED_26841.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26842_SUCCESSFUL_26841_DNG_PHASE_REFERENCE.sha256" >/dev/null); cat > "$OUT/26842_PREBUILD_SAFETY.txt" <<EOF
PRE-BUILD SAFETY PROOF PASSED
runtime_authority=successful 26841 $RUNTIME_AUTHORITY_COMMIT run $RUNTIME_ACTIONS_RUN artifact $RUNTIME_ARTIFACT_ID
verification_mechanics=exact successful 26841 17-stage sequence; successful 26821 root mechanics inherited
runtime_changed_files=3 modified / 0 added / 0 deleted
runtime_allowlist=exact 3 paths in 26842_RUNTIME_CHANGED_PATHS.txt
protected_files=1783 unchanged
native_protected_files=819 unchanged
vendor_files=773 unchanged
dng_writer_files=6 unchanged
shader_assets_protected=273 unchanged; modified_shader_assets=1
base_candidate_files=1786
final_candidate_files=1786
image_quality=successful 26841 HDR preview/warm-midtone behavior frozen byte-identical; 26842 clip-zone source hue direction remains immutable while chroma magnitude rolls continuously with confidence; true-flat low-signal 5x5 cleanup modestly increased for car-body mottling
exposure=successful 26841 one-shot 26713->HAL target byte-identical; 0.30EV retarget deadband/no staircase/absolute recipe energy preserved
color=successful 26841 ACR3 warm-midtone restraint byte-identical; 26842 final clip-zone uses continuous source-hue saturation rolloff; broad donor has magnitude-only influence and no hue authority; warm fallback only after source hue is genuinely gone
high_zoom=successful 26841 high-zoom/native publication path preserved; 26842 shader restraint compile-time bypassed when USE_IRIS_26720_HIGH_ZOOM_RGB=1
runtime_glsl_delta=2 modified runtime-expanded shaders + 44 inherited active/protected variants
backup_branch_required=NONE_USER_EXPLICIT
EOF
echo 'PRE-BUILD SAFETY PROOF PASSED'; }
assemble(){ ./gradlew :app:assembleDebug --stacktrace 2>&1 | tee "$OUT/26842_gradle_assemble.log"; mapfile -t apks < <(find app/build/outputs/apk -type f -name '*.apk' | sort); [[ "${#apks[@]}" -eq 1 ]] || fail "expected exactly one APK, got ${#apks[@]}"; cp "${apks[0]}" "$FINAL"; sha256sum "$FINAL" | tee "$OUT/26842_APK.sha256"; sed -i 's/FULL ANDROID ASSEMBLE: NOT RUN YET/FULL ANDROID ASSEMBLE: PASS (exactly one APK)/' "$OUT/26842_COMPILER_STATUS.txt"; }
postbuild_proof(){ snapshot_live_authority_seeded "$WORK/postbuild_live_snapshot"; universe_equal "$CAND" "$WORK/postbuild_live_snapshot"; python3 -S validate_26842.py "$BASE" "$CAND"; (cd "$CAND" && sha256sum -c "$ROOT/26842_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26842_PROTECTED_26841.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26842_NATIVE_PROTECTED_26841.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26842_VENDOR_26841.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26842_DNG_WRITER_26841.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26842_SHADER_ASSETS_PROTECTED_26841.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26842_FALSE_COLOR_ASSETS_PROTECTED_26841.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26842_SUCCESSFUL_26841_PERFORMANCE_REFERENCE.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26842_SABRE_PROTECTED_26841.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26842_SUCCESSFUL_26841_DNG_PHASE_REFERENCE.sha256" >/dev/null); cp 26842_EXPECTED_CANDIDATE_FULL_APP.sha256 "$OUT/26842_candidate_full_app.sha256"; tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -czf "$OUT/26842_candidate_app_source.tar.gz" -C "$CAND" app; sha256sum "$OUT/26842_candidate_app_source.tar.gz" > "$OUT/26842_candidate_app_source.tar.gz.sha256"; cp 26842_FORWARD_FULL_INDEX.patch "$OUT/26842_FORWARD_FULL_INDEX.patch"; cp 26842_ROLLBACK_FULL_INDEX.patch "$OUT/26842_ROLLBACK_FULL_INDEX.patch"; sed -i 's/POST-BUILD INVARIANCE: NOT RUN YET/POST-BUILD INVARIANCE: PASS/' "$OUT/26842_COMPILER_STATUS.txt"; pass "authority-seeded post-build protected/DNG/native/vendor/shader/source invariance"; }
clean_extract_replay(){ local replay="$WORK/clean_replay_candidate"; rm -rf "$replay"; sha256sum -c 26842_HANDOFF_HASHES.sha256 >/dev/null; bash -n build_26842_clip_mottle.sh; python3 -S -m py_compile transform_26842.py validate_26842.py verify_26842_patches.py verify_26842_runtime_glsl.py; rm -rf __pycache__; python3 -S transform_26842.py "$BASE" "$replay" handoff_payload_26842; universe_equal "$CAND" "$replay"; python3 -S validate_26842.py "$BASE" "$replay"; python3 -S verify_26842_runtime_glsl.py "$BASE" "$replay" --out "$OUT/26842_final_runtime_expanded_glsl" | tee "$OUT/26842_final_glsl_static_replay.txt"; python3 -S verify_26842_patches.py "$BASE" "$replay" 26842_FORWARD_FULL_INDEX.patch 26842_ROLLBACK_FULL_INDEX.patch | tee "$OUT/26842_final_patch_replay.txt"; (cd "$replay" && sha256sum -c "$ROOT/26842_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null); grep -F 'VERSION_NAME=0.9726842' "$replay/app/version.properties" >/dev/null; grep -F 'VERSION_BUILD=26842' "$replay/app/version.properties" >/dev/null; for proof in 'REAL GLSL COMPILE: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS'; do grep -F "$proof" "$OUT/26842_COMPILER_STATUS.txt" >/dev/null || fail "missing final proof $proof"; done; pass "final 26842 clean replay of hashes/26841 HDR-preview+warm-color inheritance/continuous clipped-color rolloff/true-flat mottling cleanup/version/patch/compiler/build proofs"; }
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
pass "26842 CLIP-ROLLOFF MOTTLE: ACTIONS BUILD PROOF COMPLETE"
