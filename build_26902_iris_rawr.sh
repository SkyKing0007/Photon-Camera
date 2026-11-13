#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
ROOT="$(pwd)"; EXPECTED_BRANCH="experimental-clean-photon-rebuild"
# Successful 26901 compiled candidate is runtime authority.
# Keep successful 26886 V6 17-stage verification mechanics unchanged by default.
REPO_SCAFFOLD_BASE_COMMIT="ee59eeb6f4fec16af10969ed7fbf90269b11a16a"
RUNTIME_ARTIFACT_ID="13297535320"; RUNTIME_ACTIONS_RUN="41774585178"
RUNTIME_AUTHORITY_COMMIT="ee59eeb6f4fec16af10969ed7fbf90269b11a16a"
RUNTIME_ARTIFACT_SHA="6de45e5fa5c26e581c9d010175ed8691941ce14122b64ef13fee2020e70c68a5"
RUNTIME_TAR_SHA="759109721bfc05c70c85d215542333a667107f0e652531ec9966768e8658a615"
MECHANICS_GIT_BLOB="d043b05d58a3d63b8fb48af5fadde2e8a59712ba"
VERSION_NAME="0.9726902"; VERSION_BUILD="26902"; GLSLANG_VERSION="16.5.0"
GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"
GLSLANG_URL="https://github.com/KhronosGroup/glslang/releases/download/16.5.0/glslang-16.5.0-linux-x86_64-release.tar.gz"
OUT="$ROOT/build_26902_iris_rawr_outputs"; WORK="$ROOT/.build_26902_iris_rawr_work"
ARTZIP="$WORK/26901_artifact.zip"; ARTDIR="$WORK/artifact_26901"
BASE="$WORK/exact_successful_26901_compiled_candidate"; CAND="$WORK/candidate_26902"
LIVE_CANON="$WORK/live_compiler_candidate_snapshot"; POST_LANG="$WORK/post_language_compiler_source_snapshot"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-iris-rawr-debug.apk"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR"
cat > "$OUT/26902_COMPILER_STATUS.txt" <<'STATUS'
REAL GLSL COMPILE: NOT RUN YET
REAL SPIR-V VALIDATION: NOT RUN YET
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
NATIVE/NDK COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
STATUS
# IRIS_26902_AUTHORITATIVE_ACTIONS_STAGE_ORDER
verify_package(){
 sha256sum -c 26886_HANDOFF_HASHES.sha256 >/dev/null || fail 'sealed 26886 upload hashes drift'
 sha256sum -c 26886_GENERATED_BUILD_SHA256.txt >/dev/null || fail 'generated 26886 build script hash drift'
 bash -n build_26886_iris_rawr.sh || fail 'exact inherited guarded script shell syntax'
 python3 -S -m py_compile regressions/26885_actions_40604341240_historical_scope.py verify_26886_candidate.py verify_26886_patches.py verify_26880_rawr_shader_universe.py verify_26880_runtime_glsl_scope.py verify_26880_highlight_runtime_shader.py regressions/26880_runtime_ownership_spektra.py regressions/26879_runtime_ownership_spektra.py regressions/26878_runtime_ownership_spektra.py regressions/26877_runtime_ownership_spektra.py regressions/26880_wr_no_fit_optional_wavelet.py
 rm -rf __pycache__ regressions/__pycache__
 for patch in 26886_FORWARD_FULL_INDEX.patch 26886_ROLLBACK_FULL_INDEX.patch;do
  ! grep -Eq '^(rename from|rename to|copy from|copy to) ' "$patch" || fail 'unexpected rename'
 done
 [[ $(find handoff_payload_26886 -type f | wc -l) -eq 2 ]] || fail '2-file exact B-only runtime correction scope'
 diff -u 26886_CHANGED_ALLOWLIST.txt <(find handoff_payload_26886 -type f | sed 's#^handoff_payload_26886/##' | LC_ALL=C sort) >/dev/null || fail 'strict runtime allowlist drift'
 sha256sum -c 26886_PAYLOAD_SHA256.txt >/dev/null || fail 'candidate payload hash drift'


 test -f TRIGGER_26886.txt && grep -Fx 'RUN_26886_B_ON_WRONSKI_CHROMA_NOISE_ALIAS_V1' TRIGGER_26886.txt >/dev/null || fail 'wrong 26886 trigger'
 ! find . -type f -name '*.apk' | grep -q . || fail 'APK cannot be committed'
 pass '26886 exact sealed candidate-first 2-file and inherited successful 26877 guarded package'
 python3 -S -m py_compile verify_26886_candidate.py verify_26886_patches.py verify_26881_expanded_glsl.py regressions/26881_spektra_chroma_clip.py regressions/26881_actual_generator_artifact_identity.py stage_26882_root.py
 python3 -S stage_26882_root.py --verify-only
 python3 -S regressions/26881_actual_generator_artifact_identity.py build_26881_iris_rawr.sh

 python3 -S -m py_compile verify_26882_candidate.py verify_26882_patches.py verify_26882_expanded_glsl.py verify_26882_semantics.py stage_26882_root.py
 python3 -S stage_26882_root.py
 python3 -S -m py_compile verify_26883_candidate.py verify_26883_patches.py verify_26883_expanded_glsl.py verify_26883_semantics.py regressions/26883_successor_contract.py stage_26883_root.py
 python3 -S regressions/26883_successor_contract.py
 python3 -S stage_26883_root.py
 python3 -S -m py_compile verify_26884_candidate.py verify_26884_patches.py verify_26884_expanded_glsl.py verify_26884_semantics.py regressions/26884_successor_contract.py regressions/26884_rawr_off_math.py stage_26884_root.py
 python3 -S regressions/26884_successor_contract.py
 python3 -S stage_26884_root.py

 python3 -S -m py_compile verify_26885_candidate.py verify_26885_patches.py verify_26885_expanded_glsl.py verify_26885_semantics.py stage_26885_root.py regressions/26885_successor_contract.py regressions/26885_chroma_controls.py
 python3 -S stage_26885_root.py
 python3 -S regressions/26885_successor_contract.py
 python3 -S stage_26886_root.py
 python3 -S -m py_compile generate_26886_build.py stage_26886_root.py verify_26886_candidate.py verify_26886_patches.py verify_26886_expanded_glsl.py verify_26886_semantics.py regressions/26886_chroma_controls.py regressions/26886_successor_contract.py regressions/26886_historical_scope_all_stages.py
 python3 -S regressions/26886_successor_contract.py
 test -f TRIGGER_26887.txt
 grep -Fx 'RUN_26887_B_OFF_RAW_WITNESS_HDRQ_MOTION_V1' TRIGGER_26887.txt
 python3 -S stage_26887_root.py
 python3 -S -m py_compile generate_26887_build.py verify_26887_candidate.py verify_26887_semantics.py verify_26887_patches.py verify_26887_expanded_glsl.py stage_26887_root.py regressions/26887_successor_contract.py
 python3 -S regressions/26887_successor_contract.py
 test -f TRIGGER_26888.txt && grep -Fx 'RUN_26888_B_OFF_INDEPENDENT_MOTION_SUPPORT_V1' TRIGGER_26888.txt >/dev/null || fail 'wrong exact-byte 26888 trigger'
 python3 -S stage_26888_root.py
 sha256sum -c 26888_HANDOFF_HASHES.sha256 >/dev/null || fail '26888 sealed staged bytes tampered'
 python3 -S -m py_compile generate_26888_build.py verify_26888_candidate.py verify_26888_semantics.py verify_26888_patches.py verify_26888_expanded_glsl.py stage_26888_root.py regressions/26888_successor_contract.py photon_preserve_successful_runner.py
 python3 -S regressions/26888_successor_contract.py
 sha256sum -c 26888_PAYLOAD_SHA256.txt >/dev/null || fail '26888 payload drift'
 test "$(find handoff_payload_26888 -type f | wc -l)" -eq 9 || fail '26888 frozen B-OFF runtime scope drift'
 test -f TRIGGER_26889.txt && grep -Fx 'RUN_26889_B_OFF_SHUTTER_ADJACENT_MOTION_LONG_V1' TRIGGER_26889.txt >/dev/null || fail 'immutable 26889 trigger changed'
 python3 -S stage_26889_root.py
 sha256sum -c 26889_HANDOFF_HASHES.sha256 >/dev/null || fail '26889 sealed staged bytes tampered'
 python3 -S -m py_compile generate_26889_build.py verify_26889_candidate.py verify_26889_semantics.py verify_26889_patches.py verify_26889_expanded_glsl.py stage_26889_root.py test_26889_negative_tamper.py verify_26889_compiled_push_abi.py
 (cd "$ROOT" && test "$(find handoff_payload_26889 -type f | wc -l)" -eq 10) || fail '26889 9 modified + 1 new B-OFF source scope drift'
 test -f TRIGGER_26890.txt && grep -Fx 'RUN_26890_B_TONE_TOE_DEFAULT_B_A_NAME_SINGLE_TRIGGER_V1' TRIGGER_26890.txt >/dev/null || fail '26890 exact trigger byte drift'
 python3 -S stage_26890_root.py
 sha256sum -c 26890_HANDOFF_HASHES.sha256 >/dev/null || fail '26890 sealed package tampered'
 python3 -S -m py_compile generate_26890_build.py verify_26890_candidate.py verify_26890_semantics.py verify_26890_patches.py verify_26890_expanded_glsl.py stage_26890_root.py test_26890_negative_tamper.py test_26890_tone_math.py photon_26890_replay_exact_26889_workflow.py
 test "$(find handoff_payload_26890 -type f | wc -l)" -eq 8 || fail '26890 eight-source allowlist drift'
 python3 -S test_26890_tone_math.py
 test -f TRIGGER_26891.txt && grep -Fx 'RUN_26891_B_OFF_HDRQ_RAWR_NORMALIZE_PRESERVE_26890_V1' TRIGGER_26891.txt >/dev/null || fail '26891 trigger drift'
 python3 -S stage_26891_root.py
 sha256sum -c 26891_HANDOFF_HASHES.sha256 >/dev/null || fail '26891 sealed handoff tampered'
 python3 -S -m py_compile generate_26891_build.py verify_26891_candidate.py verify_26891_semantics.py verify_26891_patches.py stage_26891_root.py verify_26891_expanded_glsl.py test_26891_negative_tamper.py photon_26891_replay_exact_26890_workflow.py
 test "$(find handoff_payload_26891 -type f | wc -l)" -eq 6 || fail '26891 six-source allowlist drift'
 test -f TRIGGER_26892.txt && grep -Fx 'RUN_26892_SCENE_ADAPTIVE_SDR_BACKLIGHT_CONTRAST_V1' TRIGGER_26892.txt >/dev/null || fail '26892 immutable trigger'
 python3 -S stage_26892_root.py
 sha256sum -c 26892_HANDOFF_HASHES.sha256 >/dev/null || fail '26892 sealed payload tampered'
 python3 -S -m py_compile generate_26892_build.py verify_26892_candidate.py verify_26892_semantics.py verify_26892_patches.py stage_26892_root.py verify_26892_expanded_glsl.py test_26892_negative_tamper.py test_26892_tone_math.py photon_26892_replay_exact_26891_workflow.py
 [[ "$(find handoff_payload_26892 -type f | wc -l)" -eq 4 ]] || fail '26892 4-file exact allowlist drift'
 test -f TRIGGER_26893.txt && grep -Fx 'RUN_26893_BACKLIT_FOREGROUND_DARKEN_ONLY_CONTRAST_V1' TRIGGER_26893.txt >/dev/null || fail '26893 exact sole trigger'
 python3 -S stage_26893_root.py
 sha256sum -c 26893_HANDOFF_HASHES.sha256 >/dev/null || fail '26893 upload hashes drift'
 python3 -S -m py_compile generate_26893_build.py verify_26893_candidate.py verify_26893_semantics.py verify_26893_patches.py verify_26893_expanded_glsl.py test_26893_negative_tamper.py test_26893_tone_math.py test_26893_three_stage_negatives.py stage_26893_root.py photon_26893_replay_exact_26892_workflow.py
 test "$(find handoff_payload_26893 -type f | wc -l)" -eq 4 || fail '26893 4-source scope drift'
 test -f TRIGGER_26894.txt && grep -Fx 'RUN_26894_SPATIAL_FOREGROUND_NOISE_SAFE_FLAT_CONTRAST_V1' TRIGGER_26894.txt >/dev/null || fail '26894 exact-byte new trigger'
 python3 -S stage_26894_root.py
 sha256sum -c 26894_HANDOFF_HASHES.sha256 >/dev/null || fail '26894 staged SHA seal drift'
 python3 -S -m py_compile generate_26894_build.py stage_26894_root.py verify_26894.py test_26894_three_stage_negatives.py
 test "$(find handoff_payload_26894 -type f | wc -l)" -eq 5 || fail '26894 five-source scope drift'
 python3 -S verify_26894.py tone
 test -f TRIGGER_26895.txt && grep -Fx 'RUN_26895_26893_BASELINE_IRIS_SATURATION_1P14_V1' TRIGGER_26895.txt >/dev/null || fail '26895 new exact single trigger'
 python3 -S stage_26895_root.py
 sha256sum -c 26895_HANDOFF_HASHES.sha256 >/dev/null || fail '26895 staged bytes SHA seal drift'
 python3 -S -m py_compile generate_26895_build.py verify_26895.py stage_26895_root.py test_26895_three_stage_negatives.py
 test "$(find handoff_payload_26895 -type f | wc -l)" -eq 4 || fail '26895 four payload files + one shader deletion scope drift'
 test -f TRIGGER_26897.txt && grep -Fx 'RUN_26897_INDEPENDENT_MOTION_DNG_SABRE_BEFORE_B_V1' TRIGGER_26897.txt >/dev/null || fail '26897 exact single trigger drift'
 python3 -S stage_26897_root.py
 sha256sum -c 26897_HANDOFF_HASHES.sha256 >/dev/null || fail '26897 staged byte seal drift'
 python3 -S -m py_compile generate_26897_build.py verify_26897.py stage_26897_root.py test_26897_three_stage_negatives.py test_26897_dng_modes.py
 test "$(find handoff_payload_26897 -type f | wc -l)" -eq 3 || fail '26897 DNG 3-file scope drift'
 test -f TRIGGER_26898.txt && grep -Fx 'RUN_26898_ISOLATED_SABRE_DNG_BEFORE_B_JPEG_V1' TRIGGER_26898.txt >/dev/null || fail '26898 trigger changed'
 python3 -S stage_26898_root.py
 sha256sum -c 26898_HANDOFF_HASHES.sha256 >/dev/null || fail '26898 sealed uploaded bytes changed'
 python3 -S -m py_compile generate_26898_build.py verify_26898.py stage_26898_root.py test_26898_three_stage_negatives.py test_26898_modes.py
 test "$(find handoff_payload_26898 -type f | wc -l)" -eq 5 || fail '26898 five exact modified runtime paths required'
 python3 -S stage_26900_root.py
 sha256sum -c 26900_HANDOFF_HASHES.sha256 >/dev/null || fail '26900 final sealed handoff bytes differ'
 python3 -S test_26900_three_stage_negatives.py
 test -f TRIGGER_26900.txt && grep -Fx 'RUN_26900_B_OFF_BICUBIC_SCALE_AWARE_LUMA_SHARPEN_V1' TRIGGER_26900.txt >/dev/null || fail '26900 immutable trigger mismatch'
 python3 -S stage_26901_root.py
 sha256sum -c 26901_HANDOFF_HASHES.sha256 >/dev/null || fail '26901 sealed staged handoff drift'
 python3 -S test_26901_three_stage_negatives.py
 test -f TRIGGER_26901.txt && grep -Fx 'RUN_26901_B_OFF_FULL_RGB_BICUBIC_UNIVERSAL_LENS_GATE_V1' TRIGGER_26901.txt >/dev/null || fail '26901 exact trigger mismatch'
 python3 -S stage_26902_root.py
 sha256sum -c 26902_HANDOFF_HASHES.sha256 >/dev/null || fail '26902 sealed staged payload drift'
 python3 -S test_26902_three_stage_negatives.py
 test -f TRIGGER_26902.txt && grep -Fx 'RUN_26902_B_OFF_LENS_RELATIVE_GENTLE_SHARPEN_V1' TRIGGER_26902.txt >/dev/null || fail '26902 immutable trigger bytes mismatch'
}
verify_scope(){
 [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail 'wrong Photon Actions branch'
 git merge-base --is-ancestor "$REPO_SCAFFOLD_BASE_COMMIT" HEAD || fail 'successful 26901 commit not ancestor'
 [[ -z "$(git diff --name-only "$REPO_SCAFFOLD_BASE_COMMIT"..HEAD -- app/src app/version.properties)" ]] || fail 'unexpected live source mutations'
 [[ -z "$(git status --porcelain -- app/src app/version.properties)" ]] || fail 'uncommitted runtime source mutations'
 diff -u 26902_REPOSITORY_UPLOAD_ALLOWLIST.txt <(git diff --name-only "$REPO_SCAFFOLD_BASE_COMMIT"..HEAD | LC_ALL=C sort) >/dev/null || fail '26902 uploaded repository path scope changed'
 [[ "$(sha build_26901_iris_rawr.sh)" == 'bcdd8bb524e5410808b4ecf2ef27760c1c28412d18389ee676c55be3509db6d9' ]] || fail 'actual successful 26901 parent runner drift'
 pass '26902 exact successful 26901 runner plus exact uploaded repository scope'
}
obtain_authority(){
 [[ -n "$TOKEN" ]] || fail 'GITHUB_TOKEN missing'
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' \
   "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/runs/${RUNTIME_ACTIONS_RUN}" -o "$WORK/26901_run.json"
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' \
   "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${RUNTIME_ARTIFACT_ID}" -o "$WORK/26901_artifact_metadata.json"
 python3 -S - "$WORK/26901_run.json" "$WORK/26901_artifact_metadata.json" <<'PY_AUTH_26902'
import json,sys
run=json.load(open(sys.argv[1]));art=json.load(open(sys.argv[2]))
assert run['id']==41774585178 and run['conclusion']=='success' and run['head_sha']=='ee59eeb6f4fec16af10969ed7fbf90269b11a16a' and run['head_branch']=='experimental-clean-photon-rebuild'
assert art['id']==13297535320 and art.get('expired') is False and art.get('digest')=='sha256:6de45e5fa5c26e581c9d010175ed8691941ce14122b64ef13fee2020e70c68a5'
print('PASS actual successful 26901 Actions run and artifact digest')
PY_AUTH_26902
 curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' \
   "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${RUNTIME_ARTIFACT_ID}/zip" -o "$ARTZIP"
 [[ "$(sha "$ARTZIP")" == "$RUNTIME_ARTIFACT_SHA" ]] || fail 'real successful 26901 artifact ZIP SHA mismatch'
 unzip -q "$ARTZIP" -d "$ARTDIR"
 local T="$ARTDIR/build_26901_iris_rawr_outputs/26901_candidate_app_source.tar.gz"
 [[ -f "$T" && "$(sha "$T")" == "$RUNTIME_TAR_SHA" ]] || fail 'exact successful compiled 26901 TAR mismatch'
 local EXEC="$ARTDIR/build_26901_iris_rawr_outputs/exact_generated_runner/build_26901_iris_rawr.sh"
 [[ -f "$EXEC" && "$(sha "$EXEC")" == 'bcdd8bb524e5410808b4ecf2ef27760c1c28412d18389ee676c55be3509db6d9' ]] || fail '26901 executed runner mismatched'
 cmp -s "$EXEC" "$ROOT/build_26901_iris_rawr.sh" || fail 'replayed 26901 runner not exact successful Actions bytes'
 test -f "$ARTDIR/build_26901_iris_rawr_outputs/exact_generated_runner/SUCCESSFUL_ACTIONS_EVIDENCE.json" || fail '26901 executed runner receipt missing'
 for k in 'REAL GLSL COMPILE: PASS' 'REAL SPIR-V VALIDATION: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS';do
   grep -F "$k" "$ARTDIR/build_26901_iris_rawr_outputs/26901_COMPILER_STATUS.txt" >/dev/null || fail "26901 successful compiler receipt missing $k"
 done
 mkdir -p "$BASE";tar -xzf "$T" -C "$BASE"
 [[ "$(find "$BASE/app" -type f | wc -l)" -eq 2026 ]] || fail '26901 compiled candidate source count wrong'
 (cd "$BASE" && sha256sum -c "$ROOT/26902_BASE_FULL_APP.sha256" >/dev/null) || fail '26901 compiled candidate source full SHA mismatch'
 cmp -s "$ARTDIR/build_26901_iris_rawr_outputs/26901_candidate_full_app.sha256" "$ROOT/26902_BASE_FULL_APP.sha256" || fail 'base manifest not actual successful 26901 bytes'
 python3 -S verify_26902.py artifact "$ARTDIR" "$ROOT/build_26902_iris_rawr.sh"
 pass '26901 actual success, compiled source TAR, 17-stage runner, full manifests and real compiler receipts'
}
historical_26888_make_candidate(){
 local NEW_BASE="$BASE" NEW_CAND="$CAND"
 local H86="$WORK/historical_26886_from_26887"
 cp -a "$NEW_BASE" "$H86";git -C "$H86" init -q
 (cd "$H86" && git apply --check --reverse "$ROOT/26887_FORWARD_FULL_INDEX.patch" &&
  git apply --reverse "$ROOT/26887_FORWARD_FULL_INDEX.patch" &&
  sha256sum -c "$ROOT/26887_BASE_26886_FULL_APP.sha256" >/dev/null) || fail '26887 successful-source rollback to exact 26886 failed'
 local BASE="$H86" CAND="$WORK/historical_26887_replayed"

 python3 -S verify_26887_candidate.py "$BASE" "$CAND" --transform --root "$ROOT"
 # Inherit real prior successful-universe rollback chain (no synthetic substitute).
 local H85="$WORK/historical_26885_from_26886"
 cp -a "$BASE" "$H85"; git -C "$H85" init -q
 (cd "$H85" && git apply --check --reverse "$ROOT/26886_FORWARD_FULL_INDEX.patch" &&
 git apply --reverse "$ROOT/26886_FORWARD_FULL_INDEX.patch" &&
 sha256sum -c "$ROOT/26886_BASE_26885_FULL_APP.sha256" >/dev/null) || fail 'exact successful 26886->26885 historical rollback failed'
 local H84="$WORK/historical_26884_from_26885"
 cp -a "$H85" "$H84";git -C "$H84" init -q
 (cd "$H84" && git apply --check --reverse "$ROOT/26885_FORWARD_FULL_INDEX.patch" &&
 git apply --reverse "$ROOT/26885_FORWARD_FULL_INDEX.patch" &&
 sha256sum -c "$ROOT/26885_BASE_26884_FULL_APP.sha256" >/dev/null) || fail 'exact successful 26885->26884 historical rollback failed'
 local H83="$WORK/historical_26883_from_26884"
 cp -a "$H84" "$H83";git -C "$H83" init -q
 (cd "$H83" && git apply --check --reverse "$ROOT/26884_FORWARD_FULL_INDEX.patch" &&
 git apply --reverse "$ROOT/26884_FORWARD_FULL_INDEX.patch" &&
 sha256sum -c "$ROOT/26884_BASE_26883_FULL_APP.sha256" >/dev/null) || fail 'exact successful 26884->26883 historical rollback failed'
 local H82="$WORK/historical_26882_from_26883"
 cp -a "$H83" "$H82";git -C "$H82" init -q
 (cd "$H82" && git apply --check --reverse "$ROOT/26883_FORWARD_FULL_INDEX.patch" &&
  git apply --reverse "$ROOT/26883_FORWARD_FULL_INDEX.patch" &&
  sha256sum -c "$ROOT/26883_BASE_26882_FULL_APP.sha256" >/dev/null) || fail '26883->26882 REAL successful compiled candidate rollback failed'
 local H81="$WORK/historical_26881_from_26882"
 cp -a "$H82" "$H81";git -C "$H81" init -q
 (cd "$H81" && git apply --check --reverse "$ROOT/26882_FORWARD_FULL_INDEX.patch" &&
  git apply --reverse "$ROOT/26882_FORWARD_FULL_INDEX.patch" &&
  sha256sum -c "$ROOT/26882_BASE_26881_FULL_APP.sha256" >/dev/null) || fail 'real successful 26882->26881 compiled candidate rollback failed'
 local H80="$WORK/historical_26880_from_26881"
 cp -a "$H81" "$H80";git -C "$H80" init -q
 (cd "$H80" && git apply --check --reverse "$ROOT/26881_FORWARD_FULL_INDEX.patch" &&
  git apply --reverse "$ROOT/26881_FORWARD_FULL_INDEX.patch" &&
  sha256sum -c "$ROOT/26881_BASE_26880_FULL_APP.sha256" >/dev/null) || fail '26881->26880 actual compiled candidate rollback failed'
 local H79="$WORK/historical_26879_from_26880"
 cp -a "$H80" "$H79";git -C "$H79" init -q
 (cd "$H79" && git apply --check --reverse "$ROOT/26880_FORWARD_FULL_INDEX.patch" &&
  git apply --reverse "$ROOT/26880_FORWARD_FULL_INDEX.patch" &&
  sha256sum -c "$ROOT/26880_BASE_26879_FULL_APP.sha256" >/dev/null) || fail '26880->26879 real compiled historical rollback failed'
 local H78="$WORK/historical_26878_from_26879"
 cp -a "$H79" "$H78";git -C "$H78" init -q
 (cd "$H78" && git apply --check --reverse "$ROOT/26879_FORWARD_FULL_INDEX.patch" &&
  git apply --reverse "$ROOT/26879_FORWARD_FULL_INDEX.patch" &&
  sha256sum -c "$ROOT/26879_BASE_26878_FULL_APP.sha256" >/dev/null) || fail 'real 26879->26878 successful candidate rollback failed'
 local H77="$WORK/historical_26877_from_26878"
 cp -a "$H78" "$H77";git -C "$H77" init -q
 (cd "$H77" && git apply --check --reverse "$ROOT/26878_FORWARD_FULL_INDEX.patch" &&
  git apply --reverse "$ROOT/26878_FORWARD_FULL_INDEX.patch" &&
  sha256sum -c "$ROOT/26878_BASE_26877_FULL_APP.sha256" >/dev/null) || fail 'real 26878->26877 rollback failed'
 local H76="$WORK/historical_26876_from_26877"
 cp -a "$H77" "$H76";git -C "$H76" init -q
 (cd "$H76" && git apply --check --reverse "$ROOT/26877_FORWARD_FULL_INDEX.patch" &&
  git apply --reverse "$ROOT/26877_FORWARD_FULL_INDEX.patch" &&
  sha256sum -c "$ROOT/26877_BASE_26876_FULL_APP.sha256" >/dev/null) || fail 'real 26877->26876 rollback failed'
 local H75="$WORK/historical_26875_from_26876"
 cp -a "$H76" "$H75";git -C "$H75" init -q
 (cd "$H75" && git apply --check --reverse "$ROOT/26876_FORWARD_FULL_INDEX.patch" &&
  git apply --reverse "$ROOT/26876_FORWARD_FULL_INDEX.patch" &&
  sha256sum -c "$ROOT/26876_BASE_26875_FULL_APP.sha256" >/dev/null) || fail 'real 26876->26875 rollback failed'
 local H74="$WORK/historical_26874_from_26875"
 cp -a "$H75" "$H74";git -C "$H74" init -q
 (cd "$H74" && git apply --check --reverse "$ROOT/26875_FORWARD_FULL_INDEX.patch" &&
  git apply --reverse "$ROOT/26875_FORWARD_FULL_INDEX.patch" &&
  sha256sum -c "$ROOT/26875_BASE_26874_FULL_APP.sha256" >/dev/null) || fail 'real 26875->26874 rollback failed'
 local H73="$WORK/historical_26873_from_26874"
 cp -a "$H74" "$H73";git -C "$H73" init -q
 (cd "$H73" && git apply --check --reverse "$ROOT/26874_FORWARD_FULL_INDEX.patch" &&
  git apply --reverse "$ROOT/26874_FORWARD_FULL_INDEX.patch" && sha256sum -c "$ROOT/26874_BASE_26873_FULL_APP.sha256" >/dev/null) || fail 'real 26874->26873 rollback failed'
 local H72="$WORK/historical_26872_from_26873"
 cp -a "$H73" "$H72";rm -rf "$H72/.git";git -C "$H72" init -q
 (cd "$H72" && git apply --check --reverse "$ROOT/26873_FORWARD_FULL_INDEX.patch" &&
  git apply --reverse "$ROOT/26873_FORWARD_FULL_INDEX.patch" && sha256sum -c "$ROOT/26873_BASE_26872_FULL_APP.sha256" >/dev/null) || fail 'real 26874->26873->26872 rollback failed'
 local H71="$WORK/historical_26871_from_26872"
 cp -a "$H72" "$H71";git -C "$H71" init -q
 (cd "$H71" && git apply --check --reverse "$ROOT/26872_FORWARD_FULL_INDEX.patch" &&
  git apply --reverse "$ROOT/26872_FORWARD_FULL_INDEX.patch" && sha256sum -c "$ROOT/26872_BASE_26871_FULL_APP.sha256" >/dev/null) || fail 'actual 26872->26871 rollback failed'
 local H70="$WORK/historical_26870_from_26871" H68="$WORK/historical_26868_from_26870"
 local H67="$WORK/historical_26867_from_26868" H66="$WORK/historical_26866_from_26867"
 cp -a "$H71" "$H70";rm -rf "$H70/.git";git -C "$H70" init -q
 (cd "$H70" && git apply --check --reverse "$ROOT/26871_FORWARD_FULL_INDEX.patch" &&
  git apply --reverse "$ROOT/26871_FORWARD_FULL_INDEX.patch" && sha256sum -c "$ROOT/26871_BASE_26870_FULL_APP.sha256" >/dev/null) || fail 'actual 26871->26870 rollback failed'
 cp -a "$H70" "$H68";rm -rf "$H68/.git";git -C "$H68" init -q
 (cd "$H68" && git apply --check --reverse "$ROOT/26870_FORWARD_FULL_INDEX.patch" &&
  git apply --reverse "$ROOT/26870_FORWARD_FULL_INDEX.patch" && sha256sum -c "$ROOT/26870_BASE_26868_FULL_APP.sha256" >/dev/null) || fail '26870->26868 rollback failed'
 cp -a "$H68" "$H67";rm -rf "$H67/.git";git -C "$H67" init -q
 (cd "$H67" && git apply --check --reverse "$ROOT/26868_FORWARD_FULL_INDEX.patch" &&
  git apply --reverse "$ROOT/26868_FORWARD_FULL_INDEX.patch" && sha256sum -c "$ROOT/26868_BASE_26867_FULL_APP.sha256" >/dev/null) || fail '26868->26867 rollback failed'
 cp -a "$H67" "$H66";rm -rf "$H66/.git";git -C "$H66" init -q
 (cd "$H66" && git apply --check --reverse "$ROOT/26867_FORWARD_FULL_INDEX.patch" &&
  git apply --reverse "$ROOT/26867_FORWARD_FULL_INDEX.patch" && sha256sum -c "$ROOT/26867_BASE_26866_FULL_APP.sha256" >/dev/null) || fail '26867->26866 rollback failed'
 (cd "$H71" && sha256sum -c "$ROOT/26872_BASE_26871_FULL_APP.sha256" >/dev/null) || fail 'historical replay mutated 26871 candidate'
 python3 -S regressions/26865_b_lsc_owner.py "$CAND/app"
 python3 -S regressions/26866_b_color_only.py "$H66/app"
 python3 -S regressions/26867_b_highlight_ab_retired.py "$H67/app"
 python3 -S regressions/26868_direct_b_long_retire_ab.py "$H68/app"
 python3 -S regressions/26870_b_automatic_iq.py "$H68/app" "$H70/app"
 python3 -S regressions/26871_b_shutter_group.py "$H70" "$H71"
 python3 -S regressions/26872_b_preview_only.py "$H71" "$H72"
 python3 -S regressions/26873_gpu_resident_owner.py "$H72" "$H73"
 python3 -S regressions/26874_b_jpeg_owner.py "$H73" "$H74"
 python3 -S regressions/26875_device_failures.py "$H74" "$H75"
 python3 -S regressions/26876_superres_ownership.py "$H75" "$H76"
 python3 -S regressions/26877_runtime_ownership_spektra.py "$H76" "$H77"
 python3 -S regressions/26878_runtime_ownership_spektra.py "$H77" "$H78"
 python3 -S regressions/26879_runtime_ownership_spektra.py "$H78" "$H79"
 python3 -S regressions/26880_runtime_ownership_spektra.py "$H79" "$H80"
 python3 -S regressions/26881_spektra_chroma_clip.py "$H80" "$H81"
 python3 -S regressions/26880_wr_no_fit_optional_wavelet.py "$CAND/app/src/main/cpp/iris26864/Iris26864JniGpuInteropImpl.inc"
 python3 -S verify_26880_spektra_abi.py "$H80/app"
 python3 -S verify_26880_native_shaders.py "$CAND"
 python3 -S verify_26887_candidate.py "$BASE" "$CAND"
 python3 -S verify_26876_expanded_shaders.py "$CAND" --source-only
 python3 -S verify_26871_runtime_shader.py "$CAND" --out "$OUT/26887_inherited_26871_shader_expansion"
 python3 -S verify_26872_runtime_shader.py "$CAND" --out "$OUT/26887_precompile_preview_expansion"
 python3 -S verify_26880_rawr_shader_universe.py "$H84/app"
 python3 -S verify_26880_runtime_glsl_scope.py "$H79" "$H80" --out "$OUT/26887_inherited11_current_shader_preflight"
 python3 -S verify_26880_highlight_runtime_shader.py "$H80" --out "$OUT/26887_current_highlight_preflight"
 python3 -S regressions/26864_glsl_reserved_identifiers.py "$CAND/app"
 python3 -S regressions/26864_wronski_publisher.py "$H67/app"
 python3 -S verify_26864_semantics.py "$H67/app" --numeric
 pass 'real 26874->26873->26872->26871->26870->26868->26867->26866 historical universes and B-only preview detector regression'
 python3 -S verify_26881_expanded_glsl.py "$H81" --out "$OUT/26887_new_shader_preflight"

 python3 -S verify_26882_semantics.py "$H81" "$H82"
 python3 -S verify_26882_expanded_glsl.py "$H82" --out "$OUT/26887_successful_26882_white_preflight"
 python3 -S verify_26882_candidate.py "$H81" "$H82"
 python3 -S verify_26883_semantics.py "$H82" "$H83"
 python3 -S verify_26883_expanded_glsl.py "$H83" --out "$OUT/26887_prior_shared_white_preflight"
 python3 -S verify_26883_candidate.py "$H82" "$H83"
 python3 -S verify_26884_semantics.py "$H83" "$H84"
 python3 -S regressions/26884_rawr_off_math.py "$H84"
 python3 -S verify_26884_expanded_glsl.py "$H84" --out "$OUT/26887_current_rawr_off_source_preflight"

 python3 -S verify_26884_candidate.py "$H83" "$H84"
 python3 -S verify_26887_semantics.py "$BASE" "$CAND"
 python3 -S regressions/26886_chroma_controls.py "$H85" "$BASE"
 python3 -S verify_26887_expanded_glsl.py "$CAND"
 python3 -S verify_26887_candidate.py "$BASE" "$CAND"
 python3 -S regressions/26885_actions_40604341240_historical_scope.py "$H84" "$H85" "$ROOT/build_26885_iris_rawr.sh"
 python3 -S verify_26885_candidate.py "$H84" "$H85"
 python3 -S verify_26885_semantics.py "$H84" "$H85"
 python3 -S regressions/26885_chroma_controls.py "$H85" "$H84"
 python3 -S verify_26885_expanded_glsl.py "$H85"
 python3 -S regressions/26886_historical_scope_all_stages.py "$H84" "$H85" "$BASE" "$ROOT/build_26885_iris_rawr.sh" "$ROOT/build_26886_iris_rawr.sh"
 python3 -S verify_26886_candidate.py "$H85" "$BASE"
 python3 -S verify_26886_semantics.py "$H85" "$BASE"
 python3 -S verify_26886_expanded_glsl.py "$BASE"
 python3 -S verify_26886_patches.py "$H85" "$BASE" 26886_FORWARD_FULL_INDEX.patch 26886_ROLLBACK_FULL_INDEX.patch
 python3 -S verify_26887_candidate.py "$BASE" "$CAND"
 python3 -S verify_26887_semantics.py "$BASE" "$CAND"
 python3 -S verify_26887_expanded_glsl.py "$CAND"
 diff -qr "$CAND/app" "$NEW_BASE/app" >/dev/null || fail '26887 own successful historical candidate replay changed bytes'
 python3 -S verify_26888_candidate.py "$NEW_BASE" "$NEW_CAND" --root "$ROOT" --transform
 python3 -S verify_26888_semantics.py "$NEW_BASE" "$NEW_CAND"
 python3 -S verify_26888_expanded_glsl.py "$NEW_CAND"
}
historical_26889_make_candidate(){
 local H87="$WORK/historical_26887_from_26888" H88="$WORK/historical_26888_replayed"
 cp -a "$BASE" "$H87"; git -C "$H87" init -q
 (cd "$H87" && git apply --check --reverse "$ROOT/26888_FORWARD_FULL_INDEX.patch" && \
  git apply --reverse "$ROOT/26888_FORWARD_FULL_INDEX.patch" && \
  sha256sum -c "$ROOT/26888_BASE_26887_FULL_APP.sha256" >/dev/null) || fail '26888 exact original source rollback failed'
 ( local BASE="$H87" CAND="$H88"; historical_26888_make_candidate )
 diff -qr "$H88/app" "$BASE/app" >/dev/null || fail 'original 26888 successful historical generated candidate mismatches actual compiled source'
 python3 -S verify_26888_candidate.py "$H87" "$BASE"
 python3 -S verify_26888_semantics.py "$H87" "$BASE"
 python3 -S verify_26888_patches.py "$H87" "$BASE" 26888_FORWARD_FULL_INDEX.patch 26888_ROLLBACK_FULL_INDEX.patch
 python3 -S verify_26889_candidate.py "$BASE" "$CAND" --transform
 python3 -S verify_26889_semantics.py "$BASE" "$CAND"
 python3 -S verify_26889_expanded_glsl.py "$CAND"
}

historical_26890_make_candidate(){
 local H88="$WORK/historical_26888_from_26889" H89="$WORK/historical_26889_replayed"
 cp -a "$BASE" "$H88";git -C "$H88" init -q
 (cd "$H88" && git apply --check --reverse "$ROOT/26889_FORWARD_FULL_INDEX.patch" && \
  git apply --reverse "$ROOT/26889_FORWARD_FULL_INDEX.patch" && \
  sha256sum -c "$ROOT/26889_BASE_FULL_APP.sha256" >/dev/null) || fail 'actual 26889 to exact 26888 rollback invalid'
 # Original 26889 validator hashes the whole root, so discard temporary Git metadata.
 rm -rf "$H88/.git"
 ( local BASE="$H88" CAND="$H89";historical_26889_make_candidate )
 diff -qr "$H89/app" "$BASE/app" >/dev/null || fail 'original 26889 candidate generation differs from actual successful compiled 26889 bytes'
 python3 -S verify_26889_candidate.py "$H88" "$BASE"
 python3 -S verify_26889_semantics.py "$H88" "$BASE"
 python3 -S verify_26889_expanded_glsl.py "$BASE"
 python3 -S verify_26889_patches.py "$H88" "$BASE" 26889_FORWARD_FULL_INDEX.patch 26889_ROLLBACK_FULL_INDEX.patch
 python3 -S verify_26890_candidate.py "$BASE" "$CAND" --transform
 python3 -S verify_26890_semantics.py "$BASE" "$CAND"
 python3 -S verify_26890_expanded_glsl.py "$CAND"
 python3 -S test_26890_tone_math.py
}

historical_26891_make_candidate(){
 local H89="$WORK/historical_26889_from_26890" H90="$WORK/historical_26890_replayed"
 cp -a "$BASE" "$H89"; git -C "$H89" init -q
 (cd "$H89" && git apply --check --reverse "$ROOT/26890_FORWARD_FULL_INDEX.patch" && \
  git apply --reverse "$ROOT/26890_FORWARD_FULL_INDEX.patch" && \
  sha256sum -c "$ROOT/26890_BASE_FULL_APP.sha256" >/dev/null) || fail '26890 original-source rollback failed'
 rm -rf "$H89/.git"
 ( local BASE="$H89" CAND="$H90"; historical_26890_make_candidate )
 diff -qr "$H90/app" "$BASE/app" >/dev/null || fail 'original generated 26890 candidate != actual compiled 26890'
 python3 -S verify_26890_candidate.py "$H89" "$BASE"
 python3 -S verify_26890_semantics.py "$H89" "$BASE"
 python3 -S verify_26890_expanded_glsl.py "$BASE"
 python3 -S verify_26890_patches.py "$H89" "$BASE" 26890_FORWARD_FULL_INDEX.patch 26890_ROLLBACK_FULL_INDEX.patch
 python3 -S test_26890_negative_tamper.py "$H89" "$BASE"
 python3 -S test_26890_tone_math.py
 python3 -S verify_26891_candidate.py "$BASE" "$CAND" --transform
 python3 -S verify_26891_semantics.py "$BASE" "$CAND"
}
historical_26892_make_candidate(){
 local H90="$WORK/historical_26890_from_26891" H91="$WORK/historical_26891_replayed"
 cp -a "$BASE" "$H90"; git -C "$H90" init -q
 (cd "$H90" && git apply --check --reverse "$ROOT/26891_FORWARD_FULL_INDEX.patch" && \
  git apply --reverse "$ROOT/26891_FORWARD_FULL_INDEX.patch" && \
  sha256sum -c "$ROOT/26891_BASE_FULL_APP.sha256" >/dev/null) || fail '26891 original-source rollback failed'
 rm -rf "$H90/.git"
 (local BASE="$H90" CAND="$H91"; historical_26891_make_candidate)
 diff -qr "$H91/app" "$BASE/app" >/dev/null || fail 'original generated 26891 source != actual compiled 26891'
 python3 -S verify_26891_candidate.py "$H90" "$BASE"
 python3 -S verify_26891_semantics.py "$H90" "$BASE"
 python3 -S verify_26891_expanded_glsl.py "$BASE"
 python3 -S verify_26891_patches.py "$H90" "$BASE" 26891_FORWARD_FULL_INDEX.patch 26891_ROLLBACK_FULL_INDEX.patch
 python3 -S test_26891_negative_tamper.py "$H90" "$BASE"
 python3 -S verify_26892_candidate.py "$BASE" "$CAND" --transform
 python3 -S verify_26892_semantics.py "$BASE" "$CAND"
 python3 -S test_26892_tone_math.py
}
historical_26893_make_candidate(){
 local H91="$WORK/historical_26891_from_26892" H92="$WORK/historical_26892_replayed"
 cp -a "$BASE" "$H91"; git -C "$H91" init -q
 (cd "$H91" && git apply --check --reverse "$ROOT/26892_FORWARD_FULL_INDEX.patch" && \
  git apply --reverse "$ROOT/26892_FORWARD_FULL_INDEX.patch" && \
  sha256sum -c "$ROOT/26892_BASE_FULL_APP.sha256" >/dev/null) || fail '26892 ACTUAL successful original-source rollback failed'
 rm -rf "$H91/.git"
 (local BASE="$H91" CAND="$H92"; historical_26892_make_candidate)
 diff -qr "$H92/app" "$BASE/app" >/dev/null || fail '26892 original generated successful source != actual compiled 26892'
 python3 -S verify_26892_candidate.py "$H91" "$BASE"
 python3 -S verify_26892_semantics.py "$H91" "$BASE"
 python3 -S verify_26892_patches.py "$H91" "$BASE" 26892_FORWARD_FULL_INDEX.patch 26892_ROLLBACK_FULL_INDEX.patch
 python3 -S test_26892_negative_tamper.py "$H91" "$BASE"
 python3 -S test_26892_tone_math.py
 python3 -S verify_26893_candidate.py "$BASE" "$CAND" --transform
 python3 -S verify_26893_semantics.py "$BASE" "$CAND"
 python3 -S test_26893_tone_math.py
}
historical_26894_make_candidate(){
 local H92="$WORK/historical_26892_from_26893" H93="$WORK/historical_26893_replayed"
 cp -a "$BASE" "$H92"; git -C "$H92" init -q
 (cd "$H92" && git apply --check --reverse "$ROOT/26893_FORWARD_FULL_INDEX.patch" && \
  git apply --reverse "$ROOT/26893_FORWARD_FULL_INDEX.patch" && \
  sha256sum -c "$ROOT/26893_BASE_FULL_APP.sha256" >/dev/null) || fail '26893 ACTUAL successful original-source rollback failed'
 rm -rf "$H92/.git"
 (local BASE="$H92" CAND="$H93"; historical_26893_make_candidate)
 diff -qr "$H93/app" "$BASE/app" >/dev/null || fail '26893 original generated successful source != ACTUAL successful compiled 26893'
 python3 -S verify_26893_candidate.py "$H92" "$BASE"
 python3 -S verify_26893_semantics.py "$H92" "$BASE"
 python3 -S verify_26893_patches.py "$H92" "$BASE" 26893_FORWARD_FULL_INDEX.patch 26893_ROLLBACK_FULL_INDEX.patch
 python3 -S test_26893_negative_tamper.py "$H92" "$BASE"
 python3 -S test_26893_tone_math.py
 python3 -S verify_26894.py candidate "$BASE" "$CAND" --transform
 python3 -S verify_26894.py semantics "$BASE" "$CAND"
 python3 -S verify_26894.py tone
}
historical_26895_make_candidate(){
 local H93="$WORK/historical_26893_from_26894" H94="$WORK/historical_26894_replayed"
 cp -a "$BASE" "$H93"; git -C "$H93" init -q
 (cd "$H93" && git apply --check --reverse "$ROOT/26894_FORWARD_FULL_INDEX.patch" && \
  git apply --reverse "$ROOT/26894_FORWARD_FULL_INDEX.patch" && \
  sha256sum -c "$ROOT/26894_BASE_FULL_APP.sha256" >/dev/null) || fail '26894 compiled authority rollback to successful 26893 failed'
 rm -rf "$H93/.git"
 (local BASE="$H93" CAND="$H94"; historical_26894_make_candidate)
 diff -qr "$BASE/app" "$H94/app" >/dev/null || fail 'historical 26894 generated candidate differs from actual compiled 26894'
 python3 -S verify_26894.py candidate "$H93" "$H94"
 python3 -S verify_26894.py semantics "$H93" "$H94"
 python3 -S verify_26894.py tone
 python3 -S verify_26894.py patch "$H93" "$H94" 26894_FORWARD_FULL_INDEX.patch 26894_ROLLBACK_FULL_INDEX.patch
 python3 -S verify_26894.py tamper "$H93" "$H94"
 python3 -S verify_26895.py candidate "$BASE" "$CAND" --transform
 python3 -S verify_26895.py semantics "$BASE" "$CAND"
 python3 -S verify_26895.py shader "$CAND"
}
historical_26897_make_candidate(){
 local H94="$WORK/historical_26894_from_26895" H95="$WORK/historical_26895_replayed"
 cp -a "$BASE" "$H94"; git -C "$H94" init -q
 (cd "$H94" && git apply --check --reverse "$ROOT/26895_FORWARD_FULL_INDEX.patch" && \
  git apply --reverse "$ROOT/26895_FORWARD_FULL_INDEX.patch" && \
  sha256sum -c "$ROOT/26895_BASE_FULL_APP.sha256" >/dev/null) || fail 'successful 26895 2025 source cannot reverse to exact successful 26894'
 rm -rf "$H94/.git"
 (local BASE="$H94" CAND="$H95"; historical_26895_make_candidate)
 diff -qr "$BASE/app" "$H95/app" >/dev/null || fail 'historical exact 26895 generator differs from successful compiled 26895 authority'
 python3 -S verify_26895.py candidate "$H94" "$H95"
 python3 -S verify_26895.py semantics "$H94" "$H95"
 python3 -S verify_26895.py patch "$H94" "$H95" 26895_FORWARD_FULL_INDEX.patch 26895_ROLLBACK_FULL_INDEX.patch
 python3 -S verify_26895.py tamper "$H94" "$H95"
 python3 -S verify_26897.py candidate "$BASE" "$CAND" --transform
 python3 -S verify_26897.py semantics "$BASE" "$CAND"
}
historical_26898_make_candidate(){
 local H95="$WORK/historical_26895_from_26897" H97="$WORK/historical_26897_replayed"
 mkdir -p "$H95"
 local T95="$ARTDIR/build_26901_iris_rawr_outputs/26895_historical_candidate_app_source.tar.gz"
 [[ -f "$T95" && "$(sha "$T95")" == '9df70bdc87756847b7c5a479cb3b22fee7a47920ac277a70d14a5402e3cb6942' ]] || fail '26897 artifact historical 26895 TAR missing or modified'
 tar -xzf "$T95" -C "$H95"
 (cd "$H95" && sha256sum -c "$ROOT/26897_BASE_FULL_APP.sha256" >/dev/null) || fail '26897 historical 26895 source manifest mismatch'
 (local BASE="$H95" CAND="$H97"; historical_26897_make_candidate)
 diff -qr "$BASE/app" "$H97/app" >/dev/null || fail 'historical 26897 transform differs from exact successful compiled authority'
 python3 -S verify_26897.py candidate "$H95" "$H97"
 python3 -S verify_26897.py semantics "$H95" "$H97"
 python3 -S verify_26897.py patch "$H95" "$H97" 26897_FORWARD_FULL_INDEX.patch 26897_ROLLBACK_FULL_INDEX.patch
 python3 -S verify_26897.py tamper "$H95" "$H97"
 python3 -S test_26897_dng_modes.py "$H97"
 python3 -S verify_26898.py candidate "$BASE" "$CAND" --transform
 python3 -S verify_26898.py semantics "$BASE" "$CAND"
}
historical_26899_make_candidate(){
 local H97="$WORK/historical_26897_from_26898" H98="$WORK/historical_26898_replayed"
 mkdir -p "$H97"
 local T97="$ARTDIR/build_26901_iris_rawr_outputs/26897_historical_candidate_app_source.tar.gz"
 [[ -f "$T97" && "$(sha "$T97")" == '23462eec3c2d03b55f97cdb63b686ea9133a4d5f9e50e9ffa0a26ba8a13eebe6' ]] || fail 'actual 26898 historical 26897 TAR SHA mismatch'
 tar -xzf "$T97" -C "$H97"
 (cd "$H97" && sha256sum -c "$ROOT/26898_BASE_FULL_APP.sha256" >/dev/null) || fail '26898 historical successful 26897 source manifest incorrect'
 (local BASE="$H97" CAND="$H98"; historical_26898_make_candidate)
 diff -qr "$H98/app" "$BASE/app" >/dev/null || fail '26898 generated historical candidate differs from successful compiled 26898 runtime'
 python3 -S verify_26898.py candidate "$H97" "$H98"
 python3 -S verify_26898.py semantics "$H97" "$H98"
 python3 -S verify_26898.py patch "$H97" "$H98" 26898_FORWARD_FULL_INDEX.patch 26898_ROLLBACK_FULL_INDEX.patch
 python3 -S verify_26898.py tamper "$H97" "$H98"
 python3 -S test_26898_modes.py "$H98"
 python3 -S verify_26899.py candidate "$BASE" "$CAND" --transform
 python3 -S verify_26899.py semantics "$BASE" "$CAND"
 python3 -S test_26899_modes.py "$CAND"
}
historical_26900_make_candidate(){
 local H98="$WORK/historical_26898_from_26899" H99="$WORK/historical_26899_replayed"
 mkdir -p "$H98"
 local T98="$ARTDIR/build_26901_iris_rawr_outputs/26898_historical_candidate_app_source.tar.gz"
 [[ -f "$T98" && "$(sha "$T98")" == '7ac15724f3cc30753f41f08038443e24b4931c8861fe10217cc4c3b059755a61' ]] || fail 'actual 26899 historical successful 26898 TAR mismatch'
 tar -xzf "$T98" -C "$H98"
 (cd "$H98" && sha256sum -c "$ROOT/26899_BASE_FULL_APP.sha256" >/dev/null) || fail '26899 historical 26898 source manifest wrong'
 (local BASE="$H98" CAND="$H99"; historical_26899_make_candidate)
 diff -qr "$H99/app" "$BASE/app" >/dev/null || fail 'historic derived 26899 candidate is not exact successful compiled runtime'
 python3 -S verify_26899.py candidate "$H98" "$H99"
 python3 -S verify_26899.py semantics "$H98" "$H99"
 python3 -S verify_26899.py patch "$H98" "$H99" 26899_FORWARD_FULL_INDEX.patch 26899_ROLLBACK_FULL_INDEX.patch
 python3 -S verify_26899.py tamper "$H98" "$H99"
 python3 -S test_26899_modes.py "$H99"
 python3 -S verify_26900.py candidate "$BASE" "$CAND" --transform
 python3 -S verify_26900.py semantics "$BASE" "$CAND"
 python3 -S test_26900_modes.py "$CAND"
}
historical_26901_make_candidate(){
 local H99="$WORK/historical_26899_from_26900" H00="$WORK/historical_26900_replayed"
 mkdir -p "$H99"
 local T99="$ARTDIR/build_26901_iris_rawr_outputs/26899_historical_candidate_app_source.tar.gz"
 [[ -f "$T99" && "$(sha "$T99")" == 'b468173a2eae7100f3180b8a178e37961dc1c0465560fad90113e8181507c80f' ]] || fail 'actual 26900 historical successful 26899 TAR mismatch'
 tar -xzf "$T99" -C "$H99"
 (cd "$H99" && sha256sum -c "$ROOT/26900_BASE_FULL_APP.sha256" >/dev/null) || fail 'historical 26900 source must use original successful 26899 bytes'
 (local BASE="$H99" CAND="$H00"; historical_26900_make_candidate)
 diff -qr "$H00/app" "$BASE/app" >/dev/null || fail 'historical derived 26900 not identical to exact successful compiled 26900'
 python3 -S verify_26900.py candidate "$H99" "$H00"
 python3 -S verify_26900.py semantics "$H99" "$H00"
 python3 -S verify_26900.py patch "$H99" "$H00" 26900_FORWARD_FULL_INDEX.patch 26900_ROLLBACK_FULL_INDEX.patch
 python3 -S verify_26900.py tamper "$H99" "$H00"
 python3 -S test_26900_modes.py "$H00"
 python3 -S verify_26901.py candidate "$BASE" "$CAND" --transform
 python3 -S verify_26901.py semantics "$BASE" "$CAND"
 python3 -S test_26901_modes.py "$CAND"
}
make_candidate(){
 local H00="$WORK/historical_26900_from_26901" H01="$WORK/historical_26901_replayed"
 mkdir -p "$H00"
 local T00="$ARTDIR/build_26901_iris_rawr_outputs/26900_historical_candidate_app_source.tar.gz"
 [[ -f "$T00" && "$(sha "$T00")" == 'f629f785bbcf89bef05bb13e0d3398f5e513847c40f7aa22d907fc0781b867fd' ]] || fail 'successful 26901 artifact historical compiled 26900 TAR missing or SHA wrong'
 tar -xzf "$T00" -C "$H00"
 (cd "$H00" && sha256sum -c "$ROOT/26901_BASE_FULL_APP.sha256" >/dev/null) || fail '26901 historical source is not original successful compiled 26900'
 (local BASE="$H00" CAND="$H01"; historical_26901_make_candidate)
 diff -qr "$H01/app" "$BASE/app" >/dev/null || fail 'replayed 26901 source differs successful compiled 26901'
 (cd "$H01" && sha256sum -c "$ROOT/26902_BASE_FULL_APP.sha256" >/dev/null) || fail 'historical 26901 must exactly reproduce current parent compiled source'
 python3 -S verify_26901.py candidate "$H00" "$H01"
 python3 -S verify_26901.py semantics "$H00" "$H01"
 python3 -S verify_26901.py patch "$H00" "$H01" 26901_FORWARD_FULL_INDEX.patch 26901_ROLLBACK_FULL_INDEX.patch
 python3 -S verify_26901.py tamper "$H00" "$H01"
 python3 -S test_26901_modes.py "$H01"
 python3 -S verify_26902.py candidate "$BASE" "$CAND" --transform
 python3 -S verify_26902.py semantics "$BASE" "$CAND"
 python3 -S test_26902_modes.py "$CAND"
}




verify_successful_mechanics(){
 [[ "$(sha build_26886_iris_rawr.sh)" == '3f816088f564bfd575d5dc8e1681b9b1b18ec435de41ed34f2c22df866c5e8fa' ]] || fail 'real successful 26877 generated mechanics drift'
 [[ "$(git rev-parse "$RUNTIME_AUTHORITY_COMMIT:generate_26886_build.py")" == "$MECHANICS_GIT_BLOB" ]] || fail 'successful 26877 generator blob drift'
 for validator in regressions/26874_b_jpeg_owner.py regressions/26873_gpu_resident_owner.py verify_26864_rawr_sources.py verify_26864_runtime_glsl.py verify_26864_semantics.py verify_26868_runtime_shader.py verify_26870_runtime_shader.py verify_26871_runtime_shader.py verify_26872_runtime_shader.py regressions/26868_direct_b_long_retire_ab.py regressions/26870_b_automatic_iq.py regressions/26871_b_shutter_group.py regressions/26872_b_preview_only.py;do
  local prior="$WORK/prior_$validator";mkdir -p "$(dirname "$prior")"
  git show "$RUNTIME_AUTHORITY_COMMIT:$validator" > "$prior"
  cmp -s "$prior" "$ROOT/$validator" || fail "successful 26877 validator differs $validator"
 done
 python3 -S - "$ROOT/build_26886_iris_rawr.sh" "$ROOT/build_26887_iris_rawr.sh" <<'PY_STAGES'
from pathlib import Path
import sys
stages=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','verify_candidate_patches','prebuild_safety','assemble','postbuild_proof','clean_extract_replay']
for name in sys.argv[1:]:
 txt=Path(name).read_text();pos=-1
 for stage in stages:
  nxt=txt.find('\n'+stage+'(){',pos+1);assert nxt>pos,(name,stage,'17-stage order deviation');pos=nxt
for cmd in ['./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace",'./gradlew :app:assembleDebug --stacktrace']:
 assert all(cmd in Path(name).read_text() for name in sys.argv[1:]),('real language/native/assemble command deviation',cmd)
print('PASS exact inherited successful 26877 17-stage compiler/NDK/assembly mechanics')
PY_STAGES
 pass 'actual successful 26877 verification mechanics unchanged; 26887 B-only device correction diff audited'
 [[ "$(sha build_26887_iris_rawr.sh)" == 'f969d504a59a95c8304e7cc4be6beea3fc404cb6c52e9aba228bfbb694486d56' ]] || fail 'successful 26887 V4 exact generated runner changed'
 [[ "$(git rev-parse "$RUNTIME_AUTHORITY_COMMIT:generate_26887_build.py")" == 'f18d4a78940d0d3ef482a8fa33dd613b9cc1dcc2' ]] || fail 'successful 26887 V4 generator blob changed'
 python3 -S regressions/26888_successor_contract.py --generated
 [[ "$(sha build_26888_iris_rawr.sh)" == '5e9bc28287ba38099390b9cad99168c314e3058473e9924137aaf2f02d7f4753' ]] || fail 'successful actual 26888 17-stage executable runner drift'
 python3 -S verify_26891_candidate.py "$WORK/historical_26890_from_26891" "$WORK/historical_26891_replayed"
 python3 -S verify_26891_semantics.py "$WORK/historical_26890_from_26891" "$WORK/historical_26891_replayed"
 python3 -S verify_26889_compiled_push_abi.py "$ARTDIR/build_26901_iris_rawr_outputs/26888_modified_shader_spirv/Iris26887BOffHdrqMerge_prod.spv" "$WORK/historical_26888_from_26889" "$WORK/historical_26889_replayed"
 [[ "$(sha build_26889_iris_rawr.sh)" == '4070c3a0f47fb043d99ad18a1b2d53a629be26891d1147ef9bfc60d790cb7d73' ]] || fail '26889 real Actions successful runner drift'
 python3 -S verify_26891_candidate.py "$WORK/historical_26890_from_26891" "$WORK/historical_26891_replayed"
 python3 -S verify_26891_semantics.py "$WORK/historical_26890_from_26891" "$WORK/historical_26891_replayed"
 python3 -S test_26890_tone_math.py
 [[ "$(sha build_26890_iris_rawr.sh)" == '525b56e735d24b24461cf2575bdfcdfe90b242ec87514b9ddfcaf83c442ee3df' ]] || fail '26890 successfully executed runner drift'
 python3 -S verify_26891_candidate.py "$WORK/historical_26890_from_26891" "$WORK/historical_26891_replayed"
 python3 -S verify_26891_semantics.py "$WORK/historical_26890_from_26891" "$WORK/historical_26891_replayed"
 [[ "$(sha build_26891_iris_rawr.sh)" == 'f0b25de61cc661a461c10e7665623ba15ddda0362ba047c05e543aaf670f094b' ]] || fail 'successful 26891 runner differs from generated'
 python3 -S verify_26892_candidate.py "$WORK/historical_26891_from_26892" "$WORK/historical_26892_replayed"
 python3 -S verify_26892_semantics.py "$WORK/historical_26891_from_26892" "$WORK/historical_26892_replayed"
 python3 -S test_26892_tone_math.py
 [[ "$(sha build_26892_iris_rawr.sh)" == '37b12a9cbb5918b49d279d40d51f11fa086a0682dd487f88b6ecc7f17313069d' ]] || fail 'successful 26892 executed runner drift'
 python3 -S verify_26892_candidate.py "$WORK/historical_26891_from_26892" "$WORK/historical_26892_replayed"
 python3 -S verify_26892_semantics.py "$WORK/historical_26891_from_26892" "$WORK/historical_26892_replayed"
 python3 -S test_26892_tone_math.py
 python3 -S verify_26893_candidate.py "$WORK/historical_26892_from_26893" "$WORK/historical_26893_replayed"
 python3 -S verify_26893_semantics.py "$WORK/historical_26892_from_26893" "$WORK/historical_26893_replayed"
 python3 -S test_26893_tone_math.py
 python3 -S verify_26894.py candidate "$WORK/historical_26893_from_26894" "$WORK/historical_26894_replayed"
 python3 -S verify_26894.py semantics "$WORK/historical_26893_from_26894" "$WORK/historical_26894_replayed"
 python3 -S verify_26894.py tone
 python3 -S verify_26895.py candidate "$WORK/historical_26894_from_26895" "$WORK/historical_26895_replayed"
 python3 -S verify_26895.py semantics "$WORK/historical_26894_from_26895" "$WORK/historical_26895_replayed"
 python3 -S verify_26897.py candidate "$WORK/historical_26895_from_26897" "$WORK/historical_26897_replayed"
 python3 -S verify_26897.py semantics "$WORK/historical_26895_from_26897" "$WORK/historical_26897_replayed"
 python3 -S test_26897_dng_modes.py "$WORK/historical_26897_replayed"
 python3 -S verify_26898.py candidate "$WORK/historical_26897_from_26898" "$WORK/historical_26898_replayed"
 python3 -S verify_26898.py semantics "$WORK/historical_26897_from_26898" "$WORK/historical_26898_replayed"
 python3 -S test_26898_modes.py "$WORK/historical_26898_replayed"
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
 "$compiler" --version | tee "$OUT/26887_glslang_version.txt"
 grep -F '16.5.0' "$OUT/26887_glslang_version.txt" >/dev/null || fail 'glslang version mismatch'
 export IRIS26864_GLSLANG="$compiler";export IRIS26681_SPEKTRA_GLSLANG="$compiler"
 # Inherit exact successful 26864 real SPIR-V post-validation, no substitutions.
 sudo apt-get update -qq
 sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq spirv-tools
 command -v spirv-val >/dev/null && command -v spirv-opt >/dev/null || fail 'real SPIRV-Tools missing'
 spirv-val --version > "$OUT/26887_spirv_tools_version.txt"
 spirv-opt --version >> "$OUT/26887_spirv_tools_version.txt"
 pass 'pinned real glslang 16.5.0 + real SPIRV-Tools toolchain'
}
compile_modified_runtime_shaders(){
 # Exact successful 26871 11 inherited GLES owners + native 58 SPIR-V owners.
 git show "$RUNTIME_AUTHORITY_COMMIT:verify_26864_runtime_glsl.py" > "$WORK/successful_26864_runtime_glsl.py"
 [[ "$(git hash-object "$WORK/successful_26864_runtime_glsl.py")" == 'c5208e94865afbbbc437c31e09fd7b893e50ca20' ]] || fail 'protected historical shader validator drift'
 python3 -S verify_26880_runtime_glsl_scope.py "$WORK/historical_26879_from_26880" "$WORK/historical_26880_from_26881" --compiler "$IRIS26864_GLSLANG" --out "$OUT/26887_runtime_expanded_glsl" | tee "$OUT/26887_gles_shader_proof.txt"
 grep -F 'PASS 26864 GLSL ownership:' "$OUT/26887_gles_shader_proof.txt" >/dev/null || fail 'inherited expanded shader ownership failed'
 python3 -S verify_26867_runtime_shader.py "$WORK/historical_26867_from_26868" --compiler "$IRIS26864_GLSLANG" --out "$OUT/26887_inherited_white_fade" | tee "$OUT/26887_white_fade_glsl.txt"
 grep -F 'pinned-glslang=PASS' "$OUT/26887_white_fade_glsl.txt" >/dev/null || fail 'inherited white fade real compiler missing'
 # The historical 26867 proof is replayed on EXACT 26867 bytes, while the
 # changed 26887 source is separately PINNED-COMPILED (not a static substitute).
 python3 -S verify_26880_highlight_runtime_shader.py "$WORK/historical_26880_from_26881" --compiler "$IRIS26864_GLSLANG" --out "$OUT/26887_current_highlight_compiled" | tee "$OUT/26887_current_highlight_glsl.txt"
 grep -Fx 'PASS 26880 THREE CURRENT HIGHROOM/SMOOTH-WHITE SHADERS REAL GLSL' "$OUT/26887_current_highlight_glsl.txt" >/dev/null || fail 'three changed highlight owners not really compiled'

 python3 -S verify_26868_runtime_shader.py "$WORK/historical_26868_from_26870" --compiler "$IRIS26864_GLSLANG" --out "$OUT/26887_inherited_b_long" | tee "$OUT/26887_inherited_b_long_glsl.txt"
 [[ $(grep -c 'pinned-glslang=PASS' "$OUT/26887_inherited_b_long_glsl.txt") -eq 2 ]] || fail 'inherited two LONG shader compilers failed'
 python3 -S verify_26871_runtime_shader.py "$CAND" --compiler "$IRIS26864_GLSLANG" --out "$OUT/26887_inherited_26871_glsl" | tee "$OUT/26887_inherited_26871_glsl.txt"
 [[ $(grep -c 'pinned-glslang=PASS' "$OUT/26887_inherited_26871_glsl.txt") -eq 4 ]] || fail 'four inherited 26871 GLSL owners failed'
 python3 -S verify_26872_runtime_shader.py "$CAND" --compiler "$IRIS26864_GLSLANG" --out "$OUT/26887_preview_exact_expanded" | tee "$OUT/26887_new_preview_glsl.txt"
 [[ $(grep -c 'pinned-glslang=PASS' "$OUT/26887_new_preview_glsl.txt") -eq 4 ]] || fail 'four new exact runtime-expanded preview GL programs failed pinned compiler'
 python3 -S regressions/26864_glsl_reserved_identifiers.py "$CAND/app"
 python3 -S verify_26880_rawr_shader_universe.py "$WORK/historical_26884_from_26885/app" --compile "$IRIS26864_GLSLANG" \
  --spirv-val "$(command -v spirv-val)" --spirv-opt "$(command -v spirv-opt)" \
  --out "$OUT/26887_all_native_expanded_spirv" | tee "$OUT/26887_spirv_validation.txt"
 grep -F 'PASS 26864 real 58 SPIR-V compute shaders' "$OUT/26887_spirv_validation.txt" >/dev/null || fail 'real inherited native shader compiler proof missing'
 python3 -S verify_26880_native_shaders.py "$CAND" --compiler "$IRIS26864_GLSLANG" \
  --spirv-val "$(command -v spirv-val)" --spirv-opt "$(command -v spirv-opt)" \
  --out "$OUT/26887_original_rawwavelet_spirv" | tee "$OUT/26887_original_rawwavelet_shader_proof.txt"
 grep -Fx 'PASS REAL 26880 FIVE ORIGINAL RAWR WAVELET SPIR-V COMPILERS' "$OUT/26887_original_rawwavelet_shader_proof.txt" >/dev/null || fail '26887 pinned original wavelet shader proof absent'
 sed -i 's#REAL GLSL COMPILE: NOT RUN YET#REAL GLSL COMPILE: PASS (pinned 16.5.0 on expanded GLES300 and 58 exact native Vulkan shaders)#' "$OUT/26902_COMPILER_STATUS.txt"
 sed -i 's#REAL SPIR-V VALIDATION: NOT RUN YET#REAL SPIR-V VALIDATION: PASS (spirv-val pre/post optimized Vulkan 1.1)#' "$OUT/26902_COMPILER_STATUS.txt"
 # IRIS_26887_REGRESSION_ACTIONS_40120907467: the successful inherited
 # prepare_glslang stage already found and verified the PINNED real executable.
 # Do not look up glslangValidator a second time: the official binary can be
 # named "glslang", and its absolute location need not be on PATH.
 [[ -n "${IRIS26864_GLSLANG:-}" && -x "$IRIS26864_GLSLANG" &&
    "$IRIS26864_GLSLANG" == "${IRIS26681_SPEKTRA_GLSLANG:-}" ]] || fail '26887 inherited pinned glslang handle missing or changed'
 export IRIS_PINNED_GLSLANG_VALIDATOR="$IRIS26864_GLSLANG"
 python3 -S verify_26876_expanded_shaders.py "$CAND" || fail '26887 true runtime-expanded GLSL failed inherited pinned compiler'

 python3 -S verify_26881_expanded_glsl.py "$WORK/historical_26881_from_26882" --compiler "$IRIS26864_GLSLANG" --out "$OUT/26887_real_current_glsl" | tee "$OUT/26887_shader_compiler_proof.txt"
 grep -Fx 'PASS 26881 BOTH MODIFIED RUNTIME GLES300 PROGRAMS REAL PINNED GLSL' "$OUT/26887_shader_compiler_proof.txt" >/dev/null || fail '26887 required real changed GLSL compiler proof missing'

 python3 -S verify_26882_expanded_glsl.py "$WORK/historical_26882_from_26883" --compiler "$IRIS26864_GLSLANG" --out "$OUT/26887_real_expanded_white" | tee "$OUT/26887_modified_white_glsl.txt"
 grep -F 'pinned-glslang=PASS' "$OUT/26887_modified_white_glsl.txt" >/dev/null || fail '26887 exact modified native white shader not compiled by pinned real GLSL'
 python3 -S verify_26883_expanded_glsl.py "$WORK/historical_26883_from_26884" --compiler "$IRIS26864_GLSLANG" --out "$OUT/26887_real_shared_white" | tee "$OUT/26887_shared_white_pinned_glsl.txt"
 grep -F 'pinned-glslang=PASS' "$OUT/26887_shared_white_pinned_glsl.txt" >/dev/null || fail '26887 modified expanded shared HDRq/Wronski B highlight shader not compiled by pinned real glslang'
 python3 -S verify_26884_expanded_glsl.py "$WORK/historical_26884_from_26885" --compiler "$IRIS26864_GLSLANG" --out "$OUT/26887_real_rawr_off_fused_wb" | tee "$OUT/26887_rawr_off_pinned_glsl.txt"
 grep -F 'pinned-glslang=PASS' "$OUT/26887_rawr_off_pinned_glsl.txt" >/dev/null || fail '26887 original RAWR OFF fused WB GLSL not compiled by pinned real glslang'

 python3 -S verify_26887_expanded_glsl.py "$WORK/historical_26887_replayed" --compiler "$IRIS26864_GLSLANG" --spirv-val "$(command -v spirv-val)" --spirv-opt "$(command -v spirv-opt)" --out "$OUT/26887_modified_shader_spirv" | tee "$OUT/26887_modified_shader_compile_receipt.txt"
 grep -F 'PASS pinned REAL glslang 16.5.0/spirv-val/spirv-opt 11 compiled 26887 shader variants' "$OUT/26887_modified_shader_compile_receipt.txt" >/dev/null || fail '26887 current shader real GLSL/SPIR-V proof missing'
 python3 -S regressions/26885_actions_40604341240_historical_scope.py "$WORK/historical_26884_from_26885" "$WORK/historical_26885_from_26886" "$ROOT/build_26885_iris_rawr.sh"
 python3 -S regressions/26885_chroma_controls.py "$WORK/historical_26885_from_26886" "$WORK/historical_26884_from_26885"
 python3 -S verify_26885_expanded_glsl.py "$WORK/historical_26885_from_26886" --compiler "$IRIS26864_GLSLANG" --spirv-val "$(command -v spirv-val)" --spirv-opt "$(command -v spirv-opt)" --out "$OUT/26887_historical_26885_chroma_spirv"
 python3 -S regressions/26886_historical_scope_all_stages.py "$WORK/historical_26884_from_26885" "$WORK/historical_26885_from_26886" "$WORK/historical_26886_from_26887" "$ROOT/build_26885_iris_rawr.sh" "$ROOT/build_26886_iris_rawr.sh"
 python3 -S verify_26886_candidate.py "$WORK/historical_26885_from_26886" "$WORK/historical_26886_from_26887"
 python3 -S verify_26886_semantics.py "$WORK/historical_26885_from_26886" "$WORK/historical_26886_from_26887"
 python3 -S verify_26886_expanded_glsl.py "$WORK/historical_26886_from_26887"
 python3 -S - "$OUT/26887_modified_shader_spirv" <<'PY_26887_SHADER_RECEIPT'
import hashlib,pathlib,sys
p=pathlib.Path(sys.argv[1]); m=p/'26887_REAL_COMPILED_SHADER_SHA256.txt'
assert m.is_file(),('26887 real compiler manifest missing',m)
lines=m.read_text().splitlines()
assert len(lines)==11,('26887 wrong number of compiled shader variants',len(lines))
names=set()
for line in lines:
 h,sep,name=line.partition('  ')
 assert sep=='  ' and len(h)==64 and all(c in '0123456789abcdef' for c in h)
 assert name not in names and name.endswith('.spv') and '/' not in name and '..' not in name,(name,'duplicate or unsafe path')
 names.add(name); b=(p/name).read_bytes()
 assert len(b)>=84 and b[:4]==bytes.fromhex('03022307'),('26887 invalid SPIR-V',name)
 assert hashlib.sha256(b).hexdigest()==h,('26887 compiled SPIR-V hash drift',name)
assert len(list(p.glob('*.spv')))==11,('26887 additional/untracked SPIR-V')
print('PASS 26887 B ON actual pinned compiler receipt: 11 unique SPIR-V variants and byte-matched SHA-256')
PY_26887_SHADER_RECEIPT
 python3 -S verify_26888_expanded_glsl.py "$WORK/historical_26888_replayed" --compiler "$IRIS26864_GLSLANG" --spirv-val "$(command -v spirv-val)" --spirv-opt "$(command -v spirv-opt)" --out "$OUT/26888_modified_shader_spirv" | tee "$OUT/26888_real_shader_compile_receipt.txt"
 grep -Fx 'PASS pinned REAL glslang 16.5.0/spirv-val/spirv-opt 5 compiled 26888 shader variants' "$OUT/26888_real_shader_compile_receipt.txt" >/dev/null || fail '26888 real modified runtime GLSL compiler receipts missing'
 python3 -S - "$OUT/26888_modified_shader_spirv" <<'PY_26888_SHADER_RECEIPT'
import hashlib,pathlib,sys
p=pathlib.Path(sys.argv[1]);m=p/'26888_REAL_COMPILED_SHADER_SHA256.txt'
assert m.is_file()
lines=m.read_text().splitlines();assert len(lines)==5
assert len(list(p.glob('*.spv')))==5
for ln in lines:
 h,n=ln.split('  ',1);b=(p/n).read_bytes()
 assert len(b)>80 and b[:4]==bytes.fromhex('03022307')
 assert hashlib.sha256(b).hexdigest()==h
print('PASS 26888 exact five SPIR-V receipts')
PY_26888_SHADER_RECEIPT
 python3 -S verify_26889_expanded_glsl.py "$WORK/historical_26889_replayed" --compiler "$IRIS26864_GLSLANG" --spirv-val "$(command -v spirv-val)" --spirv-opt "$(command -v spirv-opt)" --out "$OUT/26889_modified_shader_spirv" | tee "$OUT/26889_real_shader_compile_receipt.txt"
 test -s "$OUT/26889_modified_shader_spirv/26889_REAL_COMPILED_SHADER_SHA256.txt" || fail '26889 real compiled SPIR-V receipts missing'
 sed -i 's/REAL GLSL COMPILE: NOT RUN YET/REAL GLSL COMPILE: PASS/' "$OUT/26902_COMPILER_STATUS.txt"
 sed -i 's/REAL SPIR-V VALIDATION: NOT RUN YET/REAL SPIR-V VALIDATION: PASS/' "$OUT/26902_COMPILER_STATUS.txt"
 python3 -S verify_26890_expanded_glsl.py "$WORK/historical_26890_replayed" --compiler "$IRIS26864_GLSLANG" --out "$OUT/26902_three_current_expanded_gles" | tee "$OUT/26902_real_modified_gles_compile.txt"
 grep -Fx 'PASS 26890 all THREE current exact runtime-expanded GLES fragment programs REAL PINNED COMPILE' "$OUT/26902_real_modified_gles_compile.txt" >/dev/null || fail '26890 real pinned B/SDR/UHDR tone GLSL compiler proof missing'
 python3 -S verify_26889_expanded_glsl.py "$CAND" --compiler "$IRIS26864_GLSLANG" --spirv-val "$(command -v spirv-val)" --spirv-opt "$(command -v spirv-opt)" --out "$OUT/26902_strength115_real_spirv" | tee "$OUT/26902_strength115_real_compiler_receipt.txt"
 grep -Fx 'PASS 26889 pinned REAL glslang/SPIR-V 3 modified native variants + original ESSL300 LONG' "$OUT/26902_strength115_real_compiler_receipt.txt" >/dev/null || fail '26890 changed B/OFF strength115 GLSL/SPIRV real compiler proof missing'
 python3 -S verify_26891_expanded_glsl.py "$WORK/historical_26891_replayed" --compiler "$IRIS26864_GLSLANG" --out "$OUT/26902_current_reverted_tone_GLES" | tee "$OUT/26902_current_reverted_tone_compiler_receipt.txt"
 grep -Fx 'PASS 26891 THREE current reverted 26889 tone GLES310 REAL PINNED COMPILE' "$OUT/26902_current_reverted_tone_compiler_receipt.txt" >/dev/null || fail '26891 current tone GLSL real compiler missing'
 python3 -S verify_26892_expanded_glsl.py "$WORK/historical_26892_replayed" --compiler "$IRIS26864_GLSLANG" --out "$OUT/26902_scene_sdr_exact_essl310" | tee "$OUT/26902_scene_sdr_pinned_glsl.txt"
 grep -Fx 'PASS 26892 TWO exact changed render+gainmap ESSL310 programs; REAL PINNED COMPILE PASS' "$OUT/26902_scene_sdr_pinned_glsl.txt" >/dev/null || fail '26892 actual changed GLES render+gainmap not pinned compiled'
 python3 -S verify_26893_expanded_glsl.py "$WORK/historical_26893_replayed" --compiler "$IRIS26864_GLSLANG" --out "$OUT/26902_actual_modified_sdr_essl310" | tee "$OUT/26902_real_sdr_gles_compiler_receipt.txt"
 grep -Fx 'PASS 26893 TWO exact changed render+gainmap ESSL310 programs; REAL PINNED COMPILE PASS' "$OUT/26902_real_sdr_gles_compiler_receipt.txt" >/dev/null || fail '26893 modified shader REAL PINNED compile missing'
 python3 -S verify_26894.py shader "$WORK/historical_26894_replayed" --compiler "$IRIS26864_GLSLANG" --out "$OUT/26902_real_expanded_essl310" | tee "$OUT/26902_REAL_CHANGED_SHADER_RECEIPT.txt"
 grep -Fx 'PASS 26894 THREE exact modified GLES310 runtime programs REAL PINNED COMPILE PASS' "$OUT/26902_REAL_CHANGED_SHADER_RECEIPT.txt" >/dev/null || fail '26894 THREE actual modified shaders NOT pinned compiled'
 python3 -S verify_26895.py shader "$WORK/historical_26895_replayed" --compiler "$IRIS26864_GLSLANG" --out "$OUT/26902_reverted_26893_GLES310" | tee "$OUT/26902_RESTORED_SHADER_COMPILER_RECEIPT.txt"
 grep -Fx 'PASS 26895 TWO exact restored 26893 GLES310 runtime programs REAL PINNED COMPILE PASS' "$OUT/26902_RESTORED_SHADER_COMPILER_RECEIPT.txt" >/dev/null || fail '26895 actual two restored shaders did not pass exact real pinned compiler'
 (cd "$WORK/historical_26897_replayed" && sha256sum -c "$ROOT/26897_UNCHANGED_PROTECTED.sha256" >/dev/null) || fail '26897 current unchanged shaders/protected source differs before real pinned compilers'
 # 26898 changes NO ESSL/GLSL SPIR-V shader bytes. The inherited exact
 # successful 26897 compiler matrix above still executes unmodified.
 (cd "$WORK/historical_26898_replayed" && sha256sum -c "$ROOT/26898_UNCHANGED_PROTECTED.sha256" >/dev/null) || fail '26898 shader and DNG protected source changed'
 mkdir -p "$OUT/26902_real_expanded_essl310"
 local S99="$WORK/historical_26899_replayed/app/src/main/assets/shaders/motionv2/iris26899_b_off_zoom_luma_sharpen.glsl"
 local E99="$OUT/26902_real_expanded_essl310/iris26899_b_off_zoom_luma_sharpen.frag"
 test -s "$S99" || fail '26899 actual new shader missing'
 { printf '#version 310 es\n\n#line 1\n';cat "$S99"; } > "$E99"
 if grep -En '(^|[^[:alnum:]_])(sample|input|output|common|filter)([^[:alnum:]_]|$)' "$E99" | grep -vE '^[[:digit:]]+:[[:space:]]*//';then fail 'reserved current shader identifier/token';fi
 "$IRIS26864_GLSLANG" -S frag "$E99" > "$OUT/26899_HISTORICAL_GLSLANG_16_5_0.txt" 2>&1 || fail '26899 real PINNED GLES310 shader compile FAILED'
 sha256sum "$E99" "$S99" > "$OUT/26899_HISTORICAL_NEW_SHADER_SHA256.txt"
 echo 'PASS 26899 REAL PINNED GLSLANG 16.5.0 ESSL310 new two-scale luminance shader compile' | tee -a "$OUT/26899_HISTORICAL_GLSLANG_16_5_0.txt"
 python3 -S verify_26899.py semantics "$WORK/historical_26898_from_26899" "$WORK/historical_26899_replayed"
 mkdir -p "$OUT/26900_historical_exact_real_essl310"
 # The two modified shader sources are really compiled BEFORE Kotlin/Gradle,
 # with the actual runtime #version 310 es and #line 1 injection.
 for name in render iris26899_b_off_zoom_luma_sharpen;do
   local S="$WORK/historical_26900_replayed/app/src/main/assets/shaders/motionv2/$name.glsl"
   local E="$OUT/26900_historical_exact_real_essl310/$name.frag"
   { printf '#version 310 es\n\n#line 1\n';cat "$S"; } > "$E"
   python3 -S verify_26900.py shader "$E"
   "$IRIS26864_GLSLANG" -S frag "$E" > "$OUT/26900_HISTORICAL_GLSLANG_${name}.txt" 2>&1 || fail "26900 real PINNED GLSLANG 16.5.0 ESSL310 compile failed: $name"
   sha256sum "$E" "$S" >> "$OUT/26900_HISTORICAL_NEW_SHADER_SHA256.txt"
 done
 echo 'PASS 26900 TWO EXACT runtime-expanded ESSL310 shaders REAL PINNED GLSLANG 16.5.0' | tee "$OUT/26900_HISTORICAL_GLSL_REAL_COMPILER_RECEIPT.txt"
 python3 -S verify_26900.py semantics "$WORK/historical_26899_from_26900" "$WORK/historical_26900_replayed"
 mkdir -p "$OUT/26901_historical_exact_real_essl310"
 for name in render iris26899_b_off_zoom_luma_sharpen;do
   local S="$WORK/historical_26901_replayed/app/src/main/assets/shaders/motionv2/$name.glsl"
   local E="$OUT/26901_historical_exact_real_essl310/$name.frag"
   { printf '#version 310 es\n\n#line 1\n';cat "$S"; } > "$E"
   python3 -S verify_26901.py shader "$E"
   "$IRIS26864_GLSLANG" -S frag "$E" > "$OUT/26901_HISTORICAL_GLSLANG_${name}.txt" 2>&1 || fail "26901 real PINNED GLSLANG 16.5.0 ESSL310 compile failed: $name"
   sha256sum "$E" "$S" >> "$OUT/26901_HISTORICAL_NEW_SHADER_SHA256.txt"
 done
 echo 'PASS 26901 TWO EXACT runtime-expanded ESSL310 shaders REAL PINNED GLSLANG 16.5.0' | tee "$OUT/26901_HISTORICAL_GLSL_REAL_COMPILER_RECEIPT.txt"
 python3 -S verify_26901.py semantics "$WORK/historical_26900_from_26901" "$WORK/historical_26901_replayed"
 mkdir -p "$OUT/26902_exact_real_essl310"
 local S02="$CAND/app/src/main/assets/shaders/motionv2/iris26899_b_off_zoom_luma_sharpen.glsl"
 local E02="$OUT/26902_exact_real_essl310/iris26899_b_off_zoom_luma_sharpen.frag"
 { printf '#version 310 es\n\n#line 1\n';cat "$S02"; } > "$E02"
 python3 -S verify_26902.py shader "$E02"
 "$IRIS26864_GLSLANG" -S frag "$E02" > "$OUT/26902_GLSLANG_iris26899_b_off_zoom_luma_sharpen.txt" 2>&1 || fail '26902 actual runtime-expanded shader must PASS pinned glslang 16.5.0'
 sha256sum "$E02" "$S02" > "$OUT/26902_NEW_SHADER_SHA256.txt"
 echo 'PASS 26902 EXACT runtime-expanded ESSL310 shader REAL PINNED GLSLANG 16.5.0' | tee "$OUT/26902_CURRENT_GLSL_REAL_COMPILER_RECEIPT.txt"
 python3 -S verify_26902.py semantics "$BASE" "$CAND"
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
 ./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace 2>&1 | tee "$OUT/26902_gradle_language_compilers.log"
 snapshot_live_authority_seeded "$POST_LANG";diff -qr "$CAND/app" "$POST_LANG/app" >/dev/null || fail 'language compilers changed source'
 sed -i 's/REAL KOTLIN COMPILE: NOT RUN YET/REAL KOTLIN COMPILE: PASS/' "$OUT/26902_COMPILER_STATUS.txt"
 sed -i 's/REAL JAVA COMPILE: NOT RUN YET/REAL JAVA COMPILE: PASS/' "$OUT/26902_COMPILER_STATUS.txt"
 pass 'real project Kotlin and Java compilers on frozen candidate'
}
verify_native_glslang_handoff(){
 [[ -n "${IRIS26864_GLSLANG:-}" && -x "$IRIS26864_GLSLANG" && "$IRIS26864_GLSLANG" == "$IRIS26681_SPEKTRA_GLSLANG" ]] || fail 'pinned real GLSL compiler handoff lost'
 command -v spirv-val >/dev/null && command -v spirv-opt >/dev/null || fail 'SPIR-V validator unavailable to NDK'
 pass 'same pinned real compiler handed to NDK shader subprojects'
}
compile_native(){
 ./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace 2>&1 | tee "$OUT/26902_gradle_native_compiler.log"
 snapshot_live_authority_seeded "$WORK/post_native_snapshot"
 diff -qr "$CAND/app" "$WORK/post_native_snapshot/app" >/dev/null || fail 'native compiler changed source'
 sed -i 's#NATIVE/NDK COMPILE: NOT RUN YET#NATIVE/NDK COMPILE: PASS (arm64-v8a + armeabi-v7a; real 58 inherited + 5 original RAWR wavelet pinned shader compilation)#' "$OUT/26902_COMPILER_STATUS.txt"
 pass 'real 2-ABI NDK compiler with authentic RAWR Vulkan sources'
}
verify_candidate_patches(){
 python3 -S verify_26891_candidate.py "$WORK/historical_26890_from_26891" "$WORK/historical_26891_replayed"
 python3 -S verify_26891_semantics.py "$WORK/historical_26890_from_26891" "$WORK/historical_26891_replayed"
 python3 -S verify_26891_patches.py "$WORK/historical_26890_from_26891" "$WORK/historical_26891_replayed" 26891_FORWARD_FULL_INDEX.patch 26891_ROLLBACK_FULL_INDEX.patch | tee "$OUT/26902_patch_validation.txt"
 python3 -S test_26889_negative_tamper.py "$WORK/historical_26888_from_26889" "$WORK/historical_26889_replayed"
 pass '26889 original negative tamper on historical bytes, 26893 4-path full-index forward/rollback 7/12/40'
 python3 -S test_26891_negative_tamper.py "$WORK/historical_26890_from_26891" "$WORK/historical_26891_replayed"
 python3 -S test_26890_tone_math.py
 python3 -S verify_26890_candidate.py "$WORK/historical_26889_from_26890" "$WORK/historical_26890_replayed"
 python3 -S test_26890_negative_tamper.py "$WORK/historical_26889_from_26890" "$WORK/historical_26890_replayed"
 python3 -S verify_26892_candidate.py "$WORK/historical_26891_from_26892" "$WORK/historical_26892_replayed"
 python3 -S verify_26892_semantics.py "$WORK/historical_26891_from_26892" "$WORK/historical_26892_replayed"
 python3 -S verify_26892_patches.py "$WORK/historical_26891_from_26892" "$WORK/historical_26892_replayed" 26892_FORWARD_FULL_INDEX.patch 26892_ROLLBACK_FULL_INDEX.patch | tee "$OUT/26902_patch_validation.txt"
 python3 -S test_26892_negative_tamper.py "$WORK/historical_26891_from_26892" "$WORK/historical_26892_replayed"
 python3 -S test_26892_tone_math.py
 python3 -S verify_26893_candidate.py "$WORK/historical_26892_from_26893" "$WORK/historical_26893_replayed"
 python3 -S verify_26893_semantics.py "$WORK/historical_26892_from_26893" "$WORK/historical_26893_replayed"
 python3 -S verify_26893_patches.py "$WORK/historical_26892_from_26893" "$WORK/historical_26893_replayed" 26893_FORWARD_FULL_INDEX.patch 26893_ROLLBACK_FULL_INDEX.patch | tee "$OUT/26902_patch_validation.txt"
 python3 -S test_26893_negative_tamper.py "$WORK/historical_26892_from_26893" "$WORK/historical_26893_replayed"
 python3 -S test_26893_tone_math.py
 python3 -S verify_26894.py candidate "$WORK/historical_26893_from_26894" "$WORK/historical_26894_replayed"
 python3 -S verify_26894.py semantics "$WORK/historical_26893_from_26894" "$WORK/historical_26894_replayed"
 python3 -S verify_26894.py tone
 python3 -S verify_26894.py patch "$WORK/historical_26893_from_26894" "$WORK/historical_26894_replayed" 26894_FORWARD_FULL_INDEX.patch 26894_ROLLBACK_FULL_INDEX.patch | tee "$OUT/26902_PATCH_VALIDATION.txt"
 python3 -S verify_26894.py tamper "$WORK/historical_26893_from_26894" "$WORK/historical_26894_replayed"
 python3 -S verify_26895.py candidate "$WORK/historical_26894_from_26895" "$WORK/historical_26895_replayed"
 python3 -S verify_26895.py semantics "$WORK/historical_26894_from_26895" "$WORK/historical_26895_replayed"
 python3 -S verify_26895.py patch "$WORK/historical_26894_from_26895" "$WORK/historical_26895_replayed" 26895_FORWARD_FULL_INDEX.patch 26895_ROLLBACK_FULL_INDEX.patch | tee "$OUT/26902_PATCH_VALIDATION.txt"
 python3 -S verify_26895.py tamper "$WORK/historical_26894_from_26895" "$WORK/historical_26895_replayed"
 python3 -S verify_26897.py candidate "$WORK/historical_26895_from_26897" "$WORK/historical_26897_replayed"
 python3 -S verify_26897.py semantics "$WORK/historical_26895_from_26897" "$WORK/historical_26897_replayed"
 python3 -S verify_26897.py patch "$WORK/historical_26895_from_26897" "$WORK/historical_26897_replayed" 26897_FORWARD_FULL_INDEX.patch 26897_ROLLBACK_FULL_INDEX.patch | tee "$OUT/26902_PATCH_VALIDATION.txt"
 python3 -S verify_26897.py tamper "$WORK/historical_26895_from_26897" "$WORK/historical_26897_replayed"
 python3 -S verify_26898.py candidate "$WORK/historical_26897_from_26898" "$WORK/historical_26898_replayed"
 python3 -S verify_26898.py semantics "$WORK/historical_26897_from_26898" "$WORK/historical_26898_replayed"
 python3 -S verify_26898.py patch "$WORK/historical_26897_from_26898" "$WORK/historical_26898_replayed" 26898_FORWARD_FULL_INDEX.patch 26898_ROLLBACK_FULL_INDEX.patch | tee "$OUT/26898_HISTORICAL_PATCH_PROOF.txt"
 python3 -S verify_26898.py tamper "$WORK/historical_26897_from_26898" "$WORK/historical_26898_replayed"
 python3 -S verify_26899.py candidate "$WORK/historical_26898_from_26899" "$WORK/historical_26899_replayed"
 python3 -S verify_26899.py semantics "$WORK/historical_26898_from_26899" "$WORK/historical_26899_replayed"
 python3 -S verify_26899.py patch "$WORK/historical_26898_from_26899" "$WORK/historical_26899_replayed" 26899_FORWARD_FULL_INDEX.patch 26899_ROLLBACK_FULL_INDEX.patch | tee "$OUT/26899_HISTORICAL_PATCH_PROOF.txt"
 python3 -S verify_26899.py tamper "$WORK/historical_26898_from_26899" "$WORK/historical_26899_replayed"
 python3 -S verify_26900.py candidate "$WORK/historical_26899_from_26900" "$WORK/historical_26900_replayed"
 python3 -S verify_26900.py semantics "$WORK/historical_26899_from_26900" "$WORK/historical_26900_replayed"
 python3 -S verify_26900.py patch "$WORK/historical_26899_from_26900" "$WORK/historical_26900_replayed" 26900_FORWARD_FULL_INDEX.patch 26900_ROLLBACK_FULL_INDEX.patch | tee "$OUT/26900_HISTORICAL_PATCH_PROOF.txt"
 python3 -S verify_26900.py tamper "$WORK/historical_26899_from_26900" "$WORK/historical_26900_replayed"
 python3 -S verify_26901.py candidate "$WORK/historical_26900_from_26901" "$WORK/historical_26901_replayed"
 python3 -S verify_26901.py semantics "$WORK/historical_26900_from_26901" "$WORK/historical_26901_replayed"
 python3 -S verify_26901.py patch "$WORK/historical_26900_from_26901" "$WORK/historical_26901_replayed" 26901_FORWARD_FULL_INDEX.patch 26901_ROLLBACK_FULL_INDEX.patch | tee "$OUT/26901_HISTORICAL_PATCH_PROOF.txt"
 python3 -S verify_26901.py tamper "$WORK/historical_26900_from_26901" "$WORK/historical_26901_replayed"
 python3 -S verify_26902.py candidate "$BASE" "$CAND"
 python3 -S verify_26902.py semantics "$BASE" "$CAND"
 python3 -S verify_26902.py patch "$BASE" "$CAND" 26902_FORWARD_FULL_INDEX.patch 26902_ROLLBACK_FULL_INDEX.patch | tee "$OUT/26902_CURRENT_PATCH_PROOF.txt"
 python3 -S verify_26902.py tamper "$BASE" "$CAND"
}
prebuild_safety(){
 snapshot_live_authority_seeded "$WORK/prebuild_live_snapshot"
 diff -qr "$CAND/app" "$WORK/prebuild_live_snapshot/app" >/dev/null || fail 'frozen compiled candidate versus canonical authority-seeded live mismatch'
 python3 -S verify_26891_candidate.py "$WORK/historical_26890_from_26891" "$WORK/historical_26891_replayed"
 (cd "$WORK/historical_26891_replayed" && sha256sum -c "$ROOT/26891_UNCHANGED_PROTECTED.sha256" >/dev/null) || fail 'protected DNG/vendor/preview/native file invariance failed'
 for k in 'REAL GLSL COMPILE: PASS' 'REAL SPIR-V VALIDATION: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS';do
  grep -F "$k" "$OUT/26902_COMPILER_STATUS.txt" >/dev/null || fail "mandatory prebuild compiler gate missing $k"
 done
 cat > "$OUT/26902_PREBUILD_SAFETY.txt" <<EOF_SAFETY
PRE-BUILD SAFETY PROOF PASSED
runtime_authority=successful 26901 $RUNTIME_AUTHORITY_COMMIT run $RUNTIME_ACTIONS_RUN artifact $RUNTIME_ARTIFACT_ID
verification_mechanics=EXACT successful 26901 executed 17 stages, real compiler/NDK/assemble commands
runtime_changed_files=3 modified existing, 2023 protected; B OFF lens-local strength/radius correction, full RGB bicubic unchanged
infrastructure_delta=one strict successor workflow/trigger + source validators; exact successful 26901 inherited 17-stage compiler+freeze+assemble mechanics
prior_files=2026
candidate_files=2026
version_name=$VERSION_NAME
version_build=$VERSION_BUILD
real_compilers=GLSL+SPIR-V+Kotlin+Java+NDK 2 ABI PASS
patch_proof=full-index forward/rollback 7/12/40 fuzz 0 exact
protected_source=2023 files byte-identical to successful 26901 compiled candidate; DNG/native/vendor/A/Night/LONG/UHDR protected
EOF_SAFETY
 pass 'PRE-BUILD SAFETY PROOF PASSED'
 python3 -S verify_26892_candidate.py "$WORK/historical_26891_from_26892" "$WORK/historical_26892_replayed"
 python3 -S verify_26892_semantics.py "$WORK/historical_26891_from_26892" "$WORK/historical_26892_replayed"
 (cd "$WORK/historical_26892_replayed" && sha256sum -c "$ROOT/26892_UNCHANGED_PROTECTED.sha256" >/dev/null) || fail '26892 2021 protected sources modified'
 test -s "$OUT/26902_scene_sdr_pinned_glsl.txt" && grep -F 'REAL PINNED COMPILE PASS' "$OUT/26902_scene_sdr_pinned_glsl.txt" >/dev/null || fail '26892 changed shaders MUST be compiled BEFORE build'
 cat >> "$OUT/26902_PREBUILD_SAFETY.txt" <<'EOF_26892_SAFETY'
26892_exact_successful_26891_compiled_TAR=0541b1c0324f74dca4295d956cd94148e1aa71212f621657618a707ac59d6aff
26892_actual_successful_26891_runner=f0b25de61cc661a461c10e7665623ba15ddda0362ba047c05e543aaf670f094b
26892_scope=4 existing B-SR-OFF SDR presentation/runtime files, 2021 original protected, 0 added/deleted
26892_contrast=no independent midtone/saturation increase; UHDR gainmap source-matched
26892_compile=real PINNED shader, Kotlin, Java, Android native+NDK required
EOF_26892_SAFETY
 python3 -S verify_26893_candidate.py "$WORK/historical_26892_from_26893" "$WORK/historical_26893_replayed"
 python3 -S verify_26893_semantics.py "$WORK/historical_26892_from_26893" "$WORK/historical_26893_replayed"
 (cd "$WORK/historical_26893_replayed" && sha256sum -c "$ROOT/26893_UNCHANGED_PROTECTED.sha256" >/dev/null) || fail '26893 original 2021 protected source mismatch'
 test -s "$OUT/26902_real_sdr_gles_compiler_receipt.txt" && grep -F 'REAL PINNED COMPILE PASS' "$OUT/26902_real_sdr_gles_compiler_receipt.txt" >/dev/null || fail '26893 changed shader compiler gate NOT PASSED'
 cat >> "$OUT/26902_PREBUILD_SAFETY.txt" <<'EOF_26893_SAFETY'
26893_exact_successful_26892_compiled_candidate_TAR=ff4bdf32e5e60d2434eae06887e45e776b2d5727db6ee7e16a4a59404f47e8b9
26893_exact_successful_executed_26892_runner=37b12a9cbb5918b49d279d40d51f11fa086a0682dd487f88b6ecc7f17313069d
26893_runtime_scope=4 modified existing B-off SDR presentation owner source files; 2021 protected, zero add/delete
26893_reference_calibration=12 actual captured scenes, balanced garden angles preserve, backlit sky-safe, rose darken-only
26893_compiler=PINNED GLSL, Kotlin, Java, full native both ABIs + full assemble required
EOF_26893_SAFETY
 python3 -S verify_26894.py candidate "$WORK/historical_26893_from_26894" "$WORK/historical_26894_replayed"
 python3 -S verify_26894.py semantics "$WORK/historical_26893_from_26894" "$WORK/historical_26894_replayed"
 (cd "$WORK/historical_26894_replayed" && sha256sum -c "$ROOT/26894_UNCHANGED_PROTECTED.sha256" >/dev/null) || fail '26894 protected source changed'
 test -s "$OUT/26902_REAL_CHANGED_SHADER_RECEIPT.txt" && grep -Fx 'PASS 26894 THREE exact modified GLES310 runtime programs REAL PINNED COMPILE PASS' "$OUT/26902_REAL_CHANGED_SHADER_RECEIPT.txt" >/dev/null || fail '26894 real changed GLSL compilation mandatory before APK'
 cat >> "$OUT/26902_PREBUILD_SAFETY.txt" <<'EOF_26894_SAFETY'
26894_exact_successful_26893_compiled_candidate_TAR=56c216da6a3fe895fed5eea04e70b3eaf4d3b7c534b6a89ba48d071e85c65d3b
26894_actual_executed_successful_26893_runner=9a70b375fd5f0a1e5148cef7e4640b4014fe0a24d8e5f38fcada15bbc0713956
26894_runtime=2025 to 2026 files, four modified existing + one added shader, 2021 immutable protected
26894_geometry=one B-SR-OFF 32px grid RG16F source guide, 4x4 local means, no CPU stalls, shared SDR UHDR
26894_regressions=actual 26891 garden shots3/4/2, 26892 garden, 26893 sun houses+flowers+road
26894_compiler_mandatory=three expanded GLES310 real pinned, Kotlin+Java, NDK two ABIs, full assemble
EOF_26894_SAFETY
 python3 -S verify_26895.py candidate "$WORK/historical_26894_from_26895" "$WORK/historical_26895_replayed"
 python3 -S verify_26895.py semantics "$WORK/historical_26894_from_26895" "$WORK/historical_26895_replayed"
 (cd "$WORK/historical_26895_replayed" && sha256sum -c "$ROOT/26895_UNCHANGED_PROTECTED.sha256" >/dev/null) || fail '26895 restored 26893 protected source drift'
 test -s "$OUT/26902_RESTORED_SHADER_COMPILER_RECEIPT.txt" && grep -Fx 'PASS 26895 TWO exact restored 26893 GLES310 runtime programs REAL PINNED COMPILE PASS' "$OUT/26902_RESTORED_SHADER_COMPILER_RECEIPT.txt" >/dev/null || fail '26895 final restored GLES310 real pinned compile mandatory'
 test "$(grep -Fc 'VERSION_BUILD=26895' "$WORK/historical_26895_replayed/app/version.properties")" -eq 1 || fail '26895 wrong version before assemble'
 cat >> "$OUT/26902_PREBUILD_SAFETY.txt" <<'EOF_26895_SAFETY'
26895_exact_successful_26894_runtime_TAR=3051678a91741a07ac4aa8829d35bd2de135b1c6a69b2dff7d5a55ada1e139db
26895_actual_successful_26894_runner=1f9dcc045b6ca5fa8928443dcc28b98907b7fad152546d802445b74207244be6
26895_runtime=26894 compiled 2026 to 26895 2025 files; EXACT 26893 runtime except Java saturation and version
26895_saturation=Iris per-lens 1.00 UI -> 1.14 effective; equals old 26893 1.20 UI * 0.95; Night unchanged
26895_26894_spatial_scene=DELETED; 26894 visual corrections fully reverted
26895_protected=2021 source hashes unchanged; 2 modified restored shaders REAL pinned compiled; actual Kotlin Java NDK and full assemble mandatory
EOF_26895_SAFETY
 python3 -S verify_26897.py candidate "$WORK/historical_26895_from_26897" "$WORK/historical_26897_replayed"
 python3 -S verify_26897.py semantics "$WORK/historical_26895_from_26897" "$WORK/historical_26897_replayed"
 (cd "$WORK/historical_26897_replayed" && sha256sum -c "$ROOT/26897_UNCHANGED_PROTECTED.sha256" >/dev/null) || fail '26897 protected prebuild source invariant failure'
 test "$(grep -Fc 'VERSION_BUILD=26897' "$WORK/historical_26897_replayed/app/version.properties")" -eq 1 || fail '26897 wrong version before assemble'
 test -s "$OUT/26902_PATCH_VALIDATION.txt" || fail '26897 real four-operand current patch proof required'
 cat >> "$OUT/26902_PREBUILD_SAFETY.txt" <<'EOF_26897_SAFETY'
26897_actual_successful_26895_compiled_TAR=9df70bdc87756847b7c5a479cb3b22fee7a47920ac277a70d14a5402e3cb6942
26897_successful_26895_runner_SHA=a6c341d9389887329a55545c78c5c25e727655fbae73ccedc2c353d321165b2b
26897_runtime=2025 source files, 3 modified, 2022 protected, zero additions/deletions
26897_no_scope=Spektra, Motion B native Wiener/GL and A/Night protected, no source changes to DNG writer
26897_save=early one-time DNG writer, zero duplicate post-B publication, B JPEG still independent
26897_dng=independent Sabre-normalized16 DNG saved before B JNI; RAW-only and JPEG+DNG both own DNG completion; A/Night unchanged
26897_compiler_gate=current Java/Kotlin/native+NDK ABIs mandatory; GLSL/native/A/Night/DNG writer protected byte-identical to 26895
26897_device_verification=NOT RUN - device must confirm RAW-only and JPEG+DNG files, including B error condition
EOF_26897_SAFETY
 python3 -S verify_26898.py candidate "$WORK/historical_26897_from_26898" "$WORK/historical_26898_replayed"
 python3 -S verify_26898.py semantics "$WORK/historical_26897_from_26898" "$WORK/historical_26898_replayed"
 (cd "$WORK/historical_26898_replayed" && sha256sum -c "$ROOT/26898_UNCHANGED_PROTECTED.sha256" >/dev/null) || fail '26898 frozen protected source changed before APK'
 test "$(grep -Fc 'VERSION_BUILD=26898' "$WORK/historical_26898_replayed/app/version.properties")" -eq 1 || fail '26898 incorrect version'
 test -s "$OUT/26899_HISTORICAL_PATCH_PROOF.txt" || fail '26898 actual patch verification not executed'
 cat >> "$OUT/26902_PREBUILD_SAFETY.txt" <<'EOF_26898_SAFETY'
26898_parent_run=41568669521
26898_parent_commit=217fe8ca9d63b6c144af5a8197dd0adc0025eecb
26898_parent_artifact=13200518421
26898_parent_compiled_tar_sha256=23462eec3c2d03b55f97cdb63b686ea9133a4d5f9e50e9ffa0a26ba8a13eebe6
26898_exact_executed_parent_runner_sha256=1a0b521c75e12003e0ab31e91bbe9ab8ae9c85b261ba8988ed37cf2e4cfc8dd3
26898_current_source=2025 files, 5 intentional changes, 2020 protected, no adds/deletes
26898_change_scope=Motion B optional Sabre DNG isolated no-share EGL and true DNG-only early exit; B GL detailed stage diagnostics
26898_protected=original Sabre DNG reconstruction, DNG writers/metadata, A, Night, LONG, Spektra, B HDRq/AMaZE math/GLSL/Vulkan executor, frame counts, color, DNG, UHDR
26898_compile=real pinned GLSL SPIRV Kotlin Java NDK two ABIs full assembly required
26898_device_outcome=NOT TESTED in Actions; installed-device JPG-only, DNG-only, JPG+DNG and A/Night proof mandatory
EOF_26898_SAFETY
 test -s "$OUT/26899_HISTORICAL_GLSLANG_16_5_0.txt" && grep -Fx 'PASS 26899 REAL PINNED GLSLANG 16.5.0 ESSL310 new two-scale luminance shader compile' "$OUT/26899_HISTORICAL_GLSLANG_16_5_0.txt" >/dev/null || fail '26899 current shader real pinned compiler proof missing'
 python3 -S verify_26899.py candidate "$WORK/historical_26898_from_26899" "$WORK/historical_26899_replayed"
 python3 -S verify_26899.py semantics "$WORK/historical_26898_from_26899" "$WORK/historical_26899_replayed"
 (cd "$WORK/historical_26899_replayed" && sha256sum -c "$ROOT/26899_UNCHANGED_PROTECTED.sha256" >/dev/null) || fail '26899 2021 protected source byte drift'
 grep -Fx 'VERSION_NAME=0.9726899' "$WORK/historical_26899_replayed/app/version.properties" >/dev/null
 grep -Fx 'VERSION_BUILD=26899' "$WORK/historical_26899_replayed/app/version.properties" >/dev/null
 test -s "$OUT/26899_HISTORICAL_PATCH_PROOF.txt" || fail '26899 actual patches not executed'
 cat >> "$OUT/26902_PREBUILD_SAFETY.txt" <<'EOF_26899_SAFETY'
26899_exact_parent=success run 41656090620 job 125986647940 commit 94d8900987749c9ad0f7a18a64eeb0c7083e6d04 artifact 13241316001 digest 3fa6f669ecebd7e5c460ea1228d086b7422a93c95c8bbd950f5b4fe24bf53b97
26899_actual_compiled_parent_tar_sha256=7ac15724f3cc30753f41f08038443e24b4931c8861fe10217cc4c3b059755a61
26899_actual_successful_parent_runner_sha256=9c97ed074b1d4ec48528e1d63103aed3198d44406a0c3f4820ad3309c203c99a
26899_runtime=2025 prior to 2026 proposed, 4 modified + 1 new shader, 2021 protected
26899_scope=shutter frozen B Experiment, SuperRes OFF, global zoom >=1.10; new final encoded-SDR edge-aware Y only pass
26899_zoom_curve=+100pct 1.10..10x; +100..150pct 10..20x; +150..200pct 20..30x; capped +200pct >=30x
26899_no_changes=actual A, A+B, B SR ON, Night, Spektra, DNG, RAW fusion, frame counts, Wiener, AMaZE, shader owners besides newly named GLES, color pipeline, UHDR algorithm
26899_compiler=real pinned GLSL ES 310 new shader PASS + inherited native SPIRV, Kotlin Java 2 NDK ABIs and full :app:assembleDebug mandatory
26899_device_tests=NOT RUN ON ACTIONS; visual halos, 4.1x crop vs 20x, all physical lenses, DNG and UHDR device verification required
EOF_26899_SAFETY
 test -s "$OUT/26900_HISTORICAL_GLSL_REAL_COMPILER_RECEIPT.txt" && grep -Fx 'PASS 26900 TWO EXACT runtime-expanded ESSL310 shaders REAL PINNED GLSLANG 16.5.0' "$OUT/26900_HISTORICAL_GLSL_REAL_COMPILER_RECEIPT.txt" >/dev/null || fail '26900 real changed ESSL compiler proof missing'
 python3 -S verify_26900.py candidate "$WORK/historical_26899_from_26900" "$WORK/historical_26900_replayed"
 python3 -S verify_26900.py semantics "$WORK/historical_26899_from_26900" "$WORK/historical_26900_replayed"
 (cd "$WORK/historical_26900_replayed" && sha256sum -c "$ROOT/26900_UNCHANGED_PROTECTED.sha256" >/dev/null) || fail '26900 protected files changed'
 grep -Fx 'VERSION_NAME=0.9726900' "$WORK/historical_26900_replayed/app/version.properties" >/dev/null
 grep -Fx 'VERSION_BUILD=26900' "$WORK/historical_26900_replayed/app/version.properties" >/dev/null
 test -s "$OUT/26900_HISTORICAL_PATCH_PROOF.txt" || fail '26900 actual current patches not executed'
 cat >> "$OUT/26902_PREBUILD_SAFETY.txt" <<'EOF_26900_SAFETY'
26900_parent=26899 V2 successful run 41700527054 job 126142291738 commit 5a3e3eee6086398021f57f4b4f9de24ba125af24 artifact 13264802004
26900_parent_artifact_digest=de648a61f7c4639c84c384d2ff6cbec1d057d9377cb1b47a52e0d5bc34036ff9
26900_parent_compiled_source_tar_sha256=b468173a2eae7100f3180b8a178e37961dc1c0465560fad90113e8181507c80f
26900_parent_executed_runner_sha256=a253dd089fdbdb9fc0829d165a42a1645b35405427f8ae369cfa1e08233331d7
26900_scope=only shutter-selected B Super Res OFF global >=1.10, 2 existing shaders + MotionV2Render + version
26900_curve=26899 original global +100...+200 unchanged, larger luma radius uses actual rendering pixel scale
26900_bicubic=Catmull-Rom luma on final RGB enlargement with original bilinear chroma; no new RAW/CFA/motion processing
26900_noises=no new noise reduction; old 26899 low-contrast suppression removed; clipping/halo guards retained
26900_protected=2022 identical other runtime sources, no adds/deletions, native/DNG/vendor/A/AB/SuperResON/Night/LONG/Spektra/UHDR algorithm unchanged
26900_compilers=real two changed ESSL310 pinned glslang and prior 17-stage real Kotlin/Java/NDK/Gradle assembly required
EOF_26900_SAFETY
 test -s "$OUT/26901_HISTORICAL_GLSL_REAL_COMPILER_RECEIPT.txt" && grep -Fx 'PASS 26901 TWO EXACT runtime-expanded ESSL310 shaders REAL PINNED GLSLANG 16.5.0' "$OUT/26901_HISTORICAL_GLSL_REAL_COMPILER_RECEIPT.txt" >/dev/null || fail '26901 real changed shader compiler proof missing'
 python3 -S verify_26901.py candidate "$WORK/historical_26900_from_26901" "$WORK/historical_26901_replayed"
 python3 -S verify_26901.py semantics "$WORK/historical_26900_from_26901" "$WORK/historical_26901_replayed"
 (cd "$WORK/historical_26901_replayed" && sha256sum -c "$ROOT/26901_UNCHANGED_PROTECTED.sha256" >/dev/null) || fail '26901 protected file mutation'
 grep -Fx 'VERSION_NAME=0.9726901' "$WORK/historical_26901_replayed/app/version.properties" >/dev/null
 grep -Fx 'VERSION_BUILD=26901' "$WORK/historical_26901_replayed/app/version.properties" >/dev/null
 test -s "$OUT/26901_HISTORICAL_PATCH_PROOF.txt" || fail '26901 full-index real patch proof missing'
 cat >> "$OUT/26902_PREBUILD_SAFETY.txt" <<'EOF_26901_SAFETY'
26901_parent=26900 successful run 41761560619 job 126350185660 commit 7eadca372ef38f5d02b36f5ce7ebedc358f4ae25 artifact 13290914419
26901_parent_artifact_digest=4f2fe4f5e2a3a5b3425556ffb6c917ade61224176d932f58d72d1fc1dde914ca
26901_parent_compiled_tar_sha256=f629f785bbcf89bef05bb13e0d3398f5e513847c40f7aa22d907fc0781b867fd
26901_parent_executed_runner_sha256=1671e0a86fb85573da2cfbffa1c12502cf4153e4e15e548d0bc9bf4a15254cf6
26901_scope=only shutter selected B Super Res OFF active physical lens outputLocalZoom >=1.10; no native optical sharpening
26901_curve=total displayed global zoom original 26899/26900 +100...+200 and SAME displayed total zoom drives two-scale radius
26901_bicubic=independent full RGB 4x4 Catmull-Rom final crop enlargement, per-channel central extrema clamp; no extra processing stage
26901_noise=no added noise suppression; original temporal fusion/Sabre/RAWR/demosaic unchanged
26901_protected=2020 source files unchanged from real 26900 successful compiled authority, no add/delete, native/vendor/DNG/A/AB/B-SR-ON/Night/LONG/Spektra/UHDR untouched
26901_compilers=real pinned ESSL310 shader compiles and inherited 17-stage language/NDK/full APK must PASS in Actions
EOF_26901_SAFETY
 test -s "$OUT/26901_HISTORICAL_GLSL_REAL_COMPILER_RECEIPT.txt" && grep -Fx 'PASS 26901 TWO EXACT runtime-expanded ESSL310 shaders REAL PINNED GLSLANG 16.5.0' "$OUT/26901_HISTORICAL_GLSL_REAL_COMPILER_RECEIPT.txt" >/dev/null || fail '26901 historical REAL compiled shaders missing'
 test -s "$OUT/26902_CURRENT_GLSL_REAL_COMPILER_RECEIPT.txt" && grep -Fx 'PASS 26902 EXACT runtime-expanded ESSL310 shader REAL PINNED GLSLANG 16.5.0' "$OUT/26902_CURRENT_GLSL_REAL_COMPILER_RECEIPT.txt" >/dev/null || fail '26902 changed shader REAL compiler proof missing'
 python3 -S verify_26902.py candidate "$BASE" "$CAND"
 python3 -S verify_26902.py semantics "$BASE" "$CAND"
 (cd "$CAND" && sha256sum -c "$ROOT/26902_UNCHANGED_PROTECTED.sha256" >/dev/null) || fail '26902 protected source changed'
 grep -Fx 'VERSION_NAME=0.9726902' "$CAND/app/version.properties" >/dev/null
 grep -Fx 'VERSION_BUILD=26902' "$CAND/app/version.properties" >/dev/null
 test -s "$OUT/26902_CURRENT_PATCH_PROOF.txt" || fail '26902 exact current forward/rollback proof missing'
 cat >> "$OUT/26902_PREBUILD_SAFETY.txt" <<'EOF_26902_SAFETY'
26902_parent=26901 successful Actions run 41774585178 job 126391861885 commit ee59eeb6f4fec16af10969ed7fbf90269b11a16a artifact 13297535320
26902_parent_artifact_digest=6de45e5fa5c26e581c9d010175ed8691941ce14122b64ef13fee2020e70c68a5
26902_parent_compiled_tar_sha256=759109721bfc05c70c85d215542333a667107f0e652531ec9966768e8658a615
26902_parent_executed_runner_sha256=bcdd8bb524e5410808b4ecf2ef27760c1c28412d18389ee676c55be3509db6d9
26902_scope=ONLY B Super Res OFF active physical lens local zoom >=1.10 for every Android device; native optical OFF
26902_gain=lens local <=2.5 35%; <=5 40%; <=10 55%; <=15 60%; <=20 70%; (20,30] 100 to 150; >=30 150
26902_radius=uses lens-local zoom, not total Iris displayed zoom, same prior two-scale sampling formula; viewfinder unmodified
26902_bicubic=original successful 26901 independent full RGB Catmull-Rom unchanged; no denoising/blur added
26902_protected=2023 unchanged from successful 26901 compiled source; native/vendor/DNG/RAW/Sabre/Wronski/A/AB/B-ON/Night/LONG/Spektra/UHDR/50MP unchanged
26902_compilers=real pinned GLSLANG ESSL310, historical GLSL/SPIRV, Kotlin/Java, NDK and APK must pass in real Actions
EOF_26902_SAFETY
}
assemble(){
 test -f "$OUT/26902_PREBUILD_SAFETY.txt" && grep -Fx 'PRE-BUILD SAFETY PROOF PASSED' "$OUT/26902_PREBUILD_SAFETY.txt" >/dev/null || fail 'assemble forbidden without proof'
 ./gradlew :app:assembleDebug --stacktrace 2>&1 | tee "$OUT/26902_gradle_assemble.log"
 mapfile -t apks < <(find app/build/outputs/apk -type f -name '*.apk' | sort)
 [[ "${#apks[@]}" -eq 1 ]] || fail "expected exactly one assembled APK, got ${#apks[@]}"
 cp "${apks[0]}" "$FINAL"
 [[ "$(find . -maxdepth 1 -name 'IrisCamera-*.apk' -type f | wc -l)" -eq 1 ]] || fail 'one intended APK at root'
 sha256sum "$FINAL" > "$OUT/26902_APK.sha256"
 sed -i 's/FULL ANDROID ASSEMBLE: NOT RUN YET/FULL ANDROID ASSEMBLE: PASS/' "$OUT/26902_COMPILER_STATUS.txt"
 pass 'full :app:assembleDebug including NDK, exactly one intended APK'
}
postbuild_proof(){
 snapshot_live_authority_seeded "$WORK/post_build_live_snapshot"
 diff -qr "$CAND/app" "$WORK/post_build_live_snapshot/app" >/dev/null || fail 'candidate changed after assemble'
 python3 -S verify_26891_candidate.py "$WORK/historical_26890_from_26891" "$WORK/historical_26891_replayed"
 (cd "$WORK/historical_26891_replayed" && sha256sum -c "$ROOT/26891_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null)
 (cd "$WORK/historical_26891_replayed" && sha256sum -c "$ROOT/26891_UNCHANGED_PROTECTED.sha256" >/dev/null)
 cp 26891_EXPECTED_CANDIDATE_FULL_APP.sha256 "$OUT/26902_historical_26891_candidate_full_app.sha256"
 (cd "$WORK/historical_26894_replayed" && tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -czf "$OUT/26894_historical_candidate_app_source.tar.gz" app)
 sha256sum "$OUT/26894_historical_candidate_app_source.tar.gz" > "$OUT/26894_historical_candidate_app_source.tar.gz.sha256"
 cp 26891_FORWARD_FULL_INDEX.patch 26891_ROLLBACK_FULL_INDEX.patch "$OUT/"
 sed -i 's/POST-BUILD INVARIANCE: NOT RUN YET/POST-BUILD INVARIANCE: PASS/' "$OUT/26902_COMPILER_STATUS.txt"
 pass 'postbuild authority-seeded candidate/protected/DNG/native/vendor invariance and deterministic candidate export'
 python3 -S verify_26892_candidate.py "$WORK/historical_26891_from_26892" "$WORK/historical_26892_replayed"
 (cd "$WORK/historical_26892_replayed" && sha256sum -c "$ROOT/26892_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null)
 (cd "$WORK/historical_26892_replayed" && sha256sum -c "$ROOT/26892_UNCHANGED_PROTECTED.sha256" >/dev/null)
 cp 26892_EXPECTED_CANDIDATE_FULL_APP.sha256 "$OUT/26902_historical_26892_candidate_full_app.sha256"
 (cd "$WORK/historical_26894_replayed" && tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -czf "$OUT/26894_historical_candidate_app_source.tar.gz" app)
 sha256sum "$OUT/26894_historical_candidate_app_source.tar.gz" > "$OUT/26894_historical_candidate_app_source.tar.gz.sha256"
 cp 26892_FORWARD_FULL_INDEX.patch 26892_ROLLBACK_FULL_INDEX.patch "$OUT/"
 python3 -S verify_26893_candidate.py "$WORK/historical_26892_from_26893" "$WORK/historical_26893_replayed"
 python3 -S verify_26893_semantics.py "$WORK/historical_26892_from_26893" "$WORK/historical_26893_replayed"
 (cd "$WORK/historical_26893_replayed" && sha256sum -c "$ROOT/26893_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null)
 (cd "$WORK/historical_26893_replayed" && sha256sum -c "$ROOT/26893_UNCHANGED_PROTECTED.sha256" >/dev/null)
 cp 26893_EXPECTED_CANDIDATE_FULL_APP.sha256 "$OUT/26895_historical_candidate_full_app.sha256"
 (cd "$WORK/historical_26894_replayed" && tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -czf "$OUT/26894_historical_candidate_app_source.tar.gz" app)
 sha256sum "$OUT/26894_historical_candidate_app_source.tar.gz" > "$OUT/26894_historical_candidate_app_source.tar.gz.sha256"
 cp 26893_FORWARD_FULL_INDEX.patch 26893_ROLLBACK_FULL_INDEX.patch "$OUT/"
 python3 -S verify_26894.py candidate "$WORK/historical_26893_from_26894" "$WORK/historical_26894_replayed"
 python3 -S verify_26894.py semantics "$WORK/historical_26893_from_26894" "$WORK/historical_26894_replayed"
 (cd "$WORK/historical_26894_replayed" && sha256sum -c "$ROOT/26894_UNCHANGED_PROTECTED.sha256" >/dev/null)
 (cd "$WORK/historical_26894_replayed" && sha256sum -c "$ROOT/26894_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null)
 cp 26894_EXPECTED_CANDIDATE_FULL_APP.sha256 "$OUT/26895_historical_candidate_full_app.sha256"
 (cd "$WORK/historical_26894_replayed" && tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -czf "$OUT/26894_historical_candidate_app_source.tar.gz" app)
 sha256sum "$OUT/26894_historical_candidate_app_source.tar.gz" > "$OUT/26894_historical_candidate_app_source.tar.gz.sha256"
 cp 26894_FORWARD_FULL_INDEX.patch 26894_ROLLBACK_FULL_INDEX.patch "$OUT/"
 python3 -S verify_26895.py candidate "$WORK/historical_26894_from_26895" "$WORK/historical_26895_replayed"
 python3 -S verify_26895.py semantics "$WORK/historical_26894_from_26895" "$WORK/historical_26895_replayed"
 (cd "$WORK/historical_26895_replayed" && sha256sum -c "$ROOT/26895_UNCHANGED_PROTECTED.sha256" >/dev/null) || fail '26895 protected postbuild mismatch'
 (cd "$WORK/historical_26895_replayed" && sha256sum -c "$ROOT/26895_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null) || fail '26895 full candidate postbuild mismatch'
 cp 26895_EXPECTED_CANDIDATE_FULL_APP.sha256 "$OUT/26895_historical_candidate_full_app.sha256"
 cp 26895_FORWARD_FULL_INDEX.patch 26895_ROLLBACK_FULL_INDEX.patch 26895_CHANGED_ALLOWLIST.txt 26895_DELETIONS.txt 26895_UNCHANGED_PROTECTED.sha256 "$OUT/"
 (cd "$WORK/historical_26895_replayed" && tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -czf "$OUT/26895_historical_candidate_app_source.tar.gz" app)
 sha256sum "$OUT/26895_historical_candidate_app_source.tar.gz" > "$OUT/26895_historical_candidate_app_source.tar.gz.sha256"
 python3 -S verify_26897.py candidate "$WORK/historical_26895_from_26897" "$WORK/historical_26897_replayed"
 python3 -S verify_26897.py semantics "$WORK/historical_26895_from_26897" "$WORK/historical_26897_replayed"
 (cd "$WORK/historical_26897_replayed" && sha256sum -c "$ROOT/26897_UNCHANGED_PROTECTED.sha256" >/dev/null) || fail '26897 protected postbuild source mismatch'
 (cd "$WORK/historical_26897_replayed" && sha256sum -c "$ROOT/26897_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null) || fail '26897 final compiled candidate mismatch'
 cp 26897_EXPECTED_CANDIDATE_FULL_APP.sha256 "$OUT/26897_historical_candidate_full_app.sha256"
 cp 26897_FORWARD_FULL_INDEX.patch 26897_ROLLBACK_FULL_INDEX.patch 26897_CHANGED_ALLOWLIST.txt 26897_ADDITIONS.txt 26897_DELETIONS.txt 26897_UNCHANGED_PROTECTED.sha256 "$OUT/"
 (cd "$WORK/historical_26897_replayed" && tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -czf "$OUT/26897_historical_candidate_app_source.tar.gz" app)
 sha256sum "$OUT/26897_historical_candidate_app_source.tar.gz" > "$OUT/26897_historical_candidate_app_source.tar.gz.sha256"
 python3 -S verify_26898.py candidate "$WORK/historical_26897_from_26898" "$WORK/historical_26898_replayed"
 python3 -S verify_26898.py semantics "$WORK/historical_26897_from_26898" "$WORK/historical_26898_replayed"
 (cd "$WORK/historical_26898_replayed" && sha256sum -c "$ROOT/26898_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null) || fail '26898 final compiled source SHA drift'
 (cd "$WORK/historical_26898_replayed" && sha256sum -c "$ROOT/26898_UNCHANGED_PROTECTED.sha256" >/dev/null) || fail '26898 protected shader/DNG native/vendor source changed'
 cp 26898_EXPECTED_CANDIDATE_FULL_APP.sha256 "$OUT/26898_historical_candidate_full_app.sha256"
 cp 26898_FORWARD_FULL_INDEX.patch 26898_ROLLBACK_FULL_INDEX.patch 26898_CHANGED_ALLOWLIST.txt 26898_ADDITIONS.txt 26898_DELETIONS.txt 26898_UNCHANGED_PROTECTED.sha256 "$OUT/"
 (cd "$WORK/historical_26898_replayed" && tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -czf "$OUT/26898_historical_candidate_app_source.tar.gz" app)
 sha256sum "$OUT/26898_historical_candidate_app_source.tar.gz" > "$OUT/26898_historical_candidate_app_source.tar.gz.sha256"
 python3 -S verify_26899.py candidate "$WORK/historical_26898_from_26899" "$WORK/historical_26899_replayed"
 python3 -S verify_26899.py semantics "$WORK/historical_26898_from_26899" "$WORK/historical_26899_replayed"
 (cd "$WORK/historical_26899_replayed" && sha256sum -c "$ROOT/26899_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null) || fail '26899 candidate source drift after assembly'
 (cd "$WORK/historical_26899_replayed" && sha256sum -c "$ROOT/26899_UNCHANGED_PROTECTED.sha256" >/dev/null) || fail '26899 protected DNG native A Night source drift'
 cp 26899_EXPECTED_CANDIDATE_FULL_APP.sha256 "$OUT/26899_historical_candidate_full_app.sha256"
 cp 26899_FORWARD_FULL_INDEX.patch 26899_ROLLBACK_FULL_INDEX.patch 26899_CHANGED_ALLOWLIST.txt 26899_ADDITIONS.txt 26899_DELETIONS.txt 26899_UNCHANGED_PROTECTED.sha256 "$OUT/"
 (cd "$WORK/historical_26899_replayed" && tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -czf "$OUT/26899_historical_candidate_app_source.tar.gz" app)
 sha256sum "$OUT/26899_historical_candidate_app_source.tar.gz" > "$OUT/26899_historical_candidate_app_source.tar.gz.sha256"
 python3 -S verify_26900.py candidate "$WORK/historical_26899_from_26900" "$WORK/historical_26900_replayed"
 python3 -S verify_26900.py semantics "$WORK/historical_26899_from_26900" "$WORK/historical_26900_replayed"
 (cd "$WORK/historical_26900_replayed" && sha256sum -c "$ROOT/26900_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null) || fail '26900 final source drift after compile'
 (cd "$WORK/historical_26900_replayed" && sha256sum -c "$ROOT/26900_UNCHANGED_PROTECTED.sha256" >/dev/null) || fail '26900 postbuild protected drift'
 cp 26900_EXPECTED_CANDIDATE_FULL_APP.sha256 "$OUT/26900_historical_candidate_full_app.sha256"
 cp 26900_FORWARD_FULL_INDEX.patch 26900_ROLLBACK_FULL_INDEX.patch 26900_CHANGED_ALLOWLIST.txt 26900_ADDITIONS.txt 26900_DELETIONS.txt 26900_UNCHANGED_PROTECTED.sha256 "$OUT/"
 (cd "$WORK/historical_26900_replayed" && tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -czf "$OUT/26900_historical_candidate_app_source.tar.gz" app)
 sha256sum "$OUT/26900_historical_candidate_app_source.tar.gz" > "$OUT/26900_historical_candidate_app_source.tar.gz.sha256"
 python3 -S verify_26901.py candidate "$WORK/historical_26900_from_26901" "$WORK/historical_26901_replayed"
 python3 -S verify_26901.py semantics "$WORK/historical_26900_from_26901" "$WORK/historical_26901_replayed"
 (cd "$WORK/historical_26901_replayed" && sha256sum -c "$ROOT/26901_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null) || fail '26901 candidate source drift'
 (cd "$WORK/historical_26901_replayed" && sha256sum -c "$ROOT/26901_UNCHANGED_PROTECTED.sha256" >/dev/null) || fail '26901 postbuild protected drift'
 cp 26901_EXPECTED_CANDIDATE_FULL_APP.sha256 "$OUT/26901_historical_candidate_full_app.sha256"
 cp 26901_FORWARD_FULL_INDEX.patch 26901_ROLLBACK_FULL_INDEX.patch 26901_CHANGED_ALLOWLIST.txt 26901_ADDITIONS.txt 26901_DELETIONS.txt 26901_UNCHANGED_PROTECTED.sha256 "$OUT/"
 (cd "$WORK/historical_26901_replayed" && tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -czf "$OUT/26901_historical_candidate_app_source.tar.gz" app)
 sha256sum "$OUT/26901_historical_candidate_app_source.tar.gz" > "$OUT/26901_historical_candidate_app_source.tar.gz.sha256"
 python3 -S verify_26902.py candidate "$BASE" "$CAND"
 python3 -S verify_26902.py semantics "$BASE" "$CAND"
 (cd "$CAND" && sha256sum -c "$ROOT/26902_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null) || fail '26902 candidate source changed after compilation'
 (cd "$CAND" && sha256sum -c "$ROOT/26902_UNCHANGED_PROTECTED.sha256" >/dev/null) || fail '26902 postbuild protected drift'
 cp 26902_EXPECTED_CANDIDATE_FULL_APP.sha256 "$OUT/26902_candidate_full_app.sha256"
 cp 26902_FORWARD_FULL_INDEX.patch 26902_ROLLBACK_FULL_INDEX.patch 26902_CHANGED_ALLOWLIST.txt 26902_ADDITIONS.txt 26902_DELETIONS.txt 26902_UNCHANGED_PROTECTED.sha256 "$OUT/"
 (cd "$CAND" && tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -czf "$OUT/26902_candidate_app_source.tar.gz" app)
 sha256sum "$OUT/26902_candidate_app_source.tar.gz" > "$OUT/26902_candidate_app_source.tar.gz.sha256"
}
clean_extract_replay(){
 local replay="$WORK/clean_replay_candidate" exp="$WORK/extracted_candidate_tar"
 rm -rf "$replay" "$exp";mkdir -p "$exp"
 sha256sum -c 26891_HANDOFF_HASHES.sha256
 sha256sum -c 26889_HANDOFF_HASHES.sha256 >/dev/null
 sha256sum -c 26891_GENERATED_BUILD_SHA256.txt
 sha256sum -c 26889_GENERATED_BUILD_SHA256.txt >/dev/null
 bash -n build_26891_iris_rawr.sh
 bash -n build_26889_iris_rawr.sh
 python3 -S -m py_compile verify_26887_candidate.py verify_26887_patches.py verify_26880_rawr_shader_universe.py verify_26880_runtime_glsl_scope.py verify_26880_highlight_runtime_shader.py regressions/26877_runtime_ownership_spektra.py regressions/26878_runtime_ownership_spektra.py regressions/26879_runtime_ownership_spektra.py regressions/26880_runtime_ownership_spektra.py regressions/26880_wr_no_fit_optional_wavelet.py
 rm -rf __pycache__ regressions/__pycache__
 python3 -S verify_26895.py candidate "$WORK/historical_26894_from_26895" "$replay" --transform
 diff -qr "$WORK/historical_26895_replayed"/app "$replay/app" >/dev/null || fail 'final clean extracted transform not exact'
 sha256sum -c "$OUT/26894_historical_candidate_app_source.tar.gz.sha256" >/dev/null
 tar -xzf "$OUT/26894_historical_candidate_app_source.tar.gz" -C "$exp"
 diff -qr "$WORK/historical_26894_replayed"/app "$exp/app" >/dev/null || fail 'compiler-tested frozen candidate changed during assembly'
 python3 -S verify_26891_candidate.py "$WORK/historical_26890_from_26891" "$WORK/historical_26891_replayed"
 python3 -S verify_26891_patches.py "$WORK/historical_26890_from_26891" "$WORK/historical_26891_replayed" 26891_FORWARD_FULL_INDEX.patch 26891_ROLLBACK_FULL_INDEX.patch > "$OUT/26902_final_patch_replay.txt"
 python3 -S verify_26880_runtime_glsl_scope.py "$WORK/historical_26879_from_26880" "$WORK/historical_26880_from_26881" --out "$OUT/26887_final_runtime_glsl" | tee "$OUT/26887_final_glsl_static.txt"
 python3 -S verify_26880_rawr_shader_universe.py "$WORK/historical_26884_from_26885/app"
 python3 -S verify_26880_highlight_runtime_shader.py "$WORK/historical_26880_from_26881" --out "$OUT/26887_final_highlight_preflight"
 python3 -S regressions/26864_glsl_reserved_identifiers.py "$exp/app"
 python3 -S regressions/26864_wronski_publisher.py "$WORK/historical_26867_from_26868/app"
 python3 -S verify_26864_semantics.py "$WORK/historical_26867_from_26868/app" --numeric
 python3 -S regressions/26865_b_lsc_owner.py "$exp/app"
 python3 -S regressions/26866_b_color_only.py "$WORK/historical_26866_from_26867/app"
 python3 -S regressions/26867_b_highlight_ab_retired.py "$WORK/historical_26867_from_26868/app"
 python3 -S regressions/26868_direct_b_long_retire_ab.py "$WORK/historical_26868_from_26870/app"
 python3 -S regressions/26870_b_automatic_iq.py "$WORK/historical_26868_from_26870/app" "$WORK/historical_26870_from_26871/app"
 python3 -S regressions/26871_b_shutter_group.py "$WORK/historical_26870_from_26871" "$WORK/historical_26871_from_26872"
 python3 -S regressions/26872_b_preview_only.py "$WORK/historical_26871_from_26872" "$WORK/historical_26872_from_26873"
 python3 -S regressions/26873_gpu_resident_owner.py "$WORK/historical_26872_from_26873" "$WORK/historical_26873_from_26874"
 python3 -S regressions/26874_b_jpeg_owner.py "$WORK/historical_26873_from_26874" "$WORK/historical_26874_from_26875"
 python3 -S regressions/26875_device_failures.py "$WORK/historical_26874_from_26875" "$WORK/historical_26875_from_26876"
 python3 -S regressions/26876_superres_ownership.py "$WORK/historical_26875_from_26876" "$WORK/historical_26876_from_26877"
 python3 -S regressions/26877_runtime_ownership_spektra.py "$WORK/historical_26876_from_26877" "$WORK/historical_26877_from_26878"
 python3 -S regressions/26878_runtime_ownership_spektra.py "$WORK/historical_26877_from_26878" "$WORK/historical_26878_from_26879"
 python3 -S regressions/26879_runtime_ownership_spektra.py "$WORK/historical_26878_from_26879" "$WORK/historical_26879_from_26880"
 python3 -S regressions/26880_runtime_ownership_spektra.py "$WORK/historical_26879_from_26880" "$WORK/historical_26880_from_26881"
 python3 -S regressions/26881_spektra_chroma_clip.py "$WORK/historical_26880_from_26881" "$WORK/historical_26881_from_26882"
 python3 -S regressions/26880_wr_no_fit_optional_wavelet.py "$exp/app/src/main/cpp/iris26864/Iris26864JniGpuInteropImpl.inc"
 python3 -S verify_26880_spektra_abi.py "$WORK/historical_26880_from_26881/app"
 python3 -S verify_26880_native_shaders.py "$exp"
 python3 -S verify_26891_candidate.py "$WORK/historical_26890_from_26891" "$WORK/historical_26891_replayed"
 python3 -S verify_26876_expanded_shaders.py "$exp"
 python3 -S verify_26867_runtime_shader.py "$WORK/historical_26867_from_26868" --out "$OUT/26887_final_white_fade"
 python3 -S verify_26868_runtime_shader.py "$WORK/historical_26868_from_26870" --out "$OUT/26887_final_b_long"
 python3 -S verify_26871_runtime_shader.py "$exp" --out "$OUT/26887_final_prior_shader"
 python3 -S verify_26872_runtime_shader.py "$exp" --out "$OUT/26887_final_preview_shaders"
 grep -Fx 'VERSION_NAME=0.9726894' "$exp/app/version.properties" >/dev/null
 grep -Fx 'VERSION_BUILD=26894' "$exp/app/version.properties" >/dev/null
 for k in 'REAL GLSL COMPILE: PASS' 'REAL SPIR-V VALIDATION: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS';do
  grep -F "$k" "$OUT/26902_COMPILER_STATUS.txt" >/dev/null || fail "final successful compiler proof missing $k"
 done
 pass '26887 clean-extract source/protected/regressions/manifests/patches/version + real build'
 python3 -S verify_26881_expanded_glsl.py "$WORK/historical_26881_from_26882" --out "$OUT/26887_clean_extract_shader_preflight"

 python3 -S verify_26882_semantics.py "$WORK/historical_26881_from_26882" "$WORK/historical_26882_from_26883"
 python3 -S verify_26882_expanded_glsl.py "$WORK/historical_26882_from_26883" --out "$OUT/26887_final_white_shader_source"
 python3 -S verify_26882_candidate.py "$WORK/historical_26881_from_26882" "$WORK/historical_26882_from_26883"
 python3 -S verify_26883_semantics.py "$WORK/historical_26882_from_26883" "$WORK/historical_26883_from_26884"
 python3 -S verify_26883_expanded_glsl.py "$WORK/historical_26883_from_26884" --out "$OUT/26887_final_shared_white_expanded_source"
 python3 -S verify_26883_candidate.py "$WORK/historical_26882_from_26883" "$WORK/historical_26883_from_26884"
 python3 -S verify_26884_semantics.py "$WORK/historical_26883_from_26884" "$WORK/historical_26884_from_26885"
 python3 -S regressions/26884_rawr_off_math.py "$WORK/historical_26884_from_26885"
 python3 -S verify_26884_expanded_glsl.py "$WORK/historical_26884_from_26885" --out "$OUT/26887_final_rawr_off_fused_wb_source"

 python3 -S verify_26884_candidate.py "$WORK/historical_26883_from_26884" "$WORK/historical_26884_from_26885"
 python3 -S verify_26891_candidate.py "$WORK/historical_26890_from_26891" "$WORK/historical_26891_replayed"
 python3 -S verify_26891_semantics.py "$WORK/historical_26890_from_26891" "$WORK/historical_26891_replayed"
 python3 -S regressions/26886_chroma_controls.py "$WORK/historical_26885_from_26886" "$WORK/historical_26886_from_26887"
 python3 -S verify_26890_expanded_glsl.py "$WORK/historical_26890_replayed"
 python3 -S regressions/26885_actions_40604341240_historical_scope.py "$WORK/historical_26884_from_26885" "$WORK/historical_26885_from_26886" "$ROOT/build_26885_iris_rawr.sh"
 python3 -S verify_26885_candidate.py "$WORK/historical_26884_from_26885" "$WORK/historical_26885_from_26886"
 python3 -S verify_26885_semantics.py "$WORK/historical_26884_from_26885" "$WORK/historical_26885_from_26886"
 python3 -S regressions/26885_chroma_controls.py "$WORK/historical_26885_from_26886" "$WORK/historical_26884_from_26885"
 python3 -S verify_26885_expanded_glsl.py "$WORK/historical_26885_from_26886"
 python3 -S regressions/26886_historical_scope_all_stages.py "$WORK/historical_26884_from_26885" "$WORK/historical_26885_from_26886" "$WORK/historical_26886_from_26887" "$ROOT/build_26885_iris_rawr.sh" "$ROOT/build_26886_iris_rawr.sh"
 python3 -S verify_26886_candidate.py "$WORK/historical_26885_from_26886" "$WORK/historical_26886_from_26887"
 python3 -S verify_26886_semantics.py "$WORK/historical_26885_from_26886" "$WORK/historical_26886_from_26887"
 python3 -S verify_26886_expanded_glsl.py "$WORK/historical_26886_from_26887"
 python3 -S verify_26891_candidate.py "$WORK/historical_26890_from_26891" "$WORK/historical_26891_replayed"
 python3 -S verify_26891_semantics.py "$WORK/historical_26890_from_26891" "$WORK/historical_26891_replayed"
 python3 -S verify_26890_expanded_glsl.py "$WORK/historical_26890_replayed"
 python3 -S verify_26891_patches.py "$WORK/historical_26890_from_26891" "$WORK/historical_26891_replayed" 26891_FORWARD_FULL_INDEX.patch 26891_ROLLBACK_FULL_INDEX.patch
 python3 -S verify_26887_candidate.py "$WORK/historical_26886_from_26887" "$WORK/historical_26887_replayed"
 python3 -S verify_26887_semantics.py "$WORK/historical_26886_from_26887" "$WORK/historical_26887_replayed"
 python3 -S verify_26887_expanded_glsl.py "$WORK/historical_26887_replayed"
 python3 -S verify_26887_patches.py "$WORK/historical_26886_from_26887" "$WORK/historical_26887_replayed" 26887_FORWARD_FULL_INDEX.patch 26887_ROLLBACK_FULL_INDEX.patch
 python3 -S verify_26891_candidate.py "$WORK/historical_26890_from_26891" "$WORK/historical_26891_replayed"
 python3 -S verify_26891_semantics.py "$WORK/historical_26890_from_26891" "$WORK/historical_26891_replayed"
 python3 -S verify_26890_expanded_glsl.py "$WORK/historical_26890_replayed"
 python3 -S verify_26891_patches.py "$WORK/historical_26890_from_26891" "$WORK/historical_26891_replayed" 26891_FORWARD_FULL_INDEX.patch 26891_ROLLBACK_FULL_INDEX.patch
 python3 -S verify_26888_candidate.py "$WORK/historical_26887_from_26888" "$WORK/historical_26888_replayed"
 python3 -S verify_26888_semantics.py "$WORK/historical_26887_from_26888" "$WORK/historical_26888_replayed"
 python3 -S verify_26888_expanded_glsl.py "$WORK/historical_26888_replayed"
 python3 -S verify_26888_patches.py "$WORK/historical_26887_from_26888" "$WORK/historical_26888_replayed" 26888_FORWARD_FULL_INDEX.patch 26888_ROLLBACK_FULL_INDEX.patch
 python3 -S verify_26891_candidate.py "$WORK/historical_26890_from_26891" "$WORK/historical_26891_replayed"
 python3 -S verify_26891_semantics.py "$WORK/historical_26890_from_26891" "$WORK/historical_26891_replayed"
 python3 -S verify_26890_expanded_glsl.py "$WORK/historical_26890_replayed"
 python3 -S verify_26891_patches.py "$WORK/historical_26890_from_26891" "$WORK/historical_26891_replayed" 26891_FORWARD_FULL_INDEX.patch 26891_ROLLBACK_FULL_INDEX.patch
 python3 -S verify_26889_candidate.py "$WORK/historical_26888_from_26889" "$WORK/historical_26889_replayed"
 python3 -S verify_26889_semantics.py "$WORK/historical_26888_from_26889" "$WORK/historical_26889_replayed"
 python3 -S verify_26889_expanded_glsl.py "$WORK/historical_26889_replayed"
 python3 -S verify_26889_patches.py "$WORK/historical_26888_from_26889" "$WORK/historical_26889_replayed" 26889_FORWARD_FULL_INDEX.patch 26889_ROLLBACK_FULL_INDEX.patch
 python3 -S verify_26891_candidate.py "$WORK/historical_26890_from_26891" "$WORK/historical_26891_replayed"
 python3 -S verify_26891_semantics.py "$WORK/historical_26890_from_26891" "$WORK/historical_26891_replayed"
 python3 -S verify_26890_expanded_glsl.py "$WORK/historical_26890_replayed"
 python3 -S verify_26891_patches.py "$WORK/historical_26890_from_26891" "$WORK/historical_26891_replayed" 26891_FORWARD_FULL_INDEX.patch 26891_ROLLBACK_FULL_INDEX.patch
 python3 -S test_26890_tone_math.py
 python3 -S verify_26891_expanded_glsl.py "$WORK/historical_26891_replayed"
 python3 -S verify_26891_candidate.py "$WORK/historical_26890_from_26891" "$WORK/historical_26891_replayed"
 python3 -S verify_26891_semantics.py "$WORK/historical_26890_from_26891" "$WORK/historical_26891_replayed"
 python3 -S test_26891_negative_tamper.py "$WORK/historical_26890_from_26891" "$WORK/historical_26891_replayed"
 python3 -S verify_26892_candidate.py "$WORK/historical_26891_from_26892" "$WORK/historical_26892_replayed"
 python3 -S verify_26892_semantics.py "$WORK/historical_26891_from_26892" "$WORK/historical_26892_replayed"
 python3 -S verify_26892_patches.py "$WORK/historical_26891_from_26892" "$WORK/historical_26892_replayed" 26892_FORWARD_FULL_INDEX.patch 26892_ROLLBACK_FULL_INDEX.patch
 python3 -S test_26892_negative_tamper.py "$WORK/historical_26891_from_26892" "$WORK/historical_26892_replayed"
 python3 -S test_26892_tone_math.py
 python3 -S verify_26892_expanded_glsl.py "$WORK/historical_26892_replayed"
 (cd "$WORK/historical_26892_replayed" && sha256sum -c "$ROOT/26892_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null)
 sha256sum -c "$OUT/26894_historical_candidate_app_source.tar.gz.sha256" >/dev/null
 test "$(sha build_26891_iris_rawr.sh)" = 'f0b25de61cc661a461c10e7665623ba15ddda0362ba047c05e543aaf670f094b' || fail '26891 original executed runner not preserved'
 python3 -S verify_26893_candidate.py "$WORK/historical_26892_from_26893" "$WORK/historical_26893_replayed"
 python3 -S verify_26893_semantics.py "$WORK/historical_26892_from_26893" "$WORK/historical_26893_replayed"
 python3 -S verify_26893_patches.py "$WORK/historical_26892_from_26893" "$WORK/historical_26893_replayed" 26893_FORWARD_FULL_INDEX.patch 26893_ROLLBACK_FULL_INDEX.patch
 python3 -S test_26893_negative_tamper.py "$WORK/historical_26892_from_26893" "$WORK/historical_26893_replayed"
 python3 -S test_26893_tone_math.py
 python3 -S verify_26893_expanded_glsl.py "$WORK/historical_26893_replayed"
 (cd "$WORK/historical_26893_replayed" && sha256sum -c "$ROOT/26893_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null)
 (cd "$WORK/historical_26893_replayed" && sha256sum -c "$ROOT/26893_UNCHANGED_PROTECTED.sha256" >/dev/null)
 sha256sum -c "$OUT/26894_historical_candidate_app_source.tar.gz.sha256" >/dev/null
 [[ "$(sha build_26892_iris_rawr.sh)" == '37b12a9cbb5918b49d279d40d51f11fa086a0682dd487f88b6ecc7f17313069d' ]] || fail 'successful 26892 executed runner not preserved'
 python3 -S verify_26894.py candidate "$WORK/historical_26893_from_26894" "$WORK/historical_26894_replayed"
 python3 -S verify_26894.py semantics "$WORK/historical_26893_from_26894" "$WORK/historical_26894_replayed"
 python3 -S verify_26894.py tone
 python3 -S verify_26894.py shader "$WORK/historical_26894_replayed" --compiler "$IRIS26864_GLSLANG" --out "$OUT/26902_final_real_essl310"
 python3 -S verify_26894.py patch "$WORK/historical_26893_from_26894" "$WORK/historical_26894_replayed" 26894_FORWARD_FULL_INDEX.patch 26894_ROLLBACK_FULL_INDEX.patch
 python3 -S verify_26894.py tamper "$WORK/historical_26893_from_26894" "$WORK/historical_26894_replayed"
 python3 -S test_26894_three_stage_negatives.py
 (cd "$WORK/historical_26894_replayed" && sha256sum -c "$ROOT/26894_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null)
 (cd "$WORK/historical_26894_replayed" && sha256sum -c "$ROOT/26894_UNCHANGED_PROTECTED.sha256" >/dev/null)
 sha256sum -c "$OUT/26894_historical_candidate_app_source.tar.gz.sha256" >/dev/null
 python3 -S verify_26895.py candidate "$WORK/historical_26894_from_26895" "$WORK/historical_26895_replayed"
 python3 -S verify_26895.py semantics "$WORK/historical_26894_from_26895" "$WORK/historical_26895_replayed"
 python3 -S verify_26895.py shader "$WORK/historical_26895_replayed" --compiler "$IRIS26864_GLSLANG" --out "$OUT/26902_final_restored_real_GLES310"
 python3 -S verify_26895.py patch "$WORK/historical_26894_from_26895" "$WORK/historical_26895_replayed" 26895_FORWARD_FULL_INDEX.patch 26895_ROLLBACK_FULL_INDEX.patch
 python3 -S verify_26895.py tamper "$WORK/historical_26894_from_26895" "$WORK/historical_26895_replayed"
 python3 -S test_26895_three_stage_negatives.py
 (cd "$WORK/historical_26895_replayed" && sha256sum -c "$ROOT/26895_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null)
 (cd "$WORK/historical_26895_replayed" && sha256sum -c "$ROOT/26895_UNCHANGED_PROTECTED.sha256" >/dev/null)
 sha256sum -c "$OUT/26895_historical_candidate_app_source.tar.gz.sha256" >/dev/null
 local exp95="$WORK/extracted_actual_26895_candidate_tar";rm -rf "$exp95";mkdir -p "$exp95"
 tar -xzf "$OUT/26895_historical_candidate_app_source.tar.gz" -C "$exp95"
 diff -qr "$WORK/historical_26895_replayed"/app "$exp95/app" >/dev/null || fail '26895 clean extracted compiled source differs from frozen candidate'
 grep -Fx 'VERSION_NAME=0.9726895' "$exp95/app/version.properties" >/dev/null || fail '26895 clean-extract name version check'
 grep -Fx 'VERSION_BUILD=26895' "$exp95/app/version.properties" >/dev/null || fail '26895 clean-extract build version check'
 [[ ! -e "$exp95/app/src/main/assets/shaders/motionv2/spatial_scene_26894.glsl" ]] || fail '26894 scene correction not removed'
 (cd "$exp95" && sha256sum -c "$ROOT/26895_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null)
 pass '26895 all real/locally applicable 17-stage gates inherited, clean-extract final candidate, 26893 runtime visual baseline, 1.14 saturation'
 python3 -S verify_26897.py candidate "$WORK/historical_26895_from_26897" "$WORK/historical_26897_replayed"
 python3 -S verify_26897.py semantics "$WORK/historical_26895_from_26897" "$WORK/historical_26897_replayed"
 python3 -S verify_26897.py patch "$WORK/historical_26895_from_26897" "$WORK/historical_26897_replayed" 26897_FORWARD_FULL_INDEX.patch 26897_ROLLBACK_FULL_INDEX.patch
 python3 -S verify_26897.py tamper "$WORK/historical_26895_from_26897" "$WORK/historical_26897_replayed"
 python3 -S test_26897_three_stage_negatives.py
 python3 -S test_26897_dng_modes.py "$WORK/historical_26897_replayed"
 (cd "$WORK/historical_26897_replayed" && sha256sum -c "$ROOT/26897_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null)
 (cd "$WORK/historical_26897_replayed" && sha256sum -c "$ROOT/26897_UNCHANGED_PROTECTED.sha256" >/dev/null)
 sha256sum -c "$OUT/26897_historical_candidate_app_source.tar.gz.sha256" >/dev/null
 local exp96="$WORK/extracted_actual_26897_compiled_tar";rm -rf "$exp96";mkdir -p "$exp96"
 tar -xzf "$OUT/26897_historical_candidate_app_source.tar.gz" -C "$exp96"
 diff -qr "$WORK/historical_26897_replayed"/app "$exp96/app" >/dev/null || fail 'final actual 26897 compiled TAR differs from built candidate'
 grep -Fx 'VERSION_NAME=0.9726897' "$exp96/app/version.properties" >/dev/null || fail '26897 clean-extract version name mismatch'
 grep -Fx 'VERSION_BUILD=26897' "$exp96/app/version.properties" >/dev/null || fail '26897 clean-extract version build mismatch'
 (cd "$exp96" && sha256sum -c "$ROOT/26897_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null)
 pass '26897 inherited exact seventeen-stage real Actions build, byte-perfect DNG candidate, 3-file ownership, compiler receipts and final replay'
 python3 -S verify_26898.py candidate "$WORK/historical_26897_from_26898" "$WORK/historical_26898_replayed"
 python3 -S verify_26898.py semantics "$WORK/historical_26897_from_26898" "$WORK/historical_26898_replayed"
 python3 -S verify_26898.py patch "$WORK/historical_26897_from_26898" "$WORK/historical_26898_replayed" 26898_FORWARD_FULL_INDEX.patch 26898_ROLLBACK_FULL_INDEX.patch
 python3 -S verify_26898.py tamper "$WORK/historical_26897_from_26898" "$WORK/historical_26898_replayed"
 python3 -S test_26898_three_stage_negatives.py
 python3 -S test_26898_modes.py "$WORK/historical_26898_replayed"
 (cd "$WORK/historical_26898_replayed" && sha256sum -c "$ROOT/26898_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null)
 (cd "$WORK/historical_26898_replayed" && sha256sum -c "$ROOT/26898_UNCHANGED_PROTECTED.sha256" >/dev/null)
 sha256sum -c "$OUT/26898_historical_candidate_app_source.tar.gz.sha256" >/dev/null
 local exp98="$WORK/extracted_actual_26898_candidate_tar";rm -rf "$exp98";mkdir -p "$exp98"
 tar -xzf "$OUT/26898_historical_candidate_app_source.tar.gz" -C "$exp98"
 diff -qr "$WORK/historical_26898_replayed"/app "$exp98/app" >/dev/null || fail 'actual 26898 compiled TAR differs from compiler-tested candidate'
 grep -Fx 'VERSION_NAME=0.9726898' "$exp98/app/version.properties" >/dev/null
 grep -Fx 'VERSION_BUILD=26898' "$exp98/app/version.properties" >/dev/null
 (cd "$exp98" && sha256sum -c "$ROOT/26898_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null)
 pass '26898 exact inherited 17 stages plus current real-source DNG/JPG context, 2020 protected, native/GLSL compilers and clean-extract'
 python3 -S verify_26899.py candidate "$WORK/historical_26898_from_26899" "$WORK/historical_26899_replayed"
 python3 -S verify_26899.py semantics "$WORK/historical_26898_from_26899" "$WORK/historical_26899_replayed"
 python3 -S verify_26899.py patch "$WORK/historical_26898_from_26899" "$WORK/historical_26899_replayed" 26899_FORWARD_FULL_INDEX.patch 26899_ROLLBACK_FULL_INDEX.patch
 python3 -S verify_26899.py tamper "$WORK/historical_26898_from_26899" "$WORK/historical_26899_replayed"
 python3 -S test_26899_three_stage_negatives.py
 python3 -S test_26899_modes.py "$WORK/historical_26899_replayed"
 (cd "$WORK/historical_26899_replayed" && sha256sum -c "$ROOT/26899_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null)
 (cd "$WORK/historical_26899_replayed" && sha256sum -c "$ROOT/26899_UNCHANGED_PROTECTED.sha256" >/dev/null)
 sha256sum -c "$OUT/26899_historical_candidate_app_source.tar.gz.sha256" >/dev/null
 local exp99="$WORK/extracted_actual_26899_candidate_tar";rm -rf "$exp99";mkdir -p "$exp99"
 tar -xzf "$OUT/26899_historical_candidate_app_source.tar.gz" -C "$exp99"
 diff -qr "$WORK/historical_26899_replayed"/app "$exp99/app" >/dev/null || fail '26899 final compiled candidate TAR not byte-identical'
 (cd "$exp99" && sha256sum -c "$ROOT/26899_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null)
 pass '26899 inherited all 17 stages + new exact GLES310 2-scale B-only zoom + full final clean-extract'
 python3 -S verify_26900.py candidate "$WORK/historical_26899_from_26900" "$WORK/historical_26900_replayed"
 python3 -S verify_26900.py semantics "$WORK/historical_26899_from_26900" "$WORK/historical_26900_replayed"
 python3 -S verify_26900.py patch "$WORK/historical_26899_from_26900" "$WORK/historical_26900_replayed" 26900_FORWARD_FULL_INDEX.patch 26900_ROLLBACK_FULL_INDEX.patch
 python3 -S verify_26900.py tamper "$WORK/historical_26899_from_26900" "$WORK/historical_26900_replayed"
 python3 -S test_26900_three_stage_negatives.py
 python3 -S test_26900_modes.py "$WORK/historical_26900_replayed"
 (cd "$WORK/historical_26900_replayed" && sha256sum -c "$ROOT/26900_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null)
 (cd "$WORK/historical_26900_replayed" && sha256sum -c "$ROOT/26900_UNCHANGED_PROTECTED.sha256" >/dev/null)
 sha256sum -c "$OUT/26900_historical_candidate_app_source.tar.gz.sha256" >/dev/null
 local exp00="$WORK/extracted_actual_26900_candidate_tar";rm -rf "$exp00";mkdir -p "$exp00"
 tar -xzf "$OUT/26900_historical_candidate_app_source.tar.gz" -C "$exp00"
 diff -qr "$WORK/historical_26900_replayed"/app "$exp00/app" >/dev/null || fail '26900 candidate TAR not byte-identical'
 (cd "$exp00" && sha256sum -c "$ROOT/26900_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null)
 pass '26900 original 17 stages + two exact pinned ESSL310 shaders + 2022 protected and clean extract'
 python3 -S verify_26901.py candidate "$WORK/historical_26900_from_26901" "$WORK/historical_26901_replayed"
 python3 -S verify_26901.py semantics "$WORK/historical_26900_from_26901" "$WORK/historical_26901_replayed"
 python3 -S verify_26901.py patch "$WORK/historical_26900_from_26901" "$WORK/historical_26901_replayed" 26901_FORWARD_FULL_INDEX.patch 26901_ROLLBACK_FULL_INDEX.patch
 python3 -S verify_26901.py tamper "$WORK/historical_26900_from_26901" "$WORK/historical_26901_replayed"
 python3 -S test_26901_three_stage_negatives.py
 python3 -S test_26901_modes.py "$WORK/historical_26901_replayed"
 (cd "$WORK/historical_26901_replayed" && sha256sum -c "$ROOT/26901_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null)
 (cd "$WORK/historical_26901_replayed" && sha256sum -c "$ROOT/26901_UNCHANGED_PROTECTED.sha256" >/dev/null)
 sha256sum -c "$OUT/26901_historical_candidate_app_source.tar.gz.sha256" >/dev/null
 local exp01="$WORK/extracted_actual_26901_candidate_tar";rm -rf "$exp01";mkdir -p "$exp01"
 tar -xzf "$OUT/26901_historical_candidate_app_source.tar.gz" -C "$exp01"
 diff -qr "$WORK/historical_26901_replayed"/app "$exp01/app" >/dev/null || fail '26901 compiled candidate TAR changed'
 (cd "$exp01" && sha256sum -c "$ROOT/26901_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null)
 pass '26901 exact 17-stage successful 26900 inherited; six scoped runtime changes; 2020 protected; real two ESSL310 compilers and final clean extract'
 python3 -S verify_26902.py candidate "$BASE" "$CAND"
 python3 -S verify_26902.py semantics "$BASE" "$CAND"
 python3 -S verify_26902.py patch "$BASE" "$CAND" 26902_FORWARD_FULL_INDEX.patch 26902_ROLLBACK_FULL_INDEX.patch
 python3 -S verify_26902.py tamper "$BASE" "$CAND"
 python3 -S test_26902_three_stage_negatives.py
 python3 -S test_26902_modes.py "$CAND"
 (cd "$CAND" && sha256sum -c "$ROOT/26902_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null)
 (cd "$CAND" && sha256sum -c "$ROOT/26902_UNCHANGED_PROTECTED.sha256" >/dev/null)
 sha256sum -c "$OUT/26902_candidate_app_source.tar.gz.sha256" >/dev/null
 local exp02="$WORK/extracted_actual_26902_candidate_tar";rm -rf "$exp02";mkdir -p "$exp02"
 tar -xzf "$OUT/26902_candidate_app_source.tar.gz" -C "$exp02"
 diff -qr "$CAND/app" "$exp02/app" >/dev/null || fail '26902 candidate actual compiled TAR/source mismatch'
 (cd "$exp02" && sha256sum -c "$ROOT/26902_EXPECTED_CANDIDATE_FULL_APP.sha256" >/dev/null)
 pass '26902 inherited exact successful 26901 17-stage order; three changed, 2023 protected, real pinned shader compiler, clean extract'
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
pass '26902 ALL 17 INHERITED GUARDED STAGES PASSED'
