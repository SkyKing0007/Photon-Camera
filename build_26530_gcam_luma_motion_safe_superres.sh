#!/usr/bin/env bash
set -euo pipefail
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
BASE_BRANCH="experimental-clean-photon-rebuild"
BASE_ARTIFACT="photon-26529-manual-30x-iris-spatial-rgb-v3"
BASE_SOURCE_TAR_NAME="26529_candidate_app_source.tar.gz"
BASE_SOURCE_MANIFEST_NAME="26529_candidate_source.sha256"
EXPECTED_BASE_TAR_SHA="1c5662b8c356bc84ee98431d4d020e6e26fd8b003dc275476f81321954950b92"
EXPECTED_BASE_MANIFEST_SHA="b6bb4360ccb00af8bf353bb6be0bbacfde84ee1091268deff7c0eb3f7f851c21"
REPO="${GITHUB_REPOSITORY:-SkyKing0007/Photon-Camera}"
BJZHOU_VENDOR_HEAD="09c76e57e8f01a5a8fc536ab41fc80ba642d4042"
VERSION_NAME="0.9726530"; VERSION_BUILD="26530"
APPLY="$ROOT/apply_26530_gcam_luma_motion_safe_superres.py"
VALIDATE="$ROOT/validate_26530_gcam_luma_motion_safe_superres.py"
SHADER_PREFLIGHT="$ROOT/preflight_26530_superres_shaders.py"
HANDOFF="$ROOT/26530_HANDOFF_HASHES.sha256"
EXPECTED_PATCH="$ROOT/26530_RUNTIME_DELTA_FROM_SUCCESSFUL_26529.patch"
EXPECTED_PATCH_SHA="$ROOT/26530_RUNTIME_DELTA_FROM_SUCCESSFUL_26529.patch.sha256"
EXPECTED_ROLLBACK="$ROOT/26530_RUNTIME_ROLLBACK_TO_SUCCESSFUL_26529.patch"
EXPECTED_ROLLBACK_SHA="$ROOT/26530_RUNTIME_ROLLBACK_TO_SUCCESSFUL_26529.patch.sha256"
OUT="$ROOT/build_26530_gcam_luma_motion_safe_superres_outputs"
WORK="$ROOT/.build_26530_gcam_luma_motion_safe_superres_work"
ARTROOT="$WORK/artifacts"; BASE="$WORK/tested26529"; AFTER="$WORK/candidate26530"; POST="$WORK/postbuild26530"; BJ="$WORK/bjzhou_vendor"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-gcam-luma-motion-safe-superres-debug.apk"
rm -rf "$OUT" "$WORK" "$FINAL"; mkdir -p "$OUT" "$ARTROOT" "$BASE" "$AFTER"
exec > >(tee "$OUT/26530_build.log") 2>&1

echo "=== 26530 GATE 0: branch + handoff integrity ==="
BRANCH="$(git branch --show-current)"; START_HEAD="$(git rev-parse HEAD)"
[[ "$BRANCH" == "$EXPECTED_BRANCH" && "$BRANCH" != "dev" ]] || fail "wrong/protected branch: $BRANCH"
for f in "$APPLY" "$VALIDATE" "$SHADER_PREFLIGHT" "$HANDOFF" "$EXPECTED_PATCH" "$EXPECTED_PATCH_SHA" "$EXPECTED_ROLLBACK" "$EXPECTED_ROLLBACK_SHA"; do [[ -f "$f" ]] || fail "missing $(basename "$f")"; done
sha256sum -c "$HANDOFF"
( cd "$ROOT" && sha256sum -c "$(basename "$EXPECTED_PATCH_SHA")" && sha256sum -c "$(basename "$EXPECTED_ROLLBACK_SHA")" )
python3 -m py_compile "$APPLY" "$VALIDATE" "$SHADER_PREFLIGHT"
python3 "$APPLY" --self-test
bash -n "$0"
command -v glslangValidator >/dev/null || fail "glslangValidator unavailable"
glslangValidator --version | grep -F '16.5.0' >/dev/null || fail "wrong glslang version"
pass "branch and static handoff integrity verified; no backup branch created"

echo "=== 26530 GATE 1: recover exact successful 26529 candidate artifact by content hash ==="
command -v gh >/dev/null || fail "GitHub CLI unavailable"; [[ -n "${GH_TOKEN:-}" ]] || fail "GH_TOKEN missing"
RUNS="$WORK/26529_runs.json"
gh run list --repo "$REPO" --branch "$BASE_BRANCH" --status success --limit 50 --json databaseId,createdAt,workflowName,headSha > "$RUNS"
mapfile -t RUN_IDS < <(python3 - "$RUNS" <<'PY'
import json,sys
r=json.load(open(sys.argv[1])); r.sort(key=lambda x:x.get('createdAt',''),reverse=True)
for x in r: print(x['databaseId'])
PY
)
SOURCE_TAR=""; SOURCE_MANIFEST=""; MATCH_RUN=""
for rid in "${RUN_IDS[@]}"; do
  d="$ARTROOT/$rid"; mkdir -p "$d"
  if gh run download "$rid" --repo "$REPO" --name "$BASE_ARTIFACT" --dir "$d" >/dev/null 2>&1; then
    t="$(find "$d" -type f -name "$BASE_SOURCE_TAR_NAME" -print -quit)"
    m="$(find "$d" -type f -name "$BASE_SOURCE_MANIFEST_NAME" -print -quit)"
    if [[ -n "$t" && -n "$m" && "$(sha "$t")" == "$EXPECTED_BASE_TAR_SHA" && "$(sha "$m")" == "$EXPECTED_BASE_MANIFEST_SHA" ]]; then SOURCE_TAR="$t"; SOURCE_MANIFEST="$m"; MATCH_RUN="$rid"; break; fi
  fi
  rm -rf "$d"
done
[[ -n "$SOURCE_TAR" && -n "$SOURCE_MANIFEST" ]] || fail "no successful 26529 artifact matched exact candidate hashes"
echo "$MATCH_RUN" > "$OUT/26530_predecessor_run_id.txt"
python3 - "$SOURCE_TAR" <<'PY'
import sys,tarfile
with tarfile.open(sys.argv[1],'r:gz') as t:
  for m in t.getmembers():
    n=m.name.lstrip('./')
    if not n: continue
    if not (n=='app' or n.startswith('app/src/main') or n=='app/version.properties'):
      raise SystemExit('unexpected candidate path '+n)
print('PASS: candidate archive path scope')
PY
tar -xzf "$SOURCE_TAR" -C "$BASE"
( cd "$BASE" && sha256sum -c "$SOURCE_MANIFEST" ) > "$OUT/26529_source_manifest_check.txt"
[[ "$(grep '^VERSION_NAME=' "$BASE/app/version.properties"|cut -d= -f2)" == "0.9726529" ]] || fail "base version mismatch"
[[ "$(grep '^VERSION_BUILD=' "$BASE/app/version.properties"|cut -d= -f2)" == "26529" ]] || fail "base build mismatch"
pass "exact successful 26529 runtime recovered; repository app/src is not runtime authority"

echo "=== 26530 GATE 1B: generate + freeze forward/rollback patches BEFORE writes ==="
GEN_PATCH="$OUT/26530_RUNTIME_DELTA_FROM_SUCCESSFUL_26529.patch"; GEN_PATCH_SHA="$OUT/26530_RUNTIME_DELTA_FROM_SUCCESSFUL_26529.patch.sha256"
GEN_ROLLBACK="$OUT/26530_RUNTIME_ROLLBACK_TO_SUCCESSFUL_26529.patch"; GEN_ROLLBACK_SHA="$OUT/26530_RUNTIME_ROLLBACK_TO_SUCCESSFUL_26529.patch.sha256"
python3 "$APPLY" "$BASE" --check-only --patch-out "$GEN_PATCH" --patch-sha-out "$GEN_PATCH_SHA" --rollback-out "$GEN_ROLLBACK" --rollback-sha-out "$GEN_ROLLBACK_SHA" | tee "$OUT/26530_in_memory_transform_proof.txt"
( cd "$OUT" && sha256sum -c "$(basename "$GEN_PATCH_SHA")" && sha256sum -c "$(basename "$GEN_ROLLBACK_SHA")" )
cmp -s "$GEN_PATCH" "$EXPECTED_PATCH" || fail "generated forward patch differs from certified handoff patch"
cmp -s "$GEN_ROLLBACK" "$EXPECTED_ROLLBACK" || fail "generated rollback differs from certified handoff rollback"
pass "forward+rollback patches frozen and hashed before candidate writes"

echo "=== 26530 GATE 2: transform exact base + independent validation + reversible proof ==="
cp -a "$BASE/." "$AFTER/"; python3 "$APPLY" "$AFTER"
python3 "$VALIDATE" --base "$BASE" --candidate "$AFTER" --json-out "$OUT/26530_prebuild_validation.json" | tee "$OUT/26530_prebuild_validator.txt"
python3 "$SHADER_PREFLIGHT" --root "$AFTER" --validator glslangValidator | tee "$OUT/26530_shader_preflight.txt"
PATCHCHECK="$WORK/patchcheck"; ROLLCHECK="$WORK/rollbackcheck"; cp -a "$BASE" "$PATCHCHECK"; patch -d "$PATCHCHECK" -p1 --batch --forward < "$GEN_PATCH" >/dev/null
diff -qr "$PATCHCHECK/app/src/main" "$AFTER/app/src/main" > "$OUT/26530_forward_patch_compare.txt" || fail "forward patch did not reproduce candidate"
cp -a "$AFTER" "$ROLLCHECK"; patch -d "$ROLLCHECK" -p1 --batch --forward < "$GEN_ROLLBACK" >/dev/null
diff -qr "$ROLLCHECK/app/src/main" "$BASE/app/src/main" > "$OUT/26530_rollback_compare.txt" || fail "rollback did not reproduce 26529"
[[ "$(grep '^VERSION_NAME=' "$AFTER/app/version.properties"|cut -d= -f2)" == "0.9726529" ]] || fail "version changed before guarded block"
[[ "$(grep '^VERSION_BUILD=' "$AFTER/app/version.properties"|cut -d= -f2)" == "26529" ]] || fail "build changed before guarded block"
echo "TEMPORAL_IMAGE_MATH_CHANGED=true"
echo "LUMA_CALIBRATION=GCAM_8X_TARGET_7_EFFECTIVE_FRAMES_TO_50X_THEN_SMOOTH_TO_9"
echo "SUPERRES=RAW_DOMAIN_CROP_AWARE_SHARED_CFA_GEOMETRY_CAP_2X"
echo "MOTION_SAFETY=EXISTING_SPATIAL_REJECTION_REMAINS_MULTIPLICATIVE_AUTHORITY"
echo "COLOR_SAFETY=GREEN_LUMA_SCALED_CHROMA_FULL_SUPPORT_SENSOR_COORDINATE_LSC"
echo "DNG_ZOOM_CONTRACT=UNCHANGED"
echo "PRE-BUILD SAFETY PROOF PASSED"

echo "=== 26530 GATE 3: version increment + APK build in SAME guarded command block ==="
python3 - "$AFTER/app/version.properties" "$VERSION_NAME" "$VERSION_BUILD" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]); s=p.read_text(); vn,vb=sys.argv[2:]
assert s.count('VERSION_NAME=0.9726529')==1 and s.count('VERSION_BUILD=26529')==1
p.write_text(s.replace('VERSION_NAME=0.9726529','VERSION_NAME='+vn,1).replace('VERSION_BUILD=26529','VERSION_BUILD='+vb,1))
PY
# Rehydrate the exact native third-party trees from a pinned bjzhou commit. Commit identity is the content authority.
rm -rf "$BJ"; git init -q "$BJ"; git -C "$BJ" remote add origin https://github.com/bjzhou/PhotonCamera.git; git -C "$BJ" config core.sparseCheckout true
mkdir -p "$BJ/.git/info"; cat > "$BJ/.git/info/sparse-checkout" <<'SPARSE'
/app/src/main/cpp/libjpeg-turbo/
/app/src/main/cpp/libultrahdr/
SPARSE
git -C "$BJ" fetch --depth=1 origin "$BJZHOU_VENDOR_HEAD"; git -C "$BJ" checkout -q --detach FETCH_HEAD
[[ "$(git -C "$BJ" rev-parse HEAD)" == "$BJZHOU_VENDOR_HEAD" ]] || fail "vendor commit drift"
THIRD="$AFTER/app/src/main/cpp/third_party_26507"; rm -rf "$THIRD"; mkdir -p "$THIRD"; cp -a "$BJ/app/src/main/cpp/libjpeg-turbo" "$THIRD/libjpeg-turbo"; cp -a "$BJ/app/src/main/cpp/libultrahdr" "$THIRD/libultrahdr"
rm -rf app/src/main; mkdir -p app/src; cp -a "$AFTER/app/src/main" app/src/main; cp "$AFTER/app/version.properties" app/version.properties
runtime_manifest(){ { find app/src/main -type f ! -path 'app/src/main/cpp/third_party_26507/*' ! -path 'app/src/main/cpp/deps/*' -print; [[ -f app/src/main/cpp/deps/.gitignore ]] && echo app/src/main/cpp/deps/.gitignore; echo app/version.properties; } | LC_ALL=C sort -u | while read -r f; do sha256sum "$f"; done; }
runtime_manifest > "$OUT/26530_pre_gradle_audited_runtime.sha256"
chmod +x ./gradlew; ./gradlew clean :app:assembleDebug --stacktrace
runtime_manifest > "$OUT/26530_post_gradle_audited_runtime.sha256"
cmp -s "$OUT/26530_pre_gradle_audited_runtime.sha256" "$OUT/26530_post_gradle_audited_runtime.sha256" || fail "Gradle mutated audited runtime source/version"
rm -rf "$POST"; mkdir -p "$POST/app/src"; cp -a app/src/main "$POST/app/src/main"; rm -rf "$POST/app/src/main/cpp/third_party_26507"; find "$POST/app/src/main/cpp/deps" -mindepth 1 -maxdepth 1 -type f ! -name '.gitignore' -delete 2>/dev/null || true; cp app/version.properties "$POST/app/version.properties"
python3 "$VALIDATE" --base "$BASE" --candidate "$POST" --postbuild --json-out "$OUT/26530_postbuild_validation.json" | tee "$OUT/26530_postbuild_validator.txt"
python3 "$SHADER_PREFLIGHT" --root "$POST" --validator glslangValidator | tee "$OUT/26530_shader_postbuild.txt"
mapfile -t APKS < <(find app/build/outputs/apk/debug -type f -name '*.apk' -print)
[[ "${#APKS[@]}" -eq 1 ]] || fail "expected exactly one debug APK, found ${#APKS[@]}"
cp "${APKS[0]}" "$FINAL"; sha256sum "$FINAL" > "$OUT/26530_APK.sha256"

echo "=== 26530 GATE 4: deterministic next-candidate proof ==="
NEXT="$WORK/next_candidate"; rm -rf "$NEXT"; mkdir -p "$NEXT/app/src"; cp -a "$POST/app/src/main" "$NEXT/app/src/main"; cp "$POST/app/version.properties" "$NEXT/app/version.properties"
( cd "$NEXT" && find app/src/main app/version.properties -type f -print | LC_ALL=C sort | while read -r f; do sha256sum "$f"; done ) > "$OUT/26530_candidate_source.sha256"
tar --sort=name --mtime='UTC 2020-01-01' --owner=0 --group=0 --numeric-owner -czf "$OUT/26530_candidate_app_source.tar.gz" -C "$NEXT" app/src/main app/version.properties
sha256sum "$OUT/26530_candidate_app_source.tar.gz" > "$OUT/26530_candidate_app_source.tar.gz.sha256"
VERIFY="$WORK/verify_next"; mkdir -p "$VERIFY"; tar -xzf "$OUT/26530_candidate_app_source.tar.gz" -C "$VERIFY"; ( cd "$VERIFY" && sha256sum -c "$OUT/26530_candidate_source.sha256" ) > "$OUT/26530_next_candidate_manifest_check.txt"
cat > "$OUT/26530_provenance.txt" <<EOF
26530 GCam-calibrated luma + motion-safe RAW Super Resolution
Handoff branch: $EXPECTED_BRANCH
Runtime predecessor artifact branch: $BASE_BRANCH
Matched predecessor run: $MATCH_RUN
Exact 26529 candidate tar SHA256: $EXPECTED_BASE_TAR_SHA
Exact 26529 candidate manifest SHA256: $EXPECTED_BASE_MANIFEST_SHA
Version/build: $VERSION_NAME / $VERSION_BUILD
SR threshold: displayed 8x
SR raw-domain reconstruction cap: 2x local crop; remaining crop in MotionV2Render
Luma target: 7 effective frames through 50x, smooth rise to 9 by 120x+
Motion authority: existing Spatial rejection/global frame weights
Chroma: full temporal support; no independent R/B motion geometry
Lens shading: reconstructed sensor-coordinate sampling
DNG: motionV2OutputZoom DefaultCrop unchanged
Backup branch: intentionally not created for this incremental build
EOF
pass "BUILD SUCCESSFUL / RUNTIME VALIDATION PASS / NEXT-CANDIDATE PROOF PASS"
echo "APK=$FINAL"; sha256sum "$FINAL"
