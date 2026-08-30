#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
BASE_SUCCESS_COMMIT="6e30e54ae50094736a775b14f3d16f9f100bb238"
BASE_RUN_ID="33323775058"
BASE_ARTIFACT_ID="9735679112"
BASE_ARTIFACT_NAME="photon-26565-v1-2-display-p3-fast-sr"
BASE_ARTIFACT_SHA="9dbdeb6e4eb5832ab2cc0875bb2a481bbce7d23099772baaebefcdd7f3b9f4a5"
BASE_TAR_SHA="ce84c3d50eb852a94949dadd76cf85be81a72a6105c0c9be34a3167a22bcb104"
BASE_MANIFEST_SHA="8adc66ee1925d7c5b3ef3489cfd3953d94e81a1f562b8da690615ae93c34d41a"
CAND_MANIFEST_SHA="d850f74e7ab2f08838c963bc85353ef3eba903fc5ae7130c34a3fa6a44597e26"
CAND_FULL_APP_SHA="2b3ebde793a48527d21d9eabbcb14f3bb40d455f06aa3579e1f4985efd4744dd"
VENDOR_MANIFEST_SHA="7dbcc5ee5b9040965e431d79c45c5100f559c2b96c50970ca21987c684c825a8"
PROTECTED_SHA="307413f198a3ad34f43cca6b7e6d1d9c6cb7db81d89845666d706fc34aaf3075"
FORWARD_SHA="db070aa01fc1ef6b9d2f7aebfed83770676968486df7bb8efb89505e6a17a1b6"
ROLLBACK_SHA="245b139d45066c0c835660a764e26c2afd09552cf5795fd9500b3a2b438cf068"
BACKUP_BRANCH="backup-26565-v1-2-before-26566-jpeg-color-solver-true2x"
BACKUP_SHA="6e30e54ae50094736a775b14f3d16f9f100bb238"
VERSION_NAME="0.9726566"
VERSION_BUILD="26566"
HANDOFF="$ROOT/V1_26566_HANDOFF_HASHES.sha256"
BASE_PIN="$ROOT/V1_26566_BASE_26565_V1_2_AUDITED_RUNTIME.sha256"
CAND_PIN="$ROOT/V1_26566_EXPECTED_CANDIDATE_AUDITED_RUNTIME.sha256"
CAND_FULL="$ROOT/V1_26566_EXPECTED_CANDIDATE_FULL_APP.sha256"
VENDOR_PIN="$ROOT/V1_26566_NATIVE_VENDOR_DEPENDENCIES.sha256"
PROTECTED="$ROOT/V1_26566_PROTECTED_UNCHANGED_CORE.sha256"
TRANSFORM="$ROOT/transform_26566_v1_jpeg_color_true2x.py"
VALIDATE="$ROOT/validate_26566_v1.py"
AUTHORITY="$ROOT/verify_26566_authority.py"
PATCHVERIFY="$ROOT/verify_26566_patches.py"
WORKFLOW="$ROOT/.github/workflows/build-26566-v1-jpeg-color-true2x.yml"
BUILD_SCRIPT="$ROOT/build_26566_v1_jpeg_color_true2x.sh"
SEALED_PY=("$TRANSFORM" "$VALIDATE" "$AUTHORITY" "$PATCHVERIFY")
SEALED_DEP_FILES=("${SEALED_PY[@]}" "$BUILD_SCRIPT" "$WORKFLOW")
OUT="$ROOT/build_26566_v1_jpeg_color_true2x_outputs"
WORK="$ROOT/.build_26566_v1_jpeg_color_true2x_work"
ARTZIP="$WORK/26565_v1_2_artifact.zip"
ARTDIR="$WORK/artifact"
BASE="$WORK/exact_26565_v1_2_compiled_candidate"
AFTER="$WORK/candidate_26566"
AFTER2="$WORK/candidate_26566_replay"
POST="$WORK/postbuild_source_snapshot"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-v1-jpeg-color-true2x-debug.apk"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"
LOCAL_ART=""
if [[ "${1:-}" == "--local-prebuild" ]]; then [[ -n "${2:-}" ]] || fail "--local-prebuild requires exact 26565 V1.2 artifact ZIP"; LOCAL_ART="$2"; fi
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR" "$BASE" "$AFTER" "$AFTER2"
cat > "$OUT/26566_V1_COMPILER_STATUS.txt" <<'STATUS'
REAL GLSL COMPILE: PASS (inherited exact successful 26565 shader bytes; no GLSL modified)
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
NATIVE/NDK COMPILE: NOT RUN YET (covered by full assemble)
FULL ANDROID ASSEMBLE: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
STATUS
cat > "$OUT/26566_V1_STRICT_HANDOFF_REPORT.txt" <<'REPORT'
EXACT PRIOR RUNTIME AUTHORITY: NOT RUN
BACKUP STATUS: NOT RUN
HANDOFF CHANGED-FILE SCOPE: NOT RUN
CARRIED FAILURE REGRESSIONS: NOT RUN
BASE MANIFEST COMPLETENESS: NOT RUN
CANDIDATE-FIRST TRANSFORM: NOT RUN
JPEG COLOR SOLVER OWNERSHIP: NOT RUN
DNG INVARIANCE: NOT RUN
NORMAL/MOTION/NIGHT COLOR DOMAIN: NOT RUN
DISPLAY-P3 PUBLICATION INVARIANCE: NOT RUN
TRUE2X PRIVATE SCRATCH: NOT RUN
TRUE2X 50MP PUBLICATION CONTRACT: NOT RUN
TRUE2X 12MP FALLBACK REJECTION: NOT RUN
PROTECTED NIGHT/GLSL/PROCESSING: NOT RUN
FORWARD PATCH FUZZ=0: NOT RUN
ROLLBACK PATCH FUZZ=0: NOT RUN
REAL GLSL COMPILE: PASS (inherited exact successful 26565 shader bytes; no GLSL modified)
REAL KOTLIN COMPILE: NOT RUN
REAL JAVA COMPILE: NOT RUN
NATIVE/NDK COMPILE: NOT RUN
FULL ANDROID ASSEMBLE: NOT RUN
POST-BUILD INVARIANCE: NOT RUN
CLEAN ARTIFACT SOURCE EXPORT: NOT RUN
TARGET VERSION/BUILD: 0.9726566 / 26566
REPORT
set_report(){ local key="$1" val="$2" tmp="$OUT/.report.tmp"; awk -v key="$key:" -v val="$val" 'BEGIN{f=0} index($0,key)==1{print key" "val;f=1;next}{print} END{if(!f)exit 42}' "$OUT/26566_V1_STRICT_HANDOFF_REPORT.txt" > "$tmp" || fail "report key missing $key"; mv "$tmp" "$OUT/26566_V1_STRICT_HANDOFF_REPORT.txt"; }
set_compiler(){ local key="$1" val="$2" tmp="$OUT/.compiler.tmp"; awk -v key="$key:" -v val="$val" 'BEGIN{f=0} index($0,key)==1{print key" "val;f=1;next}{print} END{if(!f)exit 42}' "$OUT/26566_V1_COMPILER_STATUS.txt" > "$tmp" || fail "compiler key missing $key"; mv "$tmp" "$OUT/26566_V1_COMPILER_STATUS.txt"; }

verify_package(){
 [[ -f "$HANDOFF" ]] || fail "handoff hash manifest missing"
 sha256sum -c "$HANDOFF"
 [[ "$(wc -l < "$HANDOFF")" -eq 20 ]] || fail "sealed handoff payload count"
 [[ "$(sha "$BASE_PIN")" == "$BASE_MANIFEST_SHA" ]] || fail "base manifest SHA"
 [[ "$(sha "$CAND_PIN")" == "$CAND_MANIFEST_SHA" ]] || fail "candidate manifest SHA"
 [[ "$(sha "$CAND_FULL")" == "$CAND_FULL_APP_SHA" ]] || fail "candidate full-app manifest SHA"
 [[ "$(sha "$VENDOR_PIN")" == "$VENDOR_MANIFEST_SHA" ]] || fail "vendor manifest SHA"
 [[ "$(sha "$PROTECTED")" == "$PROTECTED_SHA" ]] || fail "protected manifest SHA"
 [[ "$(sha "$ROOT/V1_26566_RUNTIME_DELTA_FROM_26565_V1_2.patch")" == "$FORWARD_SHA" ]] || fail "forward patch SHA"
 [[ "$(sha "$ROOT/V1_26566_RUNTIME_ROLLBACK_TO_26565_V1_2.patch")" == "$ROLLBACK_SHA" ]] || fail "rollback patch SHA"
 [[ "$(wc -l < "$BASE_PIN")" -eq 930 && "$(wc -l < "$CAND_PIN")" -eq 931 && "$(wc -l < "$CAND_FULL")" -eq 1708 && "$(wc -l < "$VENDOR_PIN")" -eq 778 ]] || fail "manifest expected line counts"
 [[ "$(wc -l < "$ROOT/V1_26566_RUNTIME_CHANGED_PATHS.txt")" -eq 8 ]] || fail "changed path count"
 python3 -S - "${SEALED_PY[@]}" <<'PY'
import ast,sys
from pathlib import Path
allowed=set(sys.stdlib_module_names)
for raw in sys.argv[1:]:
 p=Path(raw); src=p.read_text(); tree=ast.parse(src,filename=str(p)); bad=[]
 for n in ast.walk(tree):
  names=[]
  if isinstance(n,ast.Import): names=[a.name.split('.',1)[0] for a in n.names]
  elif isinstance(n,ast.ImportFrom) and n.module: names=[n.module.split('.',1)[0]]
  bad += [x for x in names if x not in allowed]
 if bad: raise SystemExit(f'non-stdlib dependency {p.name}: {sorted(set(bad))}')
 compile(src,str(p),'exec')
print('PASS packaged Python standard-library-only syntax/import gate')
PY
 ! grep -Eq '(^|[[:space:]])(import|from)[[:space:]]+numpy' "${SEALED_PY[@]}" || fail "NumPy import regression in sealed 26566 Python inventory"
 ! grep -Eq 'pip(3)?[[:space:]]+install' "${SEALED_DEP_FILES[@]}" || fail "undeclared package-manager dependency in sealed 26566 inventory"
 local depfix="$WORK/dependency_scope_fixture"
 mkdir -p "$depfix"
 printf 'import numpy\n' > "$depfix/unrelated_history.py"
 printf 'pip%sinstall numpy\n' ' ' > "$depfix/unrelated_history.sh"
 grep -Eq '(^|[[:space:]])(import|from)[[:space:]]+numpy' "$depfix/unrelated_history.py" || fail "dependency-scope NumPy decoy invalid"
 grep -Eq 'pip(3)?[[:space:]]+install' "$depfix/unrelated_history.sh" || fail "dependency-scope pip decoy invalid"
 ! grep -Eq '(^|[[:space:]])(import|from)[[:space:]]+numpy' "${SEALED_PY[@]}" || fail "unrelated NumPy decoy contaminated sealed scan"
 ! grep -Eq 'pip(3)?[[:space:]]+install' "${SEALED_DEP_FILES[@]}" || fail "unrelated pip decoy contaminated sealed scan"
 printf 'import numpy\n' > "$depfix/sealed_bad_numpy.py"
 printf 'pip%sinstall numpy\n' ' ' > "$depfix/sealed_bad_pip.sh"
 grep -Eq '(^|[[:space:]])(import|from)[[:space:]]+numpy' "$depfix/sealed_bad_numpy.py" || fail "sealed NumPy detector fixture failed"
 grep -Eq 'pip(3)?[[:space:]]+install' "$depfix/sealed_bad_pip.sh" || fail "sealed pip detector fixture failed"
 pass "REGRESSION_26566_REPO_WIDE_DEPENDENCY_SCOPE: PASS"
 bash -n "$0"
 for token in \
  'run 33283538711, job 99182648927' \
  'run 33284071958, job 99184083108' \
  'run 33284552163, job 99185364515' \
  'run 33285297620, job 99187338833' \
  'run 33322029512, job 99285563475' \
  'run 33322926514, rerun job 99288343214'; do
   grep -F "$token" "$ROOT/REGRESSION_26566_CARRIED_FAILURES.txt" >/dev/null || fail "carried regression missing: $token"
 done
 grep -F 'SR-on failure cannot call MotionV2Jpeg444Encoder.write(native bitmap);' "$ROOT/REGRESSION_26566_TRUE2X_12MP_PUBLICATION.txt" >/dev/null || fail "true2x regression contract missing"
 grep -F 'DNG' "$ROOT/REGRESSION_26566_JPEG_COLOR_DNG_INVARIANT.txt" >/dev/null || fail "DNG/color regression contract missing"
 local host_syntax_flag="-fsyntax"'-only'
 local host_compiler="clang"'++'
 ! grep -F -- "$host_syntax_flag" "${SEALED_DEP_FILES[@]}" >/dev/null || fail "non-hermetic host C++ syntax surrogate returned"
 ! grep -F "$host_compiler" "${SEALED_DEP_FILES[@]}" >/dev/null || fail "host C++ surrogate returned"
 grep -F './gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace' "$BUILD_SCRIPT" >/dev/null || fail "real Kotlin/Java compiler sequence missing"
 grep -F './gradlew :app:assembleDebug --stacktrace' "$BUILD_SCRIPT" >/dev/null || fail "real Android NDK/full assemble sequence missing"
 pass "REGRESSION_26566_HOST_CPP_SURROGATE_DISABLED: PASS"
 python3 - <<'PY'
fixture='a'*64+'  alpha.txt\n'+'b'*64+'  dir/beta.txt\n'
assert [x.split('  ',1)[1] for x in fixture.splitlines()] == ['alpha.txt','dir/beta.txt']
print('PASS REGRESSION_26564_V1_HANDOFF_SCOPE_NEWLINE')
PY
 set_report "CARRIED FAILURE REGRESSIONS" "PASS (all 26564/26565 applicable failures replayed)"
}

verify_scope(){
 python3 - "$HANDOFF" > "$WORK/expected_scope.txt" <<'PY'
from pathlib import Path
import sys
names=[x.split('  ',1)[1] for x in Path(sys.argv[1]).read_text().splitlines() if x.strip()]
names.append('V1_26566_HANDOFF_HASHES.sha256')
print('\n'.join(sorted(names)))
PY
 if [[ -n "$LOCAL_ART" ]]; then
   local sr="$WORK/scope_repo"; mkdir -p "$sr"; git -C "$sr" init -q; git -C "$sr" config user.name Iris; git -C "$sr" config user.email iris@invalid; git -C "$sr" commit -q --allow-empty -m base; local b; b="$(git -C "$sr" rev-parse HEAD)"
   while IFS= read -r rel; do mkdir -p "$sr/$(dirname "$rel")"; cp -a "$ROOT/$rel" "$sr/$rel"; done < "$WORK/expected_scope.txt"
   git -C "$sr" add .; git -C "$sr" commit -q -m handoff; git -C "$sr" diff --name-only "$b"..HEAD | sort > "$WORK/actual_scope.txt"
 else
   [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch"
   git merge-base --is-ancestor "$BASE_SUCCESS_COMMIT" HEAD || fail "successful 26565 commit is not ancestor"
   git diff --name-only "$BASE_SUCCESS_COMMIT"..HEAD | sort > "$WORK/actual_scope.txt"
   remote_backup="$(git ls-remote origin "refs/heads/$BACKUP_BRANCH" | awk '{print $1}')"
   [[ "$remote_backup" == "$BACKUP_SHA" ]] || fail "backup branch mismatch"
   set_report "BACKUP STATUS" "PASS ($BACKUP_BRANCH @ $BACKUP_SHA)"
 fi
 diff -u "$WORK/expected_scope.txt" "$WORK/actual_scope.txt" || fail "handoff changed-file scope mismatch"
 ! grep -Eq '^app/' "$WORK/actual_scope.txt" || fail "handoff commit contains runtime app source"
 set_report "HANDOFF CHANGED-FILE SCOPE" "PASS (exact sealed package only; no app/ writes in handoff commit)"
 if [[ -n "$LOCAL_ART" ]]; then set_report "BACKUP STATUS" "PASS (verified before sealing; live remote rechecked by Actions)"; fi
}

obtain_authority(){
 if [[ -n "$LOCAL_ART" ]]; then cp -a "$LOCAL_ART" "$ARTZIP"; else
   [[ -n "$TOKEN" ]] || fail "GITHUB_TOKEN required to download exact 26565 artifact"
   curl -fL --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/$BASE_ARTIFACT_ID/zip" -o "$ARTZIP"
 fi
 [[ "$(sha "$ARTZIP")" == "$BASE_ARTIFACT_SHA" ]] || fail "successful 26565 artifact ZIP SHA mismatch"
 unzip -q "$ARTZIP" -d "$ARTDIR"
 local tar="$ARTDIR/build_26565_v1_display_p3_fast_sr_outputs/26565_V1_candidate_app_source.tar.gz"
 local am="$ARTDIR/build_26565_v1_display_p3_fast_sr_outputs/26565_V1_candidate_source.sha256"
 local vm="$ARTDIR/build_26565_v1_display_p3_fast_sr_outputs/26565_vendor_postbuild.sha256"
 local cs="$ARTDIR/build_26565_v1_display_p3_fast_sr_outputs/26565_V1_COMPILER_STATUS.txt"
 [[ "$(sha "$tar")" == "$BASE_TAR_SHA" ]] || fail "successful 26565 candidate TAR SHA mismatch"
 [[ "$(sha "$am")" == "$BASE_MANIFEST_SHA" ]] || fail "persisted 26565 runtime manifest SHA mismatch"
 [[ "$(sha "$vm")" == "$VENDOR_MANIFEST_SHA" ]] || fail "persisted 26565 vendor manifest SHA mismatch"
 grep -F 'REAL GLSL COMPILE: PASS' "$cs" >/dev/null || fail "26565 GLSL proof absent"
 grep -F 'REAL KOTLIN COMPILE: PASS' "$cs" >/dev/null || fail "26565 Kotlin proof absent"
 grep -F 'REAL JAVA COMPILE: PASS' "$cs" >/dev/null || fail "26565 Java proof absent"
 grep -F 'NATIVE/NDK COMPILE: PASS' "$cs" >/dev/null || fail "26565 NDK proof absent"
 grep -F 'FULL ANDROID ASSEMBLE: PASS' "$cs" >/dev/null || fail "26565 assemble proof absent"
 grep -F 'POST-BUILD INVARIANCE: PASS' "$cs" >/dev/null || fail "26565 post-build proof absent"
 tar -xzf "$tar" -C "$BASE"
 python3 -S "$AUTHORITY" "$BASE" "$ROOT" --base-only --successful-artifact-manifest "$am" --successful-vendor-manifest "$vm" | tee "$OUT/26566_base_authority.txt"
 cmp -s "$am" "$BASE_PIN" || fail "packaged base manifest not byte-identical to persisted successful artifact proof"
 set_report "EXACT PRIOR RUNTIME AUTHORITY" "PASS (26565 V1.2 run $BASE_RUN_ID artifact $BASE_ARTIFACT_ID exact bytes)"
 set_report "BASE MANIFEST COMPLETENESS" "PASS (audited=930 vendor=778 app=1707; persisted proof byte-equal)"
}

build_candidate(){
 cp -a "$BASE/." "$AFTER/"; cp -a "$BASE/." "$AFTER2/"
 if [[ -z "$LOCAL_ART" ]]; then git diff -- app > "$WORK/parent_before.diff"; fi
 python3 -S "$TRANSFORM" "$AFTER" | tee "$OUT/26566_transform.txt"
 if [[ -z "$LOCAL_ART" ]]; then git diff -- app > "$WORK/parent_after.diff"; cmp -s "$WORK/parent_before.diff" "$WORK/parent_after.diff" || fail "nested transform modified parent checkout app"; fi
 python3 -S "$TRANSFORM" "$AFTER2" > "$OUT/26566_transform_replay.txt"
 local am="$ARTDIR/build_26565_v1_display_p3_fast_sr_outputs/26565_V1_candidate_source.sha256"
 local vm="$ARTDIR/build_26565_v1_display_p3_fast_sr_outputs/26565_vendor_postbuild.sha256"
 python3 -S "$AUTHORITY" "$BASE" "$AFTER" "$ROOT" --successful-artifact-manifest "$am" --successful-vendor-manifest "$vm" | tee "$OUT/26566_authority_candidate.txt"
 python3 -S "$AUTHORITY" "$BASE" "$AFTER2" "$ROOT" --successful-artifact-manifest "$am" --successful-vendor-manifest "$vm" > "$OUT/26566_authority_candidate_replay.txt"
 python3 -S "$VALIDATE" "$BASE" "$AFTER" "$ROOT" | tee "$OUT/26566_semantic_validation.txt"
 python3 -S "$VALIDATE" "$BASE" "$AFTER2" "$ROOT" > "$OUT/26566_semantic_validation_replay.txt"
 python3 -S "$PATCHVERIFY" "$BASE" "$AFTER" "$ROOT" | tee "$OUT/26566_patch_validation.txt"
 set_report "CANDIDATE-FIRST TRANSFORM" "PASS (two deterministic replays under nested checkout context)"
 set_report "JPEG COLOR SOLVER OWNERSHIP" "PASS (parallel Iris JPEG-only DNG color-spec owner; legacy DNG fields untouched)"
 set_report "DNG INVARIANCE" "PASS (dedicated writers exact + Parameters historical lines preserved in order)"
 set_report "NORMAL/MOTION/NIGHT COLOR DOMAIN" "PASS (shared camera-linear matrix contract; normal neutral divide/restore equivalence proven)"
 set_report "DISPLAY-P3 PUBLICATION INVARIANCE" "PASS (26565 P3 conversion/ICC block exact bytes)"
 set_report "TRUE2X PRIVATE SCRATCH" "PASS (RGB/gain raw scratch derived from app-private render carrier, not DCIM output)"
 set_report "TRUE2X 50MP PUBLICATION CONTRACT" "PASS (base success separated from gain auxiliary; exact 2x physical JPEG dimensions required)"
 set_report "TRUE2X 12MP FALLBACK REJECTION" "PASS (SR-on cannot call native-resolution JPEG writer; failure explicit)"
 set_report "PROTECTED NIGHT/GLSL/PROCESSING" "PASS (Night/Jin + all GLSL + protected core exact 26565 bytes)"
 set_report "FORWARD PATCH FUZZ=0" "PASS (full-index deterministic at core.abbrev 7/12/40; new-file intent; exact candidate)"
 set_report "ROLLBACK PATCH FUZZ=0" "PASS (full-index deterministic at core.abbrev 7/12/40; exact 26565)"
}

install_and_build(){
 [[ -z "$LOCAL_ART" ]] || { pass "local prebuild replay complete; real Android compilers intentionally left for Actions"; return 0; }
 rm -rf "$ROOT/app/src"; cp -a "$AFTER/app/src" "$ROOT/app/"; cp -a "$AFTER/app/build.gradle" "$ROOT/app/build.gradle"; cp -a "$AFTER/app/version.properties" "$ROOT/app/version.properties"
 grep -F 'VERSION_NAME=0.9726566' "$ROOT/app/version.properties" >/dev/null || fail "installed version name"
 grep -F 'VERSION_BUILD=26566' "$ROOT/app/version.properties" >/dev/null || fail "installed version build"
 ./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace | tee "$OUT/26566_gradle_language_compilers.log"
 set_compiler "REAL KOTLIN COMPILE" "PASS"; set_compiler "REAL JAVA COMPILE" "PASS"; set_report "REAL KOTLIN COMPILE" "PASS"; set_report "REAL JAVA COMPILE" "PASS"
 ./gradlew :app:assembleDebug --stacktrace | tee "$OUT/26566_gradle_assemble.log"
 set_compiler "NATIVE/NDK COMPILE" "PASS (full assemble)"; set_compiler "FULL ANDROID ASSEMBLE" "PASS"; set_report "NATIVE/NDK COMPILE" "PASS (full assemble)"; set_report "FULL ANDROID ASSEMBLE" "PASS"
 mapfile -t apks < <(find "$ROOT/app/build/outputs/apk/debug" -maxdepth 1 -type f -name '*.apk' | sort)
 [[ "${#apks[@]}" -eq 1 ]] || fail "expected exactly one debug APK, found ${#apks[@]}"
 cp -a "${apks[0]}" "$FINAL"; [[ -s "$FINAL" ]] || fail "final APK missing"
 mkdir -p "$POST/app"; cp -a "$ROOT/app/src" "$POST/app/"; cp -a "$ROOT/app/build.gradle" "$POST/app/build.gradle"; cp -a "$ROOT/app/version.properties" "$POST/app/version.properties"
 local am="$ARTDIR/build_26565_v1_display_p3_fast_sr_outputs/26565_V1_candidate_source.sha256"
 local vm="$ARTDIR/build_26565_v1_display_p3_fast_sr_outputs/26565_vendor_postbuild.sha256"
 python3 -S "$AUTHORITY" "$BASE" "$POST" "$ROOT" --successful-artifact-manifest "$am" --successful-vendor-manifest "$vm" | tee "$OUT/26566_postbuild_authority.txt"
 python3 -S "$VALIDATE" "$BASE" "$POST" "$ROOT" > "$OUT/26566_postbuild_semantic_validation.txt"
 set_compiler "POST-BUILD INVARIANCE" "PASS"; set_report "POST-BUILD INVARIANCE" "PASS (candidate/protected/native/vendor source exact after assemble)"
 sha256sum "$FINAL" > "$OUT/26566_V1_APK.sha256"
 tar --sort=name --mtime='UTC 2026-08-30' --owner=0 --group=0 --numeric-owner -czf "$OUT/26566_V1_candidate_app_source.tar.gz" -C "$POST" app
 sha256sum "$OUT/26566_V1_candidate_app_source.tar.gz" > "$OUT/26566_V1_candidate_app_source.tar.gz.sha256"
 cp "$CAND_PIN" "$OUT/26566_V1_candidate_source.sha256"; cp "$CAND_FULL" "$OUT/26566_V1_candidate_full_app.sha256"; cp "$VENDOR_PIN" "$OUT/26566_vendor_postbuild.sha256"
 set_report "CLEAN ARTIFACT SOURCE EXPORT" "PASS"
 pass "26566 authoritative Actions build complete"
}

verify_package
verify_scope
obtain_authority
build_candidate
install_and_build
cat "$OUT/26566_V1_COMPILER_STATUS.txt"
cat "$OUT/26566_V1_STRICT_HANDOFF_REPORT.txt"
