#!/usr/bin/env bash
set -euo pipefail

fail(){ echo "ERROR: $*" >&2; exit 1; }
sha(){ sha256sum "$1" | awk '{print $1}'; }

ROOT="$(pwd)"
OUT="$ROOT/build_26501_proper_spatial_rgb_outputs"
WORK="$ROOT/.build_26501_proper_spatial_rgb_work"
BASE="$WORK/base26499"
CAND="$WORK/candidate26501"
PATCH="$ROOT/26501_proper_per_frame_spatial_rgb_runtime.patch"
BASE_TAR="$ROOT/26499_v7_successful_app_source.tar.gz"
BASE_MANIFEST="$ROOT/26499_v7_successful_after.sha256"
VALIDATOR="$ROOT/validate_26501_proper_spatial_rgb.py"
INTEGRITY="$ROOT/verify_26501_source_integrity.py"
V7_SHA="ed5470179aea9514c15d52dcb35613c7925778c6"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
BASE_TAR_SHA="ce5be58fa20b9e28786b9c6e4355743066fe92e78791b50b5ee2df568c5ae9e1"
BASE_MANIFEST_SHA="9af4b1cf5411b5cae445c3e2b782e07d824c3d4a2bcd16f3c7cf28ba79b5a74f"
PATCH_SHA="49dfedc17f93c636f90140125ee127a2429f3afb3c365832d97bb74e40318386"

rm -rf "$OUT" "$WORK"
mkdir -p "$OUT" "$BASE" "$CAND"
exec > >(tee "$OUT/26501_build.log") 2>&1

echo "=== 26501 GATE 1: BRANCH / LINEAGE / HANDOFF IDENTITY ==="
BRANCH="$(git branch --show-current)"
[[ "$BRANCH" == "$EXPECTED_BRANCH" ]] || fail "branch=$BRANCH expected=$EXPECTED_BRANCH"
[[ "$BRANCH" != "dev" ]] || fail "refusing dev"
git merge-base --is-ancestor "$V7_SHA" HEAD || fail "26499/V7 commit is not an ancestor of HEAD"
# Handoff commits remain infrastructure-only. Runtime is reconstructed from the exact successful V7 artifact.
if git diff --name-only "$V7_SHA"..HEAD -- app/src/main app/version.properties | grep -q .; then
  git diff --name-status "$V7_SHA"..HEAD -- app/src/main app/version.properties >&2 || true
  fail "handoff commit directly modified runtime app source"
fi
for f in "$PATCH" "$BASE_TAR" "$BASE_MANIFEST" "$VALIDATOR" "$INTEGRITY"; do
  [[ -f "$f" ]] || fail "missing handoff file: $(basename "$f")"
done
[[ "$(sha "$BASE_TAR")" == "$BASE_TAR_SHA" ]] || fail "26499 successful source tar hash mismatch"
[[ "$(sha "$BASE_MANIFEST")" == "$BASE_MANIFEST_SHA" ]] || fail "26499 successful manifest hash mismatch"
[[ "$(sha "$PATCH")" == "$PATCH_SHA" ]] || fail "26501 runtime patch hash mismatch"
echo "PASS: exact 26499/V7 successful-source artifact is the only runtime base"

echo "=== 26501 GATE 2: RECONSTRUCT EXACT SUCCESSFUL 26499 SOURCE ==="
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

echo "=== 26501 GATE 3: APPLY ONLY THE AUDITED PROPER SPATIAL RGB PATCH ==="
patch --dry-run -p1 -d "$CAND" < "$PATCH" > "$OUT/26501_patch_dry_run.txt"
patch -p1 -d "$CAND" < "$PATCH" > "$OUT/26501_patch_apply.txt"
python3 "$VALIDATOR" "$CAND" --base "$BASE" | tee "$OUT/26501_prebuild_validator.txt"
python3 - "$BASE/app" "$CAND/app" "$OUT/26501_scope.txt" <<'PY'
from pathlib import Path
import hashlib,sys
b,c,o=map(Path,sys.argv[1:])
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
bf={p.relative_to(b).as_posix():p for p in b.rglob('*') if p.is_file()}
cf={p.relative_to(c).as_posix():p for p in c.rglob('*') if p.is_file()}
new=sorted(set(cf)-set(bf)); rem=sorted(set(bf)-set(cf)); mod=sorted(k for k in bf.keys()&cf.keys() if h(bf[k])!=h(cf[k]))
Path(o).write_text('MODIFIED\n'+'\n'.join(mod)+'\nNEW\n'+'\n'.join(new)+'\nREMOVED\n'+'\n'.join(rem)+'\n')
assert len(mod)==5,(len(mod),mod); assert len(new)==4,(len(new),new); assert not rem,rem
print('PASS: exact 5 modified + 4 new runtime scope')
PY

echo "=== 26501 GATE 4: JAVA / GLSL / PHOTON RUNTIME-COMPATIBILITY PREFLIGHT ==="
command -v glslangValidator >/dev/null 2>&1 || fail "glslangValidator missing on runner"
python3 - "$CAND" "$OUT" <<'PY'
from pathlib import Path
import subprocess,sys,re
root,out=Path(sys.argv[1]),Path(sys.argv[2])
items=[
 ('app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_chroma_guide_26501.glsl','frag'),
 ('app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_contribute_26501.glsl','frag'),
 ('app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_normalize_26501.glsl','frag'),
 ('app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_short_weight_26501.glsl','comp'),
 ('app/src/main/assets/shaders/motionv2/shadow_aux_bayer_fuse.glsl','comp'),
 ('app/src/main/assets/shaders/motionv2/render.glsl','frag'),
 ('app/src/main/assets/shaders/motionv2/mfsr_mgc_covariance.glsl','comp'),
]
log=[]
for rel,stage in items:
 p=root/rel; src=p.read_text()
 if stage=='comp':
  if not src.startswith('#define LAYOUT //'):
   raise SystemExit(f'{rel}: missing Photon LAYOUT define')
  src=src.replace('#define LAYOUT //','#define LAYOUT layout(local_size_x=8, local_size_y=8, local_size_z=1) in;',1)
 wrapper='#version 310 es\n'+src
 tmp=out/(p.name+'.'+stage); tmp.write_text(wrapper)
 cp=subprocess.run(['glslangValidator','-S',stage,str(tmp)],capture_output=True,text=True)
 diagnostic=f'{rel}: rc={cp.returncode}\n{cp.stdout}{cp.stderr}'
 log.append(diagnostic)
 if cp.returncode:
  print(diagnostic,file=sys.stderr,flush=True)
  (out/'26501_glsl_validation.txt').write_text('\n'.join(log))
  raise SystemExit(cp.returncode)
(out/'26501_glsl_validation.txt').write_text('\n'.join(log))

# Reproduce Photon's fragile physical-line layout parser for every changed shader.
for rel,_ in items:
 src=(root/rel).read_text().splitlines()
 for lineno,line in enumerate(src,1):
  if 'layout' not in line: continue
  if line.count('layout(')>1:
   raise SystemExit(f'{rel}:{lineno}: multiple layout declarations on one physical line')
  l=line.find('('); r=line.rfind(')')
  if l<0 or r<l: raise SystemExit(f'{rel}:{lineno}: malformed layout declaration')
  params=line[l+1:r].split(',')
  for param in params:
   if '=' in param:
    key,val=param.replace(' ','').split('=',1)
    if key in {'binding','location','local_size_x','local_size_y','local_size_z'}:
     int(val)
print('PASS: 7 active/changed GLSL paths compile and Photon physical-line layout parser is safe')
PY

# Java parser smoke test: missing Android/project classes are expected in raw javac, syntax errors are not.
javac -proc:none -Xmaxerrs 10000 -d "$WORK/javac_parse" \
  "$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java" \
  "$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java" \
  "$CAND/app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2CfaInput.java" \
  > "$OUT/26501_javac_parse.log" 2>&1 || true
python3 - "$OUT/26501_javac_parse.log" <<'PY'
from pathlib import Path
import sys
s=Path(sys.argv[1]).read_text(errors='replace')
patterns=['; expected','illegal start of','reached end of file while parsing',"')' expected","'}' expected",'not a statement','class, interface, enum, or record expected','unclosed']
hits=[line for line in s.splitlines() if any(p in line for p in patterns)]
if hits: raise SystemExit('Java parse diagnostics: '+repr(hits[:20]))
print('PASS: modified Java files contain no javac syntax/parse diagnostics')
PY

[[ "$(grep '^VERSION_NAME=' "$CAND/app/version.properties" | cut -d= -f2)" == "0.9726499" ]] || fail "version changed before safety proof"
[[ "$(grep '^VERSION_BUILD=' "$CAND/app/version.properties" | cut -d= -f2)" == "26499" ]] || fail "build changed before safety proof"
echo "PRE-BUILD SAFETY PROOF PASSED"

echo "=== 26501 GATE 5: VERSION BUMP + EXACT CANDIDATE OVERLAY ==="
python3 - "$CAND/app/version.properties" <<'PY'
from pathlib import Path
import re,sys
p=Path(sys.argv[1]); s=p.read_text()
s=re.sub(r'^VERSION_NAME=.*$','VERSION_NAME=0.9726501',s,flags=re.M)
s=re.sub(r'^VERSION_BUILD=.*$','VERSION_BUILD=26501',s,flags=re.M)
p.write_text(s)
PY
[[ -f "$ROOT/app/build.gradle" ]] || fail "app/build.gradle missing before overlay"
find "$ROOT/app" -maxdepth 1 -type f ! -name version.properties -print0 | sort -z | xargs -0 sha256sum > "$OUT/app_module_shell_before.sha256"
rm -rf "$ROOT/app/src/main"; rm -f "$ROOT/app/version.properties"
cp -a "$CAND/app/src/main" "$ROOT/app/src/main"
cp -a "$CAND/app/version.properties" "$ROOT/app/version.properties"
find "$ROOT/app" -maxdepth 1 -type f ! -name version.properties -print0 | sort -z | xargs -0 sha256sum > "$OUT/app_module_shell_after.sha256"
diff -u "$OUT/app_module_shell_before.sha256" "$OUT/app_module_shell_after.sha256" > "$OUT/app_module_shell_diff.txt" || fail "Android app module shell changed"
[[ "$(grep '^VERSION_NAME=' app/version.properties | cut -d= -f2)" == "0.9726501" ]] || fail "version bump failed"
[[ "$(grep '^VERSION_BUILD=' app/version.properties | cut -d= -f2)" == "26501" ]] || fail "build bump failed"
python3 - "$CAND" "$ROOT" <<'PY'
from pathlib import Path
import hashlib,sys
a,b=Path(sys.argv[1]),Path(sys.argv[2])
def collect(root):
 out={}
 for p in (root/'app/src/main').rglob('*'):
  if p.is_file(): out[p.relative_to(root).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
 p=root/'app/version.properties'; out[p.relative_to(root).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
 return out
x,y=collect(a),collect(b)
if x!=y:
 bad=sorted(k for k in set(x)|set(y) if x.get(k)!=y.get(k))
 raise SystemExit('candidate/final canonical source mismatch before Gradle: '+repr(bad[:50]))
print('PASS: full candidate/final canonical source parity before Gradle')
PY
echo "PASS: version 0.9726501 / 26501 applied only after safety proof"

echo "=== 26501 GATE 6: REAL APP BUILD IN SAME GUARDED SCRIPT ==="
python3 "$INTEGRITY" snapshot "$ROOT/app" "$OUT/26501_pre_gradle_app_manifest.json"
chmod +x ./gradlew
./gradlew clean :app:assembleDebug --stacktrace
python3 "$INTEGRITY" verify "$ROOT/app" "$OUT/26501_pre_gradle_app_manifest.json" | tee "$OUT/26501_post_gradle_integrity.txt"
mapfile -t APKS < <(find app/build -type f -name '*.apk' 2>/dev/null | sort)
[[ "${#APKS[@]}" -eq 1 ]] || fail "expected exactly one APK under app/build, found ${#APKS[@]}: ${APKS[*]-}"
APK_BASENAME="$(basename "${APKS[0]}")"
[[ "$APK_BASENAME" == "IrisCamera-0.9726501-26501-debug.apk" ]] || fail "unexpected APK identity: $APK_BASENAME"
FINAL="$ROOT/IrisCamera-0.9726501-26501-proper-per-frame-spatial-rgb-debug.apk"
rm -f "$ROOT"/*.apk
cp "${APKS[0]}" "$FINAL"
sha256sum "$FINAL" > "$OUT/26501_apk.sha256"
echo "PASS: :app:assembleDebug produced exactly one expected APK"

echo "=== 26501 GATE 7: EMIT CLEAN SUCCESSFUL SOURCE CHECKPOINT ==="
( cd "$CAND" && tar --sort=name --mtime='UTC 2026-08-17 00:00:00' --owner=0 --group=0 --numeric-owner -czf "$OUT/26501_successful_app_source.tar.gz" app/src/main app/version.properties )
( cd "$CAND" && { find app/src/main -type f -print; echo app/version.properties; } | LC_ALL=C sort | while read -r f; do sha256sum "$f"; done ) > "$OUT/26501_successful_after.sha256"
[[ "$(wc -l < "$OUT/26501_successful_after.sha256")" -eq 869 ]] || fail "26501 successful source manifest expected 869 files"
for generated in archive.h archive_entry.h technicallyflac.h tiny_dng_writer.h; do
  ! tar -tzf "$OUT/26501_successful_app_source.tar.gz" | grep -qx "app/src/main/cpp/deps/$generated" || fail "generated dependency leaked into successful source: $generated"
done
sha256sum "$PATCH" "$BASE_TAR" "$BASE_MANIFEST" "$FINAL" "$OUT/26501_successful_app_source.tar.gz" > "$OUT/26501_artifact_hashes.sha256"
cat > "$OUT/26501_build_report.txt" <<EOF
26501 Proper Per-Frame Spatial RGB
Branch: $BRANCH
Rollback/base commit: $V7_SHA (26499/V7)
Base source artifact SHA256: $BASE_TAR_SHA
Version: 0.9726501 / 26501
APK: $(basename "$FINAL")
APK SHA256: $(sha "$FINAL")
Runtime scope: 5 modified + 4 new files; no removals
Normal stack: frame 0 + every admitted Wronski normal contributes native RAW semantic G/R-G/B-G exactly once
Persistent RGB owner: two additive RGBA16F accumulators; normalize exactly once after burst/HDR roles
Alignment/rejection: 26499 Wronski geometry, covariance/rejection authority preserved
Per-frame radiometry: timestamp-owned dynamic black/white and Camera2 Sx+O consumed by RGB owner
Noise: controls cross-edge chroma borrowing only; no post-SNR color eraser
Green guide: native green + edge-directed same-color correction; R/B never become a green lower bound
Short-A: existing correspondence/radiometry validator preserved; native short RAW contributes with four phase-specific validated weights
Shadow auxiliary: existing correspondence/SNR proof preserved; native shadow RAW contributes with exact four phase-specific blend weights
Lens shading: applied after completed RGB, never inside opponent reconstruction
Temporary WB: explicitly inverted once before downstream Camera2 color transform
Helper fused Bayer: brightness/provenance only; no ordinary color authority
Physical border: reference phase-owned; OOB auxiliary evidence has zero authority
Highlight output: existing 0.80 exposure retained; final headroom can reach neutral SDR white
Standard Bayer RCD/demosaic: bypassed by explicit full-resolution RGB carrier contract
UHDR geometry: unchanged downstream
Sharpening / residual spatial denoise: unchanged/off
EOF
echo "PASS: APK built exactly once and clean successful-source checkpoint emitted"
echo "PASS: 26501 PROPER PER-FRAME SPATIAL RGB BUILD COMPLETE: $FINAL"
