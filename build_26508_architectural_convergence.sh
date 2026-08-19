#!/usr/bin/env bash
set -euo pipefail
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
ROOT="$(pwd)"
OUT="$ROOT/build_26508_architectural_convergence_outputs"
WORK="$ROOT/.build_26508_architectural_convergence_work"
CANON="$WORK/canonical26502"; V26506="$WORK/exact26506"; BEFORE="$WORK/tested26507"; AFTER="$WORK/candidate26508"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
CANONICAL_26502_HEAD="6118984523296945a0910e55ddaa4d3126184059"
TESTED_26507_V5_HEAD="c4f99d7f3212ac82b0976b41621c8b5bb917d31b"
BACKUP_26507_V5_BRANCH="backup-26507-tested-before-26508-20260818"
BJZHOU_HEAD="09c76e57e8f01a5a8fc536ab41fc80ba642d4042"
SEED_26503="$ROOT/26503_v2_seed_safe_highlight_shadow_runtime.patch"
APPLY_26504="$ROOT/apply_26504_integrated.py"; VALIDATOR_26504="$ROOT/validate_26504_integrated.py"
APPLY_26505="$ROOT/apply_26505_bjzhou_consistency.py"; VALIDATOR_26505="$ROOT/validate_26505_bjzhou_consistency.py"
APPLY_26506="$ROOT/apply_26506_uhdr_parity_opponent_chroma.py"; VALIDATOR_26506="$ROOT/validate_26506_uhdr_parity_opponent_chroma.py"
APPLY_26507="$ROOT/apply_26507_mgc_parity_immutable_hdr_jpeg444.py"; VALIDATOR_26507="$ROOT/validate_26507_mgc_parity_immutable_hdr_jpeg444.py"
APPLY_26508="$ROOT/apply_26508_architectural_convergence.py"; VALIDATOR_26508="$ROOT/validate_26508_architectural_convergence.py"
INTEGRITY="$ROOT/verify_26501_source_integrity.py"
SEED_26503_SHA="c5d4e13e6f8a59243eedac8c2beab9d737444a231f21411bf7dec1636dca5a1e"
APPLY_26504_SHA="96f44374c564231abf13e219362add26c4a3ff1be1e1bbd793b3cd4af3ef6348"
VALIDATOR_26504_SHA="c071526c04b36a5c8d19525c1485b01c5eea4befe89abc7443b24fef4f4d28f3"
APPLY_26505_SHA="2a718c5972ab4a8f518c3f25d769e9ac37e87050989e85dcb1f747272e6bd9bf"
VALIDATOR_26505_SHA="703df94241c2a4effcf088eb757809dbc9da141b0c295a46aaf40e93ec8a0345"
APPLY_26506_SHA="c34f71ccbfc436df604be410a8dff373d81963826a3359cfff43f28d9807bccd"
VALIDATOR_26506_SHA="9aca6c1bf3e65360542ec1e158bfcb663bf54df1d5c3b8847c103b542f738a6e"
APPLY_26507_SHA="3552094867cbc56db3fad891cd86c4b1dee2cdbd3d85d1bedc4c8f7bdb4a2723"
VALIDATOR_26507_SHA="0b74b72c96a1e51604cb2f934e32b69aa5e692cb7101a231d3cf33127975f1b5"
APPLY_26508_SHA="dc24617dd324f18127e3cd0b1cb980f1708e17c6a4d18142da5ed0c96f125d29"
VALIDATOR_26508_SHA="8859a5fea5fad747ab80cf3e631694ee55db1fa9d6081b85e32e6decc9570c4c"
rm -rf "$OUT" "$WORK"; mkdir -p "$OUT" "$CANON" "$V26506" "$BEFORE" "$AFTER"
exec > >(tee "$OUT/26508_build.log") 2>&1

echo "=== GATE 1: exact tested 26507 V5 lineage + backup + dependency identity ==="
BRANCH="$(git branch --show-current)"; START_HEAD="$(git rev-parse HEAD)"
[[ "$BRANCH" == "$EXPECTED_BRANCH" && "$BRANCH" != "dev" ]] || fail "wrong/protected branch $BRANCH"
git merge-base --is-ancestor "$TESTED_26507_V5_HEAD" HEAD || fail "tested 26507 V5 handoff missing from lineage"
git merge-base --is-ancestor "$CANONICAL_26502_HEAD" HEAD || fail "canonical 26502 missing from lineage"
git diff --name-only "$CANONICAL_26502_HEAD"..HEAD -- app/src/main app/version.properties > "$OUT/runtime_diff_from_canonical_26502.txt"
[[ ! -s "$OUT/runtime_diff_from_canonical_26502.txt" ]] || { cat "$OUT/runtime_diff_from_canonical_26502.txt" >&2; fail "committed runtime drift exists"; }
REMOTE_BACKUP="$(git ls-remote origin "refs/heads/$BACKUP_26507_V5_BRANCH" | awk '{print $1}')"
[[ "$REMOTE_BACKUP" == "$TESTED_26507_V5_HEAD" ]] || fail "backup missing/wrong: $BACKUP_26507_V5_BRANCH -> ${REMOTE_BACKUP:-MISSING}"
for f in "$SEED_26503" "$APPLY_26504" "$VALIDATOR_26504" "$APPLY_26505" "$VALIDATOR_26505" "$APPLY_26506" "$VALIDATOR_26506" "$APPLY_26507" "$VALIDATOR_26507" "$APPLY_26508" "$VALIDATOR_26508" "$INTEGRITY"; do [[ -f "$f" ]] || fail "missing $(basename "$f")"; done
[[ "$(sha "$SEED_26503")" == "$SEED_26503_SHA" ]] || fail "26503 seed hash mismatch"
[[ "$(sha "$APPLY_26504")" == "$APPLY_26504_SHA" && "$(sha "$VALIDATOR_26504")" == "$VALIDATOR_26504_SHA" ]] || fail "26504 dependency hash mismatch"
[[ "$(sha "$APPLY_26505")" == "$APPLY_26505_SHA" && "$(sha "$VALIDATOR_26505")" == "$VALIDATOR_26505_SHA" ]] || fail "26505 dependency hash mismatch"
[[ "$(sha "$APPLY_26506")" == "$APPLY_26506_SHA" && "$(sha "$VALIDATOR_26506")" == "$VALIDATOR_26506_SHA" ]] || fail "26506 dependency hash mismatch"
[[ "$(sha "$APPLY_26507")" == "$APPLY_26507_SHA" && "$(sha "$VALIDATOR_26507")" == "$VALIDATOR_26507_SHA" ]] || fail "26507 V5 transform/validator hash mismatch"
[[ "$(sha "$APPLY_26508")" == "$APPLY_26508_SHA" && "$(sha "$VALIDATOR_26508")" == "$VALIDATOR_26508_SHA" ]] || fail "26508 transform/validator hash mismatch"
pass "GATE 1 exact branch/lineage + backup-26507-tested-before-26508 + dependency hashes"

echo "=== GATE 2: reconstruct exact tested 26507 and freeze PRE-26508 safety artifacts ==="
git archive "$CANONICAL_26502_HEAD" app/src/main app/version.properties | tar -x -C "$CANON"
# Proven 26506 safety step: fresh checkout runtime must be byte-identical to canonical 26502
# before any reconstruction transform is allowed to run.
python3 - "$CANON" "$ROOT" "$OUT/26502_canonical_runtime_snapshot.json" <<'PYBASE'
from pathlib import Path
import hashlib,json,sys
pre=Path(sys.argv[1]); root=Path(sys.argv[2]); out=Path(sys.argv[3])
def collect(base):
 d={}
 for p in (base/'app/src/main').rglob('*'):
  if p.is_file(): d[p.relative_to(base/'app').as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
 vp=base/'app/version.properties'; d[vp.relative_to(base/'app').as_posix()]=hashlib.sha256(vp.read_bytes()).hexdigest()
 return d
p=collect(pre); r=collect(root)
assert p==r,'working runtime is not byte-identical to canonical tested 26502'
out.write_text(json.dumps(p,sort_keys=True,indent=2))
print('PASS: canonical tested 26502 working runtime byte-identity',len(p),'files')
PYBASE
cp -a "$CANON/app/." "$V26506/app/"
patch --dry-run --batch --forward --fuzz=0 --no-backup-if-mismatch -p1 -d "$V26506" < "$SEED_26503" > "$OUT/26503_seed_dry.txt"
patch --batch --forward --fuzz=0 --no-backup-if-mismatch -p1 -d "$V26506" < "$SEED_26503" > "$OUT/26503_seed_apply.txt"
python3 "$APPLY_26504" "$V26506" | tee "$OUT/26504_apply.txt"; python3 "$VALIDATOR_26504" "$V26506" --base-root "$CANON" | tee "$OUT/26504_validate.txt"
python3 "$APPLY_26505" "$V26506" | tee "$OUT/26505_apply.txt"; python3 "$VALIDATOR_26505" "$V26506" --base-root "$CANON" | tee "$OUT/26505_validate.txt"
python3 "$APPLY_26506" "$V26506" | tee "$OUT/26506_apply.txt"; python3 "$VALIDATOR_26506" "$V26506" --base-root "$CANON" | tee "$OUT/26506_validate.txt"
cp -a "$V26506/app/." "$BEFORE/app/"
python3 "$APPLY_26507" "$BEFORE" | tee "$OUT/26507_apply.txt"
python3 "$VALIDATOR_26507" "$BEFORE" --base-root "$V26506" | tee "$OUT/26507_validate.txt"
# Required PRE-26508 recovery artifacts are emitted before the 26508 transform.
set +e; git diff --no-index --binary "$CANON/app" "$BEFORE/app" > "$OUT/26508_PRECHANGE_TESTED_26507_RUNTIME.patch"; rc=$?; set -e
[[ "$rc" -eq 1 && -s "$OUT/26508_PRECHANGE_TESTED_26507_RUNTIME.patch" ]] || fail "prechange tested-26507 patch generation failed"
sha256sum "$OUT/26508_PRECHANGE_TESTED_26507_RUNTIME.patch" > "$OUT/26508_PRECHANGE_TESTED_26507_RUNTIME.patch.sha256"
( cd "$BEFORE" && tar --sort=name --mtime='UTC 2026-08-18 00:00:00' --owner=0 --group=0 --numeric-owner -czf "$OUT/26508_PRECHANGE_TESTED_26507_RUNTIME.tar.gz" app/src/main app/version.properties )
( cd "$BEFORE" && { find app/src/main -type f -print; echo app/version.properties; } | LC_ALL=C sort | while read -r f; do sha256sum "$f"; done ) > "$OUT/26508_prechange_tested_26507.sha256"
grep -F 'IRIS_26507_MGC_RAW_HALF_GUIDE_PARITY' "$BEFORE/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java" >/dev/null
grep -F 'IRIS_26507_FROZEN_AUX_BATCH_BOUNDARY' "$BEFORE/app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java" >/dev/null
grep -F 'IRIS_26507_GPU_LOCAL_8_CONNECTED_SHORT_TOPOLOGY' "$BEFORE/app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_short_weight_26501.glsl" >/dev/null
pass "GATE 2 exact tested 26507/V5 runtime reconstructed; pre-26508 patch/archive frozen"

echo "=== GATE 3: apply 26508 and prove exact architectural delta ==="
cp -a "$BEFORE/app/." "$AFTER/app/"
python3 "$APPLY_26508" "$AFTER" | tee "$OUT/26508_apply.txt"
python3 "$VALIDATOR_26508" "$AFTER" --base-root "$BEFORE" | tee "$OUT/26508_validate.txt"
set +e; git diff --no-index --binary "$BEFORE/app" "$AFTER/app" > "$OUT/26508_EXACT_DELTA_FROM_TESTED_26507.patch"; rc=$?; set -e
[[ "$rc" -eq 1 && -s "$OUT/26508_EXACT_DELTA_FROM_TESTED_26507.patch" ]] || fail "26508 exact delta patch generation failed"
sha256sum "$OUT/26508_EXACT_DELTA_FROM_TESTED_26507.patch" > "$OUT/26508_EXACT_DELTA_FROM_TESTED_26507.patch.sha256"
pass "GATE 3 exact 9-file 26508 delta + architectural validator"

echo "=== GATE 4: pinned native deps + GLSL/Java preflight + retained authority proof ==="
BJ="$WORK/bjzhou-$BJZHOU_HEAD"; rm -rf "$BJ"; git init -q "$BJ"; git -C "$BJ" remote add origin https://github.com/bjzhou/PhotonCamera.git
git -C "$BJ" config core.sparseCheckout true; mkdir -p "$BJ/.git/info"; printf '%s\n' '/app/src/main/cpp/libjpeg-turbo/' '/app/src/main/cpp/libultrahdr/' > "$BJ/.git/info/sparse-checkout"
git -C "$BJ" fetch --depth=1 origin "$BJZHOU_HEAD"; git -C "$BJ" checkout -q --detach FETCH_HEAD
[[ "$(git -C "$BJ" rev-parse HEAD)" == "$BJZHOU_HEAD" ]] || fail "bjzhou dependency checkout drift"
THIRD="$AFTER/app/src/main/cpp/third_party_26507"; mkdir -p "$THIRD"; cp -a "$BJ/app/src/main/cpp/libjpeg-turbo" "$THIRD/libjpeg-turbo"; cp -a "$BJ/app/src/main/cpp/libultrahdr" "$THIRD/libultrahdr"
[[ -f "$THIRD/libjpeg-turbo/src/turbojpeg.h" && -f "$THIRD/libultrahdr/ultrahdr_api.h" && -f "$THIRD/libultrahdr/lib/src/ultrahdr_api.cpp" ]] || fail "pinned native dependency layout missing"
( cd "$THIRD" && find libjpeg-turbo libultrahdr -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum ) > "$OUT/26508_bjzhou_native_dependencies.sha256"
echo "$BJZHOU_HEAD" > "$OUT/26508_bjzhou_dependency_commit.txt"
command -v glslangValidator >/dev/null || fail "glslangValidator missing"
grep -F '16.5.0' <<<"$(glslangValidator --version | head -1)" >/dev/null || fail "wrong glslangValidator"
python3 - "$AFTER" "$WORK" "$OUT" <<'PYGLSL'
from pathlib import Path
import subprocess,sys
root,work,out=map(Path,sys.argv[1:])
items=[
 ('mfsr_bjzhou_guide.glsl','comp'),('mfsr_mgc_covariance.glsl','comp'),('mfsr_bjzhou_rejection_base.glsl','comp'),
 ('short_highlight_bayer_recover.glsl','comp'),('mfsr_spatial_rgb_short_weight_26501.glsl','comp'),
 ('mfsr_bridge_flow_compose_26508.glsl','comp'),('mfsr_short_region_seed_26508.glsl','comp'),
 ('mfsr_short_region_propagate_26508.glsl','comp'),('mfsr_short_region_finalize_26508.glsl','comp'),
 ('mfsr_spatial_rgb_contribute_26501.glsl','frag'),('mfsr_spatial_rgb_normalize_26501.glsl','frag')]
for name,stage in items:
 src=(root/'app/src/main/assets/shaders/motionv2'/name).read_text()
 if stage=='comp': src=src.replace('#define LAYOUT //','',1).replace('LAYOUT','layout(local_size_x=8,local_size_y=8,local_size_z=1) in;',1)
 tmp=work/(name+'.'+stage); tmp.write_text('#version 310 es\n'+src)
 cp=subprocess.run(['glslangValidator','-S',stage,str(tmp)],capture_output=True,text=True)
 (out/(name+'.glslang.txt')).write_text(cp.stdout+cp.stderr)
 if cp.returncode: raise SystemExit('GLSL failed '+name+'\n'+cp.stdout+cp.stderr)
print('PASS: changed + retained MGC/Spatial-RGB shaders compile with glslang 16.5.0')
PYGLSL
python3 -m py_compile "$APPLY_26508" "$VALIDATOR_26508"
mkdir -p "$WORK/javac_parse"
javac -proc:none -Xmaxerrs 10000 -d "$WORK/javac_parse"  "$AFTER/app/src/main/java/com/particlesdevs/photoncamera/processing/MotionBatch.java"  "$AFTER/app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java"  "$AFTER/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java"  > "$OUT/26508_javac_parse.log" 2>&1 || true
python3 - "$OUT/26508_javac_parse.log" <<'PYJAVA'
from pathlib import Path
import sys
s=Path(sys.argv[1]).read_text(errors='replace')
pats=['; expected','illegal start of','reached end of file while parsing',"')' expected","'}' expected",'not a statement','class, interface, enum, or record expected','unclosed']
bad=[x for x in s.splitlines() if any(p in x for p in pats)]
assert not bad,bad[:50]
print('PASS: changed Java owners contain no syntax/parse diagnostics')
PYJAVA
# Hard architectural gates.
HOST="$AFTER/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java"
SHORT="$AFTER/app/src/main/assets/shaders/motionv2/short_highlight_bayer_recover.glsl"
WEIGHT="$AFTER/app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_short_weight_26501.glsl"
grep -F 'IRIS_26508_SHARED_NORMAL_LONG_MGC_FUSION_OWNER' "$HOST" >/dev/null
! grep -F 'useAssetProgram("motionv2/shadow_aux_bayer_fuse"' "$HOST" >/dev/null || fail "post-hoc Long semantic owner survived"
! grep -F 'refineObservableCorrespondence' "$SHORT" >/dev/null || fail "old direct Short correspondence survived"
! grep -F 'IRIS_26503_BOUNDARY_ANCHORED_SHORT_OBSERVABILITY' "$SHORT" >/dev/null || fail "old boundary fallback survived"
grep -F 'IRIS_26508_BRIDGE_GEOMETRY_ONLY_NEVER_CONTRIBUTES_RGB' "$SHORT" >/dev/null
grep -F 'IRIS_26508_GPU_8_CONNECTED_REGION_PROPAGATION' "$AFTER/app/src/main/assets/shaders/motionv2/mfsr_short_region_propagate_26508.glsl" >/dev/null
! grep -F 'IRIS_26507_GPU_LOCAL_8_CONNECTED_SHORT_TOPOLOGY' "$WEIGHT" >/dev/null || fail "one-hop 26507 topology survived"
grep -F 'IRIS_26507_FULL_HDR_DISPLAY_CAPACITY_PARITY' "$AFTER/app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java" >/dev/null
grep -F 'TJSAMP_444' "$AFTER/app/src/main/cpp/motionv2_jpeg444_jni.cpp" >/dev/null
[[ "$(grep '^VERSION_NAME=' "$AFTER/app/version.properties" | cut -d= -f2)" == "0.9726502" ]] || fail "version changed before safety proof"
[[ "$(grep '^VERSION_BUILD=' "$AFTER/app/version.properties" | cut -d= -f2)" == "26502" ]] || fail "build changed before safety proof"
echo "PRE-BUILD SAFETY PROOF PASSED"
pass "GATE 4 bridge/Long/topology ownership + shader/Java/native + 26507 preservation proof"

echo "=== GATE 5: VERSION 0.9726508 / 26508 + BUILD IN SAME GUARDED BLOCK ==="
python3 - "$AFTER/app/version.properties" <<'PYVER'
from pathlib import Path
import re,sys
p=Path(sys.argv[1]);s=p.read_text()
s=re.sub(r'^VERSION_NAME=.*$','VERSION_NAME=0.9726508',s,flags=re.M)
s=re.sub(r'^VERSION_BUILD=.*$','VERSION_BUILD=26508',s,flags=re.M)
p.write_text(s)
assert 'VERSION_NAME=0.9726508' in s and 'VERSION_BUILD=26508' in s
PYVER
# Proven 26506 module-shell protection: overlay only src/main + version.properties.
find app -maxdepth 1 -type f ! -name version.properties -print0 | sort -z | xargs -0 sha256sum > "$OUT/app_shell_pre_26508_overlay.sha256"
rm -rf app/src/main; cp -a "$AFTER/app/src/main" app/src/main; cp "$AFTER/app/version.properties" app/version.properties
find app -maxdepth 1 -type f ! -name version.properties -print0 | sort -z | xargs -0 sha256sum > "$OUT/app_shell_post_26508_overlay.sha256"
diff -u "$OUT/app_shell_pre_26508_overlay.sha256" "$OUT/app_shell_post_26508_overlay.sha256" >/dev/null || fail "module shell changed"
# Proven 26506 Gradle-mutation guard.
python3 "$INTEGRITY" snapshot "$ROOT/app" "$OUT/26508_pre_gradle_manifest.json"
find "$ROOT" -maxdepth 1 -type f -name '*.apk' -delete
chmod +x ./gradlew
./gradlew clean :app:assembleDebug --stacktrace
python3 "$INTEGRITY" verify "$ROOT/app" "$OUT/26508_pre_gradle_manifest.json" | tee "$OUT/26508_post_gradle_integrity.txt"
mapfile -t APKS < <(find app/build -type f -name '*.apk' | sort)
[[ "${#APKS[@]}" -eq 1 ]] || fail "expected exactly one Gradle APK, found ${#APKS[@]}"
[[ "$(basename "${APKS[0]}")" == "IrisCamera-0.9726508-26508-debug.apk" ]] || fail "unexpected APK identity $(basename "${APKS[0]}")"
FINAL="$ROOT/IrisCamera-0.9726508-26508-architectural-convergence-debug.apk"; cp "${APKS[0]}" "$FINAL"; rm -f "${APKS[0]}"
mapfile -t ALL_APKS < <(find "$ROOT" -type f -name '*.apk' -not -path '*/.gradle/*' | sort)
[[ "${#ALL_APKS[@]}" -eq 1 && "${ALL_APKS[0]}" == "$FINAL" ]] || { printf '%s\n' "${ALL_APKS[@]}"; fail "exactly-one APK output invariant failed"; }
python3 - "$FINAL" "$AFTER" <<'PYAPK'
import hashlib,sys,zipfile
p=sys.argv[1]; root=sys.argv[2]
h=lambda b:hashlib.sha256(b).hexdigest()
with zipfile.ZipFile(p) as z:
 names=set(z.namelist()); assert 'AndroidManifest.xml' in names
 libs=[n for n in names if n.endswith('/libmotionv2jpeg.so')]; assert libs,'libmotionv2jpeg.so missing'
 dex=b''.join(z.read(n) for n in sorted(names) if n.endswith('.dex'))
 for marker in [b'IRIS_26508_FROZEN_GEOMETRY_BRIDGE',b'IRIS_26508_NEAREST_NORMAL_BRIDGE_SELECTION',b'IRIS_26508_SHARED_NORMAL_LONG_MGC_FUSION_OWNER',b'IRIS_26508_SHORT_ARCHITECTURAL_RESULT',b'IRIS_26507_FULL_HDR_DISPLAY_CAPACITY_PARITY',b'IRIS_26507_JPEG444']:
  assert marker in dex,b'missing runtime DEX marker '+marker
 shaders={
 'assets/shaders/motionv2/mfsr_bjzhou_guide.glsl':b'IRIS_26507_MGC_RAW_HALF_GUIDE_PARITY',
 'assets/shaders/motionv2/mfsr_bjzhou_rejection_base.glsl':b'IRIS_26507_DYNAMIC_MGC_FLOW_THRESHOLD',
 'assets/shaders/motionv2/mfsr_spatial_rgb_contribute_26501.glsl':b'IRIS_26507_COVARIANCE_QUAD_CENTER_UV',
 'assets/shaders/motionv2/short_highlight_bayer_recover.glsl':b'IRIS_26508_SHORT_TO_NEAREST_NORMAL_BRIDGE_AUTHORITY',
 'assets/shaders/motionv2/mfsr_bridge_flow_compose_26508.glsl':b'IRIS_26508_WRONSKI_BRIDGE_FLOW_COMPOSITION',
 'assets/shaders/motionv2/mfsr_short_region_seed_26508.glsl':b'IRIS_26508_GPU_REGION_BOUNDARY_SEED',
 'assets/shaders/motionv2/mfsr_short_region_propagate_26508.glsl':b'IRIS_26508_GPU_8_CONNECTED_REGION_PROPAGATION',
 'assets/shaders/motionv2/mfsr_short_region_finalize_26508.glsl':b'IRIS_26508_REGION_TO_FINAL_PROVENANCE_AUTHORITY',
 'assets/shaders/motionv2/mfsr_spatial_rgb_short_weight_26501.glsl':b'IRIS_26508_REGION_FINAL_SHORT_PHASE_WEIGHT'}
 for suffix,marker in shaders.items():
  xs=[n for n in names if n.endswith(suffix)];assert len(xs)==1,(suffix,xs)
  payload=z.read(xs[0]); assert marker in payload,marker
  rel=suffix.split('assets/shaders/motionv2/',1)[1]
  source=(__import__('pathlib').Path(root)/'app/src/main/assets/shaders/motionv2'/rel).read_bytes()
  assert h(payload)==h(source),('packaged shader differs from candidate source',rel)
 print('PASS: APK typed proof + exact source-to-packaged shader hash parity + retained 26507 native/JPEG')
PYAPK
# Re-extract independently and verify manifest identity/version with Android SDK analyzer.
REX="$WORK/apk_reextract"; rm -rf "$REX"; mkdir -p "$REX"; unzip -q "$FINAL" -d "$REX"; [[ -s "$REX/AndroidManifest.xml" ]] || fail "re-extracted AndroidManifest missing"
SDK_ROOT="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-}}"
[[ -n "$SDK_ROOT" ]] || fail "Android SDK root unavailable for manifest verification"
APKANALYZER="$(find "$SDK_ROOT" -type f -name apkanalyzer 2>/dev/null | sort -V | tail -1 || true)"
[[ -n "$APKANALYZER" ]] || fail "apkanalyzer not found for manifest verification"
[[ "$("$APKANALYZER" manifest version-name "$FINAL" | tr -d '\r')" == "0.9726508" ]] || fail "manifest versionName mismatch"
[[ "$("$APKANALYZER" manifest version-code "$FINAL" | tr -d '\r')" == "26508" ]] || fail "manifest versionCode mismatch"
sha256sum "$FINAL" > "$OUT/26508_APK.sha256"
pass "GATE 5 exactly one 0.9726508/26508 APK built + source integrity + typed APK proof + fresh manifest re-extraction proof"

echo "=== GATE 6: SUCCESSFUL SOURCE CHECKPOINT / REPORT — NO PROMOTION ==="
rm -rf "$AFTER/app/src/main/cpp/third_party_26507"
( cd "$AFTER" && tar --sort=name --mtime='UTC 2026-08-18 00:00:00' --owner=0 --group=0 --numeric-owner -czf "$OUT/26508_successful_app_source.tar.gz" app/src/main app/version.properties )
( cd "$AFTER" && { find app/src/main -type f -print; echo app/version.properties; } | LC_ALL=C sort | while read -r f; do sha256sum "$f"; done ) > "$OUT/26508_successful_after.sha256"
cat > "$OUT/26508_build_report.txt" <<EOF
26508 Architectural Convergence
Start infrastructure HEAD: $START_HEAD
Protected tested-26507/V5 backup: $BACKUP_26507_V5_BRANCH -> $TESTED_26507_V5_HEAD
Canonical runtime base: tested 26502 $CANONICAL_26502_HEAD
Version/build: 0.9726508 / 26508
APK: $(basename "$FINAL")
APK SHA256: $(sha "$FINAL")
Reconstruction: exact canonical 26502 -> validated 26503 -> 26504 -> 26505 -> 26506 -> tested 26507/V5, then exact 9-file 26508 delta.
Build procedure: 26506 canonical byte identity + module-shell + pre/post-Gradle integrity retained; 26507 pinned native dependency + typed APK proof retained.
Long-A: separate physical capture remains outside equal-exposure Wronski list; final accepted color contribution converges into the one Spatial-RGB accumulator/normalizer.
Short-A: geometry-only nearest-Normal bridge + Wronski flow composition replaces old direct local reference correspondence as final authority.
Topology: GPU 8-connected region propagation replaces 26507 one-hop local proxy.
UHDR/JPEG: tested 26507 HDR metadata and JPEG 4:4:4/JPEG_R path preserved.
Promotion: NONE until on-device acceptance.
EOF
pass "GATE 6 successful-source checkpoint + build report emitted; no promotion"
echo "PASS: 26508 ARCHITECTURAL CONVERGENCE BUILD COMPLETE"
echo "APK=$FINAL"
