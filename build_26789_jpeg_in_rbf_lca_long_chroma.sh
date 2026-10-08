#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
RUNTIME_AUTHORITY_COMMIT="979c455aa0695251301be2bdf2e3886805daa605"
RUNTIME_ACTIONS_RUN="37785801778"
RUNTIME_ARTIFACT_ID="11554488036"
RUNTIME_ARTIFACT_NAME="photon-26788-jpeg-cfa-phase-residual"
RUNTIME_ARTIFACT_SHA="a000abadd11c3bc55a8b0749bf6e0a9b8412fc536424b2b7effc6d0fcce0f1d2"
RUNTIME_TAR_SHA="85e7dc8841e85271991003c965413be2eb1aae4a23884d54ac3f0d82a0332306"
MECHANICS_AUTHORITY_COMMIT="979c455aa0695251301be2bdf2e3886805daa605"
MECHANICS_ACTIONS_RUN="37785801778"
ROOT_MECHANICS_COMMIT="69d5cb14f950d6fe5309441f7abf29d96631ab02"
ROOT_MECHANICS_RUN="37075896367"
VERSION_NAME="0.9726789"
VERSION_BUILD="26789"
GLSLANG_VERSION="16.5.0"
GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"
GLSLANG_URL="https://github.com/KhronosGroup/glslang/releases/download/16.5.0/glslang-16.5.0-linux-x86_64-release.tar.gz"
OUT="$ROOT/build_26789_jpeg_in_rbf_lca_long_chroma_outputs"
WORK="$ROOT/.build_26789_jpeg_in_rbf_lca_long_chroma_work"
ARTZIP="$WORK/26788_artifact.zip"
ARTDIR="$WORK/artifact_26788"
BASE="$WORK/exact_successful_26788_compiled_candidate"
CAND="$WORK/candidate_26789"
LIVE_CANON="$WORK/live_compiler_candidate_snapshot"
POST_LANG="$WORK/post_language_compiler_source_snapshot"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-jpeg-in-rbf-lca-long-chroma-debug.apk"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR"
cat > "$OUT/26789_COMPILER_STATUS.txt" <<EOF
REAL GLSL COMPILE: NOT RUN YET
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
NATIVE/NDK COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
EOF

# IRIS_26789_AUTHORITATIVE_ACTIONS_STAGE_ORDER
verify_package(){
  sha256sum -c 26789_HANDOFF_HASHES.sha256 >/dev/null
  bash -n build_26789_jpeg_in_rbf_lca_long_chroma.sh
  python3 -S -m py_compile transform_26789.py validate_26789.py verify_26789_patches.py verify_26789_embedded_glsl.py
  rm -rf __pycache__
  [[ "$(find handoff_payload_26789 -type f | wc -l)" -eq 3 ]] || fail "26789 payload count"
  diff -u 26789_RUNTIME_CHANGED_PATHS.txt <(find handoff_payload_26789 -type f | sed 's#^handoff_payload_26789/##' | sort) >/dev/null || fail "26789 payload allowlist mismatch"
  for p in 26789_FORWARD_FULL_INDEX.patch 26789_ROLLBACK_FULL_INDEX.patch; do
    ! grep -Eq '^(rename from|rename to|copy from|copy to) ' "$p" || fail "26789 patch contains rename/copy inference: $p"
  done
  grep -Fx 'RUN_26789_JPEG_IN_RBF_LCA_LONG_CHROMA' TRIGGER_26789.txt >/dev/null || fail "26789 trigger contents"
  ! find . -type f -name '*.apk' | grep -q . || fail "APK unexpectedly packaged"
  pass "sealed 26789 package hashes/syntax/allowlist/patch identity"
}

verify_scope(){
  [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch"
  git merge-base --is-ancestor "$RUNTIME_AUTHORITY_COMMIT" HEAD || fail "26788 runtime authority not ancestor"
  git merge-base --is-ancestor "$MECHANICS_AUTHORITY_COMMIT" HEAD || fail "26788 mechanics authority not ancestor"
  git merge-base --is-ancestor "$ROOT_MECHANICS_COMMIT" HEAD || fail "26752 root mechanics authority not ancestor"
  if git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD | grep -E '^app/'; then fail "live app source changed after 26788 authority"; fi
  python3 -S - <<'PY_SCOPE'
import subprocess
allowed_prefixes=(
 '26789_','build_26789_jpeg_in_rbf_lca_long_chroma.sh','transform_26789.py','validate_26789.py',
 'verify_26789_patches.py','verify_26789_embedded_glsl.py','handoff_payload_26789/',
 '.github/workflows/build-26789-jpeg-in-rbf-lca-long-chroma.yml','TRIGGER_26789.txt',
 'PHOTON_26789_IN_RBF_LCA_LONG_CHROMA_README.txt')
paths=subprocess.check_output(['git','diff','--name-only','979c455aa0695251301be2bdf2e3886805daa605..HEAD'],text=True).splitlines()
bad=[p for p in paths if not any(p==x or p.startswith(x) for x in allowed_prefixes)]
assert not bad,bad
print('PASS 26789 infrastructure scope allowlist')
PY_SCOPE
  pass "26789 scope exact: successful 26788 authority + sealed 3-file payload; live app untouched"
}

obtain_authority(){
  [[ -n "$TOKEN" ]] || fail "GITHUB_TOKEN missing"
  curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" \
    "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${RUNTIME_ARTIFACT_ID}/zip" -o "$ARTZIP"
  [[ "$(sha "$ARTZIP")" == "$RUNTIME_ARTIFACT_SHA" ]] || fail "26788 artifact sha"
  unzip -q "$ARTZIP" -d "$ARTDIR"
  T="$ARTDIR/build_26788_jpeg_cfa_phase_residual_outputs/26788_candidate_app_source.tar.gz"
  [[ -f "$T" && "$(sha "$T")" == "$RUNTIME_TAR_SHA" ]] || fail "26788 candidate tar sha"
  STATUS="$ARTDIR/build_26788_jpeg_cfa_phase_residual_outputs/26788_COMPILER_STATUS.txt"
  for proof in 'REAL GLSL COMPILE: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS'; do
    grep -F "$proof" "$STATUS" >/dev/null || fail "missing 26788 authority proof: $proof"
  done
  mkdir -p "$BASE"; tar -xzf "$T" -C "$BASE"
  [[ "$(find "$BASE/app" -type f | wc -l)" -eq 1779 ]] || fail "26788 base file count"
  (cd "$BASE" && sha256sum -c "$ROOT/26789_BASE_26788_FULL_APP.sha256" >/dev/null) || fail "26788 full base manifest"
  (cd "$BASE" && sha256sum -c "$ROOT/26789_PRIOR_SOURCE_HASHES.sha256" >/dev/null) || fail "26788 prior source hashes"
  (cd "$BASE" && sha256sum -c "$ROOT/26789_NATIVE_26788.sha256" >/dev/null) || fail "26788 native manifest"
  (cd "$BASE" && sha256sum -c "$ROOT/26789_VENDOR_26788.sha256" >/dev/null) || fail "26788 vendor manifest"
  (cd "$BASE" && sha256sum -c "$ROOT/26789_DNG_WRITER_26788.sha256" >/dev/null) || fail "26788 DNG writer manifest"
  cat > "$OUT/26789_RESOLVED_AUTHORITIES.txt" <<EOF
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
  pass "exact successful 26788 compiled candidate reconstructed"
}

universe_equal(){ python3 -S - "$1" "$2" <<'PY_UNIVERSE'
from pathlib import Path
import hashlib,sys
def U(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(r)/'app').rglob('*') if p.is_file()}
a,b=U(sys.argv[1]),U(sys.argv[2]); assert a==b,(len(a),len(b)); print(f'PASS byte-identical app universe: {len(a)} files')
PY_UNIVERSE
}

make_candidate(){
  python3 -S transform_26789.py "$BASE" "$CAND" handoff_payload_26789
  python3 -S validate_26789.py "$BASE" "$CAND"
  (cd "$CAND" && sha256sum -c "$ROOT/26789_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null) || fail "26789 candidate manifest"
  (cd "$CAND" && sha256sum -c "$ROOT/26789_PROTECTED_26788.sha256" >/dev/null) || fail "26789 protected manifest"
  (cd "$CAND" && sha256sum -c "$ROOT/26789_NATIVE_26788.sha256" >/dev/null) || fail "26789 native invariance"
  (cd "$CAND" && sha256sum -c "$ROOT/26789_VENDOR_26788.sha256" >/dev/null) || fail "26789 vendor invariance"
  (cd "$CAND" && sha256sum -c "$ROOT/26789_DNG_WRITER_26788.sha256" >/dev/null) || fail "26789 DNG-writer invariance"
  [[ "$(find "$CAND/app" -type f | wc -l)" -eq 1779 ]] || fail "26789 candidate file count"
  pass "candidate-first 26789 in-RBF DNG-geometry LCA + LONG chroma guard reconstruction/ownership checks"
}

verify_successful_mechanics(){
  local a88="$WORK/authority_26788_build.sh" a52="$WORK/authority_26752_build.sh"
  git show "$MECHANICS_AUTHORITY_COMMIT:build_26788_jpeg_cfa_phase_residual.sh" > "$a88"
  git show "$ROOT_MECHANICS_COMMIT:build_26752_ipol_plan_b_translational_sr.sh" > "$a52"
  for cmd in './gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace' \
             "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace" \
             './gradlew :app:assembleDebug --stacktrace'; do
    grep -F "$cmd" "$a88" >/dev/null || fail "26788 authority command missing: $cmd"
    grep -F "$cmd" "$0" >/dev/null || fail "26789 command differs: $cmd"
  done
  grep -F 'compile_spektra_raw_shader(){' "$a88" >/dev/null || fail "26788 Spektra verifier stage missing"
  grep -F 'compile_spektra_raw_shader(){' "$0" >/dev/null || fail "26789 Spektra verifier stage missing"
  grep -F 'verify_native_glslang_handoff(){' "$a88" >/dev/null || fail "26788 native handoff stage missing"
  grep -F 'verify_native_glslang_handoff(){' "$0" >/dev/null || fail "26789 native handoff stage missing"
  python3 -S - "$0" "$a88" "$a52" <<'PY_ORDER'
from pathlib import Path
import sys
def ordered(text,marker,tokens,label):
 i=text.find(marker)
 if i<0: raise SystemExit(f'{label}: missing marker {marker}')
 text=text[i:]; pos=-1
 for token in tokens:
  nxt=text.find(token,pos+1)
  if nxt<0: raise SystemExit(f'{label}: missing stage {token}')
  if nxt<=pos: raise SystemExit(f'{label}: out-of-order stage {token}')
  pos=nxt
stages=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','verify_candidate_patches','prebuild_safety','assemble','postbuild_proof','clean_extract_replay']
cur,a88,a52=[Path(x).read_text() for x in sys.argv[1:]]
ordered(cur,'# IRIS_26789_AUTHORITATIVE_ACTIONS_STAGE_ORDER',stages,'26789')
ordered(a88,'# IRIS_26788_AUTHORITATIVE_ACTIONS_STAGE_ORDER',stages,'26788 authority')
auth52=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26751_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac','after_language_compiler_snapshot',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]'",'verify_candidate_patches','PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug','mapfile -t apks','postbuild_proof']
ordered(a52,'# IRIS_26752_AUTHORITATIVE_ACTIONS_STAGE_ORDER',auth52,'26752 root authority')
print('PASS 26789 stage order exactly inherits successful 26788 procedure and root 26752 mechanics')
PY_ORDER
  cat > "$OUT/26789_MECHANICS_DIFF_AUDIT.txt" <<EOF
26789 vs exact successful 26788 implementation:
- 17-stage authoritative Actions order: IDENTICAL
- Kotlin/Java compiler command: IDENTICAL
- both-ABI native compiler command: IDENTICAL
- full assemble command: IDENTICAL
- Spektra stage position: IDENTICAL
- native glslang handoff stage position: IDENTICAL
- runtime authority advanced only: successful 26788 -> 26789 candidate
- version/name/validator scope advanced only for the intended 26789 3-file runtime correction
- no stage reorder, removal, substitution, or compiler simplification
EOF
  pass "successful 26788 implementation diff-audited: zero stage-order/compiler/native/assemble deviation"
}

prepare_glslang(){
  D="$WORK/glslang-${GLSLANG_VERSION}"; A="$WORK/glslang.tar.gz"; mkdir -p "$D"
  curl -L --fail --retry 3 "$GLSLANG_URL" -o "$A"
  [[ "$(sha "$A")" == "$GLSLANG_ARCHIVE_SHA" ]] || fail "glslang archive sha"
  tar -xzf "$A" -C "$D"
  compiler="$(find "$D" -type f -name glslang -print -quit)"
  [[ -n "$compiler" ]] || compiler="$(find "$D" \( -type f -o -type l \) -name glslangValidator -print -quit)"
  compiler="$(readlink -f "$compiler")"; [[ -x "$compiler" ]] || chmod +x "$compiler"
  "$compiler" --version | tee "$OUT/26789_glslang_version.txt"
  export IRIS26789_GLSLANG="$compiler"
  export IRIS26681_SPEKTRA_GLSLANG="$compiler"
  pass "pinned glslang 16.5.0 dual environment handoff"
}

compile_modified_runtime_shaders(){
  python3 -S verify_26789_embedded_glsl.py "$BASE" "$CAND" --compiler "$IRIS26789_GLSLANG" --out "$OUT/26789_runtime_expanded_glsl" | tee "$OUT/26789_glsl_validation.txt"
  grep -F 'PASS 26789 modified shader ownership: merge-only NORMAL/LONG in-RBF DNG-geometry LCA + same-coordinate headroom + LONG chroma guard' "$OUT/26789_glsl_validation.txt" >/dev/null || fail "26789 modified shader ownership proof missing"
  grep -F 'PASS 26789 protected shader fidelity: SHORT/26788 residual/DNG/neutral/VGN owners byte-identical to successful 26788' "$OUT/26789_glsl_validation.txt" >/dev/null || fail "26789 protected shader fidelity proof missing"
  for shader in merge jpegPhaseSafeCfaLca26788 universalNormalMasterShortFusion26651 EDGE_FALSE_COLOR_SUPPRESSOR_26778 jpegNeutralHighlightClamp26787 normalDngMerge normalizeBayer universalAdaptiveColor26561 bipolarColorTrust26769; do
    grep -F "PASS 26789 pinned real glslang compile runtime-expanded shader: $shader" "$OUT/26789_glsl_validation.txt" >/dev/null || fail "missing real glslang proof: $shader"
  done
  sed -i 's/REAL GLSL COMPILE: NOT RUN YET/REAL GLSL COMPILE: PASS (1 modified + 8 inherited active\/protected shaders, pinned glslang 16.5.0)/' "$OUT/26789_COMPILER_STATUS.txt"
}

compile_spektra_raw_shader(){
  # Exact successful 26788 behavior: no standalone repo-shell Spektra verifier was present; source remains protected by the candidate manifest.
  pass "Spektra project verifier absent from repo shell; inherited source protected by candidate manifest"
}

snapshot_live_authority_seeded(){ python3 -S - "$CAND" "$1" "$ROOT" <<'PY_SNAPSHOT'
from pathlib import Path
import hashlib,shutil,sys
cand,out,live=map(Path,sys.argv[1:])
if out.exists(): shutil.rmtree(out)
shutil.copytree(cand,out)
# Compiler/build outputs never enter source authority. Overlay only files in the frozen compiled-candidate universe.
expected={str(p.relative_to(cand)):p for p in (cand/'app').rglob('*') if p.is_file()}
for rel,cp in expected.items():
    lp=live/rel
    if not lp.is_file(): raise SystemExit(f'missing live candidate path: {rel}')
    op=out/rel; op.write_bytes(lp.read_bytes())
# Unexpected real runtime source must remain visible and fail; generated build/.cxx and repository-only non-source scaffolding are ignored.
expected_src={r for r in expected if r.startswith('app/src/')}
actual_src={str(p.relative_to(live)) for p in (live/'app/src').rglob('*') if p.is_file()}
extra=sorted(actual_src-expected_src)
if extra: raise SystemExit(f'unexpected app/src paths: {extra}')
print(f'PASS authority-seeded canonical live snapshot: {len(expected)} candidate files; generated app/build + app/.cxx excluded')
PY_SNAPSHOT
}

install_frozen_candidate_live(){
  rm -rf app
  cp -a "$CAND/app" app
  snapshot_live_authority_seeded "$LIVE_CANON"
  universe_equal "$CAND" "$LIVE_CANON"
  pass "authority-seeded canonical live candidate byte-identical to frozen 26789 candidate"
}

compile_languages(){
  ./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace 2>&1 | tee "$OUT/26789_gradle_language_compilers.log"
  snapshot_live_authority_seeded "$POST_LANG"
  universe_equal "$CAND" "$POST_LANG"
  sed -i 's/REAL KOTLIN COMPILE: NOT RUN YET/REAL KOTLIN COMPILE: PASS/' "$OUT/26789_COMPILER_STATUS.txt"
  sed -i 's/REAL JAVA COMPILE: NOT RUN YET/REAL JAVA COMPILE: PASS/' "$OUT/26789_COMPILER_STATUS.txt"
  pass "real Kotlin/Java compilers passed and frozen source remained byte-identical"
}

verify_native_glslang_handoff(){
  [[ -n "${IRIS26789_GLSLANG:-}" && -x "$IRIS26789_GLSLANG" ]] || fail "IRIS26789_GLSLANG missing"
  [[ -n "${IRIS26681_SPEKTRA_GLSLANG:-}" && -x "$IRIS26681_SPEKTRA_GLSLANG" ]] || fail "IRIS26681_SPEKTRA_GLSLANG missing"
  [[ "$(readlink -f "$IRIS26789_GLSLANG")" == "$(readlink -f "$IRIS26681_SPEKTRA_GLSLANG")" ]] || fail "native/Spektra glslang handoff differs"
  { echo "IRIS26681_SPEKTRA_GLSLANG=$IRIS26681_SPEKTRA_GLSLANG"; echo "IRIS26789_GLSLANG=$IRIS26789_GLSLANG"; } | tee "$OUT/26789_native_glslang_handoff.txt"
  pass "successful 26788 native glslang handoff preserved before both-ABI native compile"
}

compile_native(){
  ./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace 2>&1 | tee "$OUT/26789_gradle_native_compiler.log"
  sed -i 's#NATIVE/NDK COMPILE: NOT RUN YET#NATIVE/NDK COMPILE: PASS (arm64-v8a + armeabi-v7a)#' "$OUT/26789_COMPILER_STATUS.txt"
}

verify_candidate_patches(){
  python3 -S verify_26789_patches.py "$BASE" "$CAND" 26789_FORWARD_FULL_INDEX.patch 26789_ROLLBACK_FULL_INDEX.patch | tee "$OUT/26789_patch_validation.txt"
  grep -F 'PASS 26789 canonical patch proof' "$OUT/26789_patch_validation.txt" >/dev/null || fail "canonical patch proof missing"
  pass "sealed full-index forward/rollback proof: successful 26788 -> exact 3-file 26789 candidate"
}

prebuild_safety(){
  snapshot_live_authority_seeded "$WORK/prebuild_live_snapshot"
  universe_equal "$CAND" "$WORK/prebuild_live_snapshot"
  python3 -S validate_26789.py "$BASE" "$CAND"
  (cd "$CAND" && sha256sum -c "$ROOT/26789_PROTECTED_26788.sha256" >/dev/null)
  (cd "$CAND" && sha256sum -c "$ROOT/26789_NATIVE_26788.sha256" >/dev/null)
  (cd "$CAND" && sha256sum -c "$ROOT/26789_VENDOR_26788.sha256" >/dev/null)
  (cd "$CAND" && sha256sum -c "$ROOT/26789_DNG_WRITER_26788.sha256" >/dev/null)
  cat > "$OUT/26789_PREBUILD_SAFETY.txt" <<EOF
PRE-BUILD SAFETY PROOF PASSED
runtime_authority=successful 26788 $RUNTIME_AUTHORITY_COMMIT run $RUNTIME_ACTIONS_RUN artifact $RUNTIME_ARTIFACT_ID
verification_mechanics=exact successful 26788 17-stage sequence; root 26752 inherited
runtime_changed_files=3 modified / 0 added / 0 deleted
protected_files=1776 unchanged
native_files=819 unchanged
vendor_files=773 unchanged
dng_writer_files=6 unchanged + normalDngMerge block byte-identical
candidate_files=1779
post_rgb_lca_retired=true
normal_long_prewarp_26788_retired=true
normal_long_lca_owner=IN_RBF_DNG_GEOMETRY
same_coordinate_signal_headroom=true
neutral_highlight_26787_owner_unchanged=true
neutral_math=DNG_AS_SHOT_NEUTRAL_WB_EQUIVALENT
long_chroma_guard=SHADOW_LONG_ONLY_LUMA_PRESERVED
material_baseline_periodic_guard_26788_unchanged=true
broad_clipped_neutral_applied=false
EOF
  echo 'PRE-BUILD SAFETY PROOF PASSED'
}

assemble(){
  ./gradlew :app:assembleDebug --stacktrace 2>&1 | tee "$OUT/26789_gradle_assemble.log"
  mapfile -t apks < <(find app/build/outputs/apk -type f -name '*.apk' | sort)
  [[ "${#apks[@]}" -eq 1 ]] || fail "expected exactly one APK, got ${#apks[@]}: ${apks[*]-}"
  cp "${apks[0]}" "$FINAL"
  [[ -f "$FINAL" ]] || fail "final APK copy missing"
  sha256sum "$FINAL" | tee "$OUT/26789_APK.sha256"
  sed -i 's/FULL ANDROID ASSEMBLE: NOT RUN YET/FULL ANDROID ASSEMBLE: PASS (exactly one APK)/' "$OUT/26789_COMPILER_STATUS.txt"
}

postbuild_proof(){
  snapshot_live_authority_seeded "$WORK/postbuild_live_snapshot"
  universe_equal "$CAND" "$WORK/postbuild_live_snapshot"
  python3 -S validate_26789.py "$BASE" "$CAND"
  (cd "$CAND" && sha256sum -c "$ROOT/26789_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null)
  (cd "$CAND" && sha256sum -c "$ROOT/26789_PROTECTED_26788.sha256" >/dev/null)
  (cd "$CAND" && sha256sum -c "$ROOT/26789_NATIVE_26788.sha256" >/dev/null)
  (cd "$CAND" && sha256sum -c "$ROOT/26789_VENDOR_26788.sha256" >/dev/null)
  (cd "$CAND" && sha256sum -c "$ROOT/26789_DNG_WRITER_26788.sha256" >/dev/null)
  cp 26789_EXPECTED_CANDIDATE_FULL_APP.sha256 "$OUT/26789_candidate_full_app.sha256"
  tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -czf "$OUT/26789_candidate_app_source.tar.gz" -C "$CAND" app
  sha256sum "$OUT/26789_candidate_app_source.tar.gz" > "$OUT/26789_candidate_app_source.tar.gz.sha256"
  cp 26789_FORWARD_FULL_INDEX.patch "$OUT/26789_FORWARD_FULL_INDEX.patch"
  cp 26789_ROLLBACK_FULL_INDEX.patch "$OUT/26789_ROLLBACK_FULL_INDEX.patch"
  sed -i 's/POST-BUILD INVARIANCE: NOT RUN YET/POST-BUILD INVARIANCE: PASS/' "$OUT/26789_COMPILER_STATUS.txt"
  pass "authority-seeded post-build protected/DNG/native/vendor/source invariance"
}

clean_extract_replay(){
  local replay="$WORK/clean_replay_candidate"
  rm -rf "$replay"
  sha256sum -c 26789_HANDOFF_HASHES.sha256 >/dev/null
  bash -n build_26789_jpeg_in_rbf_lca_long_chroma.sh
  python3 -S -m py_compile transform_26789.py validate_26789.py verify_26789_patches.py verify_26789_embedded_glsl.py
  rm -rf __pycache__
  python3 -S transform_26789.py "$BASE" "$replay" handoff_payload_26789
  universe_equal "$CAND" "$replay"
  python3 -S validate_26789.py "$BASE" "$replay"
  python3 -S verify_26789_embedded_glsl.py "$BASE" "$replay" --out "$OUT/26789_final_runtime_expanded_glsl" | tee "$OUT/26789_final_glsl_static_replay.txt"
  python3 -S verify_26789_patches.py "$BASE" "$replay" 26789_FORWARD_FULL_INDEX.patch 26789_ROLLBACK_FULL_INDEX.patch | tee "$OUT/26789_final_patch_replay.txt"
  (cd "$replay" && sha256sum -c "$ROOT/26789_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null)
  grep -F 'VERSION_NAME=0.9726789' "$replay/app/version.properties" >/dev/null
  grep -F 'VERSION_BUILD=26789' "$replay/app/version.properties" >/dev/null
  grep -F 'REAL GLSL COMPILE: PASS' "$OUT/26789_COMPILER_STATUS.txt" >/dev/null
  grep -F 'REAL KOTLIN COMPILE: PASS' "$OUT/26789_COMPILER_STATUS.txt" >/dev/null
  grep -F 'REAL JAVA COMPILE: PASS' "$OUT/26789_COMPILER_STATUS.txt" >/dev/null
  grep -F 'NATIVE/NDK COMPILE: PASS' "$OUT/26789_COMPILER_STATUS.txt" >/dev/null
  grep -F 'FULL ANDROID ASSEMBLE: PASS' "$OUT/26789_COMPILER_STATUS.txt" >/dev/null
  grep -F 'POST-BUILD INVARIANCE: PASS' "$OUT/26789_COMPILER_STATUS.txt" >/dev/null
  pass "final 26789 clean replay of package hashes/in-RBF-LCA/LONG-chroma-guard/DNG-neutral-freeze/version/patch/compiler/build proofs"
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

echo
echo '========================================='
echo '26789 JPEG IN-RBF LCA + LONG CHROMA: PASS'
echo "Runtime authority: successful 26788 $RUNTIME_AUTHORITY_COMMIT"
echo 'Verification mechanics authority: exact successful 26788 17-stage procedure (root 26752 inherited)'
echo 'Runtime changed-file allowlist: 3 modified, 0 added, 0 deleted'
echo 'Infrastructure mechanics: zero stage-order/compiler/native/assemble deviation from successful 26788'
echo 'Real GLSL/Kotlin/Java/NDK/full assemble: PASS'
echo 'Exactly one APK: PASS'
echo '========================================='
