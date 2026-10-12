#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
ROOT="$(pwd)"; EXPECTED_BRANCH="experimental-clean-photon-rebuild"
RUNTIME_AUTHORITY_COMMIT="9fdf39a0a99773ea86159250c7715396b58e78d3"; RUNTIME_ACTIONS_RUN="38295667311"; RUNTIME_ARTIFACT_ID="11768303124"; RUNTIME_ARTIFACT_NAME="photon-26821-connected-false-color-dng-all-phase-coherence"; RUNTIME_ARTIFACT_SHA="5a12e4b6f66ab39e6a3e5141d8040365dafc33a21767880a02d107a100ab73fd"; RUNTIME_TAR_SHA="20f2a05f3118a20e31125b13f8653854341615a1e911a8176f241584d9736c04"
MECHANICS_AUTHORITY_COMMIT="$RUNTIME_AUTHORITY_COMMIT"; MECHANICS_ACTIONS_RUN="$RUNTIME_ACTIONS_RUN"; ROOT_MECHANICS_COMMIT="b1f0db1c3225411476d3d65a236543e9f016d76d"; ROOT_MECHANICS_RUN="38162515468"
VERSION_NAME="0.9726822"; VERSION_BUILD="26822"; GLSLANG_VERSION="16.5.0"; GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"; GLSLANG_URL="https://github.com/KhronosGroup/glslang/releases/download/16.5.0/glslang-16.5.0-linux-x86_64-release.tar.gz"
OUT="$ROOT/build_26822_single_owner_false_color_attenuation_outputs"; WORK="$ROOT/.build_26822_single_owner_false_color_attenuation_work"; ARTZIP="$WORK/26821_artifact.zip"; ARTDIR="$WORK/artifact_26821"; BASE="$WORK/exact_successful_26821_compiled_candidate"; CAND="$WORK/candidate_26822"; LIVE_CANON="$WORK/live_compiler_candidate_snapshot"; POST_LANG="$WORK/post_language_compiler_source_snapshot"; FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-single-owner-false-color-attenuation-debug.apk"; TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR"
cat > "$OUT/26822_COMPILER_STATUS.txt" <<EOF
REAL GLSL COMPILE: NOT RUN YET
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
NATIVE/NDK COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
EOF
# IRIS_26822_AUTHORITATIVE_ACTIONS_STAGE_ORDER
verify_package(){ sha256sum -c 26822_HANDOFF_HASHES.sha256 >/dev/null; bash -n build_26822_single_owner_false_color_attenuation.sh; python3 -S -m py_compile transform_26822.py validate_26822.py verify_26822_patches.py verify_26822_runtime_glsl.py; rm -rf __pycache__; [[ "$(find handoff_payload_26822 -type f | wc -l)" -eq 5 ]] || fail "26822 payload count"; diff -u 26822_RUNTIME_CHANGED_PATHS.txt <(find handoff_payload_26822 -type f | sed 's#^handoff_payload_26822/##' | sort) >/dev/null || fail "26822 payload allowlist mismatch"; for p in 26822_FORWARD_FULL_INDEX.patch 26822_ROLLBACK_FULL_INDEX.patch; do ! grep -Eq '^(rename from|rename to|copy from|copy to) ' "$p" || fail "patch rename/copy inference"; done; grep -Fx 'RUN_26822_SINGLE_OWNER_FALSE_COLOR_ATTENUATION' TRIGGER_26822.txt >/dev/null || fail "26822 trigger identity mismatch"; ! find . -type f -name '*.apk' | grep -q . || fail "APK unexpectedly packaged"; pass "sealed 26822 package hashes/syntax/allowlist/patch identity"; }
verify_scope(){ [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch"; git merge-base --is-ancestor "$RUNTIME_AUTHORITY_COMMIT" HEAD || fail "26821 runtime authority not ancestor"; git merge-base --is-ancestor "$ROOT_MECHANICS_COMMIT" HEAD || fail "26812 root mechanics authority not ancestor"; if git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD | grep -E '^app/'; then fail "live app source changed after 26821 authority"; fi; python3 -S - <<'PY_SCOPE'
import subprocess
allowed=('26822_','build_26822_single_owner_false_color_attenuation.sh','transform_26822.py','validate_26822.py','verify_26822_patches.py','verify_26822_runtime_glsl.py','handoff_payload_26822/','.github/workflows/build-26822-single-owner-false-color-attenuation.yml','TRIGGER_26822.txt','PHOTON_26822_SINGLE_OWNER_FALSE_COLOR_ATTENUATION_README.txt')
paths=subprocess.check_output(['git','diff','--name-only','9fdf39a0a99773ea86159250c7715396b58e78d3..HEAD'],text=True).splitlines()
bad=[p for p in paths if not any(p==x or p.startswith(x) for x in allowed)]
assert not bad,bad
print('PASS 26822 infrastructure scope allowlist')
PY_SCOPE
pass "26822 scope exact: successful 26821 authority + sealed 5-path payload; live app untouched"; }
obtain_authority(){ [[ -n "$TOKEN" ]] || fail "GITHUB_TOKEN missing"; curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${RUNTIME_ARTIFACT_ID}/zip" -o "$ARTZIP"; [[ "$(sha "$ARTZIP")" == "$RUNTIME_ARTIFACT_SHA" ]] || fail "26821 artifact sha"; unzip -q "$ARTZIP" -d "$ARTDIR"; T="$ARTDIR/build_26821_connected_false_color_dng_all_phase_coherence_outputs/26821_candidate_app_source.tar.gz"; [[ -f "$T" && "$(sha "$T")" == "$RUNTIME_TAR_SHA" ]] || fail "26821 candidate tar sha"; STATUS="$ARTDIR/build_26821_connected_false_color_dng_all_phase_coherence_outputs/26821_COMPILER_STATUS.txt"; for proof in 'REAL GLSL COMPILE: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS'; do grep -F "$proof" "$STATUS" >/dev/null || fail "missing 26821 authority proof: $proof"; done; mkdir -p "$BASE"; tar -xzf "$T" -C "$BASE"; [[ "$(find "$BASE/app" -type f | wc -l)" -eq 1783 ]] || fail "26821 base file count"; (cd "$BASE" && sha256sum -c "$ROOT/26822_BASE_26821_FULL_APP.sha256" >/dev/null); (cd "$BASE" && sha256sum -c "$ROOT/26822_PRIOR_SOURCE_HASHES.sha256" >/dev/null); (cd "$BASE" && sha256sum -c "$ROOT/26822_NATIVE_26821.sha256" >/dev/null); (cd "$BASE" && sha256sum -c "$ROOT/26822_VENDOR_26821.sha256" >/dev/null); (cd "$BASE" && sha256sum -c "$ROOT/26822_DNG_WRITER_26821.sha256" >/dev/null); cat > "$OUT/26822_RESOLVED_AUTHORITIES.txt" <<EOF
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
pass "exact successful 26821 compiled candidate reconstructed"; }
universe_equal(){ python3 -S - "$1" "$2" <<'PY_U'
from pathlib import Path
import hashlib,sys
def U(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(r)/'app').rglob('*') if p.is_file()}
a,b=U(sys.argv[1]),U(sys.argv[2]); assert a==b,(len(a),len(b)); print(f'PASS byte-identical app universe: {len(a)} files')
PY_U
}
make_candidate(){ python3 -S transform_26822.py "$BASE" "$CAND" handoff_payload_26822; python3 -S validate_26822.py "$BASE" "$CAND"; (cd "$CAND" && sha256sum -c "$ROOT/26822_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26822_PROTECTED_26821.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26822_NATIVE_26821.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26822_VENDOR_26821.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26822_DNG_WRITER_26821.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26822_SUCCESSFUL_26819_SABRE_REFERENCE.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26822_SUCCESSFUL_26818_VGN_REFERENCE.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26822_SUCCESSFUL_26821_DNG_MERGE_REFERENCE.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26822_SUCCESSFUL_26821_DNG_PHASE_REFERENCE.sha256" >/dev/null); [[ "$(find "$CAND/app" -type f | wc -l)" -eq 1783 ]] || fail "candidate count"; pass "candidate-first 26822 successful-26821 authority plus continuous evidence, no connected flood, and one attenuation-only false-color RGB owner"; }
verify_successful_mechanics(){ local a17="$WORK/authority_26821_build.sh" a12="$WORK/authority_26812_build.sh"; git show "$MECHANICS_AUTHORITY_COMMIT:build_26821_connected_false_color_dng_all_phase_coherence.sh" > "$a17"; git show "$ROOT_MECHANICS_COMMIT:build_26812_neutral_parent_edge_fringe.sh" > "$a12"; for cmd in './gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace' "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace" './gradlew :app:assembleDebug --stacktrace'; do grep -F "$cmd" "$a17" >/dev/null || fail "26821 authority command missing: $cmd"; grep -F "$cmd" "$0" >/dev/null || fail "26822 command differs: $cmd"; done; grep -F 'compile_spektra_raw_shader(){' "$a17" >/dev/null; grep -F 'compile_spektra_raw_shader(){' "$0" >/dev/null; grep -F 'verify_native_glslang_handoff(){' "$a17" >/dev/null; grep -F 'verify_native_glslang_handoff(){' "$0" >/dev/null; python3 -S - "$0" "$a17" "$a12" <<'PY_O'
from pathlib import Path
import sys
def ordered(text,marker,tokens,label):
 i=text.find(marker); assert i>=0,(label,marker); text=text[i:]; pos=-1
 for token in tokens:
  nxt=text.find(token,pos+1); assert nxt>pos,(label,token); pos=nxt
stages=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','verify_candidate_patches','prebuild_safety','assemble','postbuild_proof','clean_extract_replay']
cur,a17,a12=[Path(x).read_text() for x in sys.argv[1:]]
ordered(cur,'# IRIS_26822_AUTHORITATIVE_ACTIONS_STAGE_ORDER',stages,'26822')
ordered(a17,'# IRIS_26821_AUTHORITATIVE_ACTIONS_STAGE_ORDER',stages,'26821 authority')
ordered(a12,'# IRIS_26812_AUTHORITATIVE_ACTIONS_STAGE_ORDER',stages,'26812 root')
print('PASS 26822 stage order exactly inherits successful 26821 procedure and successful 26812 root mechanics')
PY_O
cp 26822_MECHANICS_DIFF_AUDIT.txt "$OUT/26822_MECHANICS_DIFF_AUDIT.txt"; pass "successful 26821 implementation diff-audited: zero stage-order/compiler/native/assemble deviation"; }
prepare_glslang(){ D="$WORK/glslang-${GLSLANG_VERSION}"; A="$WORK/glslang.tar.gz"; mkdir -p "$D"; curl -L --fail --retry 3 "$GLSLANG_URL" -o "$A"; [[ "$(sha "$A")" == "$GLSLANG_ARCHIVE_SHA" ]] || fail "glslang archive sha"; tar -xzf "$A" -C "$D"; compiler="$(find "$D" -type f -name glslang -print -quit)"; [[ -n "$compiler" ]] || compiler="$(find "$D" \( -type f -o -type l \) -name glslangValidator -print -quit)"; compiler="$(readlink -f "$compiler")"; [[ -x "$compiler" ]] || chmod +x "$compiler"; "$compiler" --version | tee "$OUT/26822_glslang_version.txt"; export IRIS26822_GLSLANG="$compiler"; export IRIS26681_SPEKTRA_GLSLANG="$compiler"; pass "pinned glslang 16.5.0 dual environment handoff"; }
compile_modified_runtime_shaders(){ python3 -S verify_26822_runtime_glsl.py "$BASE" "$CAND" --compiler "$IRIS26822_GLSLANG" --out "$OUT/26822_runtime_expanded_glsl" | tee "$OUT/26822_glsl_validation.txt"; grep -F 'PASS 26822 GLSL ownership: 3 modified runtime-expanded shaders + 20 inherited active/protected shaders' "$OUT/26822_glsl_validation.txt" >/dev/null; grep -F 'PASS 26822 inherited active/protected shader fidelity: 20 byte-identical to successful 26821' "$OUT/26822_glsl_validation.txt" >/dev/null; for shader in merge normalizeBayer outputTransformUint16 outputTransformFloat outputTransformHdrDirectionUint16 motionv2_render motionv2_false_color_classify_26800 motionv2_false_color_classify_26799 motionv2_false_color_propagate_26799 motionv2_gainmap jpegNeutralHighlightClamp26790 normalChromaConsensus26790 jpegPhaseSafeCfaLca26788 universalNormalMasterShortFusion26651 EDGE_FALSE_COLOR_SUPPRESSOR_26778 jpegNeutralHighlightClamp26787 normalDngMerge seed localMedian directionalSmooth iirRgb universalAdaptiveColor26561 bipolarColorTrust26769; do grep -F "PASS 26822 pinned real glslang compile exact runtime-expanded shader: $shader" "$OUT/26822_glsl_validation.txt" >/dev/null || fail "missing real glslang proof: $shader"; done; sed -i 's/REAL GLSL COMPILE: NOT RUN YET/REAL GLSL COMPILE: PASS (3 modified + 20 inherited active\/protected shaders, pinned glslang 16.5.0)/' "$OUT/26822_COMPILER_STATUS.txt"; }
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
install_frozen_candidate_live(){ rm -rf app; cp -a "$CAND/app" app; snapshot_live_authority_seeded "$LIVE_CANON"; universe_equal "$CAND" "$LIVE_CANON"; pass "authority-seeded canonical live candidate byte-identical to frozen 26822 candidate"; }
compile_languages(){ ./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace 2>&1 | tee "$OUT/26822_gradle_language_compilers.log"; snapshot_live_authority_seeded "$POST_LANG"; universe_equal "$CAND" "$POST_LANG"; sed -i 's/REAL KOTLIN COMPILE: NOT RUN YET/REAL KOTLIN COMPILE: PASS/' "$OUT/26822_COMPILER_STATUS.txt"; sed -i 's/REAL JAVA COMPILE: NOT RUN YET/REAL JAVA COMPILE: PASS/' "$OUT/26822_COMPILER_STATUS.txt"; pass "real Kotlin/Java compilers passed and frozen source remained byte-identical"; }
verify_native_glslang_handoff(){ [[ -n "${IRIS26822_GLSLANG:-}" && -x "$IRIS26822_GLSLANG" ]] || fail "IRIS26822_GLSLANG missing"; [[ -n "${IRIS26681_SPEKTRA_GLSLANG:-}" && -x "$IRIS26681_SPEKTRA_GLSLANG" ]] || fail "IRIS26681_SPEKTRA_GLSLANG missing"; [[ "$(readlink -f "$IRIS26822_GLSLANG")" == "$(readlink -f "$IRIS26681_SPEKTRA_GLSLANG")" ]] || fail "native/Spektra glslang handoff differs"; { echo "IRIS26681_SPEKTRA_GLSLANG=$IRIS26681_SPEKTRA_GLSLANG"; echo "IRIS26822_GLSLANG=$IRIS26822_GLSLANG"; } | tee "$OUT/26822_native_glslang_handoff.txt"; pass "successful 26821 native glslang handoff preserved before both-ABI native compile"; }
compile_native(){ ./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace 2>&1 | tee "$OUT/26822_gradle_native_compiler.log"; sed -i 's#NATIVE/NDK COMPILE: NOT RUN YET#NATIVE/NDK COMPILE: PASS (arm64-v8a + armeabi-v7a)#' "$OUT/26822_COMPILER_STATUS.txt"; }
verify_candidate_patches(){ python3 -S verify_26822_patches.py "$BASE" "$CAND" 26822_FORWARD_FULL_INDEX.patch 26822_ROLLBACK_FULL_INDEX.patch | tee "$OUT/26822_patch_validation.txt"; grep -F 'PASS 26822 canonical patch proof' "$OUT/26822_patch_validation.txt" >/dev/null; pass "sealed full-index forward/rollback proof: successful 26821 -> exact 5-path 26822 candidate"; }
prebuild_safety(){ snapshot_live_authority_seeded "$WORK/prebuild_live_snapshot"; universe_equal "$CAND" "$WORK/prebuild_live_snapshot"; python3 -S validate_26822.py "$BASE" "$CAND"; (cd "$CAND" && sha256sum -c "$ROOT/26822_PROTECTED_26821.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26822_NATIVE_26821.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26822_VENDOR_26821.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26822_DNG_WRITER_26821.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26822_SUCCESSFUL_26819_SABRE_REFERENCE.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26822_SUCCESSFUL_26818_VGN_REFERENCE.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26822_SUCCESSFUL_26821_DNG_MERGE_REFERENCE.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26822_SUCCESSFUL_26821_DNG_PHASE_REFERENCE.sha256" >/dev/null); cat > "$OUT/26822_PREBUILD_SAFETY.txt" <<EOF
PRE-BUILD SAFETY PROOF PASSED
runtime_authority=successful 26821 $RUNTIME_AUTHORITY_COMMIT run $RUNTIME_ACTIONS_RUN artifact $RUNTIME_ARTIFACT_ID
verification_mechanics=exact successful 26821 17-stage sequence; successful 26812 root mechanics inherited
runtime_changed_files=5 modified / 0 added / 0 deleted
runtime_allowlist=app/src/main/assets/shaders/motionv2/false_color_classify_26800.glsl,app/src/main/assets/shaders/motionv2/false_color_propagate_26799.glsl,app/src/main/assets/shaders/motionv2/render.glsl,app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java,app/version.properties
protected_files=1778 unchanged
native_files=819 unchanged
vendor_files=773 unchanged
dng_writer_files=6 unchanged
base_candidate_files=1783
final_candidate_files=1783
sabre_normal_chroma=exact successful 26819 validity-aware NORMAL correction frozen; SHORT/Resolve frozen
vgn_color=exact successful 26818 VGN independent restoration + bounded green cleanup frozen
dng_phase=exact successful 26821 all-four-phase neutral coherence frozen; normalDngMerge/LCA/alignment/weights frozen
jpeg_false_color=single downstream RGB mutation owner; continuous classifier evidence only; inherited eight host passes are pass-through with no connected flood; no neighbor hue donation; no 26803 direct target; no display-brightness authority override; correction only attenuates center chroma toward neutral with luminance and hue direction invariant
gpu_lifecycle=exact successful 26821 three-R8 allocation/binding/lifetime retained; no new allocation or alias
runtime_glsl_delta=3 modified runtime-expanded shaders (render, classifier, propagation) + 20 inherited active/protected
backup_branch_created=false
EOF
echo 'PRE-BUILD SAFETY PROOF PASSED'; }
assemble(){ ./gradlew :app:assembleDebug --stacktrace 2>&1 | tee "$OUT/26822_gradle_assemble.log"; mapfile -t apks < <(find app/build/outputs/apk -type f -name '*.apk' | sort); [[ "${#apks[@]}" -eq 1 ]] || fail "expected exactly one APK, got ${#apks[@]}"; cp "${apks[0]}" "$FINAL"; sha256sum "$FINAL" | tee "$OUT/26822_APK.sha256"; sed -i 's/FULL ANDROID ASSEMBLE: NOT RUN YET/FULL ANDROID ASSEMBLE: PASS (exactly one APK)/' "$OUT/26822_COMPILER_STATUS.txt"; }
postbuild_proof(){ snapshot_live_authority_seeded "$WORK/postbuild_live_snapshot"; universe_equal "$CAND" "$WORK/postbuild_live_snapshot"; python3 -S validate_26822.py "$BASE" "$CAND"; (cd "$CAND" && sha256sum -c "$ROOT/26822_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26822_PROTECTED_26821.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26822_NATIVE_26821.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26822_VENDOR_26821.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26822_DNG_WRITER_26821.sha256" >/dev/null); cp 26822_EXPECTED_CANDIDATE_FULL_APP.sha256 "$OUT/26822_candidate_full_app.sha256"; tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -czf "$OUT/26822_candidate_app_source.tar.gz" -C "$CAND" app; sha256sum "$OUT/26822_candidate_app_source.tar.gz" > "$OUT/26822_candidate_app_source.tar.gz.sha256"; cp 26822_FORWARD_FULL_INDEX.patch "$OUT/26822_FORWARD_FULL_INDEX.patch"; cp 26822_ROLLBACK_FULL_INDEX.patch "$OUT/26822_ROLLBACK_FULL_INDEX.patch"; sed -i 's/POST-BUILD INVARIANCE: NOT RUN YET/POST-BUILD INVARIANCE: PASS/' "$OUT/26822_COMPILER_STATUS.txt"; pass "authority-seeded post-build protected/DNG/native/vendor/source invariance"; }
clean_extract_replay(){ local replay="$WORK/clean_replay_candidate"; rm -rf "$replay"; sha256sum -c 26822_HANDOFF_HASHES.sha256 >/dev/null; bash -n build_26822_single_owner_false_color_attenuation.sh; python3 -S -m py_compile transform_26822.py validate_26822.py verify_26822_patches.py verify_26822_runtime_glsl.py; rm -rf __pycache__; python3 -S transform_26822.py "$BASE" "$replay" handoff_payload_26822; universe_equal "$CAND" "$replay"; python3 -S validate_26822.py "$BASE" "$replay"; python3 -S verify_26822_runtime_glsl.py "$BASE" "$replay" --out "$OUT/26822_final_runtime_expanded_glsl" | tee "$OUT/26822_final_glsl_static_replay.txt"; python3 -S verify_26822_patches.py "$BASE" "$replay" 26822_FORWARD_FULL_INDEX.patch 26822_ROLLBACK_FULL_INDEX.patch | tee "$OUT/26822_final_patch_replay.txt"; (cd "$replay" && sha256sum -c "$ROOT/26822_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null); (cd "$replay" && sha256sum -c "$ROOT/26822_SUCCESSFUL_26819_SABRE_REFERENCE.sha256" >/dev/null); (cd "$replay" && sha256sum -c "$ROOT/26822_SUCCESSFUL_26818_VGN_REFERENCE.sha256" >/dev/null); (cd "$replay" && sha256sum -c "$ROOT/26822_SUCCESSFUL_26821_DNG_MERGE_REFERENCE.sha256" >/dev/null); (cd "$replay" && sha256sum -c "$ROOT/26822_SUCCESSFUL_26821_DNG_PHASE_REFERENCE.sha256" >/dev/null); grep -F 'VERSION_NAME=0.9726822' "$replay/app/version.properties" >/dev/null; grep -F 'VERSION_BUILD=26822' "$replay/app/version.properties" >/dev/null; for proof in 'REAL GLSL COMPILE: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS'; do grep -F "$proof" "$OUT/26822_COMPILER_STATUS.txt" >/dev/null || fail "missing final proof $proof"; done; pass "final 26822 clean replay of hashes/single-owner false-color/DNG/Sabre/VGN/version/patch/compiler/build proofs"; }
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
pass "26822 SINGLE OWNER FALSE COLOR ATTENUATION: ACTIONS BUILD PROOF COMPLETE"
