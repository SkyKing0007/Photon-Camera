#!/usr/bin/env bash
set -euo pipefail
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }

ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
BASE_HEAD="9b59a27235747733bacdde68bf6a888ebffefa18"
BACKUP="backup-26519-before-26521-iris-rgb-rewrite"
BASE_WORKFLOW="build-26519-per-lens-viewfinder-response.yml"
BASE_ARTIFACT="photon-26519-per-lens-viewfinder-response-v2"
BASE_SOURCE_TAR_NAME="26519_candidate_app_source.tar.gz"
BASE_SOURCE_MANIFEST_NAME="26519_candidate_source.sha256"
REPO="${GITHUB_REPOSITORY:-SkyKing0007/Photon-Camera}"
APPLY20="$ROOT/apply_26520_zsl_stacked_dng.py"
APPLY21="$ROOT/apply_26521_iris_rgb_rewrite.py"
VALIDATE="$ROOT/validate_26521_iris_rgb_rewrite.py"
HANDOFF="$ROOT/26521_HANDOFF_HASHES.sha256"
OUT="$ROOT/build_26521_iris_rgb_rewrite_outputs"
WORK="$ROOT/.build_26521_work"
ART="$WORK/26519_artifact"
BASE="$WORK/tested26519"
AFTER="$WORK/candidate26521"
VERSION_NAME="0.9726521"
VERSION_BUILD="26521"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-iris-rgb-rewrite-debug.apk"

rm -rf "$OUT" "$WORK"
mkdir -p "$OUT" "$ART" "$BASE" "$AFTER"
exec > >(tee "$OUT/26521_build.log") 2>&1

echo "=== 26521 GATE 0 ==="
[[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch"
[[ "$(git branch --show-current)" != "dev" ]] || fail "dev protected"
git merge-base --is-ancestor "$BASE_HEAD" HEAD || fail "not descended from exact 26519"
REMOTE_BACKUP="$(git ls-remote origin "refs/heads/$BACKUP" | awk '{print $1}')"
[[ "$REMOTE_BACKUP" == "$BASE_HEAD" ]] || fail "backup missing/wrong"
sha256sum -c "$HANDOFF"
python3 -m py_compile "$APPLY20" "$APPLY21" "$VALIDATE"
bash -n "$0"
git diff --name-only "$BASE_HEAD"..HEAD -- app/src/main app/version.properties > "$OUT/committed_runtime_drift.txt"
[[ ! -s "$OUT/committed_runtime_drift.txt" ]] || fail "runtime source committed before guarded build"
git diff --name-only "$BASE_HEAD"..HEAD -- gradlew gradlew.bat gradle build.gradle settings.gradle gradle.properties app/build.gradle app/proguard-rules.pro > "$OUT/protected_build_infrastructure_drift.txt"
[[ ! -s "$OUT/protected_build_infrastructure_drift.txt" ]] || fail "protected build infrastructure drift after 26519"
pass "exact 26519 sibling + existing backup verified"

echo "=== 26521 GATE 1: recover exact successful 26519 artifact ==="
command -v gh >/dev/null || fail "gh unavailable"
[[ -n "${GH_TOKEN:-}" ]] || fail "GH_TOKEN missing"
gh run list --repo "$REPO" --workflow "$BASE_WORKFLOW" --branch "$EXPECTED_BRANCH" --status success --limit 50 --json databaseId,headSha,conclusion > "$WORK/runs.json"
RUN_ID="$(python3 - "$WORK/runs.json" "$BASE_HEAD" <<'PY'
import json,sys
r=[x for x in json.load(open(sys.argv[1])) if x.get('headSha')==sys.argv[2] and x.get('conclusion')=='success']
if not r: raise SystemExit('no successful exact 26519 run')
print(r[0]['databaseId'])
PY
)"
gh run download "$RUN_ID" --repo "$REPO" --name "$BASE_ARTIFACT" --dir "$ART"
mapfile -t SOURCE_TARS < <(find "$ART" -type f -name "$BASE_SOURCE_TAR_NAME" -print)
mapfile -t SOURCE_MANIFESTS < <(find "$ART" -type f -name "$BASE_SOURCE_MANIFEST_NAME" -print)
[[ "${#SOURCE_TARS[@]}" -eq 1 && "${#SOURCE_MANIFESTS[@]}" -eq 1 ]] || fail "26519 source artifact cardinality mismatch"
SOURCE_TAR="${SOURCE_TARS[0]}"; SOURCE_MANIFEST="${SOURCE_MANIFESTS[0]}"
BASE_TAR_SHA="$(sha "$SOURCE_TAR")"; SOURCE_MANIFEST_SHA="$(sha "$SOURCE_MANIFEST")"
python3 - "$SOURCE_TAR" <<'PYTAR'
import sys,tarfile
with tarfile.open(sys.argv[1],'r:gz') as t:
    names=[m.name.lstrip('./') for m in t.getmembers() if m.name not in ('.','./')]
for n in names:
    if not (n in {'app','app/','app/src','app/src/','app/src/main','app/src/main/','app/version.properties'} or n.startswith('app/src/main/')):
        raise SystemExit('unexpected path in 26519 source archive: '+n)
print('PASS: 26519 source archive contains runtime source + version only')
PYTAR
tar -xzf "$SOURCE_TAR" -C "$BASE"
( cd "$BASE" && sha256sum -c "$SOURCE_MANIFEST" ) > "$OUT/26519_source_manifest_check.txt"
[[ "$(grep '^VERSION_NAME=' "$BASE/app/version.properties"|cut -d= -f2)" == "0.9726519" ]] || fail "base version name mismatch"
[[ "$(grep '^VERSION_BUILD=' "$BASE/app/version.properties"|cut -d= -f2)" == "26519" ]] || fail "base build mismatch"
grep -F 'IRIS_26519_PER_LENS_VIEWFINDER_RESPONSE' "$BASE/app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java" >/dev/null || fail "26519 matcher missing"
grep -F 'pref_motion_viewfinder_match_strength' "$BASE/app/src/main/res/xml/preferences.xml" >/dev/null || fail "26519 slider missing"
grep -F 'IRIS_26518_RELEASED_1271_RESULT_ABI_SNR_BRIDGE' "$BASE/app/src/main/java/com/hinnka/mycamera/processor/GlesMgc1271ReleasedSpatialStacker.kt" >/dev/null || fail "26518 SNR ABI missing"
grep -F 'IRIS_26517_RELEASED_1271_SPATIAL_RGB_OWNER' "$BASE/app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt" >/dev/null || fail "c4ff owner missing"
pass "successful 26519 source recovered and runtime owners proven"

echo "=== 26521 GATE 1B: prove COMPLETE 26520+26521 transforms against ACTUAL successful 26519 artifact BEFORE writes ==="
python3 - "$BASE" "$APPLY20" "$APPLY21" "$OUT/26521_BASE_CHANGED_INPUTS.sha256" "$OUT/26521_ACTUAL_26519_HDRX_RECONSTRUCT_CONTEXT.txt" <<'PYCOMPAT'
from __future__ import annotations
import hashlib,importlib.util,sys
from pathlib import Path
base=Path(sys.argv[1]).resolve(); a20=Path(sys.argv[2]).resolve(); a21=Path(sys.argv[3]).resolve(); hashes=Path(sys.argv[4]); context=Path(sys.argv[5])
def load(name,p):
    spec=importlib.util.spec_from_file_location(name,p); m=importlib.util.module_from_spec(spec); assert spec.loader is not None; spec.loader.exec_module(m); return m
m20=load('iris26520_artifact_compat',a20); m21=load('iris26521_artifact_compat',a21)
# Both transforms execute only in memory against the exact manifest-verified 26519 artifact.
e20=m20.expected_map(base); e21=m21.expected_map(base,a20)
lines=[]
for rel in sorted(set(m20.CHANGED)|{m21.CFA,m21.SHADER}):
    p=base/rel
    if p.is_file(): lines.append(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {rel}")
hashes.write_text('\n'.join(lines)+'\n')
hdr=(base/m20.HDRX).read_text().replace('\r\n','\n').replace('\r','\n'); token='MotionV2CfaReconstruction.reconstruct'; pos=hdr.find(token)
assert pos>=0 and hdr.find(token,pos+1)<0, 'actual 26519 reconstruct token cardinality is not exactly one'
a=max(0,hdr.rfind('\n',0,max(0,pos-500))+1); b=hdr.find('\n',min(len(hdr),pos+900)); b=len(hdr) if b<0 else b
context.write_text(hdr[a:b]+'\n')
assert m20.HDRX in e20 and m21.CFA in e21 and m21.SHADER in e21
print('PASS: complete shared 26520 transform resolves against actual successful 26519 artifact')
print('PASS: complete 26521 RGB transform resolves on that exact same in-memory 26520 candidate')
print('PASS: repository app/src is not used as 26521 runtime authority')
PYCOMPAT

echo "=== 26521 GATE 2: combined rollback patch FIRST ==="
cp -a "$BASE/." "$AFTER/"
PATCH="$OUT/26521_COMBINED_RUNTIME_DELTA_FROM_TESTED_26519.patch"
PATCH_SHA="$OUT/26521_COMBINED_RUNTIME_DELTA_FROM_TESTED_26519.patch.sha256"
python3 "$APPLY21" "$AFTER" --apply26520 "$APPLY20" --patch-out "$PATCH" --patch-sha-out "$PATCH_SHA"
( cd "$OUT" && sha256sum -c "$(basename "$PATCH_SHA")" )
python3 "$VALIDATE" --base "$BASE" --candidate "$AFTER" --apply26520 "$APPLY20" --patch "$PATCH" --patch-sha "$PATCH_SHA" | tee "$OUT/26521_prebuild_validator.txt"
[[ "$(grep '^VERSION_NAME=' "$AFTER/app/version.properties"|cut -d= -f2)" == "0.9726519" ]] || fail "version changed before build block"
[[ "$(grep '^VERSION_BUILD=' "$AFTER/app/version.properties"|cut -d= -f2)" == "26519" ]] || fail "build changed before build block"
echo "PRE-BUILD SAFETY PROOF PASSED"

echo "=== 26521 GATE 3: version increment + APK build same block ==="
python3 - "$AFTER/app/version.properties" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]); s=p.read_text()
assert 'VERSION_NAME=0.9726519' in s and 'VERSION_BUILD=26519' in s
p.write_text(s.replace('VERSION_NAME=0.9726519','VERSION_NAME=0.9726521',1)
              .replace('VERSION_BUILD=26519','VERSION_BUILD=26521',1))
PY

BJ="$WORK/bjzhou_vendor"
VENDOR_HEAD="09c76e57e8f01a5a8fc536ab41fc80ba642d4042"
rm -rf "$BJ"; git init -q "$BJ"; git -C "$BJ" remote add origin https://github.com/bjzhou/PhotonCamera.git
git -C "$BJ" config core.sparseCheckout true; mkdir -p "$BJ/.git/info"
cat > "$BJ/.git/info/sparse-checkout" <<'SPARSE'
/app/src/main/cpp/libjpeg-turbo/
/app/src/main/cpp/libultrahdr/
SPARSE
git -C "$BJ" fetch --depth=1 origin "$VENDOR_HEAD"
git -C "$BJ" checkout -q --detach FETCH_HEAD
THIRD="$AFTER/app/src/main/cpp/third_party_26507"
rm -rf "$THIRD"; mkdir -p "$THIRD"
cp -a "$BJ/app/src/main/cpp/libjpeg-turbo" "$THIRD/libjpeg-turbo"
cp -a "$BJ/app/src/main/cpp/libultrahdr" "$THIRD/libultrahdr"
( cd "$THIRD" && sha256sum -c "$ROOT/26507_BJZHOU_NATIVE_DEPENDENCIES.sha256" ) > "$OUT/vendor_manifest_check.txt"

rm -rf app/src/main; mkdir -p app/src
cp -a "$AFTER/app/src/main" app/src/main
cp "$AFTER/app/version.properties" app/version.properties

assert_cpp_deps_exact(){
  local phase="$1" expected actual
  if [[ "$phase" == pre ]]; then expected=$'.gitignore'; else expected=$'.gitignore\narchive.h\narchive_entry.h\ntechnicallyflac.h\ntiny_dng_writer.h'; fi
  actual="$(find app/src/main/cpp/deps -mindepth 1 -maxdepth 1 -type f -printf '%f\n'|LC_ALL=C sort)"
  [[ "$actual" == "$expected" ]] || fail "unexpected deps ($phase)"
}
audited_manifest(){
  { find app/src/main -type f ! -path 'app/src/main/cpp/third_party_26507/*' ! -path 'app/src/main/cpp/deps/*' -print; echo app/src/main/cpp/deps/.gitignore; echo app/version.properties; } | LC_ALL=C sort | while read -r f; do sha256sum "$f"; done
}
assert_cpp_deps_exact pre
audited_manifest > "$OUT/pre_gradle_runtime.sha256"
chmod +x ./gradlew
./gradlew clean :app:assembleDebug --stacktrace
assert_cpp_deps_exact post
audited_manifest > "$OUT/post_gradle_runtime.sha256"
cmp -s "$OUT/pre_gradle_runtime.sha256" "$OUT/post_gradle_runtime.sha256" || fail "Gradle mutated audited runtime"
pass "Gradle preserved validated runtime"

mapfile -t APKS < <(find app/build/outputs/apk/debug -maxdepth 1 -type f -name '*.apk' -print)
[[ "${#APKS[@]}" -eq 1 ]] || fail "expected one APK"
rm -f "$FINAL"; cp "${APKS[0]}" "$FINAL"
sha256sum "$FINAL" | tee "$OUT/26521_APK.sha256"

rm -rf "$AFTER/app/src/main/cpp/third_party_26507"
( cd "$AFTER" && { find app/src/main -type f -print; echo app/version.properties; } | LC_ALL=C sort | while read -r f; do sha256sum "$f"; done ) > "$OUT/26521_candidate_source.sha256"
tar --sort=name --mtime='UTC 2026-08-21 00:00:00' --owner=0 --group=0 --numeric-owner -czf "$OUT/26521_candidate_app_source.tar.gz" -C "$AFTER" app/src/main app/version.properties

cat > "$OUT/26521_FINAL_PROVENANCE.txt" <<EOF
BUILD=0.9726521/26521
BASE_HEAD=$BASE_HEAD
BASE_ARTIFACT=$BASE_ARTIFACT
BASE_SOURCE_TAR_SHA256=$BASE_TAR_SHA
BASE_SOURCE_MANIFEST_SHA256=$SOURCE_MANIFEST_SHA
ARTIFACT_COMPATIBILITY_PROOF=true
REPOSITORY_RUNTIME_AUTHORITY=false
BACKUP=$BACKUP
SIBLING_OF_26520=true
ONE_FRAME_FIX_IDENTICAL_TO_26520=true
STACKED_DNG_ARCH_IDENTICAL_TO_26520=true
WRONSKI_ALIGNMENT_FROZEN=true
ACTIVE_C4FF_SPATIAL_RGB=false
RGB_OWNER=IRIS_26521_INDEPENDENT_FUSED_BAYER_EDGE_COLOR_DIFFERENCE
DORMANT_OLD_SPATIAL_CODE_RETAINED_FOR_ROLLBACK=true
EOF

echo "PASS 1/3: exact 26519 sibling + backup"
echo "PASS 2/3: identical 26520 capture/DNG + frozen Wronski"
echo "PASS 3/3: active c4ff Spatial RGB disabled; Iris RGB rewrite built"
