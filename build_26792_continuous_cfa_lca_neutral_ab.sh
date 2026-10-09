#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
RUNTIME_AUTHORITY_COMMIT="7fa116ec950e1d896e5a3870d94330d6ab2db191"
RUNTIME_ACTIONS_RUN="37868812412"
RUNTIME_ARTIFACT_ID="11589433800"
RUNTIME_ARTIFACT_NAME="photon-26791-sabre-scalar-cfa-lca-night-neutral"
RUNTIME_ARTIFACT_SHA="e752b4fab9ec391a8970c035745f60da669609683896cff1917cbd8549f24c70"
RUNTIME_TAR_SHA="db09e4fa4a030e9c748d617e475db720f3ddc43702f99a3f5624806aff3d8b0d"
MECHANICS_AUTHORITY_COMMIT="7fa116ec950e1d896e5a3870d94330d6ab2db191"
MECHANICS_ACTIONS_RUN="37868812412"
ROOT_MECHANICS_COMMIT="69d5cb14f950d6fe5309441f7abf29d96631ab02"
ROOT_MECHANICS_RUN="37075896367"
VERSION_NAME="0.9726792"
VERSION_BUILD="26792"
GLSLANG_VERSION="16.5.0"
GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"
GLSLANG_URL="https://github.com/KhronosGroup/glslang/releases/download/16.5.0/glslang-16.5.0-linux-x86_64-release.tar.gz"
OUT="$ROOT/build_26792_continuous_cfa_lca_neutral_ab_outputs"
WORK="$ROOT/.build_26792_continuous_cfa_lca_neutral_ab_work"
ARTZIP="$WORK/26791_artifact.zip"
ARTDIR="$WORK/artifact_26791"
BASE="$WORK/exact_successful_26791_compiled_candidate"
CAND="$WORK/candidate_26792"
LIVE_CANON="$WORK/live_compiler_candidate_snapshot"
POST_LANG="$WORK/post_language_compiler_source_snapshot"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-continuous-cfa-lca-neutral-ab-debug.apk"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR"
cat > "$OUT/26792_COMPILER_STATUS.txt" <<EOF
REAL GLSL COMPILE: NOT RUN YET
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
NATIVE/NDK COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
EOF

# IRIS_26792_AUTHORITATIVE_ACTIONS_STAGE_ORDER
verify_package(){
  sha256sum -c 26792_HANDOFF_HASHES.sha256 >/dev/null
  bash -n build_26792_continuous_cfa_lca_neutral_ab.sh
  python3 -S -m py_compile transform_26792.py validate_26792.py verify_26792_patches.py verify_26792_runtime_glsl.py
  rm -rf __pycache__
  [[ "$(find handoff_payload_26792 -type f | wc -l)" -eq 13 ]] || fail "26792 payload count"
  diff -u 26792_RUNTIME_CHANGED_PATHS.txt <(find handoff_payload_26792 -type f | sed 's#^handoff_payload_26792/##' | sort) >/dev/null || fail "26792 payload allowlist mismatch"
  for p in 26792_FORWARD_FULL_INDEX.patch 26792_ROLLBACK_FULL_INDEX.patch; do
    ! grep -Eq '^(rename from|rename to|copy from|copy to) ' "$p" || fail "26792 patch contains rename/copy inference: $p"
  done
  grep -Fx 'RUN_26792_CONTINUOUS_CFA_LCA_NEUTRAL_AB' TRIGGER_26792.txt >/dev/null || fail "26792 trigger contents"
  ! find . -type f -name '*.apk' | grep -q . || fail "APK unexpectedly packaged"
  pass "sealed 26792 package hashes/syntax/allowlist/patch identity"
}

verify_scope(){
  [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch"
  git merge-base --is-ancestor "$RUNTIME_AUTHORITY_COMMIT" HEAD || fail "26791 runtime authority not ancestor"
  git merge-base --is-ancestor "$MECHANICS_AUTHORITY_COMMIT" HEAD || fail "26791 mechanics authority not ancestor"
  git merge-base --is-ancestor "$ROOT_MECHANICS_COMMIT" HEAD || fail "26752 root mechanics authority not ancestor"
  if git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD | grep -E '^app/'; then fail "live app source changed after 26791 authority"; fi
  python3 -S - <<'PY_SCOPE'
import subprocess
allowed_prefixes=(
 '26792_','build_26792_continuous_cfa_lca_neutral_ab.sh','transform_26792.py','validate_26792.py',
 'verify_26792_patches.py','verify_26792_runtime_glsl.py','handoff_payload_26792/',
 '.github/workflows/build-26792-continuous-cfa-lca-neutral-ab.yml','TRIGGER_26792.txt',
 'PHOTON_26792_CONTINUOUS_CFA_LCA_NEUTRAL_AB_README.txt')
paths=subprocess.check_output(['git','diff','--name-only','7fa116ec950e1d896e5a3870d94330d6ab2db191..HEAD'],text=True).splitlines()
bad=[p for p in paths if not any(p==x or p.startswith(x) for x in allowed_prefixes)]
assert not bad,bad
print('PASS 26792 infrastructure scope allowlist')
PY_SCOPE
  pass "26792 scope exact: successful 26791 authority + sealed 13-file payload; live app untouched"
}

obtain_authority(){
  [[ -n "$TOKEN" ]] || fail "GITHUB_TOKEN missing"
  curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" \
    "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${RUNTIME_ARTIFACT_ID}/zip" -o "$ARTZIP"
  [[ "$(sha "$ARTZIP")" == "$RUNTIME_ARTIFACT_SHA" ]] || fail "26791 artifact sha"
  unzip -q "$ARTZIP" -d "$ARTDIR"
  T="$ARTDIR/build_26791_sabre_scalar_cfa_lca_night_neutral_outputs/26791_candidate_app_source.tar.gz"
  [[ -f "$T" && "$(sha "$T")" == "$RUNTIME_TAR_SHA" ]] || fail "26791 candidate tar sha"
  STATUS="$ARTDIR/build_26791_sabre_scalar_cfa_lca_night_neutral_outputs/26791_COMPILER_STATUS.txt"
  for proof in 'REAL GLSL COMPILE: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS'; do
    grep -F "$proof" "$STATUS" >/dev/null || fail "missing 26791 authority proof: $proof"
  done
  mkdir -p "$BASE"; tar -xzf "$T" -C "$BASE"
  [[ "$(find "$BASE/app" -type f | wc -l)" -eq 1779 ]] || fail "26791 base file count"
  (cd "$BASE" && sha256sum -c "$ROOT/26792_BASE_26791_FULL_APP.sha256" >/dev/null) || fail "26791 full base manifest"
  (cd "$BASE" && sha256sum -c "$ROOT/26792_PRIOR_SOURCE_HASHES.sha256" >/dev/null) || fail "26791 prior source hashes"
  (cd "$BASE" && sha256sum -c "$ROOT/26792_NATIVE_26791.sha256" >/dev/null) || fail "26791 native manifest"
  (cd "$BASE" && sha256sum -c "$ROOT/26792_VENDOR_26791.sha256" >/dev/null) || fail "26791 vendor manifest"
  (cd "$BASE" && sha256sum -c "$ROOT/26792_DNG_WRITER_26791.sha256" >/dev/null) || fail "26791 DNG writer manifest"
  cat > "$OUT/26792_RESOLVED_AUTHORITIES.txt" <<EOF
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
  pass "exact successful 26791 compiled candidate reconstructed"
}

universe_equal(){ python3 -S - "$1" "$2" <<'PY_UNIVERSE'
from pathlib import Path
import hashlib,sys
def U(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(r)/'app').rglob('*') if p.is_file()}
a,b=U(sys.argv[1]),U(sys.argv[2]); assert a==b,(len(a),len(b)); print(f'PASS byte-identical app universe: {len(a)} files')
PY_UNIVERSE
}

make_candidate(){
  python3 -S transform_26792.py "$BASE" "$CAND" handoff_payload_26792
  python3 -S validate_26792.py "$BASE" "$CAND"
  (cd "$CAND" && sha256sum -c "$ROOT/26792_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null) || fail "26792 candidate manifest"
  (cd "$CAND" && sha256sum -c "$ROOT/26792_PROTECTED_26791.sha256" >/dev/null) || fail "26792 protected manifest"
  (cd "$CAND" && sha256sum -c "$ROOT/26792_NATIVE_26791.sha256" >/dev/null) || fail "26792 native invariance"
  (cd "$CAND" && sha256sum -c "$ROOT/26792_VENDOR_26791.sha256" >/dev/null) || fail "26792 vendor invariance"
  (cd "$CAND" && sha256sum -c "$ROOT/26792_DNG_WRITER_26791.sha256" >/dev/null) || fail "26792 DNG-writer invariance"
  [[ "$(find "$CAND/app" -type f | wc -l)" -eq 1779 ]] || fail "26792 candidate file count"
  pass "candidate-first 26792 continuous scalar-CFA LCA + CFA neutral + visible A/B checks"
}

verify_successful_mechanics(){
  local a89="$WORK/authority_26791_build.sh" a52="$WORK/authority_26752_build.sh"
  git show "$MECHANICS_AUTHORITY_COMMIT:build_26791_sabre_scalar_cfa_lca_night_neutral.sh" > "$a89"
  git show "$ROOT_MECHANICS_COMMIT:build_26752_ipol_plan_b_translational_sr.sh" > "$a52"
  for cmd in './gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace' \
             "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace" \
             './gradlew :app:assembleDebug --stacktrace'; do
    grep -F "$cmd" "$a89" >/dev/null || fail "26791 authority command missing: $cmd"
    grep -F "$cmd" "$0" >/dev/null || fail "26792 command differs: $cmd"
  done
  grep -F 'compile_spektra_raw_shader(){' "$a89" >/dev/null || fail "26791 Spektra verifier stage missing"
  grep -F 'compile_spektra_raw_shader(){' "$0" >/dev/null || fail "26792 Spektra verifier stage missing"
  grep -F 'verify_native_glslang_handoff(){' "$a89" >/dev/null || fail "26791 native handoff stage missing"
  grep -F 'verify_native_glslang_handoff(){' "$0" >/dev/null || fail "26792 native handoff stage missing"
  python3 -S - "$0" "$a89" "$a52" <<'PY_ORDER'
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
cur,a89,a52=[Path(x).read_text() for x in sys.argv[1:]]
ordered(cur,'# IRIS_26792_AUTHORITATIVE_ACTIONS_STAGE_ORDER',stages,'26792')
ordered(a89,'# IRIS_26791_AUTHORITATIVE_ACTIONS_STAGE_ORDER',stages,'26791 authority')
auth52=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26751_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac','after_language_compiler_snapshot',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]'",'verify_candidate_patches','PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug','mapfile -t apks','postbuild_proof']
ordered(a52,'# IRIS_26752_AUTHORITATIVE_ACTIONS_STAGE_ORDER',auth52,'26752 root authority')
print('PASS 26792 stage order exactly inherits successful 26791 procedure and root 26752 mechanics')
PY_ORDER
  cat > "$OUT/26792_MECHANICS_DIFF_AUDIT.txt" <<EOF
26792 vs exact successful 26791 implementation:
- 17-stage authoritative Actions order: IDENTICAL
- Kotlin/Java compiler command: IDENTICAL
- both-ABI native compiler command: IDENTICAL
- full assemble command: IDENTICAL
- Spektra stage position: IDENTICAL
- native glslang handoff stage position: IDENTICAL
- runtime authority advanced only: successful 26791 -> 26792 candidate
- version/name/validator scope advanced only for the intended 26792 13-file LCA/neutral/A-B correction
- no stage reorder, removal, substitution, or compiler simplification
EOF
  pass "successful 26791 implementation diff-audited: zero stage-order/compiler/native/assemble deviation"
}

prepare_glslang(){
  D="$WORK/glslang-${GLSLANG_VERSION}"; A="$WORK/glslang.tar.gz"; mkdir -p "$D"
  curl -L --fail --retry 3 "$GLSLANG_URL" -o "$A"
  [[ "$(sha "$A")" == "$GLSLANG_ARCHIVE_SHA" ]] || fail "glslang archive sha"
  tar -xzf "$A" -C "$D"
  compiler="$(find "$D" -type f -name glslang -print -quit)"
  [[ -n "$compiler" ]] || compiler="$(find "$D" \( -type f -o -type l \) -name glslangValidator -print -quit)"
  compiler="$(readlink -f "$compiler")"; [[ -x "$compiler" ]] || chmod +x "$compiler"
  "$compiler" --version | tee "$OUT/26792_glslang_version.txt"
  export IRIS26792_GLSLANG="$compiler"
  export IRIS26681_SPEKTRA_GLSLANG="$compiler"
  pass "pinned glslang 16.5.0 dual environment handoff"
}

compile_modified_runtime_shaders(){
  python3 -S verify_26792_runtime_glsl.py "$BASE" "$CAND" --compiler "$IRIS26792_GLSLANG" --out "$OUT/26792_runtime_expanded_glsl" | tee "$OUT/26792_glsl_validation.txt"
  grep -F 'PASS 26792 modified shader ownership: continuous scalar-CFA LCA/neutral + paired SDR/UHDR body-contrast rebase' "$OUT/26792_glsl_validation.txt" >/dev/null || fail "26792 modified shader ownership proof missing"
  grep -F 'PASS 26792 protected shader fidelity: DNG/normalize/SHORT/residual/neutral/LONG-consensus/VGN byte-identical to successful 26791' "$OUT/26792_glsl_validation.txt" >/dev/null || fail "26792 protected shader fidelity proof missing"
  for shader in merge motionv2_render motionv2_gainmap jpegNeutralHighlightClamp26790 normalChromaConsensus26790 jpegPhaseSafeCfaLca26788 universalNormalMasterShortFusion26651 EDGE_FALSE_COLOR_SUPPRESSOR_26778 jpegNeutralHighlightClamp26787 normalDngMerge normalizeBayer universalAdaptiveColor26561 bipolarColorTrust26769; do
    grep -F "PASS 26792 pinned real glslang compile exact runtime-expanded shader: $shader" "$OUT/26792_glsl_validation.txt" >/dev/null || fail "missing real glslang proof: $shader"
  done
  sed -i 's/REAL GLSL COMPILE: NOT RUN YET/REAL GLSL COMPILE: PASS (3 modified + 10 inherited active\/protected shaders, pinned glslang 16.5.0)/' "$OUT/26792_COMPILER_STATUS.txt"
}

compile_spektra_raw_shader(){
  # Exact successful 26791 behavior: no standalone repo-shell Spektra verifier was present; source remains protected by the candidate manifest.
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
  pass "authority-seeded canonical live candidate byte-identical to frozen 26792 candidate"
}

compile_languages(){
  ./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace 2>&1 | tee "$OUT/26792_gradle_language_compilers.log"
  snapshot_live_authority_seeded "$POST_LANG"
  universe_equal "$CAND" "$POST_LANG"
  sed -i 's/REAL KOTLIN COMPILE: NOT RUN YET/REAL KOTLIN COMPILE: PASS/' "$OUT/26792_COMPILER_STATUS.txt"
  sed -i 's/REAL JAVA COMPILE: NOT RUN YET/REAL JAVA COMPILE: PASS/' "$OUT/26792_COMPILER_STATUS.txt"
  pass "real Kotlin/Java compilers passed and frozen source remained byte-identical"
}

verify_native_glslang_handoff(){
  [[ -n "${IRIS26792_GLSLANG:-}" && -x "$IRIS26792_GLSLANG" ]] || fail "IRIS26792_GLSLANG missing"
  [[ -n "${IRIS26681_SPEKTRA_GLSLANG:-}" && -x "$IRIS26681_SPEKTRA_GLSLANG" ]] || fail "IRIS26681_SPEKTRA_GLSLANG missing"
  [[ "$(readlink -f "$IRIS26792_GLSLANG")" == "$(readlink -f "$IRIS26681_SPEKTRA_GLSLANG")" ]] || fail "native/Spektra glslang handoff differs"
  { echo "IRIS26681_SPEKTRA_GLSLANG=$IRIS26681_SPEKTRA_GLSLANG"; echo "IRIS26792_GLSLANG=$IRIS26792_GLSLANG"; } | tee "$OUT/26792_native_glslang_handoff.txt"
  pass "successful 26791 native glslang handoff preserved before both-ABI native compile"
}

compile_native(){
  ./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace 2>&1 | tee "$OUT/26792_gradle_native_compiler.log"
  sed -i 's#NATIVE/NDK COMPILE: NOT RUN YET#NATIVE/NDK COMPILE: PASS (arm64-v8a + armeabi-v7a)#' "$OUT/26792_COMPILER_STATUS.txt"
}

verify_candidate_patches(){
  python3 -S verify_26792_patches.py "$BASE" "$CAND" 26792_FORWARD_FULL_INDEX.patch 26792_ROLLBACK_FULL_INDEX.patch | tee "$OUT/26792_patch_validation.txt"
  grep -F 'PASS 26792 canonical patch proof' "$OUT/26792_patch_validation.txt" >/dev/null || fail "canonical patch proof missing"
  pass "sealed full-index forward/rollback proof: successful 26791 -> exact 13-file 26792 candidate"
}

prebuild_safety(){
  snapshot_live_authority_seeded "$WORK/prebuild_live_snapshot"
  universe_equal "$CAND" "$WORK/prebuild_live_snapshot"
  python3 -S validate_26792.py "$BASE" "$CAND"
  (cd "$CAND" && sha256sum -c "$ROOT/26792_PROTECTED_26791.sha256" >/dev/null)
  (cd "$CAND" && sha256sum -c "$ROOT/26792_NATIVE_26791.sha256" >/dev/null)
  (cd "$CAND" && sha256sum -c "$ROOT/26792_VENDOR_26791.sha256" >/dev/null)
  (cd "$CAND" && sha256sum -c "$ROOT/26792_DNG_WRITER_26791.sha256" >/dev/null)
  cat > "$OUT/26792_PREBUILD_SAFETY.txt" <<EOF
PRE-BUILD SAFETY PROOF PASSED
runtime_authority=successful 26791 $RUNTIME_AUTHORITY_COMMIT run $RUNTIME_ACTIONS_RUN artifact $RUNTIME_ARTIFACT_ID
verification_mechanics=exact successful 26791 17-stage sequence; root 26752 inherited
runtime_changed_files=13 modified / 0 added / 0 deleted
protected_files=1766 unchanged
native_files=819 unchanged
vendor_files=773 unchanged
dng_writer_files=6 unchanged + normalDngMerge/normalizeBayer byte-identical
candidate_files=1779
cfa_lca_owner=CONTINUOUS_FIXED_PHASE_SCALAR_ONLY
lca_snap_code_paths=0
lca_continuity_sweep_0_to_2px=PASS
lca_max_step_px_le_0_05=PASS
lca_sign_and_zero_control=PASS
jpeg_dealias_states_same_scalar_topology=PASS
sabre_rgb_owner=SOLE_CFA_TO_RGB_OWNER
normal_long_scalar_cfa_owner_shared=true
neutral_owner=PER_FRAME_CFA_BEFORE_RGB
neutral_two_green_continuous_rule=PASS
neutral_one_green_does_not_force=PASS
neutral_colored_full_censor_resolves_neutral=PASS
post_rgb_neutral_owner=false
night_dng_jpeg_physical_rule_shared=true
stacked_dng_normal_only=true
long_chroma_anchor=COMPLETED_NORMAL_CONSENSUS
short_unchanged=true
edge_suppress_all_default_off=true
edge_suppress_all_thresholds=0.15_0.80_0.025_0.080
sdr_body_contrast_default=0.35
sdr_body_contrast_ab=0.35_or_0.0
uhdr_identical_input_rebase=PASS
decoded_uhdr_target_frozen=true
vgn_denoise_alignment_exposure_native_vendor_frozen=true
EOF
  echo 'PRE-BUILD SAFETY PROOF PASSED' 
}

assemble(){
  ./gradlew :app:assembleDebug --stacktrace 2>&1 | tee "$OUT/26792_gradle_assemble.log"
  mapfile -t apks < <(find app/build/outputs/apk -type f -name '*.apk' | sort)
  [[ "${#apks[@]}" -eq 1 ]] || fail "expected exactly one APK, got ${#apks[@]}: ${apks[*]-}"
  cp "${apks[0]}" "$FINAL"
  [[ -f "$FINAL" ]] || fail "final APK copy missing"
  sha256sum "$FINAL" | tee "$OUT/26792_APK.sha256"
  sed -i 's/FULL ANDROID ASSEMBLE: NOT RUN YET/FULL ANDROID ASSEMBLE: PASS (exactly one APK)/' "$OUT/26792_COMPILER_STATUS.txt"
}

postbuild_proof(){
  snapshot_live_authority_seeded "$WORK/postbuild_live_snapshot"
  universe_equal "$CAND" "$WORK/postbuild_live_snapshot"
  python3 -S validate_26792.py "$BASE" "$CAND"
  (cd "$CAND" && sha256sum -c "$ROOT/26792_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null)
  (cd "$CAND" && sha256sum -c "$ROOT/26792_PROTECTED_26791.sha256" >/dev/null)
  (cd "$CAND" && sha256sum -c "$ROOT/26792_NATIVE_26791.sha256" >/dev/null)
  (cd "$CAND" && sha256sum -c "$ROOT/26792_VENDOR_26791.sha256" >/dev/null)
  (cd "$CAND" && sha256sum -c "$ROOT/26792_DNG_WRITER_26791.sha256" >/dev/null)
  cp 26792_EXPECTED_CANDIDATE_FULL_APP.sha256 "$OUT/26792_candidate_full_app.sha256"
  tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -czf "$OUT/26792_candidate_app_source.tar.gz" -C "$CAND" app
  sha256sum "$OUT/26792_candidate_app_source.tar.gz" > "$OUT/26792_candidate_app_source.tar.gz.sha256"
  cp 26792_FORWARD_FULL_INDEX.patch "$OUT/26792_FORWARD_FULL_INDEX.patch"
  cp 26792_ROLLBACK_FULL_INDEX.patch "$OUT/26792_ROLLBACK_FULL_INDEX.patch"
  sed -i 's/POST-BUILD INVARIANCE: NOT RUN YET/POST-BUILD INVARIANCE: PASS/' "$OUT/26792_COMPILER_STATUS.txt"
  pass "authority-seeded post-build protected/DNG/native/vendor/source invariance"
}

clean_extract_replay(){
  local replay="$WORK/clean_replay_candidate"
  rm -rf "$replay"
  sha256sum -c 26792_HANDOFF_HASHES.sha256 >/dev/null
  bash -n build_26792_continuous_cfa_lca_neutral_ab.sh
  python3 -S -m py_compile transform_26792.py validate_26792.py verify_26792_patches.py verify_26792_runtime_glsl.py
  rm -rf __pycache__
  python3 -S transform_26792.py "$BASE" "$replay" handoff_payload_26792
  universe_equal "$CAND" "$replay"
  python3 -S validate_26792.py "$BASE" "$replay"
  python3 -S verify_26792_runtime_glsl.py "$BASE" "$replay" --out "$OUT/26792_final_runtime_expanded_glsl" | tee "$OUT/26792_final_glsl_static_replay.txt"
  python3 -S verify_26792_patches.py "$BASE" "$replay" 26792_FORWARD_FULL_INDEX.patch 26792_ROLLBACK_FULL_INDEX.patch | tee "$OUT/26792_final_patch_replay.txt"
  (cd "$replay" && sha256sum -c "$ROOT/26792_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null)
  grep -F 'VERSION_NAME=0.9726792' "$replay/app/version.properties" >/dev/null
  grep -F 'VERSION_BUILD=26792' "$replay/app/version.properties" >/dev/null
  grep -F 'REAL GLSL COMPILE: PASS' "$OUT/26792_COMPILER_STATUS.txt" >/dev/null
  grep -F 'REAL KOTLIN COMPILE: PASS' "$OUT/26792_COMPILER_STATUS.txt" >/dev/null
  grep -F 'REAL JAVA COMPILE: PASS' "$OUT/26792_COMPILER_STATUS.txt" >/dev/null
  grep -F 'NATIVE/NDK COMPILE: PASS' "$OUT/26792_COMPILER_STATUS.txt" >/dev/null
  grep -F 'FULL ANDROID ASSEMBLE: PASS' "$OUT/26792_COMPILER_STATUS.txt" >/dev/null
  grep -F 'POST-BUILD INVARIANCE: PASS' "$OUT/26792_COMPILER_STATUS.txt" >/dev/null
  pass "final 26792 clean replay of package hashes/continuous-CFA-LCA/CFA-neutral/A-B/version/patch/compiler/build proofs"
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
echo '26792 CONTINUOUS CFA LCA + NEUTRAL A/B: PASS'
echo "Runtime authority: successful 26791 $RUNTIME_AUTHORITY_COMMIT"
echo 'Verification mechanics authority: exact successful 26791 17-stage procedure (root 26752 inherited)'
echo 'Runtime changed-file allowlist: 13 modified, 0 added, 0 deleted'
echo 'Infrastructure mechanics: zero stage-order/compiler/native/assemble deviation from successful 26791'
echo 'Real GLSL/Kotlin/Java/NDK/full assemble: PASS'
echo 'Exactly one APK: PASS'
echo '========================================='
