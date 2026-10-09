#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
RUNTIME_AUTHORITY_COMMIT="46c5cd4b4fd1ae28b4394a2e2388edffb276a85a"
RUNTIME_ACTIONS_RUN="37877930275"
RUNTIME_ARTIFACT_ID="11592844879"
RUNTIME_ARTIFACT_NAME="photon-26792-continuous-cfa-lca-neutral-ab"
RUNTIME_ARTIFACT_SHA="8a9eaeecf687838cdad9655811ecaf9183d66ac2621f9d89daf86b33c1ad0c6d"
RUNTIME_TAR_SHA="00ac3858ec090c9735114ce4a189ead7730741208526c63c3c68496b5dcf181a"
MECHANICS_AUTHORITY_COMMIT="46c5cd4b4fd1ae28b4394a2e2388edffb276a85a"
MECHANICS_ACTIONS_RUN="37877930275"
ROOT_MECHANICS_COMMIT="69d5cb14f950d6fe5309441f7abf29d96631ab02"
ROOT_MECHANICS_RUN="37075896367"
VERSION_NAME="0.9726793"
VERSION_BUILD="26793"
GLSLANG_VERSION="16.5.0"
GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"
GLSLANG_URL="https://github.com/KhronosGroup/glslang/releases/download/16.5.0/glslang-16.5.0-linux-x86_64-release.tar.gz"
OUT="$ROOT/build_26793_sabre_same_location_cfa_color_outputs"
WORK="$ROOT/.build_26793_sabre_same_location_cfa_color_work"
ARTZIP="$WORK/26792_artifact.zip"
ARTDIR="$WORK/artifact_26792"
BASE="$WORK/exact_successful_26792_compiled_candidate"
CAND="$WORK/candidate_26793"
LIVE_CANON="$WORK/live_compiler_candidate_snapshot"
POST_LANG="$WORK/post_language_compiler_source_snapshot"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-sabre-same-location-cfa-color-debug.apk"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR"
cat > "$OUT/26793_COMPILER_STATUS.txt" <<EOF
REAL GLSL COMPILE: NOT RUN YET
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
NATIVE/NDK COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
EOF

# IRIS_26793_AUTHORITATIVE_ACTIONS_STAGE_ORDER
verify_package(){
  sha256sum -c 26793_HANDOFF_HASHES.sha256 >/dev/null
  bash -n build_26793_sabre_same_location_cfa_color.sh
  python3 -S -m py_compile transform_26793.py validate_26793.py verify_26793_patches.py verify_26793_runtime_glsl.py
  rm -rf __pycache__
  [[ "$(find handoff_payload_26793 -type f | wc -l)" -eq 2 ]] || fail "26793 payload count"
  diff -u 26793_RUNTIME_CHANGED_PATHS.txt <(find handoff_payload_26793 -type f | sed 's#^handoff_payload_26793/##' | sort) >/dev/null || fail "26793 payload allowlist mismatch"
  for p in 26793_FORWARD_FULL_INDEX.patch 26793_ROLLBACK_FULL_INDEX.patch; do
    ! grep -Eq '^(rename from|rename to|copy from|copy to) ' "$p" || fail "26793 patch contains rename/copy inference: $p"
  done
  grep -Fx 'RUN_26793_SABRE_SAME_LOCATION_CFA_COLOR' TRIGGER_26793.txt >/dev/null || fail "26793 trigger contents"
  ! find . -type f -name '*.apk' | grep -q . || fail "APK unexpectedly packaged"
  pass "sealed 26793 package hashes/syntax/allowlist/patch identity"
}

verify_scope(){
  [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch"
  git merge-base --is-ancestor "$RUNTIME_AUTHORITY_COMMIT" HEAD || fail "26792 runtime authority not ancestor"
  git merge-base --is-ancestor "$MECHANICS_AUTHORITY_COMMIT" HEAD || fail "26792 mechanics authority not ancestor"
  git merge-base --is-ancestor "$ROOT_MECHANICS_COMMIT" HEAD || fail "26752 root mechanics authority not ancestor"
  if git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD | grep -E '^app/'; then fail "live app source changed after 26792 authority"; fi
  python3 -S - <<'PY_SCOPE'
import subprocess
allowed_prefixes=(
 '26793_','build_26793_sabre_same_location_cfa_color.sh','transform_26793.py','validate_26793.py',
 'verify_26793_patches.py','verify_26793_runtime_glsl.py','handoff_payload_26793/',
 '.github/workflows/build-26793-sabre-same-location-cfa-color.yml','TRIGGER_26793.txt',
 'PHOTON_26793_SABRE_SAME_LOCATION_CFA_COLOR_README.txt')
paths=subprocess.check_output(['git','diff','--name-only','46c5cd4b4fd1ae28b4394a2e2388edffb276a85a..HEAD'],text=True).splitlines()
bad=[p for p in paths if not any(p==x or p.startswith(x) for x in allowed_prefixes)]
assert not bad,bad
print('PASS 26793 infrastructure scope allowlist')
PY_SCOPE
  pass "26793 scope exact: successful 26792 authority + sealed 2-file payload; live app untouched"
}

obtain_authority(){
  [[ -n "$TOKEN" ]] || fail "GITHUB_TOKEN missing"
  curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" \
    "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${RUNTIME_ARTIFACT_ID}/zip" -o "$ARTZIP"
  [[ "$(sha "$ARTZIP")" == "$RUNTIME_ARTIFACT_SHA" ]] || fail "26792 artifact sha"
  unzip -q "$ARTZIP" -d "$ARTDIR"
  T="$ARTDIR/build_26792_continuous_cfa_lca_neutral_ab_outputs/26792_candidate_app_source.tar.gz"
  [[ -f "$T" && "$(sha "$T")" == "$RUNTIME_TAR_SHA" ]] || fail "26792 candidate tar sha"
  STATUS="$ARTDIR/build_26792_continuous_cfa_lca_neutral_ab_outputs/26792_COMPILER_STATUS.txt"
  for proof in 'REAL GLSL COMPILE: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS'; do
    grep -F "$proof" "$STATUS" >/dev/null || fail "missing 26792 authority proof: $proof"
  done
  mkdir -p "$BASE"; tar -xzf "$T" -C "$BASE"
  [[ "$(find "$BASE/app" -type f | wc -l)" -eq 1779 ]] || fail "26792 base file count"
  (cd "$BASE" && sha256sum -c "$ROOT/26793_BASE_26792_FULL_APP.sha256" >/dev/null) || fail "26792 full base manifest"
  (cd "$BASE" && sha256sum -c "$ROOT/26793_PRIOR_SOURCE_HASHES.sha256" >/dev/null) || fail "26792 prior source hashes"
  (cd "$BASE" && sha256sum -c "$ROOT/26793_NATIVE_26792.sha256" >/dev/null) || fail "26792 native manifest"
  (cd "$BASE" && sha256sum -c "$ROOT/26793_VENDOR_26792.sha256" >/dev/null) || fail "26792 vendor manifest"
  (cd "$BASE" && sha256sum -c "$ROOT/26793_DNG_WRITER_26792.sha256" >/dev/null) || fail "26792 DNG writer manifest"
  cat > "$OUT/26793_RESOLVED_AUTHORITIES.txt" <<EOF
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
  pass "exact successful 26792 compiled candidate reconstructed"
}

universe_equal(){ python3 -S - "$1" "$2" <<'PY_UNIVERSE'
from pathlib import Path
import hashlib,sys
def U(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(r)/'app').rglob('*') if p.is_file()}
a,b=U(sys.argv[1]),U(sys.argv[2]); assert a==b,(len(a),len(b)); print(f'PASS byte-identical app universe: {len(a)} files')
PY_UNIVERSE
}

make_candidate(){
  python3 -S transform_26793.py "$BASE" "$CAND" handoff_payload_26793
  python3 -S validate_26793.py "$BASE" "$CAND"
  (cd "$CAND" && sha256sum -c "$ROOT/26793_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null) || fail "26793 candidate manifest"
  (cd "$CAND" && sha256sum -c "$ROOT/26793_PROTECTED_26792.sha256" >/dev/null) || fail "26793 protected manifest"
  (cd "$CAND" && sha256sum -c "$ROOT/26793_NATIVE_26792.sha256" >/dev/null) || fail "26793 native invariance"
  (cd "$CAND" && sha256sum -c "$ROOT/26793_VENDOR_26792.sha256" >/dev/null) || fail "26793 vendor invariance"
  (cd "$CAND" && sha256sum -c "$ROOT/26793_DNG_WRITER_26792.sha256" >/dev/null) || fail "26793 DNG-writer invariance"
  [[ "$(find "$CAND/app" -type f | wc -l)" -eq 1779 ]] || fail "26793 candidate file count"
  pass "candidate-first 26793 same-location CFA color-difference reconstruction"
}

verify_successful_mechanics(){
  local a92="$WORK/authority_26792_build.sh" a52="$WORK/authority_26752_build.sh"
  git show "$MECHANICS_AUTHORITY_COMMIT:build_26792_continuous_cfa_lca_neutral_ab.sh" > "$a92"
  git show "$ROOT_MECHANICS_COMMIT:build_26752_ipol_plan_b_translational_sr.sh" > "$a52"
  for cmd in './gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace' \
             "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace" \
             './gradlew :app:assembleDebug --stacktrace'; do
    grep -F "$cmd" "$a92" >/dev/null || fail "26792 authority command missing: $cmd"
    grep -F "$cmd" "$0" >/dev/null || fail "26793 command differs: $cmd"
  done
  grep -F 'compile_spektra_raw_shader(){' "$a92" >/dev/null || fail "26792 Spektra verifier stage missing"
  grep -F 'compile_spektra_raw_shader(){' "$0" >/dev/null || fail "26793 Spektra verifier stage missing"
  grep -F 'verify_native_glslang_handoff(){' "$a92" >/dev/null || fail "26792 native handoff stage missing"
  grep -F 'verify_native_glslang_handoff(){' "$0" >/dev/null || fail "26793 native handoff stage missing"
  python3 -S - "$0" "$a92" "$a52" <<'PY_ORDER'
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
cur,a92,a52=[Path(x).read_text() for x in sys.argv[1:]]
ordered(cur,'# IRIS_26793_AUTHORITATIVE_ACTIONS_STAGE_ORDER',stages,'26793')
ordered(a92,'# IRIS_26792_AUTHORITATIVE_ACTIONS_STAGE_ORDER',stages,'26792 authority')
auth52=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26751_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac','after_language_compiler_snapshot',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]'",'verify_candidate_patches','PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug','mapfile -t apks','postbuild_proof']
ordered(a52,'# IRIS_26752_AUTHORITATIVE_ACTIONS_STAGE_ORDER',auth52,'26752 root authority')
print('PASS 26793 stage order exactly inherits successful 26792 procedure and root 26752 mechanics')
PY_ORDER
  cp 26793_MECHANICS_DIFF_AUDIT.txt "$OUT/26793_MECHANICS_DIFF_AUDIT.txt"
  pass "successful 26792 implementation diff-audited: zero stage-order/compiler/native/assemble deviation"
}

prepare_glslang(){
  D="$WORK/glslang-${GLSLANG_VERSION}"; A="$WORK/glslang.tar.gz"; mkdir -p "$D"
  curl -L --fail --retry 3 "$GLSLANG_URL" -o "$A"
  [[ "$(sha "$A")" == "$GLSLANG_ARCHIVE_SHA" ]] || fail "glslang archive sha"
  tar -xzf "$A" -C "$D"
  compiler="$(find "$D" -type f -name glslang -print -quit)"
  [[ -n "$compiler" ]] || compiler="$(find "$D" \( -type f -o -type l \) -name glslangValidator -print -quit)"
  compiler="$(readlink -f "$compiler")"; [[ -x "$compiler" ]] || chmod +x "$compiler"
  "$compiler" --version | tee "$OUT/26793_glslang_version.txt"
  export IRIS26793_GLSLANG="$compiler"
  export IRIS26681_SPEKTRA_GLSLANG="$compiler"
  pass "pinned glslang 16.5.0 dual environment handoff"
}

compile_modified_runtime_shaders(){
  python3 -S verify_26793_runtime_glsl.py "$BASE" "$CAND" --compiler "$IRIS26793_GLSLANG" --out "$OUT/26793_runtime_expanded_glsl" | tee "$OUT/26793_glsl_validation.txt"
  grep -F 'PASS 26793 modified shader ownership: main + SHORT Sabre same-location CFA color difference; no other shader owner changed' "$OUT/26793_glsl_validation.txt" >/dev/null || fail "26793 modified shader ownership proof missing"
  grep -F 'PASS 26793 inherited active/protected shader fidelity: 11 byte-identical to successful 26792' "$OUT/26793_glsl_validation.txt" >/dev/null || fail "26793 protected shader fidelity proof missing"
  for shader in merge motionv2_render motionv2_gainmap jpegNeutralHighlightClamp26790 normalChromaConsensus26790 jpegPhaseSafeCfaLca26788 universalNormalMasterShortFusion26651 EDGE_FALSE_COLOR_SUPPRESSOR_26778 jpegNeutralHighlightClamp26787 normalDngMerge normalizeBayer universalAdaptiveColor26561 bipolarColorTrust26769; do
    grep -F "PASS 26793 pinned real glslang compile exact runtime-expanded shader: $shader" "$OUT/26793_glsl_validation.txt" >/dev/null || fail "missing real glslang proof: $shader"
  done
  sed -i 's/REAL GLSL COMPILE: NOT RUN YET/REAL GLSL COMPILE: PASS (2 modified + 11 inherited active\/protected shaders, pinned glslang 16.5.0)/' "$OUT/26793_COMPILER_STATUS.txt"
}

compile_spektra_raw_shader(){
  # Exact successful 26792 behavior: no standalone repo-shell Spektra verifier was present; source remains protected by the candidate manifest.
  pass "Spektra project verifier absent from repo shell; inherited source protected by candidate manifest"
}

snapshot_live_authority_seeded(){ python3 -S - "$CAND" "$1" "$ROOT" <<'PY_SNAPSHOT'
from pathlib import Path
import hashlib,shutil,sys
cand,out,live=map(Path,sys.argv[1:])
if out.exists(): shutil.rmtree(out)
shutil.copytree(cand,out)
expected={str(p.relative_to(cand)):p for p in (cand/'app').rglob('*') if p.is_file()}
for rel,cp in expected.items():
    lp=live/rel
    if not lp.is_file(): raise SystemExit(f'missing live candidate path: {rel}')
    op=out/rel; op.write_bytes(lp.read_bytes())
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
  pass "authority-seeded canonical live candidate byte-identical to frozen 26793 candidate"
}

compile_languages(){
  ./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace 2>&1 | tee "$OUT/26793_gradle_language_compilers.log"
  snapshot_live_authority_seeded "$POST_LANG"
  universe_equal "$CAND" "$POST_LANG"
  sed -i 's/REAL KOTLIN COMPILE: NOT RUN YET/REAL KOTLIN COMPILE: PASS/' "$OUT/26793_COMPILER_STATUS.txt"
  sed -i 's/REAL JAVA COMPILE: NOT RUN YET/REAL JAVA COMPILE: PASS/' "$OUT/26793_COMPILER_STATUS.txt"
  pass "real Kotlin/Java compilers passed and frozen source remained byte-identical"
}

verify_native_glslang_handoff(){
  [[ -n "${IRIS26793_GLSLANG:-}" && -x "$IRIS26793_GLSLANG" ]] || fail "IRIS26793_GLSLANG missing"
  [[ -n "${IRIS26681_SPEKTRA_GLSLANG:-}" && -x "$IRIS26681_SPEKTRA_GLSLANG" ]] || fail "IRIS26681_SPEKTRA_GLSLANG missing"
  [[ "$(readlink -f "$IRIS26793_GLSLANG")" == "$(readlink -f "$IRIS26681_SPEKTRA_GLSLANG")" ]] || fail "native/Spektra glslang handoff differs"
  { echo "IRIS26681_SPEKTRA_GLSLANG=$IRIS26681_SPEKTRA_GLSLANG"; echo "IRIS26793_GLSLANG=$IRIS26793_GLSLANG"; } | tee "$OUT/26793_native_glslang_handoff.txt"
  pass "successful 26792 native glslang handoff preserved before both-ABI native compile"
}

compile_native(){
  ./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace 2>&1 | tee "$OUT/26793_gradle_native_compiler.log"
  sed -i 's#NATIVE/NDK COMPILE: NOT RUN YET#NATIVE/NDK COMPILE: PASS (arm64-v8a + armeabi-v7a)#' "$OUT/26793_COMPILER_STATUS.txt"
}

verify_candidate_patches(){
  python3 -S verify_26793_patches.py "$BASE" "$CAND" 26793_FORWARD_FULL_INDEX.patch 26793_ROLLBACK_FULL_INDEX.patch | tee "$OUT/26793_patch_validation.txt"
  grep -F 'PASS 26793 canonical patch proof' "$OUT/26793_patch_validation.txt" >/dev/null || fail "canonical patch proof missing"
  pass "sealed full-index forward/rollback proof: successful 26792 -> exact 2-file 26793 candidate"
}

prebuild_safety(){
  snapshot_live_authority_seeded "$WORK/prebuild_live_snapshot"
  universe_equal "$CAND" "$WORK/prebuild_live_snapshot"
  python3 -S validate_26793.py "$BASE" "$CAND"
  (cd "$CAND" && sha256sum -c "$ROOT/26793_PROTECTED_26792.sha256" >/dev/null)
  (cd "$CAND" && sha256sum -c "$ROOT/26793_NATIVE_26792.sha256" >/dev/null)
  (cd "$CAND" && sha256sum -c "$ROOT/26793_VENDOR_26792.sha256" >/dev/null)
  (cd "$CAND" && sha256sum -c "$ROOT/26793_DNG_WRITER_26792.sha256" >/dev/null)
  cat > "$OUT/26793_PREBUILD_SAFETY.txt" <<EOF
PRE-BUILD SAFETY PROOF PASSED
runtime_authority=successful 26792 $RUNTIME_AUTHORITY_COMMIT run $RUNTIME_ACTIONS_RUN artifact $RUNTIME_ARTIFACT_ID
verification_mechanics=exact successful 26792 17-stage sequence; root 26752 inherited
runtime_changed_files=2 modified / 0 added / 0 deleted
protected_files=1777 unchanged
native_files=819 unchanged
vendor_files=773 unchanged
dng_writer_files=6 unchanged + normalDngMerge/normalizeBayer byte-identical
candidate_files=1779
main_sabre_same_location_cfa_color=true
short_sabre_same_location_cfa_color=true
night_shared_sabre=true
super_res_chroma_owner_native_sabre_vgn=true
super_res_direct_detail_frozen=true
legacy_sabre_luma_preserved=true
lca_neutral_scalar_owner_frozen=true
vgn_denoise_floor_alignment_exposure_uhdr_dng_native_vendor_frozen=true
EOF
  echo 'PRE-BUILD SAFETY PROOF PASSED'
}

assemble(){
  ./gradlew :app:assembleDebug --stacktrace 2>&1 | tee "$OUT/26793_gradle_assemble.log"
  mapfile -t apks < <(find app/build/outputs/apk -type f -name '*.apk' | sort)
  [[ "${#apks[@]}" -eq 1 ]] || fail "expected exactly one APK, got ${#apks[@]}: ${apks[*]-}"
  cp "${apks[0]}" "$FINAL"
  [[ -f "$FINAL" ]] || fail "final APK copy missing"
  sha256sum "$FINAL" | tee "$OUT/26793_APK.sha256"
  sed -i 's/FULL ANDROID ASSEMBLE: NOT RUN YET/FULL ANDROID ASSEMBLE: PASS (exactly one APK)/' "$OUT/26793_COMPILER_STATUS.txt"
}

postbuild_proof(){
  snapshot_live_authority_seeded "$WORK/postbuild_live_snapshot"
  universe_equal "$CAND" "$WORK/postbuild_live_snapshot"
  python3 -S validate_26793.py "$BASE" "$CAND"
  (cd "$CAND" && sha256sum -c "$ROOT/26793_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null)
  (cd "$CAND" && sha256sum -c "$ROOT/26793_PROTECTED_26792.sha256" >/dev/null)
  (cd "$CAND" && sha256sum -c "$ROOT/26793_NATIVE_26792.sha256" >/dev/null)
  (cd "$CAND" && sha256sum -c "$ROOT/26793_VENDOR_26792.sha256" >/dev/null)
  (cd "$CAND" && sha256sum -c "$ROOT/26793_DNG_WRITER_26792.sha256" >/dev/null)
  cp 26793_EXPECTED_CANDIDATE_FULL_APP.sha256 "$OUT/26793_candidate_full_app.sha256"
  tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -czf "$OUT/26793_candidate_app_source.tar.gz" -C "$CAND" app
  sha256sum "$OUT/26793_candidate_app_source.tar.gz" > "$OUT/26793_candidate_app_source.tar.gz.sha256"
  cp 26793_FORWARD_FULL_INDEX.patch "$OUT/26793_FORWARD_FULL_INDEX.patch"
  cp 26793_ROLLBACK_FULL_INDEX.patch "$OUT/26793_ROLLBACK_FULL_INDEX.patch"
  sed -i 's/POST-BUILD INVARIANCE: NOT RUN YET/POST-BUILD INVARIANCE: PASS/' "$OUT/26793_COMPILER_STATUS.txt"
  pass "authority-seeded post-build protected/DNG/native/vendor/source invariance"
}

clean_extract_replay(){
  local replay="$WORK/clean_replay_candidate"
  rm -rf "$replay"
  sha256sum -c 26793_HANDOFF_HASHES.sha256 >/dev/null
  bash -n build_26793_sabre_same_location_cfa_color.sh
  python3 -S -m py_compile transform_26793.py validate_26793.py verify_26793_patches.py verify_26793_runtime_glsl.py
  rm -rf __pycache__
  python3 -S transform_26793.py "$BASE" "$replay" handoff_payload_26793
  universe_equal "$CAND" "$replay"
  python3 -S validate_26793.py "$BASE" "$replay"
  python3 -S verify_26793_runtime_glsl.py "$BASE" "$replay" --out "$OUT/26793_final_runtime_expanded_glsl" | tee "$OUT/26793_final_glsl_static_replay.txt"
  python3 -S verify_26793_patches.py "$BASE" "$replay" 26793_FORWARD_FULL_INDEX.patch 26793_ROLLBACK_FULL_INDEX.patch | tee "$OUT/26793_final_patch_replay.txt"
  (cd "$replay" && sha256sum -c "$ROOT/26793_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null)
  grep -F 'VERSION_NAME=0.9726793' "$replay/app/version.properties" >/dev/null
  grep -F 'VERSION_BUILD=26793' "$replay/app/version.properties" >/dev/null
  grep -F 'REAL GLSL COMPILE: PASS' "$OUT/26793_COMPILER_STATUS.txt" >/dev/null
  grep -F 'REAL KOTLIN COMPILE: PASS' "$OUT/26793_COMPILER_STATUS.txt" >/dev/null
  grep -F 'REAL JAVA COMPILE: PASS' "$OUT/26793_COMPILER_STATUS.txt" >/dev/null
  grep -F 'NATIVE/NDK COMPILE: PASS' "$OUT/26793_COMPILER_STATUS.txt" >/dev/null
  grep -F 'FULL ANDROID ASSEMBLE: PASS' "$OUT/26793_COMPILER_STATUS.txt" >/dev/null
  grep -F 'POST-BUILD INVARIANCE: PASS' "$OUT/26793_COMPILER_STATUS.txt" >/dev/null
  pass "final 26793 clean replay of package hashes/same-location-CFA-color/version/patch/compiler/build proofs"
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
pass "26793 SABRE SAME-LOCATION CFA COLOR: ACTIONS BUILD PROOF COMPLETE"
