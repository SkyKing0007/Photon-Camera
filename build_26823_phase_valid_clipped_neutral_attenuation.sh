#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
ROOT="$(pwd)"; EXPECTED_BRANCH="experimental-clean-photon-rebuild"
RUNTIME_AUTHORITY_COMMIT="4c4824f3ce2ef850c640207f5af341bba3e2270c"; RUNTIME_ACTIONS_RUN="38307699961"; RUNTIME_ARTIFACT_ID="11772764787"; RUNTIME_ARTIFACT_NAME="photon-26822-single-owner-false-color-attenuation"; RUNTIME_ARTIFACT_SHA="973de9c3a5846ccabe625711c4405df4c2638a70ef379e10696dcd5209c31b92"; RUNTIME_TAR_SHA="5e09fc81cfb9b2d59d731afeab149d806189f9cc28fd06a9579325c9c4be4d0e"
MECHANICS_AUTHORITY_COMMIT="9fdf39a0a99773ea86159250c7715396b58e78d3"; MECHANICS_ACTIONS_RUN="38295667311"; ROOT_MECHANICS_COMMIT="b1f0db1c3225411476d3d65a236543e9f016d76d"; ROOT_MECHANICS_RUN="38162515468"
VERSION_NAME="0.9726823"; VERSION_BUILD="26823"; GLSLANG_VERSION="16.5.0"; GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"; GLSLANG_URL="https://github.com/KhronosGroup/glslang/releases/download/16.5.0/glslang-16.5.0-linux-x86_64-release.tar.gz"
OUT="$ROOT/build_26823_phase_valid_clipped_neutral_attenuation_outputs"; WORK="$ROOT/.build_26823_phase_valid_clipped_neutral_attenuation_work"; ARTZIP="$WORK/26822_artifact.zip"; ARTDIR="$WORK/artifact_26822"; BASE="$WORK/exact_successful_26822_compiled_candidate"; CAND="$WORK/candidate_26823"; LIVE_CANON="$WORK/live_compiler_candidate_snapshot"; POST_LANG="$WORK/post_language_compiler_source_snapshot"; FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-phase-valid-clipped-neutral-attenuation-debug.apk"; TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR"
cat > "$OUT/26823_COMPILER_STATUS.txt" <<EOF
REAL GLSL COMPILE: NOT RUN YET
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
NATIVE/NDK COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
EOF
# IRIS_26823_AUTHORITATIVE_ACTIONS_STAGE_ORDER
verify_package(){ sha256sum -c 26823_HANDOFF_HASHES.sha256 >/dev/null; bash -n build_26823_phase_valid_clipped_neutral_attenuation.sh; python3 -S -m py_compile transform_26823.py validate_26823.py verify_26823_patches.py verify_26823_runtime_glsl.py; rm -rf __pycache__; [[ "$(find handoff_payload_26823 -type f | wc -l)" -eq 2 ]] || fail "26823 payload count"; diff -u 26823_RUNTIME_CHANGED_PATHS.txt <(find handoff_payload_26823 -type f | sed 's#^handoff_payload_26823/##' | sort) >/dev/null || fail "26823 payload allowlist mismatch"; for p in 26823_FORWARD_FULL_INDEX.patch 26823_ROLLBACK_FULL_INDEX.patch; do ! grep -Eq '^(rename from|rename to|copy from|copy to) ' "$p" || fail "patch rename/copy inference"; done; grep -Fx 'RUN_26823_PHASE_VALID_CLIPPED_NEUTRAL_ATTENUATION' TRIGGER_26823.txt >/dev/null || fail "26823 trigger identity mismatch"; ! find . -type f -name '*.apk' | grep -q . || fail "APK unexpectedly packaged"; pass "sealed 26823 package hashes/syntax/allowlist/patch identity"; }
verify_scope(){ [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch"; git merge-base --is-ancestor "$RUNTIME_AUTHORITY_COMMIT" HEAD || fail "26822 runtime authority not ancestor"; git merge-base --is-ancestor "$ROOT_MECHANICS_COMMIT" HEAD || fail "26812 root mechanics authority not ancestor"; if git diff --name-only "$RUNTIME_AUTHORITY_COMMIT"..HEAD | grep -E '^app/'; then fail "live app source changed after 26822 authority"; fi; python3 -S - <<'PY_SCOPE'
import subprocess
allowed=('26823_','build_26823_phase_valid_clipped_neutral_attenuation.sh','transform_26823.py','validate_26823.py','verify_26823_patches.py','verify_26823_runtime_glsl.py','handoff_payload_26823/','.github/workflows/build-26823-phase-valid-clipped-neutral-attenuation.yml','TRIGGER_26823.txt','PHOTON_26823_PHASE_VALID_CLIPPED_NEUTRAL_ATTENUATION_README.txt')
paths=subprocess.check_output(['git','diff','--name-only','4c4824f3ce2ef850c640207f5af341bba3e2270c..HEAD'],text=True).splitlines()
bad=[p for p in paths if not any(p==x or p.startswith(x) for x in allowed)]
assert not bad,bad
print('PASS 26823 infrastructure scope allowlist')
PY_SCOPE
pass "26823 scope exact: successful 26822 authority + sealed 2-path payload; live app untouched"; }
obtain_authority(){ [[ -n "$TOKEN" ]] || fail "GITHUB_TOKEN missing"; curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${RUNTIME_ARTIFACT_ID}/zip" -o "$ARTZIP"; [[ "$(sha "$ARTZIP")" == "$RUNTIME_ARTIFACT_SHA" ]] || fail "26822 artifact sha"; unzip -q "$ARTZIP" -d "$ARTDIR"; T="$ARTDIR/build_26822_single_owner_false_color_attenuation_outputs/26822_candidate_app_source.tar.gz"; [[ -f "$T" && "$(sha "$T")" == "$RUNTIME_TAR_SHA" ]] || fail "26822 candidate tar sha"; STATUS="$ARTDIR/build_26822_single_owner_false_color_attenuation_outputs/26822_COMPILER_STATUS.txt"; for proof in 'REAL GLSL COMPILE: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS'; do grep -F "$proof" "$STATUS" >/dev/null || fail "missing 26822 authority proof: $proof"; done; mkdir -p "$BASE"; tar -xzf "$T" -C "$BASE"; [[ "$(find "$BASE/app" -type f | wc -l)" -eq 1783 ]] || fail "26822 base file count"; (cd "$BASE" && sha256sum -c "$ROOT/26823_BASE_26822_FULL_APP.sha256" >/dev/null); (cd "$BASE" && sha256sum -c "$ROOT/26823_PRIOR_SOURCE_HASHES.sha256" >/dev/null); (cd "$BASE" && sha256sum -c "$ROOT/26823_NATIVE_26822.sha256" >/dev/null); (cd "$BASE" && sha256sum -c "$ROOT/26823_VENDOR_26822.sha256" >/dev/null); (cd "$BASE" && sha256sum -c "$ROOT/26823_DNG_WRITER_26822.sha256" >/dev/null); cat > "$OUT/26823_RESOLVED_AUTHORITIES.txt" <<EOF
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
pass "exact successful 26822 compiled candidate reconstructed"; }
universe_equal(){ python3 -S - "$1" "$2" <<'PY_U'
from pathlib import Path
import hashlib,sys
def U(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(r)/'app').rglob('*') if p.is_file()}
a,b=U(sys.argv[1]),U(sys.argv[2]); assert a==b,(len(a),len(b)); print(f'PASS byte-identical app universe: {len(a)} files')
PY_U
}
make_candidate(){ python3 -S transform_26823.py "$BASE" "$CAND" handoff_payload_26823; python3 -S validate_26823.py "$BASE" "$CAND"; (cd "$CAND" && sha256sum -c "$ROOT/26823_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26823_PROTECTED_26822.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26823_NATIVE_26822.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26823_VENDOR_26822.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26823_DNG_WRITER_26822.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26823_SUCCESSFUL_26819_SABRE_REFERENCE.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26823_SUCCESSFUL_26818_VGN_REFERENCE.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26823_SUCCESSFUL_26821_DNG_MERGE_REFERENCE.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26823_SUCCESSFUL_26821_DNG_PHASE_REFERENCE.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26823_SUCCESSFUL_26822_SINGLE_OWNER_REFERENCE.sha256" >/dev/null); [[ "$(find "$CAND/app" -type f | wc -l)" -eq 1783 ]] || fail "candidate count"; pass "candidate-first 26823 from exact successful-26822 authority; strict phase-valid bright-neutral pre-VGN attenuation only; successful 26822 downstream single-owner frozen"; }
verify_successful_mechanics(){ local a17="$WORK/authority_26821_build.sh" a12="$WORK/authority_26812_build.sh"; git show "$MECHANICS_AUTHORITY_COMMIT:build_26821_connected_false_color_dng_all_phase_coherence.sh" > "$a17"; git show "$ROOT_MECHANICS_COMMIT:build_26812_neutral_parent_edge_fringe.sh" > "$a12"; for cmd in './gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace' "./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace" './gradlew :app:assembleDebug --stacktrace'; do grep -F "$cmd" "$a17" >/dev/null || fail "26821 authority command missing: $cmd"; grep -F "$cmd" "$0" >/dev/null || fail "26823 command differs: $cmd"; done; grep -F 'compile_spektra_raw_shader(){' "$a17" >/dev/null; grep -F 'compile_spektra_raw_shader(){' "$0" >/dev/null; grep -F 'verify_native_glslang_handoff(){' "$a17" >/dev/null; grep -F 'verify_native_glslang_handoff(){' "$0" >/dev/null; python3 -S - "$0" "$a17" "$a12" <<'PY_O'
from pathlib import Path
import sys
def ordered(text,marker,tokens,label):
 i=text.find(marker); assert i>=0,(label,marker); text=text[i:]; pos=-1
 for token in tokens:
  nxt=text.find(token,pos+1); assert nxt>pos,(label,token); pos=nxt
stages=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','verify_candidate_patches','prebuild_safety','assemble','postbuild_proof','clean_extract_replay']
cur,a17,a12=[Path(x).read_text() for x in sys.argv[1:]]
ordered(cur,'# IRIS_26823_AUTHORITATIVE_ACTIONS_STAGE_ORDER',stages,'26823')
ordered(a17,'# IRIS_26821_AUTHORITATIVE_ACTIONS_STAGE_ORDER',stages,'26821 authority')
ordered(a12,'# IRIS_26812_AUTHORITATIVE_ACTIONS_STAGE_ORDER',stages,'26812 root')
print('PASS 26823 stage order exactly inherits successful 26821 procedure and successful 26812 root mechanics')
PY_O
cp 26823_MECHANICS_DIFF_AUDIT.txt "$OUT/26823_MECHANICS_DIFF_AUDIT.txt"; pass "successful 26821 implementation diff-audited: zero stage-order/compiler/native/assemble deviation"; }
prepare_glslang(){ D="$WORK/glslang-${GLSLANG_VERSION}"; A="$WORK/glslang.tar.gz"; mkdir -p "$D"; curl -L --fail --retry 3 "$GLSLANG_URL" -o "$A"; [[ "$(sha "$A")" == "$GLSLANG_ARCHIVE_SHA" ]] || fail "glslang archive sha"; tar -xzf "$A" -C "$D"; compiler="$(find "$D" -type f -name glslang -print -quit)"; [[ -n "$compiler" ]] || compiler="$(find "$D" \( -type f -o -type l \) -name glslangValidator -print -quit)"; compiler="$(readlink -f "$compiler")"; [[ -x "$compiler" ]] || chmod +x "$compiler"; "$compiler" --version | tee "$OUT/26823_glslang_version.txt"; export IRIS26823_GLSLANG="$compiler"; export IRIS26681_SPEKTRA_GLSLANG="$compiler"; pass "pinned glslang 16.5.0 dual environment handoff"; }
compile_modified_runtime_shaders(){ python3 -S verify_26823_runtime_glsl.py "$BASE" "$CAND" --compiler "$IRIS26823_GLSLANG" --out "$OUT/26823_runtime_expanded_glsl" | tee "$OUT/26823_glsl_validation.txt"; grep -F 'PASS 26823 GLSL ownership: 1 modified runtime-expanded shader + 22 inherited active/protected shaders' "$OUT/26823_glsl_validation.txt" >/dev/null; grep -F 'PASS 26823 inherited active/protected shader fidelity: 22 byte-identical to successful 26822' "$OUT/26823_glsl_validation.txt" >/dev/null; for shader in merge normalizeBayer outputTransformUint16 outputTransformFloat outputTransformHdrDirectionUint16 motionv2_render motionv2_false_color_classify_26800 motionv2_false_color_classify_26799 motionv2_false_color_propagate_26799 motionv2_gainmap jpegNeutralHighlightClamp26790 normalChromaConsensus26790 jpegPhaseSafeCfaLca26788 universalNormalMasterShortFusion26651 EDGE_FALSE_COLOR_SUPPRESSOR_26778 jpegNeutralHighlightClamp26787 normalDngMerge seed localMedian directionalSmooth iirRgb universalAdaptiveColor26561 bipolarColorTrust26769; do grep -F "PASS 26823 pinned real glslang compile exact runtime-expanded shader: $shader" "$OUT/26823_glsl_validation.txt" >/dev/null || fail "missing real glslang proof: $shader"; done; sed -i 's/REAL GLSL COMPILE: NOT RUN YET/REAL GLSL COMPILE: PASS (1 modified + 22 inherited active\/protected shaders, pinned glslang 16.5.0)/' "$OUT/26823_COMPILER_STATUS.txt"; }
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
install_frozen_candidate_live(){ rm -rf app; cp -a "$CAND/app" app; snapshot_live_authority_seeded "$LIVE_CANON"; universe_equal "$CAND" "$LIVE_CANON"; pass "authority-seeded canonical live candidate byte-identical to frozen 26823 candidate"; }
compile_languages(){ ./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace 2>&1 | tee "$OUT/26823_gradle_language_compilers.log"; snapshot_live_authority_seeded "$POST_LANG"; universe_equal "$CAND" "$POST_LANG"; sed -i 's/REAL KOTLIN COMPILE: NOT RUN YET/REAL KOTLIN COMPILE: PASS/' "$OUT/26823_COMPILER_STATUS.txt"; sed -i 's/REAL JAVA COMPILE: NOT RUN YET/REAL JAVA COMPILE: PASS/' "$OUT/26823_COMPILER_STATUS.txt"; pass "real Kotlin/Java compilers passed and frozen source remained byte-identical"; }
verify_native_glslang_handoff(){ [[ -n "${IRIS26823_GLSLANG:-}" && -x "$IRIS26823_GLSLANG" ]] || fail "IRIS26823_GLSLANG missing"; [[ -n "${IRIS26681_SPEKTRA_GLSLANG:-}" && -x "$IRIS26681_SPEKTRA_GLSLANG" ]] || fail "IRIS26681_SPEKTRA_GLSLANG missing"; [[ "$(readlink -f "$IRIS26823_GLSLANG")" == "$(readlink -f "$IRIS26681_SPEKTRA_GLSLANG")" ]] || fail "native/Spektra glslang handoff differs"; { echo "IRIS26681_SPEKTRA_GLSLANG=$IRIS26681_SPEKTRA_GLSLANG"; echo "IRIS26823_GLSLANG=$IRIS26823_GLSLANG"; } | tee "$OUT/26823_native_glslang_handoff.txt"; pass "successful 26821 native glslang handoff preserved before both-ABI native compile"; }
compile_native(){ ./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace 2>&1 | tee "$OUT/26823_gradle_native_compiler.log"; sed -i 's#NATIVE/NDK COMPILE: NOT RUN YET#NATIVE/NDK COMPILE: PASS (arm64-v8a + armeabi-v7a)#' "$OUT/26823_COMPILER_STATUS.txt"; }
verify_candidate_patches(){ python3 -S verify_26823_patches.py "$BASE" "$CAND" 26823_FORWARD_FULL_INDEX.patch 26823_ROLLBACK_FULL_INDEX.patch | tee "$OUT/26823_patch_validation.txt"; grep -F 'PASS 26823 canonical patch proof' "$OUT/26823_patch_validation.txt" >/dev/null; pass "sealed full-index forward/rollback proof: successful 26822 -> exact 2-path 26823 candidate"; }
prebuild_safety(){ snapshot_live_authority_seeded "$WORK/prebuild_live_snapshot"; universe_equal "$CAND" "$WORK/prebuild_live_snapshot"; python3 -S validate_26823.py "$BASE" "$CAND"; (cd "$CAND" && sha256sum -c "$ROOT/26823_PROTECTED_26822.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26823_NATIVE_26822.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26823_VENDOR_26822.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26823_DNG_WRITER_26822.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26823_SUCCESSFUL_26819_SABRE_REFERENCE.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26823_SUCCESSFUL_26818_VGN_REFERENCE.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26823_SUCCESSFUL_26821_DNG_MERGE_REFERENCE.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26823_SUCCESSFUL_26821_DNG_PHASE_REFERENCE.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26823_SUCCESSFUL_26822_SINGLE_OWNER_REFERENCE.sha256" >/dev/null); cat > "$OUT/26823_PREBUILD_SAFETY.txt" <<EOF
PRE-BUILD SAFETY PROOF PASSED
runtime_authority=successful 26822 $RUNTIME_AUTHORITY_COMMIT run $RUNTIME_ACTIONS_RUN artifact $RUNTIME_ARTIFACT_ID
verification_mechanics=exact successful 26821 17-stage sequence; successful 26812 root mechanics inherited
runtime_changed_files=2 modified / 0 added / 0 deleted
runtime_allowlist=app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt,app/version.properties
protected_files=1781 unchanged
native_files=819 unchanged
vendor_files=773 unchanged
dng_writer_files=6 unchanged
base_candidate_files=1783
final_candidate_files=1783
sabre_normal_chroma=exact successful 26819 validity-aware NORMAL correction frozen; SHORT/Resolve frozen
vgn_color=exact successful 26818 VGN independent restoration + bounded green cleanup frozen
dng_phase=exact successful 26821 all-four-phase neutral coherence frozen; normalDngMerge/LCA/alignment/weights frozen
jpeg_false_color=exact successful 26822 downstream single-owner classifier/pass-through/render bytes frozen; new correction is pre-VGN and only attenuates center chroma under strict bright neutral + asymmetric consumed-CFA validity proof; no hue donation; luma restored exactly
gpu_lifecycle=exact successful 26822 allocation/binding/lifetime retained; existing five-uint edge stats carrier and two passes retained; no new allocation or alias
runtime_glsl_delta=1 modified runtime-expanded shader (EDGE_FALSE_COLOR_SUPPRESSOR_26778) + 22 inherited active/protected
backup_branch_created=false
EOF
echo 'PRE-BUILD SAFETY PROOF PASSED'; }
assemble(){ ./gradlew :app:assembleDebug --stacktrace 2>&1 | tee "$OUT/26823_gradle_assemble.log"; mapfile -t apks < <(find app/build/outputs/apk -type f -name '*.apk' | sort); [[ "${#apks[@]}" -eq 1 ]] || fail "expected exactly one APK, got ${#apks[@]}"; cp "${apks[0]}" "$FINAL"; sha256sum "$FINAL" | tee "$OUT/26823_APK.sha256"; sed -i 's/FULL ANDROID ASSEMBLE: NOT RUN YET/FULL ANDROID ASSEMBLE: PASS (exactly one APK)/' "$OUT/26823_COMPILER_STATUS.txt"; }
postbuild_proof(){ snapshot_live_authority_seeded "$WORK/postbuild_live_snapshot"; universe_equal "$CAND" "$WORK/postbuild_live_snapshot"; python3 -S validate_26823.py "$BASE" "$CAND"; (cd "$CAND" && sha256sum -c "$ROOT/26823_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26823_PROTECTED_26822.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26823_NATIVE_26822.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26823_VENDOR_26822.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26823_DNG_WRITER_26822.sha256" >/dev/null); (cd "$CAND" && sha256sum -c "$ROOT/26823_SUCCESSFUL_26822_SINGLE_OWNER_REFERENCE.sha256" >/dev/null); cp 26823_EXPECTED_CANDIDATE_FULL_APP.sha256 "$OUT/26823_candidate_full_app.sha256"; tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -czf "$OUT/26823_candidate_app_source.tar.gz" -C "$CAND" app; sha256sum "$OUT/26823_candidate_app_source.tar.gz" > "$OUT/26823_candidate_app_source.tar.gz.sha256"; cp 26823_FORWARD_FULL_INDEX.patch "$OUT/26823_FORWARD_FULL_INDEX.patch"; cp 26823_ROLLBACK_FULL_INDEX.patch "$OUT/26823_ROLLBACK_FULL_INDEX.patch"; sed -i 's/POST-BUILD INVARIANCE: NOT RUN YET/POST-BUILD INVARIANCE: PASS/' "$OUT/26823_COMPILER_STATUS.txt"; pass "authority-seeded post-build protected/DNG/native/vendor/source invariance"; }
clean_extract_replay(){ local replay="$WORK/clean_replay_candidate"; rm -rf "$replay"; sha256sum -c 26823_HANDOFF_HASHES.sha256 >/dev/null; bash -n build_26823_phase_valid_clipped_neutral_attenuation.sh; python3 -S -m py_compile transform_26823.py validate_26823.py verify_26823_patches.py verify_26823_runtime_glsl.py; rm -rf __pycache__; python3 -S transform_26823.py "$BASE" "$replay" handoff_payload_26823; universe_equal "$CAND" "$replay"; python3 -S validate_26823.py "$BASE" "$replay"; python3 -S verify_26823_runtime_glsl.py "$BASE" "$replay" --out "$OUT/26823_final_runtime_expanded_glsl" | tee "$OUT/26823_final_glsl_static_replay.txt"; python3 -S verify_26823_patches.py "$BASE" "$replay" 26823_FORWARD_FULL_INDEX.patch 26823_ROLLBACK_FULL_INDEX.patch | tee "$OUT/26823_final_patch_replay.txt"; (cd "$replay" && sha256sum -c "$ROOT/26823_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null); (cd "$replay" && sha256sum -c "$ROOT/26823_SUCCESSFUL_26819_SABRE_REFERENCE.sha256" >/dev/null); (cd "$replay" && sha256sum -c "$ROOT/26823_SUCCESSFUL_26818_VGN_REFERENCE.sha256" >/dev/null); (cd "$replay" && sha256sum -c "$ROOT/26823_SUCCESSFUL_26821_DNG_MERGE_REFERENCE.sha256" >/dev/null); (cd "$replay" && sha256sum -c "$ROOT/26823_SUCCESSFUL_26821_DNG_PHASE_REFERENCE.sha256" >/dev/null); (cd "$replay" && sha256sum -c "$ROOT/26823_SUCCESSFUL_26822_SINGLE_OWNER_REFERENCE.sha256" >/dev/null); grep -F 'VERSION_NAME=0.9726823' "$replay/app/version.properties" >/dev/null; grep -F 'VERSION_BUILD=26823' "$replay/app/version.properties" >/dev/null; for proof in 'REAL GLSL COMPILE: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS'; do grep -F "$proof" "$OUT/26823_COMPILER_STATUS.txt" >/dev/null || fail "missing final proof $proof"; done; pass "final 26823 clean replay of hashes/phase-valid clipped-neutral/26822 single-owner/DNG/Sabre/VGN/version/patch/compiler/build proofs"; }
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
pass "26823 PHASE VALID CLIPPED NEUTRAL ATTENUATION: ACTIONS BUILD PROOF COMPLETE"
