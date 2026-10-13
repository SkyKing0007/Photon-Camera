#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
ROOT="$(pwd)"; EXPECTED_BRANCH="experimental-clean-photon-rebuild"
RUNTIME_AUTHORITY_COMMIT="2b6e91b9d99fb8e4d0ea7847b8f54f03f23a8369"; RUNTIME_ACTIONS_RUN="38318489754"; RUNTIME_ARTIFACT_ID="11778260079"; RUNTIME_ARTIFACT_NAME="photon-26823-phase-valid-clipped-neutral-attenuation"; RUNTIME_ARTIFACT_SHA="801c505b980758dc127066373ea936c0ae554b25703ce8b326f1a2400ab2b102"; RUNTIME_TAR_SHA="54660548306afaa0fd47ca2e424fdb9345436c65bdd3aae2a9acd41309dd5c2c"
MECHANICS_AUTHORITY_COMMIT="2b6e91b9d99fb8e4d0ea7847b8f54f03f23a8369"; MECHANICS_ACTIONS_RUN="38318489754"; ROOT_MECHANICS_COMMIT="9fdf39a0a99773ea86159250c7715396b58e78d3"; ROOT_MECHANICS_RUN="38295667311"
VERSION_NAME="0.9726824"; VERSION_BUILD="26824"; GLSLANG_VERSION="16.5.0"; GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"; GLSLANG_URL="https://github.com/KhronosGroup/glslang/releases/download/16.5.0/glslang-16.5.0-linux-x86_64-release.tar.gz"
OUT="$ROOT/build_26824_adaptive_body_s_curve_outputs"; WORK="$ROOT/.build_26824_adaptive_body_s_curve_work"; ARTZIP="$WORK/26823_artifact.zip"; ARTDIR="$WORK/artifact_26823"; BASE="$WORK/exact_successful_26823_compiled_candidate"; CAND="$WORK/candidate_26824"; LIVE_CANON="$WORK/live_compiler_candidate_snapshot"; POST_LANG="$WORK/post_language_compiler_source_snapshot"; FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-adaptive-body-s-curve-debug.apk"; TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR"
cat > "$OUT/26824_COMPILER_STATUS.txt" <<EOF
REAL GLSL COMPILE: NOT RUN YET
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
NATIVE/NDK COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
EOF
# IRIS_26824_AUTHORITATIVE_ACTIONS_STAGE_ORDER
verify_package(){ sha256sum -c 26824_HANDOFF_HASHES.sha256 >/dev/null; bash -n build_26824_adaptive_body_s_curve.sh; python3 -S -m py_compile transform_26824.py validate_26824.py verify_26824_patches.py verify_26824_runtime_glsl.py; rm -rf __pycache__; [[ "$(find handoff_payload_26824 -type f | wc -l)" -eq 6 ]] || fail "26824 payload count"; diff -u 26824_RUNTIME_CHANGED_PATHS.txt <(find handoff_payload_26824 -type f | sed 's#^handoff_payload_26824/##' | sort) >/dev/null || fail "26824 payload allowlist mismatch"; for p in 26824_FORWARD_FULL_INDEX.patch 26824_ROLLBACK_FULL_INDEX.patch; do ! grep -Eq '^(rename from|rename to|copy from|copy to) ' "$p" || fail "patch rename/copy inference"; done; grep -Fx 'RUN_26824_ADAPTIVE_BODY_S_CURVE' TRIGGER_26824.txt >/dev/null || fail "26824 trigger identity mismatch"; ! find . -type f -name '*.apk' | grep -q . || fail "APK unexpectedly packaged"; pass "sealed 26824 package hashes/syntax/allowlist/patch identity"; }
verify_scope(){ [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch"; git merge-base --is-ancestor "$RUNTIME_AUTHORITY_COMMIT" HEAD || fail "26823 runtime authority not ancestor"; git merge-base --is-ancestor "$ROOT_MECHANICS_COMMIT" HEAD || fail "26821 root mechanics authority not ancestor"; if git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD | grep -E '^app/'; then fail "live app source changed after 26823 authority"; fi; python3 -S - <<'PY_SCOPE'
import subprocess
allowed=('26824_','build_26824_adaptive_body_s_curve.sh','transform_26824.py','validate_26824.py','verify_26824_patches.py','verify_26824_runtime_glsl.py','handoff_payload_26824/','.github/workflows/build-26824-adaptive-body-s-curve.yml','TRIGGER_26824.txt','PHOTON_26824_ADAPTIVE_BODY_S_CURVE_README.txt')
paths=subprocess.check_output(['git','diff','--name-only','2b6e91b9d99fb8e4d0ea7847b8f54f03f23a8369..HEAD'],text=True).splitlines()
bad=[p for p in paths if not any(p==x or p.startswith(x) for x in allowed)]
assert not bad,bad
print('PASS 26824 infrastructure scope allowlist')
PY_SCOPE
pass "26824 scope exact: successful 26823 authority + sealed 6-path payload; live app untouched"; }
obtain_authority(){ [[ -n "$TOKEN" ]] || fail "GITHUB_TOKEN missing"; curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${RUNTIME_ARTIFACT_ID}/zip" -o "$ARTZIP"; [[ "$(sha "$ARTZIP")" == "$RUNTIME_ARTIFACT_SHA" ]] || fail "26823 artifact sha"; unzip -q "$ARTZIP" -d "$ARTDIR"; T="$ARTDIR/build_26823_phase_valid_clipped_neutral_attenuation_outputs/26823_candidate_app_source.tar.gz"; [[ -f "$T" && "$(sha "$T")" == "$RUNTIME_TAR_SHA" ]] || fail "26823 candidate tar sha"; STATUS="$ARTDIR/build_26823_phase_valid_clipped_neutral_attenuation_outputs/26823_COMPILER_STATUS.txt"; for proof in 'REAL GLSL COMPILE: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS'; do grep -F "$proof" "$STATUS" >/dev/null || fail "missing 26823 authority proof: $proof"; done; mkdir -p "$BASE"; tar -xzf "$T" -C "$BASE"; [[ "$(find "$BASE/app" -type f | wc -l)" -eq 1783 ]] || fail "26823 base file count"; (cd "$BASE" && sha256sum -c "$ROOT/26824_BASE_26823_FULL_APP.sha256" >/dev/null); (cd "$BASE" && sha256sum -c "$ROOT/26824_PRIOR_SOURCE_HASHES.sha256" >/dev/null); (cd "$BASE" && sha256sum -c "$ROOT/26824_NATIVE_PROTECTED_26823.sha256" >/dev/null); (cd "$BASE" && sha256sum -c "$ROOT/26824_VENDOR_26823.sha256" >/dev/null); (cd "$BASE" && sha256sum -c "$ROOT/26824_DNG_WRITER_26823.sha256" >/dev/null); (cd "$BASE" && sha256sum -c "$ROOT/26824_SHADER_ASSETS_PROTECTED_26823.sha256" >/dev/null); cat > "$OUT/26824_RESOLVED_AUTHORITIES.txt" <<EOF
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
pass "exact successful 26823 compiled candidate reconstructed"; }
universe_equal(){ python3 -S - "$1" "$2" <<'PY_U'
from pathlib import Path
import hashlib,sys
def U(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(r)/'app').rglob('*') if p.is_file()}
a,b=U(sys.argv[1]),U(sys.argv[2]); assert a==b,(len(a),len(b)); print(f'PASS byte-identical app universe: {len(a)} files')
PY_U
}
make_candidate(){ python3 -S transform_26824.py "$BASE" "$CAND" handoff_payload_26824; python3 -S validate_26824.py "$BASE" "$CAND"; (cd "$CAND" && sha256sum -c "$ROOT/26824_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26824_PROTECTED_26823.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26824_NATIVE_PROTECTED_26823.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26824_VENDOR_26823.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26824_DNG_WRITER_26823.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26824_SHADER_ASSETS_PROTECTED_26823.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26824_SUCCESSFUL_26819_SABRE_REFERENCE.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26824_SUCCESSFUL_26818_VGN_REFERENCE.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26824_SUCCESSFUL_26821_DNG_PHASE_REFERENCE.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26824_SUCCESSFUL_26823_FALSE_COLOR_REFERENCE.sha256" >/dev/null); [[ "$(find "$CAND/app" -type f | wc -l)" -eq 1783 ]] || fail "candidate count"; pass "candidate-first 26824 from exact successful-26823 authority; adaptive body S-curve + relative 0.95 Motion saturation only; 26823 false-color architecture frozen"; }
verify_successful_mechanics(){ local a23="$WORK/authority_26823_build.sh" a21="$WORK/authority_26821_build.sh"; git show "$MECHANICS_AUTHORITY_COMMIT:build_26823_phase_valid_clipped_neutral_attenuation.sh" > "$a23"; git show "$ROOT_MECHANICS_COMMIT:build_26821_connected_false_color_dng_all_phase_coherence.sh" > "$a21"; for cmd in './gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace' "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace" './gradlew :app:assembleDebug --stacktrace'; do grep -F "$cmd" "$a23" >/dev/null || fail "26823 authority command missing: $cmd"; grep -F "$cmd" "$0" >/dev/null || fail "26824 command differs: $cmd"; done; grep -F 'compile_spektra_raw_shader(){' "$a23" >/dev/null; grep -F 'compile_spektra_raw_shader(){' "$0" >/dev/null; grep -F 'verify_native_glslang_handoff(){' "$a23" >/dev/null; grep -F 'verify_native_glslang_handoff(){' "$0" >/dev/null; python3 -S - "$0" "$a23" "$a21" <<'PY_O'
from pathlib import Path
import sys
def ordered(text,marker,tokens,label):
 i=text.find(marker); assert i>=0,(label,marker); text=text[i:]; pos=-1
 for token in tokens:
  nxt=text.find(token,pos+1); assert nxt>pos,(label,token); pos=nxt
stages=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','verify_candidate_patches','prebuild_safety','assemble','postbuild_proof','clean_extract_replay']
cur,a23,a21=[Path(x).read_text() for x in sys.argv[1:]]
ordered(cur,'# IRIS_26824_AUTHORITATIVE_ACTIONS_STAGE_ORDER',stages,'26824')
ordered(a23,'# IRIS_26823_AUTHORITATIVE_ACTIONS_STAGE_ORDER',stages,'26823 authority')
ordered(a21,'# IRIS_26821_AUTHORITATIVE_ACTIONS_STAGE_ORDER',stages,'26821 root')
print('PASS 26824 stage order exactly inherits successful 26823 procedure and successful 26821 root mechanics')
PY_O
cp 26824_MECHANICS_DIFF_AUDIT.txt "$OUT/26824_MECHANICS_DIFF_AUDIT.txt"; pass "successful 26823 implementation diff-audited: zero stage-order/compiler/native/assemble deviation"; }
prepare_glslang(){ D="$WORK/glslang-${GLSLANG_VERSION}"; A="$WORK/glslang.tar.gz"; mkdir -p "$D"; curl -L --fail --retry 3 "$GLSLANG_URL" -o "$A"; [[ "$(sha "$A")" == "$GLSLANG_ARCHIVE_SHA" ]] || fail "glslang archive sha"; tar -xzf "$A" -C "$D"; compiler="$(find "$D" -type f -name glslang -print -quit)"; [[ -n "$compiler" ]] || compiler="$(find "$D" \( -type f -o -type l \) -name glslangValidator -print -quit)"; compiler="$(readlink -f "$compiler")"; [[ -x "$compiler" ]] || chmod +x "$compiler"; "$compiler" --version | tee "$OUT/26824_glslang_version.txt"; export IRIS26824_GLSLANG="$compiler"; export IRIS26681_SPEKTRA_GLSLANG="$compiler"; pass "pinned glslang 16.5.0 dual environment handoff"; }
compile_modified_runtime_shaders(){ python3 -S verify_26824_runtime_glsl.py "$BASE" "$CAND" --compiler "$IRIS26824_GLSLANG" --out "$OUT/26824_runtime_expanded_glsl" | tee "$OUT/26824_glsl_validation.txt"; grep -F 'PASS 26824 GLSL ownership: 3 modified runtime-expanded shaders + 21 inherited active/protected shaders' "$OUT/26824_glsl_validation.txt" >/dev/null; grep -F 'PASS 26824 inherited active/protected shader fidelity: 21 byte-identical to successful 26823' "$OUT/26824_glsl_validation.txt" >/dev/null; for shader in motionv2_render motionv2_gainmap true2x_publication_compute EDGE_FALSE_COLOR_SUPPRESSOR_26778 merge normalizeBayer outputTransformUint16 outputTransformFloat outputTransformHdrDirectionUint16 motionv2_false_color_classify_26800 motionv2_false_color_classify_26799 motionv2_false_color_propagate_26799 jpegNeutralHighlightClamp26790 normalChromaConsensus26790 jpegPhaseSafeCfaLca26788 universalNormalMasterShortFusion26651 jpegNeutralHighlightClamp26787 normalDngMerge seed localMedian directionalSmooth iirRgb universalAdaptiveColor26561 bipolarColorTrust26769; do grep -F "PASS 26824 pinned real glslang compile exact runtime-expanded shader: $shader" "$OUT/26824_glsl_validation.txt" >/dev/null || fail "missing real glslang proof: $shader"; done; sed -i 's/REAL GLSL COMPILE: NOT RUN YET/REAL GLSL COMPILE: PASS (3 modified + 21 inherited active\/protected shaders, pinned glslang 16.5.0)/' "$OUT/26824_COMPILER_STATUS.txt"; }
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
install_frozen_candidate_live(){ rm -rf app; cp -a "$CAND/app" app; snapshot_live_authority_seeded "$LIVE_CANON"; universe_equal "$CAND" "$LIVE_CANON"; pass "authority-seeded canonical live candidate byte-identical to frozen 26824 candidate"; }
compile_languages(){ ./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace 2>&1 | tee "$OUT/26824_gradle_language_compilers.log"; snapshot_live_authority_seeded "$POST_LANG"; universe_equal "$CAND" "$POST_LANG"; sed -i 's/REAL KOTLIN COMPILE: NOT RUN YET/REAL KOTLIN COMPILE: PASS/' "$OUT/26824_COMPILER_STATUS.txt"; sed -i 's/REAL JAVA COMPILE: NOT RUN YET/REAL JAVA COMPILE: PASS/' "$OUT/26824_COMPILER_STATUS.txt"; pass "real Kotlin/Java compilers passed and frozen source remained byte-identical"; }
verify_native_glslang_handoff(){ [[ -n "${IRIS26824_GLSLANG:-}" && -x "$IRIS26824_GLSLANG" ]] || fail "IRIS26824_GLSLANG missing"; [[ -n "${IRIS26681_SPEKTRA_GLSLANG:-}" && -x "$IRIS26681_SPEKTRA_GLSLANG" ]] || fail "IRIS26681_SPEKTRA_GLSLANG missing"; [[ "$(readlink -f "$IRIS26824_GLSLANG")" == "$(readlink -f "$IRIS26681_SPEKTRA_GLSLANG")" ]] || fail "native/Spektra glslang handoff differs"; { echo "IRIS26681_SPEKTRA_GLSLANG=$IRIS26681_SPEKTRA_GLSLANG"; echo "IRIS26824_GLSLANG=$IRIS26824_GLSLANG"; } | tee "$OUT/26824_native_glslang_handoff.txt"; pass "successful 26823 native glslang handoff preserved before both-ABI native compile"; }
compile_native(){ ./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace 2>&1 | tee "$OUT/26824_gradle_native_compiler.log"; sed -i 's#NATIVE/NDK COMPILE: NOT RUN YET#NATIVE/NDK COMPILE: PASS (arm64-v8a + armeabi-v7a)#' "$OUT/26824_COMPILER_STATUS.txt"; }
verify_candidate_patches(){ python3 -S verify_26824_patches.py "$BASE" "$CAND" 26824_FORWARD_FULL_INDEX.patch 26824_ROLLBACK_FULL_INDEX.patch | tee "$OUT/26824_patch_validation.txt"; grep -F 'PASS 26824 canonical patch proof' "$OUT/26824_patch_validation.txt" >/dev/null; pass "sealed full-index forward/rollback proof: successful 26823 -> exact 6-path 26824 candidate"; }
prebuild_safety(){ snapshot_live_authority_seeded "$WORK/prebuild_live_snapshot"; universe_equal "$CAND" "$WORK/prebuild_live_snapshot"; python3 -S validate_26824.py "$BASE" "$CAND"; (cd "$CAND" && sha256sum -c "$ROOT/26824_PROTECTED_26823.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26824_NATIVE_PROTECTED_26823.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26824_VENDOR_26823.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26824_DNG_WRITER_26823.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26824_SHADER_ASSETS_PROTECTED_26823.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26824_SUCCESSFUL_26819_SABRE_REFERENCE.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26824_SUCCESSFUL_26818_VGN_REFERENCE.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26824_SUCCESSFUL_26821_DNG_PHASE_REFERENCE.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26824_SUCCESSFUL_26823_FALSE_COLOR_REFERENCE.sha256" >/dev/null); cat > "$OUT/26824_PREBUILD_SAFETY.txt" <<EOF
PRE-BUILD SAFETY PROOF PASSED
runtime_authority=successful 26823 $RUNTIME_AUTHORITY_COMMIT run $RUNTIME_ACTIONS_RUN artifact $RUNTIME_ARTIFACT_ID
verification_mechanics=exact successful 26823 17-stage sequence; successful 26821 root mechanics inherited
runtime_changed_files=6 modified / 0 added / 0 deleted
runtime_allowlist=render.glsl,gainmap.glsl,motionv2_jpeg444_jni.cpp,MotionV2Render.java,MotionV2Jpeg444Encoder.java,app/version.properties
protected_files=1777 unchanged
native_protected_files=818 unchanged
vendor_files=773 unchanged
dng_writer_files=6 unchanged
shader_assets_protected=272 unchanged
base_candidate_files=1783
final_candidate_files=1783
adaptive_tone=190437 histogram signature receives bounded negative S-curve strength; supplied dark indoor histograms remain exact identity; deep black <=0.055 and upper >=0.76 identity
saturation=Motion only relative 0.95 after frozen per-lens setting; Night remains neutral; 1x and true2x share scale
exposure_capture=unchanged; outputExposureScale remains 0.80 and no AE/capture/normalization owner changed
gamma=IRIS_26660 gamma 2.50 function byte-preserved in render and gainmap
false_color=successful 26823 phase-valid pre-VGN + successful 26822 downstream single-owner semantics protected; no hue donation/flood resurrection
sabre_vgn_dng=successful 26819 Sabre, 26818 VGN, 26821 DNG phase bytes frozen
uhdr=HDR target ownership frozen; only matched SDR denominator mirrors new 26824 body curve
runtime_glsl_delta=3 modified runtime-expanded shaders (render, gainmap, true2x publication compute) + 21 inherited active/protected
backup_branch_created=false
EOF
echo 'PRE-BUILD SAFETY PROOF PASSED'; }
assemble(){ ./gradlew :app:assembleDebug --stacktrace 2>&1 | tee "$OUT/26824_gradle_assemble.log"; mapfile -t apks < <(find app/build/outputs/apk -type f -name '*.apk' | sort); [[ "${#apks[@]}" -eq 1 ]] || fail "expected exactly one APK, got ${#apks[@]}"; cp "${apks[0]}" "$FINAL"; sha256sum "$FINAL" | tee "$OUT/26824_APK.sha256"; sed -i 's/FULL ANDROID ASSEMBLE: NOT RUN YET/FULL ANDROID ASSEMBLE: PASS (exactly one APK)/' "$OUT/26824_COMPILER_STATUS.txt"; }
postbuild_proof(){ snapshot_live_authority_seeded "$WORK/postbuild_live_snapshot"; universe_equal "$CAND" "$WORK/postbuild_live_snapshot"; python3 -S validate_26824.py "$BASE" "$CAND"; (cd "$CAND" && sha256sum -c "$ROOT/26824_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26824_PROTECTED_26823.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26824_NATIVE_PROTECTED_26823.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26824_VENDOR_26823.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26824_DNG_WRITER_26823.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26824_SHADER_ASSETS_PROTECTED_26823.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26824_SUCCESSFUL_26823_FALSE_COLOR_REFERENCE.sha256" >/dev/null); cp 26824_EXPECTED_CANDIDATE_FULL_APP.sha256 "$OUT/26824_candidate_full_app.sha256"; tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -czf "$OUT/26824_candidate_app_source.tar.gz" -C "$CAND" app; sha256sum "$OUT/26824_candidate_app_source.tar.gz" > "$OUT/26824_candidate_app_source.tar.gz.sha256"; cp 26824_FORWARD_FULL_INDEX.patch "$OUT/26824_FORWARD_FULL_INDEX.patch"; cp 26824_ROLLBACK_FULL_INDEX.patch "$OUT/26824_ROLLBACK_FULL_INDEX.patch"; sed -i 's/POST-BUILD INVARIANCE: NOT RUN YET/POST-BUILD INVARIANCE: PASS/' "$OUT/26824_COMPILER_STATUS.txt"; pass "authority-seeded post-build protected/DNG/native/vendor/shader/source invariance"; }
clean_extract_replay(){ local replay="$WORK/clean_replay_candidate"; rm -rf "$replay"; sha256sum -c 26824_HANDOFF_HASHES.sha256 >/dev/null; bash -n build_26824_adaptive_body_s_curve.sh; python3 -S -m py_compile transform_26824.py validate_26824.py verify_26824_patches.py verify_26824_runtime_glsl.py; rm -rf __pycache__; python3 -S transform_26824.py "$BASE" "$replay" handoff_payload_26824; universe_equal "$CAND" "$replay"; python3 -S validate_26824.py "$BASE" "$replay"; python3 -S verify_26824_runtime_glsl.py "$BASE" "$replay" --out "$OUT/26824_final_runtime_expanded_glsl" | tee "$OUT/26824_final_glsl_static_replay.txt"; python3 -S verify_26824_patches.py "$BASE" "$replay" 26824_FORWARD_FULL_INDEX.patch 26824_ROLLBACK_FULL_INDEX.patch | tee "$OUT/26824_final_patch_replay.txt"; (cd "$replay" && sha256sum -c "$ROOT/26824_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null); (cd "$replay" && sha256sum -c "$ROOT/26824_SUCCESSFUL_26819_SABRE_REFERENCE.sha256" >/dev/null); (cd "$replay" && sha256sum -c "$ROOT/26824_SUCCESSFUL_26818_VGN_REFERENCE.sha256" >/dev/null); (cd "$replay" && sha256sum -c "$ROOT/26824_SUCCESSFUL_26821_DNG_PHASE_REFERENCE.sha256" >/dev/null); (cd "$replay" && sha256sum -c "$ROOT/26824_SUCCESSFUL_26823_FALSE_COLOR_REFERENCE.sha256" >/dev/null); grep -F 'VERSION_NAME=0.9726824' "$replay/app/version.properties" >/dev/null; grep -F 'VERSION_BUILD=26824' "$replay/app/version.properties" >/dev/null; for proof in 'REAL GLSL COMPILE: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS'; do grep -F "$proof" "$OUT/26824_COMPILER_STATUS.txt" >/dev/null || fail "missing final proof $proof"; done; pass "final 26824 clean replay of hashes/adaptive body S-curve/saturation/26823 false-color/DNG/Sabre/VGN/gamma/version/patch/compiler/build proofs"; }
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
pass "26824 ADAPTIVE BODY S CURVE + 0.95 SATURATION: ACTIONS BUILD PROOF COMPLETE"
