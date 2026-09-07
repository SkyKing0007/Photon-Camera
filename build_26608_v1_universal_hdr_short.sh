#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
resolve_glslang_compiler(){
  local root="$1" compiler="" compat=""
  compiler="$(find "$root" -type f -name glslang -print -quit)"
  if [[ -z "$compiler" ]]; then compat="$(find "$root" \( -type f -o -type l \) -name glslangValidator -print -quit)"; if [[ -n "$compat" ]]; then compiler="$(readlink -f "$compat" 2>/dev/null || true)"; fi; fi
  [[ -n "$compiler" && -f "$compiler" ]] || return 1; printf '%s\n' "$compiler"
}
ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
BASE_SUCCESS_COMMIT="e4a77eac946e8b56e0ce2b0e6d9a14c3085e3f9a"
MECHANICS_GOLDEN_COMMIT="7c485416a8f41f9bf8a834bf4282e7c2318fa9fb"
HANDOFF_PARENT_COMMIT="e4a77eac946e8b56e0ce2b0e6d9a14c3085e3f9a"
BASE_RUN_ID="34052539419"
BASE_JOB_ID="101538597897"
BASE_ARTIFACT_ID="9995034916"
BASE_ARTIFACT_NAME="photon-26607-v1-universal-highlight-reconstruction"
BASE_ARTIFACT_SHA="adaea99e8d88251eaf544f084d6f7caddb1f52dfe5b978bb4b64978cbbbccb23"
BASE_TAR_SHA="b69c2734015a6f75ad7689280e45e61d940fd90061b13131086eda06e7083199"
VERSION_NAME="0.9726608"
VERSION_BUILD="26608"
GLSLANG_VERSION="16.5.0"
GLSLANG_ARCHIVE_SHA="b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657"
GLSLANG_URL="https://github.com/KhronosGroup/glslang/releases/download/16.5.0/glslang-16.5.0-linux-x86_64-release.tar.gz"
SEALED_PAYLOAD_COUNT=32
HANDOFF="$ROOT/V1_26608_HANDOFF_HASHES.sha256"
BASE_FULL="$ROOT/V1_26608_BASE_26607_V1_FULL_APP.sha256"; CAND_FULL="$ROOT/V1_26608_EXPECTED_CANDIDATE_FULL_APP.sha256"
BASE_PROTECTED="$ROOT/V1_26608_PROTECTED_UNCHANGED_BASE.sha256"; CAND_PROTECTED="$ROOT/V1_26608_PROTECTED_UNCHANGED_CANDIDATE.sha256"
BASE_NATIVE="$ROOT/V1_26608_NATIVE_PROTECTED_BASE.sha256"; CAND_NATIVE="$ROOT/V1_26608_NATIVE_PROTECTED_CANDIDATE.sha256"
BASE_VENDOR="$ROOT/V1_26608_VENDOR_PROTECTED_BASE.sha256"; CAND_VENDOR="$ROOT/V1_26608_VENDOR_PROTECTED_CANDIDATE.sha256"
BASE_DNG="$ROOT/V1_26608_DNG_BASE.sha256"; CAND_DNG="$ROOT/V1_26608_DNG_CANDIDATE.sha256"
CHANGED="$ROOT/V1_26608_RUNTIME_CHANGED_PATHS.txt"; PREWRITE="$ROOT/V1_26608_PREWRITE_SOURCE_HASHES.sha256"; EXPECTED_CHANGED="$ROOT/V1_26608_EXPECTED_CHANGED_SOURCE_HASHES.sha256"
FORWARD="$ROOT/V1_26608_RUNTIME_DELTA_FROM_26607_V1.patch"; ROLLBACK="$ROOT/V1_26608_RUNTIME_ROLLBACK_TO_26607_V1.patch"; SHADER_PIN="$ROOT/V1_26608_RUNTIME_EXPANDED_SHADERS.sha256"
TRANSFORM="$ROOT/transform_26608_v1.py"; VALIDATE="$ROOT/validate_26608_v1.py"; AUTHORITY="$ROOT/verify_26608_v1_authority.py"; INFRA="$ROOT/verify_26608_v1_infrastructure.py"; PATCHVERIFY="$ROOT/verify_26608_v1_patches.py"; SHADERVERIFY="$ROOT/verify_26608_v1_shaders.py"; GATEVERIFY="$ROOT/verify_26608_v1_regressions.py"
BUILD_SCRIPT="$ROOT/build_26608_v1_universal_hdr_short.sh"; WORKFLOW="$ROOT/.github/workflows/build-26608-v1-universal-hdr-short.yml"
OUT="$ROOT/build_26608_v1_universal_hdr_short_outputs"; WORK="$ROOT/.build_26608_v1_universal_hdr_short_work"; ARTZIP="$WORK/26607_v1_artifact.zip"; ARTDIR="$WORK/artifact"; BASE="$WORK/exact_26607_v1_compiled_candidate"; AFTER="$WORK/candidate_26608_v1"; AFTER2="$WORK/candidate_26608_v1_replay"; SHADER_OUT="$WORK/runtime_expanded_shaders"; GLSLANG_DIR="$WORK/glslang-16.5.0"; LIVE_CANON="$WORK/live_compiler_candidate_snapshot"; POST="$WORK/postbuild_source_snapshot"; FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-v1-universal-hdr-short-debug.apk"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"; LOCAL_ART=""; if [[ "${1:-}" == "--local-prebuild" ]]; then [[ -n "${2:-}" ]] || fail "--local-prebuild requires exact successful 26607 V1 artifact ZIP"; LOCAL_ART="$2"; fi
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR" "$BASE" "$AFTER" "$AFTER2"
cat > "$OUT/26608_V1_COMPILER_STATUS.txt" <<'STATUS'
REAL GLSL COMPILE: NOT RUN YET
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
NATIVE/NDK COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
STATUS
cat > "$OUT/26608_V1_STRICT_HANDOFF_REPORT.txt" <<'REPORT'
RUNTIME AUTHORITY: NOT RUN
VERIFICATION MECHANICS AUTHORITY: NOT RUN
BACKUP STATUS: NOT RUN
CHANGED RUNTIME SCOPE: NOT RUN
INFRASTRUCTURE DELTA AUDIT: NOT RUN
NEW RUNTIME AUTHORITY: NOT RUN
SUPERSEDED / NEUTRALIZED AUTHORITY: NOT RUN
UPSTREAM SEMANTIC COMPATIBILITY: NOT RUN
DOWNSTREAM DUPLICATE-AUTHORITY CHECK: NOT RUN
FEEDBACK-LOOP CHECK: NOT RUN
STALE-BEHAVIOR ABSENCE CHECK: NOT RUN
UNIVERSAL HDR SHORT ACQUISITION: NOT RUN
SHORT RESCUE GEOMETRY REGRESSION: NOT RUN
PREVIEW LIFECYCLE REGRESSION: NOT RUN
26605 HDR TRANSPORT INHERITANCE: NOT RUN
LONG OWNERSHIP REGRESSION: NOT RUN
SUPER RES / DNG OWNERSHIP REGRESSION: NOT RUN
EFFECTIVE CONTRIBUTION TELEMETRY: NOT RUN
BASE/CANDIDATE MANIFEST COMPLETENESS: NOT RUN
PROTECTED/DNG/NATIVE/VENDOR INVARIANCE: NOT RUN
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
TARGET VERSION/BUILD: 0.9726608 / 26608
REPORT
set_report(){ local key="$1" val="$2" tmp="$OUT/.report.tmp"; awk -v key="$key:" -v val="$val" 'BEGIN{f=0} index($0,key)==1{print key" "val;f=1;next}{print} END{if(!f)exit 42}' "$OUT/26608_V1_STRICT_HANDOFF_REPORT.txt" > "$tmp" || fail "report key missing $key"; mv "$tmp" "$OUT/26608_V1_STRICT_HANDOFF_REPORT.txt"; }
set_compiler(){ local key="$1" val="$2" tmp="$OUT/.compiler.tmp"; awk -v key="$key:" -v val="$val" 'BEGIN{f=0} index($0,key)==1{print key" "val;f=1;next}{print} END{if(!f)exit 42}' "$OUT/26608_V1_COMPILER_STATUS.txt" > "$tmp" || fail "compiler key missing $key"; mv "$tmp" "$OUT/26608_V1_COMPILER_STATUS.txt"; }
snapshot_candidate_from_authority(){ local authority_root="$1" live_root="$2" dest_root="$3"; rm -rf "$dest_root"; mkdir -p "$dest_root"; cp -a "$authority_root/." "$dest_root/"; rm -rf "$dest_root/app/src"; cp -a "$live_root/app/src" "$dest_root/app/"; cp -a "$live_root/app/build.gradle" "$dest_root/app/build.gradle"; cp -a "$live_root/app/version.properties" "$dest_root/app/version.properties"; }
verify_package(){
  [[ -f "$HANDOFF" ]] || fail "handoff hash manifest missing"; sha256sum -c "$HANDOFF"; [[ "$(wc -l < "$HANDOFF")" -eq "$SEALED_PAYLOAD_COUNT" ]] || fail "sealed payload count"
  [[ "$(wc -l < "$CHANGED")" -eq 5 ]] || fail "runtime allowlist must be 5"; [[ "$(wc -l < "$BASE_FULL")" -eq 1708 && "$(wc -l < "$CAND_FULL")" -eq 1708 ]] || fail "full app count"; [[ "$(wc -l < "$BASE_PROTECTED")" -eq 1703 ]] || fail "protected count"; [[ "$(wc -l < "$BASE_NATIVE")" -eq 802 ]] || fail "native count"; [[ "$(wc -l < "$BASE_VENDOR")" -eq 778 ]] || fail "vendor count"; [[ "$(wc -l < "$BASE_DNG")" -eq 7 ]] || fail "DNG count"
  [[ "$(sha "$BASE_FULL")" == "14964d19d4737248cf834b2074e459e77299ec2d49e41ad47c96013343ec2d6f" ]] || fail "base manifest SHA"; [[ "$(sha "$CAND_FULL")" == "4a0768932bcb3ecdbb24c186d82d9635132a0bbfe7e67d16bedbdf3db1a5b20e" ]] || fail "candidate manifest SHA"; [[ "$(sha "$BASE_PROTECTED")" == "e59e3b6f0543d2b1e0ccb713916f7a67fc716b5e4e0cb7b46ef4af026698bead" ]] || fail "protected manifest SHA"; cmp "$BASE_PROTECTED" "$CAND_PROTECTED" || fail "protected invariance"; [[ "$(sha "$BASE_NATIVE")" == "7a1a107b63493937aac11297743876ca1544bc5e5b92d73fd8b06404cb25660e" ]] || fail "native manifest SHA"; cmp "$BASE_NATIVE" "$CAND_NATIVE" || fail "native invariance"; [[ "$(sha "$BASE_VENDOR")" == "7dbcc5ee5b9040965e431d79c45c5100f559c2b96c50970ca21987c684c825a8" ]] || fail "vendor manifest SHA"; cmp "$BASE_VENDOR" "$CAND_VENDOR" || fail "vendor invariance"; [[ "$(sha "$BASE_DNG")" == "90192bdf78607cc64415343d93aae54bbf17903d5442cab0674b6768faed7eab" ]] || fail "DNG manifest SHA"; cmp "$BASE_DNG" "$CAND_DNG" || fail "DNG invariance"; [[ "$(sha "$PREWRITE")" == "9e87f1228db2c46f51a6403b108434cb452493eb84c6b6517add15f6057c6d3a" ]] || fail "prewrite SHA"; [[ "$(sha "$EXPECTED_CHANGED")" == "6eb8017ff21bb32891fea88b596fb4e5526aca6e84ac0620ace0322d37a62312" ]] || fail "expected changed SHA"; [[ "$(sha "$FORWARD")" == "e42701b389dadda052a05c92b4a4dbebc04146f6894f6f274c1ae6027407bc72" ]] || fail "forward SHA"; [[ "$(sha "$ROLLBACK")" == "8b27c2be94a5df0fe2696dc3c0fb00de48506f6477af02037c8e75558fe6aebb" ]] || fail "rollback SHA"; [[ "$(sha "$SHADER_PIN")" == "e4a83339bb10bc3b858ae6954e45965c54e1656afd2d0a4ae81fe42dbdc1217b" ]] || fail "shader manifest SHA"
  ! awk '{print $2}' "$HANDOFF" | grep -Eq '(^|/)(\.build_|build_.*_outputs|__pycache__)(/|$)|(^|/)app/(build|\.cxx)/|\.pyc$|\.apk$' || fail "transient/generated path sealed in handoff manifest"
  bash -n "$BUILD_SCRIPT"; python3 -S - "$TRANSFORM" "$VALIDATE" "$AUTHORITY" "$INFRA" "$PATCHVERIFY" "$SHADERVERIFY" "$GATEVERIFY" <<'PY'
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
  python3 -S "$INFRA" "$BUILD_SCRIPT" "$WORKFLOW" | tee "$OUT/26608_infrastructure_local.txt"; set_report "INFRASTRUCTURE DELTA AUDIT" "PASS (identity/base/no-backup/5-file scope/universal-HDR/boundary/preview regressions/36-shader coverage only; exact successful-26607 V1 compiler/build mechanics order preserved)"; pass "sealed package syntax/hash/regression contract"
}
verify_scope(){
  if [[ -n "$LOCAL_ART" ]]; then set_report "BACKUP STATUS" "PASS (user explicitly requested no new backup; deterministic rollback packaged)"; set_report "CHANGED RUNTIME SCOPE" "PASS (local sealed handoff; exact 5-file allowlist validated after transform)"; return; fi
  [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch"; [[ "$(git rev-parse HEAD^)" == "$HANDOFF_PARENT_COMMIT" ]] || fail "26608 V1 must be one clean handoff commit directly on successful 26607 V1"
  python3 -S - "$HANDOFF" > "$WORK/expected_scope.txt" <<'PY'
from pathlib import Path
import sys
names=[line.split('  ',1)[1] for line in Path(sys.argv[1]).read_text().splitlines() if line.strip()]
names.append('V1_26608_HANDOFF_HASHES.sha256')
print('\n'.join(sorted(names)))
PY
  git diff --name-only "$HANDOFF_PARENT_COMMIT"..HEAD | sort > "$WORK/actual_scope.txt"; diff -u "$WORK/expected_scope.txt" "$WORK/actual_scope.txt" || fail "handoff commit scope mismatch"; ! grep -Eq '^app/' "$WORK/actual_scope.txt" || fail "handoff commit contains live app source"; set_report "BACKUP STATUS" "PASS (user explicitly requested no new backup; deterministic rollback packaged)"; set_report "CHANGED RUNTIME SCOPE" "PASS (sealed infrastructure/payload only; runtime written only in Actions)"
}
obtain_authority(){
  if [[ -n "$LOCAL_ART" ]]; then cp "$LOCAL_ART" "$ARTZIP"; else [[ -n "$TOKEN" ]] || fail "GITHUB_TOKEN missing"; curl -L --fail --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/${BASE_ARTIFACT_ID}/zip" -o "$ARTZIP"; fi
  [[ "$(sha "$ARTZIP")" == "$BASE_ARTIFACT_SHA" ]] || fail "26607 V1 artifact ZIP SHA"; unzip -q "$ARTZIP" -d "$ARTDIR"; local tarball="$ARTDIR/build_26607_v1_universal_highlight_reconstruction_outputs/26607_V1_candidate_app_source.tar.gz"; [[ -f "$tarball" ]] || fail "compiled 26607 V1 candidate tar missing"; [[ "$(sha "$tarball")" == "$BASE_TAR_SHA" ]] || fail "compiled 26607 V1 candidate tar SHA"; tar -xzf "$tarball" -C "$BASE"; find "$ARTDIR" -type f -name '*.apk' -delete; (cd "$BASE" && sha256sum -c "$BASE_FULL" >/dev/null && sha256sum -c "$BASE_PROTECTED" >/dev/null && sha256sum -c "$BASE_NATIVE" >/dev/null && sha256sum -c "$BASE_VENDOR" >/dev/null && sha256sum -c "$BASE_DNG" >/dev/null && sha256sum -c "$PREWRITE" >/dev/null); set_report "RUNTIME AUTHORITY" "PASS (successful 26607 V1 commit/run/job/artifact exact compiled candidate)"; pass "exact successful 26607 V1 compiled-candidate authority"
}
make_candidate(){
  rm -rf "$AFTER" "$AFTER2"; python3 -S "$TRANSFORM" "$BASE" "$AFTER" | tee "$OUT/26608_transform.txt"; python3 -S "$TRANSFORM" "$BASE" "$AFTER2" | tee "$OUT/26608_transform_replay.txt"; python3 -S - "$AFTER" "$AFTER2" <<'PY'
from pathlib import Path
import hashlib,sys
def H(r):return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((Path(r)/'app').rglob('*')) if p.is_file()}
a,b=H(sys.argv[1]),H(sys.argv[2]);assert a==b, 'candidate transform replay mismatch';print(f'PASS deterministic candidate reconstruction files={len(a)}')
PY
  while IFS= read -r rel; do [[ -n "$rel" ]] || continue; cmp "$ROOT/handoff_payload_26608_v1/$rel" "$AFTER/$rel" || fail "sealed payload differs frozen candidate $rel"; done < "$CHANGED"; python3 -S "$VALIDATE" "$BASE" "$AFTER" | tee "$OUT/26608_semantic_validation.txt"; python3 -S "$GATEVERIFY" "$BASE" "$AFTER" | tee "$OUT/26608_regressions.txt"; python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$AFTER" | tee "$OUT/26608_authority_candidate.txt"; set_report "NEW RUNTIME AUTHORITY" "PASS (successful-26607 one-tunnel/float-HDR/tone architecture retained; capture now requests SHORT for coherent exposure-domain dynamic-range conflict and literal clipping, while measurable SHORT boundaries require local residual proof)"; set_report "SUPERSEDED / NEUTRALIZED AUTHORITY" "PASS (26607 literal-near-clip-only capture limitation and predictor-overridable measurable SHORT boundary are superseded; deep two-phase censored core rescue remains inherited)"; set_report "UPSTREAM SEMANTIC COMPATIBILITY" "PASS (successful-26607 HAL AE, immutable burst roles, Camera2 color, common Sabre RBF, Resolve/VGN and float-HDR architecture inherited; existing 26380 AE sampler byte-identical)"; set_report "DOWNSTREAM DUPLICATE-AUTHORITY CHECK" "PASS (one common Sabre accumulator/Resolve/VGN and one post-VGN extended-linear HDR master; no private SHORT compositor; tone/UHDR owners unchanged)"; set_report "FEEDBACK-LOOP CHECK" "PASS (new HDR evidence is read-only in separate dithered sampler; existing AE/readiness sampler unchanged; no tone/viewfinder feedback added)"; set_report "STALE-BEHAVIOR ABSENCE CHECK" "PASS (no detached GLPreview fallback; stale Fragment cannot clear newer controller; old private SHORT owners remain dormant)"; set_report "UNIVERSAL HDR SHORT ACQUISITION" "PASS (broad DR + mixed dark/bright + compact coherent sub-clipping fixtures request SHORT; ordinary/safe/low-light/single-cell fixtures fail closed; no scene classifier)"; set_report "SHORT RESCUE GEOMETRY REGRESSION" "PASS (measurable boundaries require local residual proof; neighborhood predictor cannot override bad boundary match; two-phase censored core retains 26607 rescue; final 0.75-percent source guard unchanged)"; set_report "PREVIEW LIFECYCLE REGRESSION" "PASS (controller binds exact current Fragment GLPreview; inherited generation-deduplicated late-listener replay preserved; stale destroy protected)"; set_report "26605 HDR TRANSPORT INHERITANCE" "PASS (RGBA16F physical carrier + normalized subordinate VGN proxy + post-VGN extended master preserved)"; set_report "LONG OWNERSHIP REGRESSION" "PASS (normal Motion LONG captured-but-excluded; Night LONG common-Sabre only)"; set_report "SUPER RES / DNG OWNERSHIP REGRESSION" "PASS (SHORT remains excluded from high-frequency SR detail and DNG; common HDR master remains SR guide)"; set_report "EFFECTIVE CONTRIBUTION TELEMETRY" "PASS (capture reason and boundary/core ownership measured; direct accumulator delta, Resolve effect and final output preservation remain device-authority states)"; set_report "BASE/CANDIDATE MANIFEST COMPLETENESS" "PASS (1708 full / 1703 protected / 802 native / 778 vendor / 7 DNG)"; set_report "PROTECTED/DNG/NATIVE/VENDOR INVARIANCE" "PASS";
}
verify_candidate_patches(){ python3 -S "$PATCHVERIFY" "$BASE" "$AFTER" "$FORWARD" "$ROLLBACK" | tee "$OUT/26608_patch_validation.txt"; set_report "FORWARD PATCH FUZZ=0" "PASS"; set_report "ROLLBACK PATCH FUZZ=0" "PASS"; }
verify_shaders(){
  rm -rf "$SHADER_OUT"; mkdir -p "$SHADER_OUT"
  if [[ -n "$LOCAL_ART" ]]; then python3 -S "$SHADERVERIFY" "$BASE" "$AFTER" --out "$SHADER_OUT" | tee "$OUT/26608_shader_validation.txt"; cmp "$SHADER_OUT/V1_26608_RUNTIME_EXPANDED_SHADERS.sha256" "$SHADER_PIN" || fail "local shader pin mismatch"; cp "$SHADER_OUT/V1_26608_SHADER_VERIFICATION.json" "$OUT/26608_shader_verification.json"; set_report "RUNTIME-EXPANDED GLSL RESERVED SCAN" "PASS (36 exact variants; successful-26607 coverage with 26608 protected component/rescue boundary variants)"; set_report "REAL GLSL COMPILE" "NOT RUN locally (Actions required)"; set_compiler "REAL GLSL COMPILE" "NOT RUN locally (Actions required)"; return; fi
  mkdir -p "$GLSLANG_DIR"; local archive="$WORK/glslang-${GLSLANG_VERSION}.tar.gz"; curl -L --fail --retry 3 "$GLSLANG_URL" -o "$archive"; [[ "$(sha "$archive")" == "$GLSLANG_ARCHIVE_SHA" ]] || fail "glslang archive SHA"; tar -tzf "$archive" > "$OUT/26608_glslang_archive_contents.txt"; tar -xzf "$archive" -C "$GLSLANG_DIR"; local compiler; compiler="$(resolve_glslang_compiler "$GLSLANG_DIR")" || fail "glslang missing"; chmod +x "$compiler"; "$compiler" --version | tee "$OUT/26608_glslang_version.txt"; python3 -S "$SHADERVERIFY" "$BASE" "$AFTER" --out "$SHADER_OUT" --glslang "$compiler" | tee "$OUT/26608_shader_validation.txt"; cmp "$SHADER_OUT/V1_26608_RUNTIME_EXPANDED_SHADERS.sha256" "$SHADER_PIN" || fail "Actions shader pin mismatch"; cp "$SHADER_OUT/V1_26608_SHADER_VERIFICATION.json" "$OUT/26608_shader_verification.json"; set_report "RUNTIME-EXPANDED GLSL RESERVED SCAN" "PASS (36 exact variants; successful-26607 coverage with 26608 protected component/rescue boundary variants)"; set_report "REAL GLSL COMPILE" "PASS (pinned Khronos glslangValidator 16.5.0)"; set_compiler "REAL GLSL COMPILE" "PASS (pinned Khronos glslangValidator 16.5.0)"
}
install_and_build(){
  [[ -z "$LOCAL_ART" ]] || return 0
  local success26607Script="$WORK/successful_26607_v1_build.sh" success26607Workflow="$WORK/successful_26607_v1_workflow.yml" golden26593Script="$WORK/successful_26593_build.sh" golden26593Workflow="$WORK/successful_26593_workflow.yml"
  curl -L --fail --retry 3 "https://raw.githubusercontent.com/SkyKing0007/Photon-Camera/$BASE_SUCCESS_COMMIT/build_26607_v1_universal_highlight_reconstruction.sh" -o "$success26607Script"; curl -L --fail --retry 3 "https://raw.githubusercontent.com/SkyKing0007/Photon-Camera/$BASE_SUCCESS_COMMIT/.github/workflows/build-26607-v1-universal-highlight-reconstruction.yml" -o "$success26607Workflow"
  curl -L --fail --retry 3 "https://raw.githubusercontent.com/SkyKing0007/Photon-Camera/$MECHANICS_GOLDEN_COMMIT/build_26593_v1_total_frame_hdr_ownership.sh" -o "$golden26593Script"; curl -L --fail --retry 3 "https://raw.githubusercontent.com/SkyKing0007/Photon-Camera/$MECHANICS_GOLDEN_COMMIT/.github/workflows/build-26593-v1-total-frame-hdr-ownership.yml" -o "$golden26593Workflow"
  python3 -S "$INFRA" "$BUILD_SCRIPT" "$WORKFLOW" --success-26607-script "$success26607Script" --success-26607-workflow "$success26607Workflow" --golden-26593-script "$golden26593Script" --golden-26593-workflow "$golden26593Workflow" | tee "$OUT/26608_infrastructure_actions.txt"; set_report "VERIFICATION MECHANICS AUTHORITY" "PASS (exact successful-26607 V1 implementation/order/pins + successful-26593 compiler/build order)"
  rm -rf "$ROOT/app/src"; cp -a "$AFTER/app/src" "$ROOT/app/"; cp -a "$AFTER/app/build.gradle" "$ROOT/app/build.gradle"; cp -a "$AFTER/app/version.properties" "$ROOT/app/version.properties"; snapshot_candidate_from_authority "$BASE" "$ROOT" "$LIVE_CANON"; python3 -S "$VALIDATE" "$BASE" "$LIVE_CANON" | tee "$OUT/26608_live_semantic_validation.txt"; python3 -S "$GATEVERIFY" "$BASE" "$LIVE_CANON" | tee "$OUT/26608_live_regressions.txt"; python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$LIVE_CANON" | tee "$OUT/26608_live_authority.txt"; python3 -S - "$AFTER" "$LIVE_CANON" <<'PY'
from pathlib import Path
import hashlib,sys
def H(r):return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((Path(r)/'app').rglob('*')) if p.is_file()}
a,b=H(sys.argv[1]),H(sys.argv[2]);assert a==b,'live compiler candidate differs frozen candidate';print(f'PASS authority-seeded live compiler candidate byte-identical files={len(a)}')
PY
  ./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace 2>&1 | tee "$OUT/26608_gradle_language_compilers.log"; set_report "REAL KOTLIN COMPILE" "PASS"; set_report "REAL JAVA COMPILE" "PASS"; set_compiler "REAL KOTLIN COMPILE" "PASS"; set_compiler "REAL JAVA COMPILE" "PASS"
  ./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace 2>&1 | tee "$OUT/26608_gradle_native_compiler.log"; set_report "REAL NATIVE/NDK COMPILE" "PASS (both ABIs)"; set_compiler "NATIVE/NDK COMPILE" "PASS (both ABIs)"
  verify_candidate_patches; set_report "PRE-BUILD SAFETY PROOF" "PASS"; pass "26608 PRE-BUILD SAFETY PROOF PASSED"
  ./gradlew :app:assembleDebug --stacktrace 2>&1 | tee "$OUT/26608_gradle_assemble.log"; set_report "FULL ANDROID ASSEMBLE" "PASS"; set_compiler "FULL ANDROID ASSEMBLE" "PASS"
  mapfile -t apks < <(find "$ROOT/app/build/outputs/apk/debug" -type f -name '*.apk' | sort); [[ "${#apks[@]}" -eq 1 ]] || fail "expected exactly one Gradle debug APK"; mv "${apks[0]}" "$FINAL"; mapfile -t roots < <(find "$ROOT" -maxdepth 1 -type f -name '*.apk' | sort); [[ "${#roots[@]}" -eq 1 && "${roots[0]}" == "$FINAL" ]] || fail "exactly one final root APK"; sha256sum "$FINAL" > "$OUT/26608_V1_APK.sha256"; set_report "EXACTLY ONE APK" "PASS"
  snapshot_candidate_from_authority "$BASE" "$ROOT" "$POST"; python3 -S "$VALIDATE" "$BASE" "$POST" | tee "$OUT/26608_postbuild_semantic_validation.txt"; python3 -S "$GATEVERIFY" "$BASE" "$POST" | tee "$OUT/26608_postbuild_regressions.txt"; python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$POST" | tee "$OUT/26608_postbuild_authority.txt"; python3 -S - "$AFTER" "$POST" <<'PY'
from pathlib import Path
import hashlib,sys
def H(r):return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((Path(r)/'app').rglob('*')) if p.is_file()}
a,b=H(sys.argv[1]),H(sys.argv[2]);assert a==b,'postbuild candidate differs frozen candidate';print(f'PASS authority-seeded postbuild candidate byte-identical files={len(a)}')
PY
  set_report "POST-BUILD INVARIANCE" "PASS (candidate/protected/DNG/native/vendor exact)"; set_compiler "POST-BUILD INVARIANCE" "PASS"; tar --sort=name --mtime='UTC 1970-01-01' --owner=0 --group=0 --numeric-owner -cf - -C "$POST" app | gzip -n > "$OUT/26608_V1_candidate_app_source.tar.gz"; sha256sum "$OUT/26608_V1_candidate_app_source.tar.gz" > "$OUT/26608_V1_candidate_app_source.tar.gz.sha256"; cp "$CAND_FULL" "$OUT/26608_V1_candidate_full_app.sha256"; cp "$CAND_NATIVE" "$OUT/26608_V1_native_protected_postbuild.sha256"; cp "$CAND_VENDOR" "$OUT/26608_V1_vendor_protected_postbuild.sha256"; set_report "CLEAN ARTIFACT SOURCE EXPORT" "PASS (deterministic candidate tar + manifests)"
}
verify_package
verify_scope
obtain_authority
make_candidate
verify_shaders
if [[ -n "$LOCAL_ART" ]]; then verify_candidate_patches; set_report "VERIFICATION MECHANICS AUTHORITY" "PASS (exact successful-26607 V1 implementation/order/pins packaged; real compiler replay requires Actions)"; set_report "PRE-BUILD SAFETY PROOF" "NOT RUN (real pinned GLSL + Kotlin/Java/NDK/full Android gates require Actions)"; set_report "CLEAN ARTIFACT SOURCE EXPORT" "NOT RUN (local prebuild stops before Android build)"; cp "$OUT/26608_V1_STRICT_HANDOFF_REPORT.txt" "$OUT/26608_local_prebuild_report.txt"; pass "26608 V1 LOCAL PREBUILD PREPARED: exact successful-26607 V1 authority + 26608 universal-HDR/boundary/preview architecture/patch/static-shader gates passed; real GLSL/Kotlin/Java/NDK/full Android gates explicitly unproven locally"; exit 0; fi
install_and_build
pass "26608 V1 REAL GLSL + KOTLIN/JAVA + NDK + FULL ASSEMBLE PASSED"
pass "26608 V1 POST-BUILD INVARIANCE PASSED"
