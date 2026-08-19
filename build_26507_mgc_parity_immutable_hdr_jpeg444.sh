#!/usr/bin/env bash
set -euo pipefail
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
ROOT="$(pwd)"
OUT="$ROOT/build_26507_mgc_parity_immutable_hdr_jpeg444_outputs"
WORK="$ROOT/.build_26507_mgc_parity_immutable_hdr_jpeg444_work"
PRE="$WORK/canonical26502"; BEFORE="$WORK/tested26506"; AFTER="$WORK/candidate26507"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
CANONICAL_26502_HEAD="6118984523296945a0910e55ddaa4d3126184059"
HANDOFF_26506_HEAD="951f63980608eaaf2adba245bdd268a890f6a8ab"
BACKUP_BRANCH="backup-26506-tested-before-26507-20260818"
HANDOFF_26507_V2_HEAD="accce4a324de92dcc93300c6f696d72f38cf55e3"
BACKUP_26507_V2_BRANCH="backup-26507-v2-before-native-gate-fix-20260818"
BJZHOU_HEAD="09c76e57e8f01a5a8fc536ab41fc80ba642d4042"
SEED_26503="$ROOT/26503_v2_seed_safe_highlight_shadow_runtime.patch"
APPLY_26504="$ROOT/apply_26504_integrated.py"; VALIDATOR_26504="$ROOT/validate_26504_integrated.py"
APPLY_26505="$ROOT/apply_26505_bjzhou_consistency.py"; VALIDATOR_26505="$ROOT/validate_26505_bjzhou_consistency.py"
APPLY_26506="$ROOT/apply_26506_uhdr_parity_opponent_chroma.py"; VALIDATOR_26506="$ROOT/validate_26506_uhdr_parity_opponent_chroma.py"
APPLY_26507="$ROOT/apply_26507_mgc_parity_immutable_hdr_jpeg444.py"; VALIDATOR_26507="$ROOT/validate_26507_mgc_parity_immutable_hdr_jpeg444.py"
INTEGRITY="$ROOT/verify_26501_source_integrity.py"
SEED_26503_SHA="c5d4e13e6f8a59243eedac8c2beab9d737444a231f21411bf7dec1636dca5a1e"
APPLY_26504_SHA="96f44374c564231abf13e219362add26c4a3ff1be1e1bbd793b3cd4af3ef6348"
VALIDATOR_26504_SHA="c071526c04b36a5c8d19525c1485b01c5eea4befe89abc7443b24fef4f4d28f3"
APPLY_26505_SHA="2a718c5972ab4a8f518c3f25d769e9ac37e87050989e85dcb1f747272e6bd9bf"
VALIDATOR_26505_SHA="703df94241c2a4effcf088eb757809dbc9da141b0c295a46aaf40e93ec8a0345"
APPLY_26506_SHA="c34f71ccbfc436df604be410a8dff373d81963826a3359cfff43f28d9807bccd"
VALIDATOR_26506_SHA="9aca6c1bf3e65360542ec1e158bfcb663bf54df1d5c3b8847c103b542f738a6e"
rm -rf "$OUT" "$WORK"; mkdir -p "$OUT" "$PRE" "$BEFORE" "$AFTER"
exec > >(tee "$OUT/26507_build.log") 2>&1

BRANCH="$(git branch --show-current)"; START_HEAD="$(git rev-parse HEAD)"
[[ "$BRANCH" == "$EXPECTED_BRANCH" && "$BRANCH" != "dev" ]] || fail "wrong/protected branch $BRANCH"
git merge-base --is-ancestor "$HANDOFF_26506_HEAD" HEAD || fail "26506 V2 handoff missing from lineage"
git merge-base --is-ancestor "$HANDOFF_26507_V2_HEAD" HEAD || fail "26507 V2 handoff missing from lineage"
git merge-base --is-ancestor "$CANONICAL_26502_HEAD" HEAD || fail "canonical 26502 missing"
RUNTIME_DRIFT="$OUT/runtime_diff_from_canonical_26502.txt"
git diff --name-only "$CANONICAL_26502_HEAD"..HEAD -- app/src/main app/version.properties > "$RUNTIME_DRIFT"
[[ ! -s "$RUNTIME_DRIFT" ]] || { cat "$RUNTIME_DRIFT" >&2; fail "committed runtime drift exists"; }
REMOTE_BACKUP="$(git ls-remote origin "refs/heads/$BACKUP_BRANCH" | awk '{print $1}')"
[[ "$REMOTE_BACKUP" == "$HANDOFF_26506_HEAD" ]] || fail "backup missing/wrong: $BACKUP_BRANCH -> ${REMOTE_BACKUP:-MISSING}"
REMOTE_V2_BACKUP="$(git ls-remote origin "refs/heads/$BACKUP_26507_V2_BRANCH" | awk '{print $1}')"
[[ "$REMOTE_V2_BACKUP" == "$HANDOFF_26507_V2_HEAD" ]] || fail "V2 handoff backup missing/wrong: $BACKUP_26507_V2_BRANCH -> ${REMOTE_V2_BACKUP:-MISSING}"
for f in "$SEED_26503" "$APPLY_26504" "$VALIDATOR_26504" "$APPLY_26505" "$VALIDATOR_26505" "$APPLY_26506" "$VALIDATOR_26506" "$APPLY_26507" "$VALIDATOR_26507" "$INTEGRITY"; do [[ -f "$f" ]] || fail "missing $(basename "$f")"; done
[[ "$(sha "$SEED_26503")" == "$SEED_26503_SHA" ]] || fail "26503 seed hash mismatch"
[[ "$(sha "$APPLY_26504")" == "$APPLY_26504_SHA" && "$(sha "$VALIDATOR_26504")" == "$VALIDATOR_26504_SHA" ]] || fail "26504 dependency hash mismatch"
[[ "$(sha "$APPLY_26505")" == "$APPLY_26505_SHA" && "$(sha "$VALIDATOR_26505")" == "$VALIDATOR_26505_SHA" ]] || fail "26505 dependency hash mismatch"
[[ "$(sha "$APPLY_26506")" == "$APPLY_26506_SHA" && "$(sha "$VALIDATOR_26506")" == "$VALIDATOR_26506_SHA" ]] || fail "26506 dependency hash mismatch"
pass "GATE 1 branch/lineage/exact 26506 runtime backup + exact 26507 V2 handoff backup/dependency hashes"

echo "=== GATE 2: reconstruct exact tested 26506 and freeze pre-change proof ==="
git archive "$CANONICAL_26502_HEAD" app/src/main app/version.properties | tar -x -C "$PRE"
cp -a "$PRE/app/." "$BEFORE/app/"
patch --dry-run --batch --forward --fuzz=0 --no-backup-if-mismatch -p1 -d "$BEFORE" < "$SEED_26503" > "$OUT/26503_seed_dry.txt"
patch --batch --forward --fuzz=0 --no-backup-if-mismatch -p1 -d "$BEFORE" < "$SEED_26503" > "$OUT/26503_seed_apply.txt"
python3 "$APPLY_26504" "$BEFORE" | tee "$OUT/26504_apply.txt"; python3 "$VALIDATOR_26504" "$BEFORE" --base-root "$PRE" | tee "$OUT/26504_validate.txt"
python3 "$APPLY_26505" "$BEFORE" | tee "$OUT/26505_apply.txt"; python3 "$VALIDATOR_26505" "$BEFORE" --base-root "$PRE" | tee "$OUT/26505_validate.txt"
python3 "$APPLY_26506" "$BEFORE" | tee "$OUT/26506_apply.txt"; python3 "$VALIDATOR_26506" "$BEFORE" --base-root "$PRE" | tee "$OUT/26506_validate.txt"
set +e; git diff --no-index --binary "$PRE/app" "$BEFORE/app" > "$OUT/26507_PRECHANGE_TESTED_26506_RUNTIME.patch"; rc=$?; set -e
[[ "$rc" -eq 1 && -s "$OUT/26507_PRECHANGE_TESTED_26506_RUNTIME.patch" ]] || fail "pre-change patch generation failed"
sha256sum "$OUT/26507_PRECHANGE_TESTED_26506_RUNTIME.patch" > "$OUT/26507_PRECHANGE_TESTED_26506_RUNTIME.patch.sha256"
( cd "$BEFORE" && tar --sort=name --mtime='UTC 2026-08-18 00:00:00' --owner=0 --group=0 --numeric-owner -czf "$OUT/26507_PRECHANGE_TESTED_26506_RUNTIME.tar.gz" app/src/main app/version.properties )
( cd "$BEFORE" && { find app/src/main -type f -print; echo app/version.properties; } | LC_ALL=C sort | while read -r f; do sha256sum "$f"; done ) > "$OUT/26507_prechange_tested_26506.sha256"
pass "GATE 2 exact tested 26506 reconstructed; pre-change patch/archive emitted before modification"

echo "=== GATE 3: apply 26507 and prove exact delta ==="
cp -a "$BEFORE/app/." "$AFTER/app/"
python3 "$APPLY_26507" "$AFTER" | tee "$OUT/26507_apply.txt"
python3 "$VALIDATOR_26507" "$AFTER" --base-root "$BEFORE" | tee "$OUT/26507_validate.txt"
python3 - "$BEFORE" "$AFTER" <<'PYDELTA'
from pathlib import Path
import hashlib,sys
b,a=map(Path,sys.argv[1:])
def collect(root):
 d={}
 for p in (root/'app/src/main').rglob('*'):
  if p.is_file(): d[p.relative_to(root).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
 return d
x,y=collect(b),collect(a); changed={k for k in set(x)|set(y) if x.get(k)!=y.get(k)}
expected={
'app/src/main/assets/shaders/motionv2/mfsr_bjzhou_guide.glsl',
'app/src/main/assets/shaders/motionv2/mfsr_mgc_covariance.glsl',
'app/src/main/assets/shaders/motionv2/mfsr_bjzhou_rejection_base.glsl',
'app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_contribute_26501.glsl',
'app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_short_weight_26501.glsl',
'app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_normalize_26501.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/MotionBatch.java',
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java',
'app/src/main/cpp/CMakeLists.txt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
'app/src/main/cpp/motionv2_jpeg_r_encoder.h',
'app/src/main/cpp/motionv2_jpeg_r_encoder.cpp',
'app/src/main/cpp/motionv2_jpeg444_jni.cpp'}
assert changed==expected,(sorted(changed),sorted(expected))
print('PASS: exact 16-file 26507 delta relative to tested 26506')
PYDELTA
set +e; git diff --no-index --binary "$BEFORE/app" "$AFTER/app" > "$OUT/26507_EXACT_DELTA_FROM_TESTED_26506.patch"; rc=$?; set -e
[[ "$rc" -eq 1 && -s "$OUT/26507_EXACT_DELTA_FROM_TESTED_26506.patch" ]] || fail "26507 delta patch failed"
sha256sum "$OUT/26507_EXACT_DELTA_FROM_TESTED_26506.patch" > "$OUT/26507_EXACT_DELTA_FROM_TESTED_26506.patch.sha256"
pass "GATE 3 exact candidate delta proven"

echo "=== GATE 4: fetch exact bjzhou native dependencies + static preflight ==="
BJ="$WORK/bjzhou-$BJZHOU_HEAD"; rm -rf "$BJ"; git init -q "$BJ"; git -C "$BJ" remote add origin https://github.com/bjzhou/PhotonCamera.git
git -C "$BJ" config core.sparseCheckout true
mkdir -p "$BJ/.git/info"; printf '%s\n' '/app/src/main/cpp/libjpeg-turbo/' '/app/src/main/cpp/libultrahdr/' > "$BJ/.git/info/sparse-checkout"
git -C "$BJ" fetch --depth=1 origin "$BJZHOU_HEAD"; git -C "$BJ" checkout -q --detach FETCH_HEAD
[[ "$(git -C "$BJ" rev-parse HEAD)" == "$BJZHOU_HEAD" ]] || fail "bjzhou dependency checkout drift"
THIRD="$AFTER/app/src/main/cpp/third_party_26507"; mkdir -p "$THIRD"
cp -a "$BJ/app/src/main/cpp/libjpeg-turbo" "$THIRD/libjpeg-turbo"; cp -a "$BJ/app/src/main/cpp/libultrahdr" "$THIRD/libultrahdr"
# IRIS_26507_V3_NATIVE_DEPENDENCY_LAYOUT_PROOF
[[ -f "$THIRD/libjpeg-turbo/CMakeLists.txt" ]] || fail "pinned libjpeg-turbo CMakeLists missing after sparse checkout"
[[ -f "$THIRD/libjpeg-turbo/src/turbojpeg.h" ]] || fail "pinned libjpeg-turbo turbojpeg.h missing"
[[ -f "$THIRD/libultrahdr/ultrahdr_api.h" ]] || fail "pinned libultrahdr root ultrahdr_api.h missing"
[[ -f "$THIRD/libultrahdr/lib/src/ultrahdr_api.cpp" ]] || fail "pinned libultrahdr core source missing"
[[ -d "$THIRD/libultrahdr/lib/include/ultrahdr" ]] || fail "pinned libultrahdr internal include tree missing"
[[ ! -e "$THIRD/libultrahdr/lib/include/ultrahdr_api.h" ]] || fail "unexpected obsolete lib/include/ultrahdr_api.h layout; audited source contract changed"
( cd "$THIRD" && find libjpeg-turbo libultrahdr -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum ) > "$OUT/26507_bjzhou_native_dependencies.sha256"
echo "$BJZHOU_HEAD" > "$OUT/26507_bjzhou_dependency_commit.txt"
command -v glslangValidator >/dev/null || fail "glslangValidator missing"
grep -F '16.5.0' <<<"$(glslangValidator --version | head -1)" >/dev/null || fail "wrong glslangValidator"
python3 - "$AFTER" "$WORK" "$OUT" <<'PYGLSL'
from pathlib import Path
import subprocess,sys
root,work,out=map(Path,sys.argv[1:])
items=[
 ('mfsr_bjzhou_guide.glsl','comp'),
 ('mfsr_mgc_covariance.glsl','comp'),
 ('mfsr_bjzhou_rejection_base.glsl','comp'),
 ('mfsr_spatial_rgb_short_weight_26501.glsl','comp'),
 ('mfsr_spatial_rgb_contribute_26501.glsl','frag'),
 ('mfsr_spatial_rgb_normalize_26501.glsl','frag')]
for name,stage in items:
 src=(root/'app/src/main/assets/shaders/motionv2'/name).read_text()
 if stage=='comp':
  src=src.replace('#define LAYOUT //','',1).replace('LAYOUT','layout(local_size_x=8,local_size_y=8,local_size_z=1) in;',1)
 tmp=work/(name+'.'+stage)
 tmp.write_text('#version 310 es\n'+src)
 cp=subprocess.run(['glslangValidator','-S',stage,str(tmp)],capture_output=True,text=True)
 (out/(name+'.glslang.txt')).write_text(cp.stdout+cp.stderr)
 if cp.returncode: raise SystemExit('GLSL failed '+name+'\n'+cp.stdout+cp.stderr)
print('PASS: all six changed shaders compile with glslang 16.5.0')
PYGLSL
python3 -m py_compile "$APPLY_26507" "$VALIDATOR_26507"
mkdir -p "$WORK/javac_parse"
javac -proc:none -Xmaxerrs 10000 -d "$WORK/javac_parse"  "$AFTER/app/src/main/java/com/particlesdevs/photoncamera/processing/MotionBatch.java"  "$AFTER/app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java"  "$AFTER/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java"  "$AFTER/app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java"  "$AFTER/app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java"  "$AFTER/app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java"  > "$OUT/26507_javac_parse.log" 2>&1 || true
python3 - "$OUT/26507_javac_parse.log" <<'PYJAVA'
from pathlib import Path
import sys
s=Path(sys.argv[1]).read_text(errors='replace')
pats=['; expected','illegal start of','reached end of file while parsing',"')' expected","'}' expected",'not a statement','class, interface, enum, or record expected','unclosed']
bad=[x for x in s.splitlines() if any(p in x for p in pats)]
assert not bad,bad[:40]
print('PASS: all changed Java owners contain no syntax/parse diagnostics')
PYJAVA
# Preserve all core invariants.
grep -F 'IRIS_26507_MGC_RAW_HALF_GUIDE_PARITY' "$AFTER/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java" >/dev/null
grep -F 'IRIS_26507_FROZEN_AUX_BATCH_BOUNDARY' "$AFTER/app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java" >/dev/null
grep -F 'final boolean iris26507ShortExpected =' "$AFTER/app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java" >/dev/null
grep -F 'iris26486ShortTicket != null && iris26486ShortTicket.requested' "$AFTER/app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java" >/dev/null
grep -F 'final boolean iris26507LongExpected = mMotion26505LongRequested;' "$AFTER/app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java" >/dev/null
grep -F 'iris26507ShortExpected, iris26507LongExpected, 80L' "$AFTER/app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java" >/dev/null
if grep -F 'iris26480ShortHighlightRequested, iris26505LongRequested, 80L' "$AFTER/app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java" >/dev/null; then fail "stale out-of-scope aux freeze locals survived"; fi
grep -F 'Log.e(TAG,"IRIS_26507_JPEG444_FAILED",t);' "$AFTER/app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java" >/dev/null
if grep -F 'Log.getStackTraceString(t)' "$AFTER/app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java" >/dev/null; then fail "JPEG444 uses Exception-only stack helper with Throwable"; fi
grep -F 'IRIS_26507_SHORT_A_SHARED_MGC_PRECHROMA_GATE' "$AFTER/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java" >/dev/null
grep -F 'IRIS_26507_LONG_A_SHARED_MGC_PRECHROMA_GATE' "$AFTER/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java" >/dev/null
grep -F 'IRIS_26507_FULL_HDR_DISPLAY_CAPACITY_PARITY' "$AFTER/app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java" >/dev/null
grep -F 'TJSAMP_444' "$AFTER/app/src/main/cpp/motionv2_jpeg444_jni.cpp" >/dev/null
grep -F 'uhdr_enc_set_compressed_image' "$AFTER/app/src/main/cpp/motionv2_jpeg_r_encoder.cpp" >/dev/null
[[ "$(grep '^VERSION_NAME=' "$AFTER/app/version.properties" | cut -d= -f2)" == "0.9726502" ]] || fail "version changed before safety proof"
[[ "$(grep '^VERSION_BUILD=' "$AFTER/app/version.properties" | cut -d= -f2)" == "26502" ]] || fail "build changed before safety proof"
echo "PRE-BUILD SAFETY PROOF PASSED"
pass "GATE 4 RAW/2 MGC/shared auxiliary rejection/lifecycle/UHDR/JPEG444 dependency + shader/Java preflight"

echo "=== GATE 5: VERSION 0.9726507 / 26507 + BUILD IN SAME GUARDED BLOCK ==="
python3 - "$AFTER/app/version.properties" <<'PYVER'
from pathlib import Path
import sys
p=Path(sys.argv[1]); s=p.read_text(); s=s.replace('VERSION_NAME=0.9726502','VERSION_NAME=0.9726507').replace('VERSION_BUILD=26502','VERSION_BUILD=26507'); p.write_text(s)
assert 'VERSION_NAME=0.9726507' in s and 'VERSION_BUILD=26507' in s
PYVER
# Overlay candidate only after proof.
rm -rf app/src/main; cp -a "$AFTER/app/src/main" app/src/main; cp "$AFTER/app/version.properties" app/version.properties
chmod +x ./gradlew
./gradlew clean :app:assembleDebug --stacktrace
mapfile -t APKS < <(find app/build -type f -name '*.apk' | sort)
[[ "${#APKS[@]}" -eq 1 ]] || fail "expected exactly one APK, found ${#APKS[@]}"
[[ "$(basename "${APKS[0]}")" == "IrisCamera-0.9726507-26507-debug.apk" ]] || fail "unexpected APK identity $(basename "${APKS[0]}")"
FINAL="$ROOT/IrisCamera-0.9726507-26507-mgc-parity-immutable-hdr-jpeg444-debug.apk"; rm -f "$FINAL"; cp "${APKS[0]}" "$FINAL"
# IRIS_26507_V5_TYPED_POSTBUILD_PROOF
# Prove each artifact in the representation where it can actually survive compilation:
# runtime Java telemetry in DEX, GLSL ownership markers in packaged shader assets,
# and the native 4:4:4 bridge as an APK shared library. Java source comments are
# already proven by Gate 4 and must never be required to survive into DEX.
python3 - "$FINAL" <<'PYAPK'
import sys,zipfile
p=sys.argv[1]
with zipfile.ZipFile(p) as z:
 names=set(z.namelist())
 libs=sorted(n for n in names if n.endswith('/libmotionv2jpeg.so'))
 assert libs, 'libmotionv2jpeg.so missing from APK'
 dex_names=sorted(n for n in names if n.endswith('.dex'))
 assert dex_names, 'APK contains no DEX files'
 dex=b''.join(z.read(n) for n in dex_names)
 runtime_dex_markers=[
  b'IRIS_26507_MGC_GEOMETRY',
  b'IRIS_26507_FROZEN_AUX_BATCH_BOUNDARY',
  b'IRIS_26507_FULL_HDR_DISPLAY_CAPACITY_PARITY',
  b'IRIS_26507_JPEG444',
 ]
 for marker in runtime_dex_markers:
  assert marker in dex, b'missing runtime DEX marker: '+marker
 packaged_shader_markers={
  'assets/shaders/motionv2/mfsr_bjzhou_guide.glsl': b'IRIS_26507_MGC_RAW_HALF_GUIDE_PARITY',
  'assets/shaders/motionv2/mfsr_bjzhou_rejection_base.glsl': b'IRIS_26507_DYNAMIC_MGC_FLOW_THRESHOLD',
  'assets/shaders/motionv2/mfsr_spatial_rgb_contribute_26501.glsl': b'IRIS_26507_COVARIANCE_QUAD_CENTER_UV',
  'assets/shaders/motionv2/mfsr_spatial_rgb_short_weight_26501.glsl': b'IRIS_26507_GPU_LOCAL_8_CONNECTED_SHORT_TOPOLOGY',
 }
 for suffix,marker in packaged_shader_markers.items():
  matches=[n for n in names if n.endswith(suffix)]
  assert len(matches)==1, f'expected one packaged shader {suffix}, found {matches}'
  payload=z.read(matches[0])
  assert marker in payload, b'missing packaged shader marker: '+marker
 print('PASS: APK typed proof: runtime DEX telemetry + packaged 26507 shaders + libmotionv2jpeg.so')
PYAPK
sha256sum "$FINAL" > "$OUT/26507_APK.sha256"
# Successful source checkpoint excludes fetched third-party tree from compact project-source archive; dependency manifest/commit above proves it separately.
rm -rf "$AFTER/app/src/main/cpp/third_party_26507"
( cd "$AFTER" && tar --sort=name --mtime='UTC 2026-08-18 00:00:00' --owner=0 --group=0 --numeric-owner -czf "$OUT/26507_successful_app_source.tar.gz" app/src/main app/version.properties )
pass "GATE 5 exactly one 26507 APK built"

echo "=== GATE 6: SUCCESS ==="
echo "APK: $(basename "$FINAL")"; echo "APK SHA256: $(sha "$FINAL")"; echo "START_HEAD=$START_HEAD"; echo "BJZHOU_HEAD=$BJZHOU_HEAD"
pass "26507 root fix complete: RAW/2 MGC + immutable aux + shared Short/Long rejection + GPU Short topology + UHDR capacity parity + JPEG 4:4:4"
