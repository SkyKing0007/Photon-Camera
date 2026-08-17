#!/usr/bin/env bash
set -euo pipefail

fail(){ echo "ERROR: $*" >&2; exit 1; }
sha(){ sha256sum "$1" | awk '{print $1}'; }

ROOT="$(pwd)"
OUT="$ROOT/build_26500_joint_wronski_rgb_outputs"
WORK="$ROOT/.build_26500_joint_wronski_rgb_work"
BASE="$WORK/base26499"
CAND="$WORK/candidate26500"
PATCH="$ROOT/26500_joint_wronski_rgb_runtime.patch"
BASE_TAR="$ROOT/26499_v7_successful_app_source.tar.gz"
BASE_MANIFEST="$ROOT/26499_v7_successful_after.sha256"
VALIDATOR="$ROOT/validate_26500_joint_wronski_rgb.py"
INTEGRITY="$ROOT/verify_26500_source_integrity.py"
V7_SHA="ed5470179aea9514c15d52dcb35613c7925778c6"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
BASE_TAR_SHA="ce5be58fa20b9e28786b9c6e4355743066fe92e78791b50b5ee2df568c5ae9e1"
BASE_MANIFEST_SHA="9af4b1cf5411b5cae445c3e2b782e07d824c3d4a2bcd16f3c7cf28ba79b5a74f"
PATCH_SHA="74937118a7f832396a8d9847802a8c59cd4bb6596ca991170f986688365f40de"

rm -rf "$OUT" "$WORK"
mkdir -p "$OUT" "$BASE" "$CAND"
exec > >(tee "$OUT/26500_build.log") 2>&1

echo "=== 26500 GATE 1: BRANCH / LINEAGE / HANDOFF IDENTITY ==="
BRANCH="$(git branch --show-current)"
[[ "$BRANCH" == "$EXPECTED_BRANCH" ]] || fail "branch=$BRANCH expected=$EXPECTED_BRANCH"
[[ "$BRANCH" != "dev" ]] || fail "refusing dev"
git merge-base --is-ancestor "$V7_SHA" HEAD || fail "26499/V7 commit is not an ancestor of HEAD"
# Handoff commits are infrastructure only. Runtime source is reconstructed from the exact
# successful V7 artifact below; vscode.dev upload must not directly edit app runtime source.
if git diff --name-only "$V7_SHA"..HEAD -- app/src/main app/version.properties | grep -q .; then
  git diff --name-status "$V7_SHA"..HEAD -- app/src/main app/version.properties >&2 || true
  fail "handoff commit directly modified runtime app source"
fi
for f in "$PATCH" "$BASE_TAR" "$BASE_MANIFEST" "$VALIDATOR" "$INTEGRITY"; do
  [[ -f "$f" ]] || fail "missing handoff file: $(basename "$f")"
done
[[ "$(sha "$BASE_TAR")" == "$BASE_TAR_SHA" ]] || fail "26499 successful source tar hash mismatch"
[[ "$(sha "$BASE_MANIFEST")" == "$BASE_MANIFEST_SHA" ]] || fail "26499 successful manifest hash mismatch"
[[ "$(sha "$PATCH")" == "$PATCH_SHA" ]] || fail "26500 runtime patch hash mismatch"
echo "PASS: exact 26499/V7 successful-source artifact is the only runtime base"

echo "=== 26500 GATE 2: RECONSTRUCT EXACT SUCCESSFUL 26499 SOURCE ==="
tar -xzf "$BASE_TAR" -C "$BASE"
[[ -f "$BASE/app/version.properties" ]] || fail "base extraction missing version"
( cd "$BASE" && sha256sum -c "$BASE_MANIFEST" ) > "$OUT/26499_manifest_check.txt"
[[ "$(wc -l < "$BASE_MANIFEST")" -eq 865 ]] || fail "26499 manifest count must be 865"
BASE_COUNT="$({ find "$BASE/app/src/main" -type f -print; echo "$BASE/app/version.properties"; } | wc -l)"
[[ "$BASE_COUNT" -eq 865 ]] || fail "26499 extracted file count=$BASE_COUNT expected=865"
[[ "$(grep '^VERSION_NAME=' "$BASE/app/version.properties" | cut -d= -f2)" == "0.9726499" ]] || fail "base version name is not 26499"
[[ "$(grep '^VERSION_BUILD=' "$BASE/app/version.properties" | cut -d= -f2)" == "26499" ]] || fail "base version build is not 26499"
cp -a "$BASE/app" "$CAND/app"
echo "PASS: exact successful 26499 source reconstructed and hash-verified (865/865)"

echo "=== 26500 GATE 3: APPLY ONLY THE AUDITED RUNTIME PATCH ==="
patch --dry-run -p1 -d "$CAND" < "$PATCH" > "$OUT/26500_patch_dry_run.txt"
patch -p1 -d "$CAND" < "$PATCH" > "$OUT/26500_patch_apply.txt"
python3 "$VALIDATOR" "$BASE" "$CAND" | tee "$OUT/26500_prebuild_validator.txt"
# Patch scope is fixed: 4 modified + 3 new runtime files, no removals.
python3 - "$BASE/app" "$CAND/app" "$OUT/26500_scope.txt" <<'PY'
from pathlib import Path
import hashlib,sys
b,c,o=map(Path,sys.argv[1:])
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
bf={p.relative_to(b).as_posix():p for p in b.rglob('*') if p.is_file()}
cf={p.relative_to(c).as_posix():p for p in c.rglob('*') if p.is_file()}
new=sorted(set(cf)-set(bf)); rem=sorted(set(bf)-set(cf)); mod=sorted(k for k in bf.keys()&cf.keys() if sha(bf[k])!=sha(cf[k]))
Path(o).write_text('MODIFIED\n'+'\n'.join(mod)+'\nNEW\n'+'\n'.join(new)+'\nREMOVED\n'+'\n'.join(rem)+'\n')
assert len(mod)==4,(len(mod),mod); assert len(new)==3,(len(new),new); assert not rem,rem
print('PASS: exact 4 modified + 3 new runtime scope')
PY

echo "=== 26500 GATE 4: PHOTON GLSL RUNTIME-COMPATIBILITY PREFLIGHT ==="
command -v glslangValidator >/dev/null 2>&1 || fail "glslangValidator missing on runner"
python3 - "$CAND" "$OUT" <<'PY'
from pathlib import Path
import subprocess,sys,re
root,out=Path(sys.argv[1]),Path(sys.argv[2])
items=[
 ('app/src/main/assets/shaders/motionv2/mfsr_bayer_accumulate.glsl','comp'),
 ('app/src/main/assets/shaders/motionv2/joint_green_26500.glsl','frag'),
 ('app/src/main/assets/shaders/motionv2/joint_rgb_26500.glsl','frag'),
 ('app/src/main/assets/shaders/motionv2/render.glsl','frag'),
]
log=[]
for rel,stage in items:
 p=root/rel; src=p.read_text()
 if stage=='comp':
  assert src.startswith('#define LAYOUT //'),rel
  src=src.replace('#define LAYOUT //','#define LAYOUT layout(local_size_x=8, local_size_y=8, local_size_z=1) in;',1)
 wrapper='#version 310 es\n'+src
 tmp=out/(p.name+'.'+stage); tmp.write_text(wrapper)
 cp=subprocess.run(['glslangValidator','-S',stage,str(tmp)],capture_output=True,text=True)
 log.append(f'{rel}: rc={cp.returncode}\n{cp.stdout}{cp.stderr}')
 if cp.returncode:
  (out/'26500_glsl_validation.txt').write_text('\n'.join(log)); raise SystemExit(cp.returncode)
(out/'26500_glsl_validation.txt').write_text('\n'.join(log))
# Reproduce the custom GLInterface line parser for the changed compute shader.
s=(root/'app/src/main/assets/shaders/motionv2/mfsr_bayer_accumulate.glsl').read_text().splitlines()
layouts=[]
for line in s:
 if 'layout' not in line: continue
 if line.count('layout(')>1: raise SystemExit('multiple layout declarations on one physical line')
 m=re.search(r'layout\([^)]*binding\s*=\s*(\d+)[^)]*\)\s+uniform\s+[^;]*\s+([A-Za-z_][A-Za-z0-9_]*)\s*;',line)
 if m: layouts.append((m.group(2),int(m.group(1))))
expected=[('alterCov',0),('accumulatorNumerator',1),('accumulatorDenominator',2),('accumulatorFrameSupport',3)]
assert layouts==expected,(layouts,expected)
print('PASS: 4 changed/new GLSL paths compile and Photon layout-parser contract remains valid')
PY

# Version remains old through every source/math/parser/compiler gate.
[[ "$(grep '^VERSION_NAME=' "$CAND/app/version.properties" | cut -d= -f2)" == "0.9726499" ]] || fail "version changed before safety proof"
[[ "$(grep '^VERSION_BUILD=' "$CAND/app/version.properties" | cut -d= -f2)" == "26499" ]] || fail "build changed before safety proof"
echo "PRE-BUILD SAFETY PROOF PASSED"

echo "=== 26500 GATE 5: VERSION BUMP + PRESERVE COMPLETE ANDROID MODULE SHELL ==="
python3 - "$CAND/app/version.properties" <<'PY'
from pathlib import Path
import re,sys
p=Path(sys.argv[1]); s=p.read_text();
s=re.sub(r'^VERSION_NAME=.*$','VERSION_NAME=0.9726500',s,flags=re.M)
s=re.sub(r'^VERSION_BUILD=.*$','VERSION_BUILD=26500',s,flags=re.M)
p.write_text(s)
PY
[[ -f "$ROOT/app/build.gradle" ]] || fail "app/build.gradle missing before overlay"
find "$ROOT/app" -maxdepth 1 -type f ! -name version.properties -print0 | sort -z | xargs -0 sha256sum > "$OUT/app_module_shell_before.sha256"
rm -rf "$ROOT/app/src/main"; rm -f "$ROOT/app/version.properties"
cp -a "$CAND/app/src/main" "$ROOT/app/src/main"
cp -a "$CAND/app/version.properties" "$ROOT/app/version.properties"
find "$ROOT/app" -maxdepth 1 -type f ! -name version.properties -print0 | sort -z | xargs -0 sha256sum > "$OUT/app_module_shell_after.sha256"
diff -u "$OUT/app_module_shell_before.sha256" "$OUT/app_module_shell_after.sha256" > "$OUT/app_module_shell_diff.txt" || fail "Android app module shell changed"
[[ "$(grep '^VERSION_NAME=' app/version.properties | cut -d= -f2)" == "0.9726500" ]] || fail "version bump failed"
[[ "$(grep '^VERSION_BUILD=' app/version.properties | cut -d= -f2)" == "26500" ]] || fail "build bump failed"
echo "PASS: version 0.9726500 / 26500 applied only after safety proof"

echo "=== 26500 GATE 6: REAL APP BUILD IN SAME GUARDED SCRIPT ==="
python3 "$INTEGRITY" snapshot "$ROOT/app" "$OUT/26500_pre_gradle_app_manifest.json"
chmod +x ./gradlew
./gradlew clean :app:assembleDebug --stacktrace
python3 "$INTEGRITY" verify "$ROOT/app" "$OUT/26500_pre_gradle_app_manifest.json" | tee "$OUT/26500_post_gradle_integrity.txt"
mapfile -t APKS < <(find app/build -type f -name '*.apk' 2>/dev/null | sort)
[[ "${#APKS[@]}" -eq 1 ]] || fail "expected exactly one APK under app/build, found ${#APKS[@]}: ${APKS[*]-}"
APK_BASENAME="$(basename "${APKS[0]}")"
[[ "$APK_BASENAME" == "IrisCamera-0.9726500-26500-debug.apk" ]] || fail "unexpected APK identity: $APK_BASENAME"
FINAL="$ROOT/IrisCamera-0.9726500-26500-joint-wronski-rgb-debug.apk"
rm -f "$ROOT"/*.apk
cp "${APKS[0]}" "$FINAL"
sha256sum "$FINAL" > "$OUT/26500_apk.sha256"
echo "PASS: :app:assembleDebug produced exactly one expected APK"

echo "=== 26500 GATE 7: EMIT CLEAN SUCCESSFUL SOURCE CHECKPOINT ==="
( cd "$CAND" && tar --sort=name --mtime='UTC 2026-08-17 00:00:00' --owner=0 --group=0 --numeric-owner -czf "$OUT/26500_successful_app_source.tar.gz" app/src/main app/version.properties )
( cd "$CAND" && { find app/src/main -type f -print; echo app/version.properties; } | LC_ALL=C sort | while read -r f; do sha256sum "$f"; done ) > "$OUT/26500_successful_after.sha256"
[[ "$(wc -l < "$OUT/26500_successful_after.sha256")" -eq 868 ]] || fail "26500 successful source manifest expected 868 files"
for generated in archive.h archive_entry.h technicallyflac.h tiny_dng_writer.h; do
  ! tar -tzf "$OUT/26500_successful_app_source.tar.gz" | grep -qx "app/src/main/cpp/deps/$generated" || fail "generated dependency leaked into successful source: $generated"
done
sha256sum "$PATCH" "$BASE_TAR" "$BASE_MANIFEST" "$FINAL" "$OUT/26500_successful_app_source.tar.gz" > "$OUT/26500_artifact_hashes.sha256"
cat > "$OUT/26500_build_report.txt" <<EOF
26500 Joint Wronski RGB / evidence-complete image formation
Branch: $BRANCH
Rollback/base commit: $V7_SHA (26499/V7)
Base source artifact SHA256: $BASE_TAR_SHA
Version: 0.9726500 / 26500
APK: $(basename "$FINAL")
APK SHA256: $(sha "$FINAL")
Runtime scope: 4 modified + 3 new files; no removals
Temporal merge: 26499 Wronski alignment/rejection/admission frozen
Short-A: 26499 correspondence/provenance frozen
Shadow auxiliary: 26499 capture/fusion frozen
Joint RGB: native-resolution G/(R-G)/(B-G), provenance-aware; historical direct_rgb_* inactive
CENSORED: brightness-only; SHORT_VALIDATED: physical color authority
Shadows: Wronski Camera2 Sx+O statistical chroma confidence before display gain
Physical image boundary: immutable reference unchanged; one-sided auxiliary support tapers continuously
Highlight output: existing 0.80 exposure retained; final headroom reaches SDR white and converges gently to neutral white
Separate RCD standard-Bayer owner: inactive
UHDR geometry: unchanged
Sharpening / residual spatial denoise: unchanged/off
EOF
echo "PASS: APK built exactly once and clean successful-source checkpoint emitted"
echo "PASS: 26500 JOINT WRONSKI RGB BUILD COMPLETE: $FINAL"
