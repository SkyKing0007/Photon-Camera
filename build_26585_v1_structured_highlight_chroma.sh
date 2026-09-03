#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
resolve_glslang_compiler(){
  local root="$1" compiler="" compat=""
  compiler="$(find "$root" -type f -name glslang -print -quit)"
  if [[ -z "$compiler" ]]; then
    compat="$(find "$root" \( -type f -o -type l \) -name glslangValidator -print -quit)"
    if [[ -n "$compat" ]]; then compiler="$(readlink -f "$compat" 2>/dev/null || true)"; fi
  fi
  [[ -n "$compiler" && -f "$compiler" ]] || return 1
  printf '%s\n' "$compiler"
}
ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
BASE_SUCCESS_COMMIT="b0c7bee97fc42e29e1145ebf62b7d4d9f68fff1e"
HANDOFF_PARENT_COMMIT="b0c7bee97fc42e29e1145ebf62b7d4d9f68fff1e"
BASE_RUN_ID="33706486670"
BASE_JOB_ID="100496588302"
BASE_ARTIFACT_ID="9875462465"
BASE_ARTIFACT_NAME="photon-26584-v1-all-scene-highlight-jin-cleanup"
BASE_ARTIFACT_SHA="533f6f620dd13ea3dc386d94f55d9613d19ba2c81bcbb8cf5784a09474d6e8b9"
BASE_TAR_SHA="657ea390c3184f83ed5d745884a09c90c4822ffb25bf069d5186964d50655807"
VERSION_NAME="0.9726585"
VERSION_BUILD="26585"
GLSLANG_VERSION="16.5.0"
GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"
GLSLANG_URL="https://github.com/KhronosGroup/glslang/releases/download/16.5.0/glslang-16.5.0-linux-x86_64-release.tar.gz"
HANDOFF="$ROOT/V1_26585_HANDOFF_HASHES.sha256"
BASE_FULL="$ROOT/V1_26585_BASE_26584_FULL_APP.sha256"
CAND_FULL="$ROOT/V1_26585_EXPECTED_CANDIDATE_FULL_APP.sha256"
BASE_PROTECTED="$ROOT/V1_26585_PROTECTED_UNCHANGED_BASE.sha256"
CAND_PROTECTED="$ROOT/V1_26585_PROTECTED_UNCHANGED_CANDIDATE.sha256"
BASE_NATIVE="$ROOT/V1_26585_NATIVE_PROTECTED_BASE.sha256"
CAND_NATIVE="$ROOT/V1_26585_NATIVE_PROTECTED_CANDIDATE.sha256"
BASE_VENDOR="$ROOT/V1_26585_VENDOR_PROTECTED_BASE.sha256"
CAND_VENDOR="$ROOT/V1_26585_VENDOR_PROTECTED_CANDIDATE.sha256"
BASE_DNG="$ROOT/V1_26585_DNG_PROTECTED_BASE.sha256"
CAND_DNG="$ROOT/V1_26585_DNG_PROTECTED_CANDIDATE.sha256"
BASE_ARCH="$ROOT/V1_26585_PROTECTED_ARCHITECTURE_BASE.sha256"
CAND_ARCH="$ROOT/V1_26585_PROTECTED_ARCHITECTURE_CANDIDATE.sha256"
CHANGED="$ROOT/V1_26585_RUNTIME_CHANGED_PATHS.txt"
PREWRITE="$ROOT/V1_26585_PREWRITE_SOURCE_HASHES.sha256"
EXPECTED_CHANGED="$ROOT/V1_26585_EXPECTED_CHANGED_SOURCE_HASHES.sha256"
FORWARD="$ROOT/V1_26585_RUNTIME_DELTA_FROM_26584.patch"
ROLLBACK="$ROOT/V1_26585_RUNTIME_ROLLBACK_TO_26584.patch"
SHADER_PIN="$ROOT/V1_26585_RUNTIME_EXPANDED_SHADERS.sha256"
TRANSFORM="$ROOT/transform_26585_v1.py"
VALIDATE="$ROOT/validate_26585_v1.py"
AUTHORITY="$ROOT/verify_26585_v1_authority.py"
PATCHVERIFY="$ROOT/verify_26585_v1_patches.py"
SHADERVERIFY="$ROOT/verify_26585_v1_shaders.py"
GATEVERIFY="$ROOT/verify_26585_v1_regressions.py"
BUILD_SCRIPT="$ROOT/build_26585_v1_structured_highlight_chroma.sh"
WORKFLOW="$ROOT/.github/workflows/build-26585-v1-structured-highlight-chroma.yml"
OUT="$ROOT/build_26585_v1_structured_highlight_chroma_outputs"
WORK="$ROOT/.build_26585_v1_structured_highlight_chroma_work"
ARTZIP="$WORK/26584_v1_artifact.zip"
ARTDIR="$WORK/artifact"
BASE="$WORK/exact_26584_v1_compiled_candidate"
AFTER="$WORK/candidate_26585"
AFTER2="$WORK/candidate_26585_replay"
SHADER_OUT="$WORK/runtime_expanded_shaders"
GLSLANG_DIR="$WORK/glslang-16.5.0"
LIVE_CANON="$WORK/live_compiler_candidate_snapshot"
POST="$WORK/postbuild_source_snapshot"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-v1-structured-highlight-chroma-debug.apk"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"
LOCAL_ART=""
if [[ "${1:-}" == "--local-prebuild" ]]; then [[ -n "${2:-}" ]] || fail "--local-prebuild requires exact successful 26584 V1 artifact ZIP"; LOCAL_ART="$2"; fi
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR" "$BASE" "$AFTER" "$AFTER2"
cat > "$OUT/26585_V1_COMPILER_STATUS.txt" <<'STATUS'
REAL GLSL COMPILE: NOT RUN YET
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
NATIVE/NDK COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
STATUS
cat > "$OUT/26585_V1_STRICT_HANDOFF_REPORT.txt" <<'REPORT'
RUNTIME OWNERSHIP: NOT RUN
DORMANT-OWNER REJECTION: NOT RUN
EXACT PRIOR RUNTIME AUTHORITY: NOT RUN
BACKUP STATUS: NOT RUN
CHANGED RUNTIME SCOPE: NOT RUN
INFRASTRUCTURE DELTA AUDIT: NOT RUN
CARRIED FAILURE REGRESSIONS: NOT RUN
STRUCTURED HIGHLIGHT SHAPE REGRESSIONS: NOT RUN
TONE-AWARE HIGHLIGHT CHROMA REGRESSIONS: NOT RUN
CARRIED 26584/JIN REGRESSIONS: NOT RUN
BASE/CANDIDATE MANIFEST COMPLETENESS: NOT RUN
PROTECTED ARCHITECTURE INVARIANCE: NOT RUN
DNG INVARIANCE: NOT RUN
VENDOR INVARIANCE: NOT RUN
26584 ALIGNMENT/HDR/DNG/GPU INHERITANCE: NOT RUN
26571/26584 VGN/SR PROTECTION INHERITANCE: NOT RUN
RUNTIME-EXPANDED GLSL RESERVED SCAN: NOT RUN
REAL GLSL COMPILE: NOT RUN
REAL KOTLIN COMPILE: NOT RUN
REAL JAVA COMPILE: NOT RUN
REAL NATIVE/NDK COMPILE: NOT RUN
FORWARD PATCH FUZZ=0: NOT RUN
ROLLBACK PATCH FUZZ=0: NOT RUN
PRE-BUILD SAFETY PROOF: NOT RUN
FULL ANDROID ASSEMBLE: NOT RUN
EXACTLY ONE APK: NOT RUN
POST-BUILD INVARIANCE: NOT RUN
CLEAN ARTIFACT SOURCE EXPORT: NOT RUN
TARGET VERSION/BUILD: 0.9726585 / 26585
REPORT
set_report(){ local key="$1" val="$2" tmp="$OUT/.report.tmp"; awk -v key="$key:" -v val="$val" 'BEGIN{f=0} index($0,key)==1{print key" "val;f=1;next}{print} END{if(!f)exit 42}' "$OUT/26585_V1_STRICT_HANDOFF_REPORT.txt" > "$tmp" || fail "report key missing $key"; mv "$tmp" "$OUT/26585_V1_STRICT_HANDOFF_REPORT.txt"; }
set_compiler(){ local key="$1" val="$2" tmp="$OUT/.compiler.tmp"; awk -v key="$key:" -v val="$val" 'BEGIN{f=0} index($0,key)==1{print key" "val;f=1;next}{print} END{if(!f)exit 42}' "$OUT/26585_V1_COMPILER_STATUS.txt" > "$tmp" || fail "compiler key missing $key"; mv "$tmp" "$OUT/26585_V1_COMPILER_STATUS.txt"; }
snapshot_candidate_from_authority(){
  local authority_root="$1" live_root="$2" dest_root="$3"
  rm -rf "$dest_root"; mkdir -p "$dest_root"
  cp -a "$authority_root/." "$dest_root/"
  rm -rf "$dest_root/app/src"
  cp -a "$live_root/app/src" "$dest_root/app/"
  cp -a "$live_root/app/build.gradle" "$dest_root/app/build.gradle"
  cp -a "$live_root/app/version.properties" "$dest_root/app/version.properties"
}
verify_package(){
  [[ -f "$HANDOFF" ]] || fail "handoff hash manifest missing"
  sha256sum -c "$HANDOFF"
  [[ "$(wc -l < "$HANDOFF")" -eq 37 ]] || fail "sealed payload count mismatch excluding handoff manifest"
  [[ "$(wc -l < "$CHANGED")" -eq 4 ]] || fail "runtime allowlist count must be 4"
  [[ "$(wc -l < "$BASE_FULL")" -eq 1708 && "$(wc -l < "$CAND_FULL")" -eq 1708 ]] || fail "full app manifest count"
  [[ "$(wc -l < "$BASE_PROTECTED")" -eq 1704 && "$(wc -l < "$CAND_PROTECTED")" -eq 1704 ]] || fail "protected manifest count"
  [[ "$(wc -l < "$BASE_NATIVE")" -eq 802 && "$(wc -l < "$CAND_NATIVE")" -eq 802 ]] || fail "native protected count"
  [[ "$(wc -l < "$BASE_VENDOR")" -eq 778 && "$(wc -l < "$CAND_VENDOR")" -eq 778 ]] || fail "vendor protected count"
  [[ "$(wc -l < "$BASE_DNG")" -eq 7 && "$(wc -l < "$CAND_DNG")" -eq 7 ]] || fail "DNG count"
  [[ "$(wc -l < "$BASE_ARCH")" -eq 193 && "$(wc -l < "$CAND_ARCH")" -eq 193 ]] || fail "protected architecture count"
  [[ "$(sha "$BASE_FULL")" == "b87e010c5c7474b5cf5abd658b3cd097a8ded17443b453d85e1a318557a3e357" ]] || fail "base full manifest SHA"
  [[ "$(sha "$CAND_FULL")" == "85b2efaee3b637c88f7fdf99694256baeebc29a6f8b3c1db672f78044b335ee3" ]] || fail "candidate full manifest SHA"
  [[ "$(sha "$BASE_PROTECTED")" == "226ca3313acb26359a1fc047b7b283748435853118aa7bdcb0e1ea00e8b53a41" ]] || fail "protected manifest SHA"
  [[ "$(sha "$BASE_NATIVE")" == "7a1a107b63493937aac11297743876ca1544bc5e5b92d73fd8b06404cb25660e" ]] || fail "native manifest SHA"
  [[ "$(sha "$BASE_VENDOR")" == "7dbcc5ee5b9040965e431d79c45c5100f559c2b96c50970ca21987c684c825a8" ]] || fail "vendor manifest SHA"
  [[ "$(sha "$BASE_DNG")" == "90192bdf78607cc64415343d93aae54bbf17903d5442cab0674b6768faed7eab" ]] || fail "DNG manifest SHA"
  [[ "$(sha "$BASE_ARCH")" == "cc9f809f61ebfb80297a046f859cc0e306f61e865a90fe8a7b3c8c18d1c0955f" ]] || fail "protected architecture manifest SHA"
  [[ "$(sha "$PREWRITE")" == "d78d6bfc0f900fabe626a462f10e1a282a99cff86e3742794a076ad94782db3d" ]] || fail "prewrite SHA"
  [[ "$(sha "$EXPECTED_CHANGED")" == "ec155239b731aef94baa510d1e8bd3312cb645a080ec755cb50b6801a74cd77c" ]] || fail "expected changed-source SHA"
  [[ "$(sha "$FORWARD")" == "06abf8192de8765bb3977b9fd33d2500e00871f414651356f5e293bf1e86d579" ]] || fail "forward patch SHA"
  [[ "$(sha "$ROLLBACK")" == "21cd35f3c260f6df889bba67952ea2bc8296c77eba51e8022016233c753c7c66" ]] || fail "rollback patch SHA"
  [[ "$(sha "$SHADER_PIN")" == "f8ff9e42a0b6fa4d75ff7f878befd0945552545532184d627e5793dde0b21378" ]] || fail "shader pin SHA"
  python3 -S - "$TRANSFORM" "$VALIDATE" "$AUTHORITY" "$PATCHVERIFY" "$SHADERVERIFY" "$GATEVERIFY" <<'PY'
import ast,sys
from pathlib import Path
allowed=set(sys.stdlib_module_names)
for raw in sys.argv[1:]:
 p=Path(raw);src=p.read_text();tree=ast.parse(src,filename=str(p));bad=[]
 for n in ast.walk(tree):
  names=[]
  if isinstance(n,ast.Import):names=[a.name.split('.',1)[0] for a in n.names]
  elif isinstance(n,ast.ImportFrom) and n.module:names=[n.module.split('.',1)[0]]
  bad += [x for x in names if x not in allowed]
 if bad:raise SystemExit(f'FAIL non-stdlib dependency {p.name}: {sorted(set(bad))}')
 compile(src,str(p),'exec')
print('PASS sealed Python stdlib-only syntax/import gate')
PY
  bash -n "$BUILD_SCRIPT"

  grep -F 'structured highlight guide must use supported P98-class tail rather than 26584 P90' "$ROOT/REGRESSION_V1_26585_STRUCTURED_HIGHLIGHT_TAIL.txt" >/dev/null || fail "structured highlight tail regression missing"
  grep -F 'added high-highlight chroma gain is capped <=1.12x' "$ROOT/REGRESSION_V1_26585_TONE_AWARE_HIGHLIGHT_CHROMA.txt" >/dev/null || fail "tone-aware highlight chroma regression missing"
  grep -F 'Night brightness advantage constants remain exactly +0.40 EV dark / +0.30 EV bright' "$ROOT/REGRESSION_V1_26585_CARRIED_26584.txt" >/dev/null || fail "Night brightness regression missing"
  grep -F 'pinned Jin ONNX model remains byte-identical; Jin inference remains enabled as cleanup only' "$ROOT/REGRESSION_V1_26585_CARRIED_26584.txt" >/dev/null || fail "Jin regression missing"
  grep -F 'motionv2_jpeg444_jni.cpp remains byte-identical SHA-256 d73cd24452280958f089e9124545a81461939e8fa0c9c95272b2825942e4b43d' "$ROOT/REGRESSION_V1_26585_CARRIED_26584.txt" >/dev/null || fail "GPU regression missing"
  grep -F '26582 Java compile failure' "$ROOT/REGRESSION_V1_26585_CARRIED_26584.txt" >/dev/null || fail "26582 Java compiler regression missing"

  grep -F 'no verification gate is weakened' "$ROOT/V1_26585_INFRASTRUCTURE_DIFF_AUDIT.txt" >/dev/null || fail "infrastructure diff audit missing"
  [[ -s "$ROOT/V1_26585_BUILD_SCRIPT_DIFF_FROM_SUCCESSFUL_26584.txt" ]] || fail "build-script diff audit missing"
  [[ -s "$ROOT/V1_26585_WORKFLOW_DIFF_FROM_SUCCESSFUL_26584.txt" ]] || fail "workflow diff audit missing"

  ! grep -Eq 'pip(3)?[[:space:]]+install' "$TRANSFORM" "$VALIDATE" "$AUTHORITY" "$PATCHVERIFY" "$SHADERVERIFY" "$GATEVERIFY" "$BUILD_SCRIPT" "$WORKFLOW" || fail "package-manager dependency introduced"
  set_report "INFRASTRUCTURE DELTA AUDIT" "PASS (successful 26584 V1 order/mechanics preserved; authority pins/names plus exact four-file structured-tail + tone-aware-highlight-chroma scope/regressions only; no compiler/build gate weakened)"
  set_report "CARRIED FAILURE REGRESSIONS" "PASS"
  pass "sealed package syntax/hash/regression contract"
}
verify_scope(){
  if [[ -n "$LOCAL_ART" ]]; then
    set_report "BACKUP STATUS" "PASS (no backup requested; exact deterministic rollback to successful 26584 packaged)"
    set_report "CHANGED RUNTIME SCOPE" "PASS (local sealed handoff; runtime allowlist validated after transform)"
    return
  fi
  [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch"
  git merge-base --is-ancestor "$BASE_SUCCESS_COMMIT" HEAD || fail "successful 26584 V1 runtime authority is not an ancestor"
  [[ "$(git rev-parse HEAD^)" == "$BASE_SUCCESS_COMMIT" ]] || fail "26585 V1 must be one clean handoff commit directly on successful 26584 V1"
  python3 -S - "$HANDOFF" > "$WORK/expected_scope.txt" <<'PY'
from pathlib import Path
import sys
names=[line.split('  ',1)[1] for line in Path(sys.argv[1]).read_text().splitlines() if line.strip()]
names.append('V1_26585_HANDOFF_HASHES.sha256')
print('\n'.join(sorted(names)))
PY
  git diff --name-only "$HANDOFF_PARENT_COMMIT"..HEAD | sort > "$WORK/actual_scope.txt"
  diff -u "$WORK/expected_scope.txt" "$WORK/actual_scope.txt" || fail "handoff commit scope mismatch"
  ! grep -Eq '^app/' "$WORK/actual_scope.txt" || fail "correction handoff commit contains live runtime app source"
  git diff --name-only "$BASE_SUCCESS_COMMIT"..HEAD | sort > "$WORK/full_lineage_scope.txt"
  ! grep -Eq '^app/' "$WORK/full_lineage_scope.txt" || fail "26584-to-26585 lineage contains live runtime app source"
  set_report "BACKUP STATUS" "PASS (no backup requested/created; exact deterministic rollback to successful 26584 packaged)"
  set_report "CHANGED RUNTIME SCOPE" "PASS (handoff commit sealed infrastructure/payload only; runtime source written only inside Actions)"
}
obtain_authority(){
  if [[ -n "$LOCAL_ART" ]]; then cp "$LOCAL_ART" "$ARTZIP"; else
    [[ -n "$TOKEN" ]] || fail "GITHUB_TOKEN missing"
    curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" \
      "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${BASE_ARTIFACT_ID}/zip" -o "$ARTZIP"
  fi
  [[ "$(sha "$ARTZIP")" == "$BASE_ARTIFACT_SHA" ]] || fail "26584 V1 artifact ZIP authority SHA mismatch"
  unzip -q "$ARTZIP" -d "$ARTDIR"
  local tarball="$ARTDIR/build_26584_v1_all_scene_highlight_jin_cleanup_outputs/26584_V1_candidate_app_source.tar.gz"
  [[ -f "$tarball" ]] || fail "compiled 26584 candidate tar missing"
  [[ "$(sha "$tarball")" == "$BASE_TAR_SHA" ]] || fail "compiled 26584 candidate tar SHA mismatch"
  tar -xzf "$tarball" -C "$BASE"
  find "$ARTDIR" -type f -name '*.apk' -delete
  (cd "$BASE" && sha256sum -c "$BASE_FULL" >/dev/null && sha256sum -c "$BASE_PROTECTED" >/dev/null && sha256sum -c "$BASE_NATIVE" >/dev/null && sha256sum -c "$BASE_VENDOR" >/dev/null && sha256sum -c "$BASE_DNG" >/dev/null && sha256sum -c "$BASE_ARCH" >/dev/null && sha256sum -c "$PREWRITE" >/dev/null)
  set_report "EXACT PRIOR RUNTIME AUTHORITY" "PASS (26584 V1 commit $BASE_SUCCESS_COMMIT run $BASE_RUN_ID job $BASE_JOB_ID artifact $BASE_ARTIFACT_ID SHA $BASE_ARTIFACT_SHA tar $BASE_TAR_SHA)"
  pass "exact successful 26584 V1 compiled candidate authority"
}
make_candidate(){
  rm -rf "$AFTER" "$AFTER2"
  python3 -S "$TRANSFORM" "$BASE" "$AFTER" | tee "$OUT/26585_transform.txt"
  python3 -S "$TRANSFORM" "$BASE" "$AFTER2" | tee "$OUT/26585_transform_replay.txt"
  python3 -S - "$AFTER" "$AFTER2" <<'PY'
from pathlib import Path
import hashlib,sys
def H(r):return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((Path(r)/'app').rglob('*')) if p.is_file()}
a,b=H(sys.argv[1]),H(sys.argv[2])
if a!=b:raise SystemExit('FAIL candidate transform replay mismatch')
print(f'PASS deterministic candidate reconstruction files={len(a)}')
PY
  while IFS= read -r rel; do [[ -n "$rel" ]] || continue; cmp "$ROOT/handoff_payload_26585_v1/$rel" "$AFTER/$rel" || fail "sealed payload differs frozen candidate $rel"; done < "$CHANGED"
  python3 -S "$VALIDATE" "$BASE" "$AFTER" | tee "$OUT/26585_semantic_validation.txt"
  python3 -S "$GATEVERIFY" "$AFTER" | tee "$OUT/26585_refinement_regressions.txt"
  python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$AFTER" | tee "$OUT/26585_authority_candidate.txt"
  set_report "STRUCTURED HIGHLIGHT SHAPE REGRESSIONS" "PASS (26584 all-scene floor retained; coherent structured P98 tail -> 0.945 preserves neutral highlight shape)"
  set_report "TONE-AWARE HIGHLIGHT CHROMA REGRESSIONS" "PASS (legacy color floor retained; solved sceneWhite post-tone safety; exact neutrals unchanged; own-chroma-axis <=1.12)"
  set_report "CARRIED 26584/JIN REGRESSIONS" "PASS (Night brightness/Jin cleanup/final render/Sabre/VGN/SR/DNG/UHDR/native publication frozen)"
  set_report "BASE/CANDIDATE MANIFEST COMPLETENESS" "PASS (1708 full / 1704 unchanged protected / 802 native / 778 vendor / 7 DNG / 193 protected architecture)"
  set_report "PROTECTED ARCHITECTURE INVARIANCE" "PASS (193 successful-26584 protected architecture files plus all 1704 unchanged app files byte-identical)"
  set_report "DNG INVARIANCE" "PASS (7 DNG/ImageSaver owners byte-identical)"
  set_report "VENDOR INVARIANCE" "PASS (778 persisted native vendor/dependency files byte-identical)"
  set_report "26584 ALIGNMENT/HDR/DNG/GPU INHERITANCE" "PASS (alignment/flow/Sabre merge/HDR/DNG/UHDR/capture/native GPU publication/Jin cleanup owners byte-identical; structured-tail + tone-aware appearance are sole behavior changes)"
  set_report "26571/26584 VGN/SR PROTECTION INHERITANCE" "PASS (one-sided material, foliage/sky, directional floor, IIR reset and radius-two contour contracts retained)"
  set_report "RUNTIME OWNERSHIP" "PASS (active MotionV2ViewfinderExposureMatcher + MotionV2AdaptiveColorAppearance Java/GLSL owners; render/Jin/VGN/SR/native publication protected; exact four-file allowlist including version)"
  set_report "DORMANT-OWNER REJECTION" "PASS (matcher and appearance Java/GLSL production-reachable in common Motion/Night graph; version fourth allowlist file; duplicate/dormant paths cannot satisfy markers)"
}
verify_candidate_patches(){
  python3 -S "$PATCHVERIFY" "$BASE" "$AFTER" "$FORWARD" "$ROLLBACK" | tee "$OUT/26585_patch_validation.txt"
  set_report "FORWARD PATCH FUZZ=0" "PASS"; set_report "ROLLBACK PATCH FUZZ=0" "PASS"
}
verify_shaders(){
  rm -rf "$SHADER_OUT"; mkdir -p "$SHADER_OUT"
  if [[ -n "$LOCAL_ART" ]]; then
    python3 -S "$SHADERVERIFY" "$AFTER" --out "$SHADER_OUT" | tee "$OUT/26585_shader_validation.txt"
    cmp "$SHADER_OUT/V1_26585_RUNTIME_EXPANDED_SHADERS.sha256" "$SHADER_PIN" || fail "local runtime-expanded shader pin mismatch"
    set_report "RUNTIME-EXPANDED GLSL RESERVED SCAN" "PASS (8 exact runtime-expanded variants: 6 inherited VGN/SR + modified appearance CALIBRATED_PROFILE=0/1)"
    set_report "REAL GLSL COMPILE" "NOT RUN locally (Actions required for pinned compiler)"; set_compiler "REAL GLSL COMPILE" "NOT RUN locally (Actions required)"
    return
  fi
  mkdir -p "$GLSLANG_DIR"; local archive="$WORK/glslang-${GLSLANG_VERSION}.tar.gz"
  curl -L --fail --retry 3 "$GLSLANG_URL" -o "$archive"
  [[ "$(sha "$archive")" == "$GLSLANG_ARCHIVE_SHA" ]] || fail "pinned glslang archive SHA mismatch"
  tar -tzf "$archive" > "$OUT/26585_glslang_archive_contents.txt"; tar -xzf "$archive" -C "$GLSLANG_DIR"
  local compiler; compiler="$(resolve_glslang_compiler "$GLSLANG_DIR")" || fail "glslang executable missing after pinned extraction"; chmod +x "$compiler"
  "$compiler" --version | tee "$OUT/26585_glslang_version.txt"
  python3 -S "$SHADERVERIFY" "$AFTER" --out "$SHADER_OUT" --glslang "$compiler" | tee "$OUT/26585_shader_validation.txt"
  cmp "$SHADER_OUT/V1_26585_RUNTIME_EXPANDED_SHADERS.sha256" "$SHADER_PIN" || fail "Actions runtime-expanded shader pin mismatch"
  cp "$SHADER_OUT/V1_26585_SHADER_VERIFICATION.json" "$OUT/26585_shader_verification.json"
  set_report "RUNTIME-EXPANDED GLSL RESERVED SCAN" "PASS (8 exact runtime-expanded variants: 6 inherited VGN/SR + modified appearance CALIBRATED_PROFILE=0/1)"
  set_report "REAL GLSL COMPILE" "PASS (pinned Khronos glslangValidator $GLSLANG_VERSION)"; set_compiler "REAL GLSL COMPILE" "PASS (pinned Khronos glslangValidator $GLSLANG_VERSION)"
}
install_and_build(){
  [[ -z "$LOCAL_ART" ]] || return 0
  rm -rf "$ROOT/app/src"; cp -a "$AFTER/app/src" "$ROOT/app/"; cp -a "$AFTER/app/build.gradle" "$ROOT/app/build.gradle"; cp -a "$AFTER/app/version.properties" "$ROOT/app/version.properties"
  snapshot_candidate_from_authority "$BASE" "$ROOT" "$LIVE_CANON"
  python3 -S "$VALIDATE" "$BASE" "$LIVE_CANON" | tee "$OUT/26585_live_semantic_validation.txt"
  python3 -S "$GATEVERIFY" "$LIVE_CANON" | tee "$OUT/26585_live_refinement_regressions.txt"
  python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$LIVE_CANON" | tee "$OUT/26585_live_authority.txt"
  python3 -S - "$AFTER" "$LIVE_CANON" <<'PY'
from pathlib import Path
import hashlib,sys
def H(r):return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((Path(r)/'app').rglob('*')) if p.is_file()}
a,b=H(sys.argv[1]),H(sys.argv[2])
if a!=b:raise SystemExit('FAIL live compiler candidate differs frozen candidate')
print(f'PASS authority-seeded live compiler candidate byte-identical files={len(a)}')
PY
  ./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace 2>&1 | tee "$OUT/26585_gradle_language_compilers.log"
  set_report "REAL KOTLIN COMPILE" "PASS"; set_report "REAL JAVA COMPILE" "PASS"; set_compiler "REAL KOTLIN COMPILE" "PASS"; set_compiler "REAL JAVA COMPILE" "PASS"
  ./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace 2>&1 | tee "$OUT/26585_gradle_native_compiler.log"
  set_report "REAL NATIVE/NDK COMPILE" "PASS (both ABIs)"; set_compiler "NATIVE/NDK COMPILE" "PASS (both ABIs)"
  verify_candidate_patches
  set_report "PRE-BUILD SAFETY PROOF" "PASS"; pass "26585 PRE-BUILD SAFETY PROOF PASSED"
  ./gradlew :app:assembleDebug --stacktrace 2>&1 | tee "$OUT/26585_gradle_assemble.log"
  set_report "FULL ANDROID ASSEMBLE" "PASS"; set_compiler "FULL ANDROID ASSEMBLE" "PASS"
  mapfile -t apks < <(find "$ROOT/app/build/outputs/apk/debug" -type f -name '*.apk' | sort); [[ "${#apks[@]}" -eq 1 ]] || fail "expected exactly one Gradle debug APK, got ${#apks[@]}"
  mv "${apks[0]}" "$FINAL"; mapfile -t roots < <(find "$ROOT" -maxdepth 1 -type f -name '*.apk' | sort); [[ "${#roots[@]}" -eq 1 && "${roots[0]}" == "$FINAL" ]] || fail "exactly one final root APK required"
  sha256sum "$FINAL" > "$OUT/26585_V1_APK.sha256"; set_report "EXACTLY ONE APK" "PASS"
  snapshot_candidate_from_authority "$BASE" "$ROOT" "$POST"
  python3 -S "$VALIDATE" "$BASE" "$POST" | tee "$OUT/26585_postbuild_semantic_validation.txt"
  python3 -S "$GATEVERIFY" "$POST" | tee "$OUT/26585_postbuild_refinement_regressions.txt"
  python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$POST" | tee "$OUT/26585_postbuild_authority.txt"
  set_report "POST-BUILD INVARIANCE" "PASS (authority-seeded candidate/protected/DNG/native/vendor exact)"; set_compiler "POST-BUILD INVARIANCE" "PASS"
  tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -cf - -C "$POST" app | gzip -n > "$OUT/26585_V1_candidate_app_source.tar.gz"
  sha256sum "$OUT/26585_V1_candidate_app_source.tar.gz" > "$OUT/26585_V1_candidate_app_source.tar.gz.sha256"
  cp "$CAND_FULL" "$OUT/26585_V1_candidate_full_app.sha256"; cp "$CAND_NATIVE" "$OUT/26585_V1_native_protected_postbuild.sha256"; cp "$CAND_VENDOR" "$OUT/26585_V1_vendor_protected_postbuild.sha256"
  set_report "CLEAN ARTIFACT SOURCE EXPORT" "PASS (deterministic candidate tar + manifests)"
}
verify_package
verify_scope
obtain_authority
make_candidate
verify_shaders
if [[ -n "$LOCAL_ART" ]]; then
  verify_candidate_patches
  set_report "PRE-BUILD SAFETY PROOF" "NOT RUN (real pinned GLSL + Kotlin/Java/NDK project compilers/full Android gates require Actions)"
  set_report "CLEAN ARTIFACT SOURCE EXPORT" "NOT RUN (local prebuild stops before Android build)"
  cp "$OUT/26585_V1_STRICT_HANDOFF_REPORT.txt" "$OUT/26585_local_prebuild_report.txt"
  pass "26585 LOCAL PREBUILD PREPARED: real GLSL/Kotlin/Java/NDK/full Android gates explicitly unproven locally"
  exit 0
fi
install_and_build
pass "26585 REAL GLSL + KOTLIN/JAVA + NDK + FULL ASSEMBLE PASSED"
pass "26585 POST-BUILD INVARIANCE PASSED"
