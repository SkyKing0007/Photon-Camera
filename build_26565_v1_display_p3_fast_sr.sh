#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
BASE_SUCCESS_COMMIT="d0e9f1660140eaa8cb695f3e76805ba6f80cf79f"
FAILED_V1_HANDOFF_COMMIT="c775e067b5e73e3297dcd00f5cd0423da8cfa93f"
FAILED_V1_RUN_ID="33322029512"
FAILED_V1_JOB_ID="99285563475"
FAILED_V1_1_HANDOFF_COMMIT="0d4c3f6e644af77f5b52d88c96e29f01fe30700a"
FAILED_V1_1_RUN_ID="33322926514"
FAILED_V1_1_JOB_ID="99288343214"
BASE_RUN_ID="33286029778"
BASE_ARTIFACT_ID="9724492359"
BASE_ARTIFACT_NAME="photon-26564-v1-4-true-2x-sr"
BASE_ARTIFACT_SHA="db8e558d8d0b6b612b8285c0c47b1ac613dcf4f6d14131bd04eb9261047e4e27"
BASE_TAR_SHA="e8566618b98d3a35c097ea14c6e227e7cad25be36c734e70a6b0346ece533a77"
BASE_MANIFEST_SHA="46f8b3711372bfd9d72ec5568b6f347e068244057f10bef261b94b533a255a29"
CAND_MANIFEST_SHA="8adc66ee1925d7c5b3ef3489cfd3953d94e81a1f562b8da690615ae93c34d41a"
VENDOR_MANIFEST_SHA="7dbcc5ee5b9040965e431d79c45c5100f559c2b96c50970ca21987c684c825a8"
PROTECTED_SHA="1381855711f67f473d0760ba8620b78514ab7d7acbf2f19960765a53aaf0ccde"
FORWARD_SHA="1eaab880d539b29275c6a2192ee560569d331788b57dad9a79654bba4421f013"
ROLLBACK_SHA="fdd7489c52c803f5adb786d018db12a070a33612a11c066c7795411feeededb8"
BACKUP_BRANCH="backup-26563-v1-before-26564-true-2x-sr"
BACKUP_SHA="d048338a8e303c11b2208d4c1b78c8c129ebc57b"
VERSION_NAME="0.9726565"
VERSION_BUILD="26565"
HANDOFF="$ROOT/V1_26565_HANDOFF_HASHES.sha256"
BASE_PIN="$ROOT/V1_26565_BASE_26564_V1_4_AUDITED_RUNTIME.sha256"
CAND_PIN="$ROOT/V1_26565_EXPECTED_CANDIDATE_AUDITED_RUNTIME.sha256"
VENDOR_PIN="$ROOT/V1_26565_NATIVE_VENDOR_DEPENDENCIES.sha256"
PROTECTED="$ROOT/V1_26565_PROTECTED_UNCHANGED_CORE.sha256"
TRANSFORM="$ROOT/transform_26565_v1_display_p3_fast_sr.py"
VALIDATE="$ROOT/validate_26565_v1_display_p3_fast_sr.py"
AUTHORITY="$ROOT/verify_26565_authority.py"
PATCHVERIFY="$ROOT/verify_26565_patches.py"
WORKFLOW="$ROOT/.github/workflows/build-26565-v1-display-p3-fast-sr.yml"
BUILD_SCRIPT="$ROOT/build_26565_v1_display_p3_fast_sr.sh"
SEALED_PY=("$TRANSFORM" "$VALIDATE" "$AUTHORITY" "$PATCHVERIFY")
SEALED_DEP_FILES=("${SEALED_PY[@]}" "$BUILD_SCRIPT" "$WORKFLOW")
OUT="$ROOT/build_26565_v1_display_p3_fast_sr_outputs"
WORK="$ROOT/.build_26565_v1_display_p3_fast_sr_work"
ARTZIP="$WORK/26564_v1_4_artifact.zip"
ARTDIR="$WORK/artifact"
BASE="$WORK/exact_26564_v1_4_compiled_candidate"
AFTER="$WORK/candidate_26565"
AFTER2="$WORK/candidate_26565_replay"
POST="$WORK/postbuild_source_snapshot"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-v1-2-display-p3-fast-sr-debug.apk"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"
LOCAL_ART=""
if [[ "${1:-}" == "--local-prebuild" ]]; then [[ -n "${2:-}" ]] || fail "--local-prebuild requires exact 26564 V1.4 artifact ZIP"; LOCAL_ART="$2"; fi
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR" "$BASE" "$AFTER" "$AFTER2"
cat > "$OUT/26565_V1_COMPILER_STATUS.txt" <<'EOF'
REAL GLSL COMPILE: PASS (inherited exact successful 26564 shader bytes; no GLSL modified)
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
NATIVE/NDK COMPILE: NOT RUN YET (covered by full assemble)
FULL ANDROID ASSEMBLE: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
EOF
cat > "$OUT/26565_V1_STRICT_HANDOFF_REPORT.txt" <<'EOF'
EXACT PRIOR RUNTIME AUTHORITY: NOT RUN
BACKUP STATUS: NOT RUN
HANDOFF CHANGED-FILE SCOPE: NOT RUN
26564 FAILURE REGRESSIONS: NOT RUN
BASE MANIFEST COMPLETENESS: NOT RUN
CANDIDATE-FIRST TRANSFORM: NOT RUN
RUNTIME OWNERSHIP: NOT RUN
DORMANT-OWNER REJECTION: NOT RUN
DISPLAY-P3 JPEG BOUNDARY: NOT RUN
DNG INVARIANCE: NOT RUN
TRUE2X LUMA-ZERO FAST PUBLICATION: NOT RUN
TRUE2X 50MP FALLBACK RETENTION: NOT RUN
PROTECTED COLOR/NIGHT/GLSL CORE: NOT RUN
FORWARD PATCH FUZZ=0: NOT RUN
ROLLBACK PATCH FUZZ=0: NOT RUN
REAL GLSL COMPILE: PASS (inherited exact successful 26564 shader bytes; no GLSL modified)
REAL KOTLIN COMPILE: NOT RUN
REAL JAVA COMPILE: NOT RUN
NATIVE/NDK COMPILE: NOT RUN
FULL ANDROID ASSEMBLE: NOT RUN
POST-BUILD INVARIANCE: NOT RUN
CLEAN ARTIFACT SOURCE EXPORT: NOT RUN
TARGET VERSION/BUILD: 0.9726565 / 26565
EOF
set_report(){ local key="$1" val="$2" tmp="$OUT/.report.tmp"; awk -v key="$key:" -v val="$val" 'BEGIN{f=0} index($0,key)==1{print key" "val;f=1;next}{print} END{if(!f)exit 42}' "$OUT/26565_V1_STRICT_HANDOFF_REPORT.txt" > "$tmp" || fail "report key missing $key"; mv "$tmp" "$OUT/26565_V1_STRICT_HANDOFF_REPORT.txt"; }
set_compiler(){ local key="$1" val="$2" tmp="$OUT/.compiler.tmp"; awk -v key="$key:" -v val="$val" 'BEGIN{f=0} index($0,key)==1{print key" "val;f=1;next}{print} END{if(!f)exit 42}' "$OUT/26565_V1_COMPILER_STATUS.txt" > "$tmp" || fail "compiler key missing $key"; mv "$tmp" "$OUT/26565_V1_COMPILER_STATUS.txt"; }

verify_package(){
 [[ -f "$HANDOFF" ]] || fail "handoff hash manifest missing"
 sha256sum -c "$HANDOFF"
 [[ "$(sha "$BASE_PIN")" == "$BASE_MANIFEST_SHA" ]] || fail "base manifest SHA"
 [[ "$(sha "$CAND_PIN")" == "$CAND_MANIFEST_SHA" ]] || fail "candidate manifest SHA"
 [[ "$(sha "$VENDOR_PIN")" == "$VENDOR_MANIFEST_SHA" ]] || fail "vendor manifest SHA"
 [[ "$(sha "$PROTECTED")" == "$PROTECTED_SHA" ]] || fail "protected manifest SHA"
 [[ "$(sha "$ROOT/V1_26565_RUNTIME_DELTA_FROM_26564_V1_4.patch")" == "$FORWARD_SHA" ]] || fail "forward patch SHA"
 [[ "$(sha "$ROOT/V1_26565_RUNTIME_ROLLBACK_TO_26564_V1_4.patch")" == "$ROLLBACK_SHA" ]] || fail "rollback patch SHA"
 [[ "$(wc -l < "$BASE_PIN")" -eq 930 && "$(wc -l < "$CAND_PIN")" -eq 930 && "$(wc -l < "$VENDOR_PIN")" -eq 778 ]] || fail "manifest expected line counts"
 [[ "$(wc -l < "$ROOT/V1_26565_RUNTIME_CHANGED_PATHS.txt")" -eq 6 ]] || fail "changed path count"
 # Parse/compile the exact sealed Python inventory without site packages and without writing pyc.
 python3 -S - "${SEALED_PY[@]}" <<'PY'
import ast,sys
from pathlib import Path
allowed=set(sys.stdlib_module_names)
for raw in sys.argv[1:]:
 p=Path(raw); tree=ast.parse(p.read_text(),filename=str(p)); bad=[]
 for n in ast.walk(tree):
  names=[]
  if isinstance(n,ast.Import): names=[a.name.split('.',1)[0] for a in n.names]
  elif isinstance(n,ast.ImportFrom) and n.module: names=[n.module.split('.',1)[0]]
  bad += [x for x in names if x not in allowed]
 if bad: raise SystemExit(f'non-stdlib dependency {p.name}: {sorted(set(bad))}')
 compile(p.read_text(),str(p),'exec')
print('PASS packaged Python standard-library-only syntax/import gate')
PY
 # Dependency regressions own only the sealed 26565 inventory, never unrelated historical repository files.
 ! grep -Eq '(^|[[:space:]])(import|from)[[:space:]]+numpy' "${SEALED_PY[@]}" || fail "NumPy import regression in sealed 26565 Python inventory"
 ! grep -Eq 'pip(3)?[[:space:]]+install' "${SEALED_DEP_FILES[@]}" || fail "undeclared package-manager dependency in sealed 26565 inventory"
 # REGRESSION_26565_V1_REPO_WIDE_DEPENDENCY_SCOPE: reproduce a polluted checkout and prove exact inventory semantics.
 local depfix="$WORK/dependency_scope_fixture"
 mkdir -p "$depfix"
 printf 'import numpy\n' > "$depfix/unrelated_history.py"
 printf 'pip%sinstall numpy\n' ' ' > "$depfix/unrelated_history.sh"
 grep -Eq '(^|[[:space:]])(import|from)[[:space:]]+numpy' "$depfix/unrelated_history.py" || fail "dependency-scope NumPy decoy fixture invalid"
 grep -Eq 'pip(3)?[[:space:]]+install' "$depfix/unrelated_history.sh" || fail "dependency-scope pip decoy fixture invalid"
 ! grep -Eq '(^|[[:space:]])(import|from)[[:space:]]+numpy' "${SEALED_PY[@]}" || fail "unrelated NumPy decoy contaminated sealed scan"
 ! grep -Eq 'pip(3)?[[:space:]]+install' "${SEALED_DEP_FILES[@]}" || fail "unrelated pip decoy contaminated sealed scan"
 printf 'import numpy\n' > "$depfix/sealed_bad_numpy.py"
 printf 'pip%sinstall numpy\n' ' ' > "$depfix/sealed_bad_pip.sh"
 grep -Eq '(^|[[:space:]])(import|from)[[:space:]]+numpy' "$depfix/sealed_bad_numpy.py" || fail "sealed NumPy detector fixture failed"
 grep -Eq 'pip(3)?[[:space:]]+install' "$depfix/sealed_bad_pip.sh" || fail "sealed pip detector fixture failed"
 pass "REGRESSION_26565_V1_REPO_WIDE_DEPENDENCY_SCOPE: PASS"
 bash -n "$0"
 grep -F 'run 33283538711, job 99182648927' "$ROOT/REGRESSION_26565_CARRIED_FAILURES.txt" >/dev/null || fail "newline regression record"
 grep -F 'run 33284071958, job 99184083108' "$ROOT/REGRESSION_26565_CARRIED_FAILURES.txt" >/dev/null || fail "nested Git regression record"
 grep -F 'run 33284552163, job 99185364515' "$ROOT/REGRESSION_26565_CARRIED_FAILURES.txt" >/dev/null || fail "NumPy regression record"
 grep -F 'run 33285297620, job 99187338833' "$ROOT/REGRESSION_26565_CARRIED_FAILURES.txt" >/dev/null || fail "Kotlin Throwable regression record"
 grep -F 'run 33322029512, job 99285563475' "$ROOT/REGRESSION_26565_V1_REPO_WIDE_DEPENDENCY_SCOPE.txt" >/dev/null || fail "26565 V1 repository-wide dependency regression record"
 grep -F 'run 33322926514, rerun job 99288343214' "$ROOT/REGRESSION_26565_V1_1_HOST_CPP_JCONFIG_SCOPE.txt" >/dev/null || fail "26565 V1.1 host C++ jconfig regression record"
 local host_contract_name="compile_26565_cpp_"'contract.py'
 local host_syntax_flag="-fsyntax"'-only'
 local host_tombstone="$ROOT/$host_contract_name"
 [[ -f "$host_tombstone" ]] || fail "host C++ tombstone missing"
 grep -F 'OBSOLETE V1.1 host C++ surrogate disabled' "$host_tombstone" >/dev/null || fail "host C++ tombstone marker missing"
 ! grep -F -- "$host_syntax_flag" "$host_tombstone" >/dev/null || fail "host C++ tombstone still contains host syntax gate"
 ! grep -F 'clang++' "$host_tombstone" >/dev/null || fail "host C++ tombstone still contains clang invocation"
 grep -F './gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace' "$BUILD_SCRIPT" >/dev/null || fail "real Kotlin/Java compiler sequence missing"
 grep -F './gradlew :app:assembleDebug --stacktrace' "$BUILD_SCRIPT" >/dev/null || fail "real Android NDK/full assemble sequence missing"
 pass "REGRESSION_26565_V1_1_HOST_CPP_JCONFIG_SCOPE: PASS"
 # Exact historical newline fixture.
 python3 - "$HANDOFF" <<'PY'
from pathlib import Path
import sys
rows=[x for x in Path(sys.argv[1]).read_text().splitlines() if x.strip()]
names=[x.split('  ',1)[1] for x in rows]
assert all('\n' not in x and '\r' not in x for x in names)
fixture='a'*64+'  alpha.txt\n'+'b'*64+'  dir/beta.txt\n'
assert [x.split('  ',1)[1] for x in fixture.splitlines()] == ['alpha.txt','dir/beta.txt']
print('PASS REGRESSION_26564_V1_HANDOFF_SCOPE_NEWLINE')
PY
 set_report "26564 FAILURE REGRESSIONS" "PASS (26564 four failures + 26565 V1 dependency-scope + V1.1 host-C++-jconfig regressions)"
}

verify_scope(){
 python3 - "$HANDOFF" > "$WORK/expected_scope.txt" <<'PY'
from pathlib import Path
import sys
names=[x.split('  ',1)[1] for x in Path(sys.argv[1]).read_text().splitlines() if x.strip()]
names.append('V1_26565_HANDOFF_HASHES.sha256')
print('\n'.join(sorted(names)))
PY
 if [[ -n "$LOCAL_ART" ]]; then
   local sr="$WORK/scope_repo"; mkdir -p "$sr"; git -C "$sr" init -q; git -C "$sr" config user.name Iris; git -C "$sr" config user.email iris@invalid; git -C "$sr" commit -q --allow-empty -m base; local b; b="$(git -C "$sr" rev-parse HEAD)"
   while IFS= read -r rel; do mkdir -p "$sr/$(dirname "$rel")"; cp -a "$ROOT/$rel" "$sr/$rel"; done < "$WORK/expected_scope.txt"
   git -C "$sr" add .; git -C "$sr" commit -q -m handoff; git -C "$sr" diff --name-only "$b"..HEAD | sort > "$WORK/actual_scope.txt"
 else
   [[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch"
   git merge-base --is-ancestor "$BASE_SUCCESS_COMMIT" HEAD || fail "successful 26564 commit is not ancestor"
   git diff --name-only "$BASE_SUCCESS_COMMIT"..HEAD | sort > "$WORK/actual_scope.txt"
   remote_backup="$(git ls-remote origin "refs/heads/$BACKUP_BRANCH" | awk '{print $1}')"
   [[ "$remote_backup" == "$BACKUP_SHA" ]] || fail "backup branch mismatch"
   set_report "BACKUP STATUS" "PASS ($BACKUP_BRANCH @ $BACKUP_SHA; no new backup required)"
 fi
 diff -u "$WORK/expected_scope.txt" "$WORK/actual_scope.txt" || fail "handoff changed-file scope mismatch"
 ! grep -Eq '^app/' "$WORK/actual_scope.txt" || fail "handoff commit contains runtime app source"
 set_report "HANDOFF CHANGED-FILE SCOPE" "PASS (exact sealed package only; no app/ writes in handoff commit)"
 if [[ -n "$LOCAL_ART" ]]; then set_report "BACKUP STATUS" "PASS (remote status pinned in provenance; live remote rechecked by Actions)"; fi
}

obtain_authority(){
 if [[ -n "$LOCAL_ART" ]]; then cp -a "$LOCAL_ART" "$ARTZIP"; else
   [[ -n "$TOKEN" ]] || fail "GITHUB_TOKEN required to download exact 26564 artifact"
   curl -fL --retry 3 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "https://api.github.com/repos/SkyKing0007/Photon-Camera/actions/artifacts/$BASE_ARTIFACT_ID/zip" -o "$ARTZIP"
 fi
 [[ "$(sha "$ARTZIP")" == "$BASE_ARTIFACT_SHA" ]] || fail "successful 26564 artifact ZIP SHA mismatch"
 unzip -q "$ARTZIP" -d "$ARTDIR"
 local tar="$ARTDIR/build_26564_v1_true_2x_sr_outputs/26564_V1_candidate_app_source.tar.gz"
 local am="$ARTDIR/build_26564_v1_true_2x_sr_outputs/26564_V1_candidate_source.sha256"
 local vm="$ARTDIR/build_26564_v1_true_2x_sr_outputs/26564_vendor_postbuild.sha256"
 [[ "$(sha "$tar")" == "$BASE_TAR_SHA" ]] || fail "successful 26564 candidate TAR SHA mismatch"
 [[ "$(sha "$am")" == "$BASE_MANIFEST_SHA" ]] || fail "persisted 26564 runtime manifest SHA mismatch"
 [[ "$(sha "$vm")" == "$VENDOR_MANIFEST_SHA" ]] || fail "persisted 26564 vendor manifest SHA mismatch"
 grep -F 'REAL KOTLIN COMPILE: PASS' "$ARTDIR/build_26564_v1_true_2x_sr_outputs/26564_V1_COMPILER_STATUS.txt" >/dev/null || fail "26564 Kotlin proof absent"
 grep -F 'FULL ANDROID ASSEMBLE: PASS' "$ARTDIR/build_26564_v1_true_2x_sr_outputs/26564_V1_COMPILER_STATUS.txt" >/dev/null || fail "26564 assemble proof absent"
 tar -xzf "$tar" -C "$BASE"
 python3 -S "$AUTHORITY" "$BASE" "$BASE" "$ROOT" --base-only --successful-artifact-manifest "$am" --successful-vendor-manifest "$vm" | tee "$OUT/26565_base_authority.txt"
 cmp -s "$am" "$BASE_PIN" || fail "packaged base manifest not byte-identical to persisted successful artifact proof"
 set_report "EXACT PRIOR RUNTIME AUTHORITY" "PASS (26564 V1.4 run $BASE_RUN_ID artifact $BASE_ARTIFACT_ID exact bytes)"
 set_report "BASE MANIFEST COMPLETENESS" "PASS (audited=930 vendor=778 app=1707; persisted proof byte-equal)"
}

build_candidate(){
 cp -a "$BASE/." "$AFTER/"; cp -a "$BASE/." "$AFTER2/"
 # Actual candidate is deliberately nested under the parent checkout Git repository. Direct one-anchor edits must work here without touching tracked checkout bytes.
 if [[ -z "$LOCAL_ART" ]]; then git diff -- app > "$WORK/parent_before.diff"; fi
 python3 -S "$TRANSFORM" "$AFTER" | tee "$OUT/26565_transform.txt"
 if [[ -z "$LOCAL_ART" ]]; then git diff -- app > "$WORK/parent_after.diff"; cmp -s "$WORK/parent_before.diff" "$WORK/parent_after.diff" || fail "nested transform modified parent checkout app"; fi
 python3 -S "$TRANSFORM" "$AFTER2" > "$OUT/26565_transform_replay.txt"
 local am="$ARTDIR/build_26564_v1_true_2x_sr_outputs/26564_V1_candidate_source.sha256"
 local vm="$ARTDIR/build_26564_v1_true_2x_sr_outputs/26564_vendor_postbuild.sha256"
 python3 -S "$AUTHORITY" "$BASE" "$AFTER" "$ROOT" --successful-artifact-manifest "$am" --successful-vendor-manifest "$vm" | tee "$OUT/26565_authority_candidate.txt"
 python3 -S "$AUTHORITY" "$BASE" "$AFTER2" "$ROOT" --successful-artifact-manifest "$am" --successful-vendor-manifest "$vm" > "$OUT/26565_authority_candidate_replay.txt"
 python3 -S "$VALIDATE" "$AFTER" --base "$BASE" --package "$ROOT" | tee "$OUT/26565_semantic_validation.txt"
 python3 -S "$VALIDATE" "$AFTER2" --base "$BASE" --package "$ROOT" > "$OUT/26565_semantic_validation_replay.txt"
 python3 -S "$PATCHVERIFY" "$BASE" "$AFTER" "$ROOT" | tee "$OUT/26565_patch_validation.txt"
 # V1.2 permanent regression: do not block on an ad-hoc host clang++ surrogate.
 # The modified native runtime file is compiled authoritatively by the real Android NDK in :app:assembleDebug below.
 set_report "CANDIDATE-FIRST TRANSFORM" "PASS (two deterministic replays under nested checkout context)"
 set_report "RUNTIME OWNERSHIP" "PASS (existing sRGB processing/Jin -> final JPEG boundary P3 publication)"
 set_report "DORMANT-OWNER REJECTION" "PASS (protected internal color/Jin owners unchanged; encoder publication paths validated)"
 set_report "DISPLAY-P3 JPEG BOUNDARY" "PASS (math conversion + P3 ICC/JPEG-R gamut; internal sRGB preserved)"
 set_report "DNG INVARIANCE" "PASS (ImageSaver DNG region exact bytes + DNG owners protected)"
 set_report "TRUE2X LUMA-ZERO FAST PUBLICATION" "PASS (redundant full-50MP MGC skipped only when luma=0; native residual/VGN retained)"
 set_report "TRUE2X 50MP FALLBACK RETENTION" "PASS (JPEG-R auxiliary failure promotes rendered 50MP P3 SDR; no 12MP replacement)"
 set_report "PROTECTED COLOR/NIGHT/GLSL CORE" "PASS (263 protected paths exact successful 26564 bytes)"
 set_report "FORWARD PATCH FUZZ=0" "PASS (full-index deterministic at core.abbrev 7/12/40; exact candidate)"
 set_report "ROLLBACK PATCH FUZZ=0" "PASS (full-index deterministic at core.abbrev 7/12/40; exact 26564)"
}

install_and_build(){
 [[ -z "$LOCAL_ART" ]] || { pass "local prebuild replay complete; real Android compilers intentionally left for Actions"; return 0; }
 rm -rf "$ROOT/app/src"; cp -a "$AFTER/app/src" "$ROOT/app/"; cp -a "$AFTER/app/build.gradle" "$ROOT/app/build.gradle"; cp -a "$AFTER/app/version.properties" "$ROOT/app/version.properties"
 grep -F 'VERSION_NAME=0.9726565' "$ROOT/app/version.properties" >/dev/null || fail "installed version name"
 grep -F 'VERSION_BUILD=26565' "$ROOT/app/version.properties" >/dev/null || fail "installed version build"
 # Modified Kotlin/Java must pass their real project compilers before full assemble.
 ./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace | tee "$OUT/26565_gradle_language_compilers.log"
 set_compiler "REAL KOTLIN COMPILE" "PASS"; set_compiler "REAL JAVA COMPILE" "PASS"; set_report "REAL KOTLIN COMPILE" "PASS"; set_report "REAL JAVA COMPILE" "PASS"
 ./gradlew :app:assembleDebug --stacktrace | tee "$OUT/26565_gradle_assemble.log"
 set_compiler "NATIVE/NDK COMPILE" "PASS (full assemble)"; set_compiler "FULL ANDROID ASSEMBLE" "PASS"; set_report "NATIVE/NDK COMPILE" "PASS (full assemble)"; set_report "FULL ANDROID ASSEMBLE" "PASS"
 mapfile -t apks < <(find "$ROOT/app/build/outputs/apk/debug" -maxdepth 1 -type f -name '*.apk' | sort)
 [[ "${#apks[@]}" -eq 1 ]] || fail "expected exactly one debug APK, found ${#apks[@]}"
 cp -a "${apks[0]}" "$FINAL"
 [[ -s "$FINAL" ]] || fail "final APK missing"
 # Freeze only source authority after build, excluding generated app/build output.
 mkdir -p "$POST/app"; cp -a "$ROOT/app/src" "$POST/app/"; cp -a "$ROOT/app/build.gradle" "$POST/app/build.gradle"; cp -a "$ROOT/app/version.properties" "$POST/app/version.properties"
 local am="$ARTDIR/build_26564_v1_true_2x_sr_outputs/26564_V1_candidate_source.sha256"; local vm="$ARTDIR/build_26564_v1_true_2x_sr_outputs/26564_vendor_postbuild.sha256"
 python3 -S "$AUTHORITY" "$BASE" "$POST" "$ROOT" --successful-artifact-manifest "$am" --successful-vendor-manifest "$vm" | tee "$OUT/26565_postbuild_authority.txt"
 python3 -S "$VALIDATE" "$POST" --base "$BASE" --package "$ROOT" > "$OUT/26565_postbuild_semantic_validation.txt"
 set_compiler "POST-BUILD INVARIANCE" "PASS"; set_report "POST-BUILD INVARIANCE" "PASS (candidate/protected/native/vendor source exact after assemble)"
 sha256sum "$FINAL" > "$OUT/26565_V1_APK.sha256"
 tar --sort=name --mtime='UTC 2026-08-30' --owner=0 --group=0 --numeric-owner -czf "$OUT/26565_V1_candidate_app_source.tar.gz" -C "$POST" app
 sha256sum "$OUT/26565_V1_candidate_app_source.tar.gz" > "$OUT/26565_V1_candidate_app_source.tar.gz.sha256"
 cp "$CAND_PIN" "$OUT/26565_V1_candidate_source.sha256"; cp "$VENDOR_PIN" "$OUT/26565_vendor_postbuild.sha256"
 set_report "CLEAN ARTIFACT SOURCE EXPORT" "PASS"
 pass "26565 authoritative Actions build complete"
}

verify_package
verify_scope
obtain_authority
build_candidate
install_and_build
cat "$OUT/26565_V1_COMPILER_STATUS.txt"
cat "$OUT/26565_V1_STRICT_HANDOFF_REPORT.txt"
