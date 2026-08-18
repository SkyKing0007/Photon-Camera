#!/usr/bin/env bash
set -euo pipefail
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
ROOT="$(pwd)"
OUT="$ROOT/build_26503_v2_canonical_scene_faithful_outputs"
WORK="$ROOT/.build_26503_v2_canonical_scene_faithful_work"
BASE="$WORK/base26499"
CAND="$WORK/exact26502"
PRE="$WORK/prechange26502"
AFTER="$WORK/candidate26503"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
BASELINE_26502_HEAD="5b87d616a8d20ea0fbad9b7fd47627215cd4ba48"
V7_SHA="ed5470179aea9514c15d52dcb35613c7925778c6"
V6_HEAD="c6415d57a0d276b6ba7d4948df45ed15ea88a410"
BASE_TAR="$ROOT/26499_v7_successful_app_source.tar.gz"
BASE_MANIFEST="$ROOT/26499_v7_successful_after.sha256"
PATCH_26501="$ROOT/26501_proper_per_frame_spatial_rgb_runtime.patch"
V6_PATCH="$ROOT/26501_v6_glsl_portability_runtime_fix.patch"
PATCH_26502="$ROOT/26502_v1_stack_aware_chroma_highlight_runtime.patch"
SEED_26503="$ROOT/26503_v2_seed_safe_highlight_shadow_runtime.patch"
APPLY_26503="$ROOT/apply_26503_v2_integrated.py"
VALIDATOR_26501="$ROOT/validate_26501_proper_spatial_rgb.py"
VALIDATOR_26502="$ROOT/validate_26502_stack_aware_chroma_highlight.py"
VALIDATOR_26503="$ROOT/validate_26503_v2_integrated.py"
SEED_VALIDATOR="$ROOT/validate_26503_seed_math.py"
INTEGRITY="$ROOT/verify_26501_source_integrity.py"
BASE_TAR_SHA="ce5be58fa20b9e28786b9c6e4355743066fe92e78791b50b5ee2df568c5ae9e1"
BASE_MANIFEST_SHA="9af4b1cf5411b5cae445c3e2b782e07d824c3d4a2bcd16f3c7cf28ba79b5a74f"
PATCH_26501_SHA="49dfedc17f93c636f90140125ee127a2429f3afb3c365832d97bb74e40318386"
V6_PATCH_SHA="db574aec0e3b67504fddf64d2129cb7a2a782f27eba3271f730acb1fa05df0e6"
PATCH_26502_SHA="2725bb41bdc867b2f7dfbcb41f7373ca16e00e0eb75c4acefbc8d43fb478eb28"
SEED_26503_SHA="3337af3d4cab9a1f01688629b26e12a54c308ba4eb58bac8c9001655f5061ff1"
BASE_SHORT_SHA="9664e51a34427bd525a2000bdb01ade2be4f0e6754d388e8079eb04d57403b47"
BASE_DISPLAY_SHA="a68be9b3e4658fdfcab3a322a5c1b918863c27c581b468d2e29b16bea23a39f8"
BASE_RENDER_SHA="94373581342acd722a6778843a0d95f90d8aaefe7cba30d6b8b0800f74132bd7"
BASE_COLOR_SHA="4b14131a59e2358a9b8b18ded4c167f15cc0af5e0ab3d380768625017d7a81ac"
BASE_NORMALIZE_SHA="c3c5cfea45deba08415e4255dca934127edc878ca5fba73856ab8306a6cd958d"
BASE_CONTRIB_SHA="35fcbcce4138f29b4ee83703f6dc9f99452861917daca5e9dec6655c2de5174b"
PROMOTE_26503_SOURCE="${PROMOTE_26503_SOURCE:-false}"
rm -rf "$OUT" "$WORK"; mkdir -p "$OUT" "$BASE" "$CAND" "$PRE" "$AFTER"
exec > >(tee "$OUT/26503_v2_build.log") 2>&1

cat <<'EOF'
=== 26503 V2 CANONICAL SCENE-FAITHFUL A-G BUILD ===
Rule: latest on-device-tested build is canonical app/src/main.
This run canonicalizes tested 26502 V4 once, then builds 26503 directly from it.
No new backup branch is created, fetched, or required.
26503 source is NOT promoted unless a later explicit manual run sets promote_26503_source=true.
EOF

BRANCH="$(git branch --show-current)"; START_HEAD="$(git rev-parse HEAD)"
[[ "$BRANCH" == "$EXPECTED_BRANCH" ]] || fail "branch=$BRANCH expected=$EXPECTED_BRANCH"
[[ "$BRANCH" != "dev" ]] || fail "refusing dev"
git merge-base --is-ancestor "$BASELINE_26502_HEAD" HEAD || fail "tested 26502 V4 baseline is not ancestor"
git merge-base --is-ancestor "$V7_SHA" HEAD || fail "26499/V7 lineage missing"
git merge-base --is-ancestor "$V6_HEAD" HEAD || fail "26501/V6 lineage missing"
git diff --name-only "$BASELINE_26502_HEAD"..HEAD -- app/src/main app/version.properties > "$OUT/runtime_diff_before_canonicalization.txt"
for f in "$BASE_TAR" "$BASE_MANIFEST" "$PATCH_26501" "$V6_PATCH" "$PATCH_26502" "$SEED_26503" "$APPLY_26503" "$VALIDATOR_26501" "$VALIDATOR_26502" "$VALIDATOR_26503" "$SEED_VALIDATOR" "$INTEGRITY"; do [[ -f "$f" ]] || fail "missing dependency $(basename "$f")"; done
[[ "$(sha "$BASE_TAR")" == "$BASE_TAR_SHA" ]] || fail "26499 source archive hash mismatch"
[[ "$(sha "$BASE_MANIFEST")" == "$BASE_MANIFEST_SHA" ]] || fail "26499 source manifest hash mismatch"
[[ "$(sha "$PATCH_26501")" == "$PATCH_26501_SHA" ]] || fail "26501 patch hash mismatch"
[[ "$(sha "$V6_PATCH")" == "$V6_PATCH_SHA" ]] || fail "V6 patch hash mismatch"
[[ "$(sha "$PATCH_26502")" == "$PATCH_26502_SHA" ]] || fail "26502 patch hash mismatch"
[[ "$(sha "$SEED_26503")" == "$SEED_26503_SHA" ]] || fail "26503 seed patch hash mismatch"
pass "GATE 1 exact lineage/handoff; dev excluded; no backup branch"

echo "=== GATE 2: ONE-TIME RECONSTRUCTION OF EXACT TESTED 26502 ==="
tar -xzf "$BASE_TAR" -C "$BASE"
( cd "$BASE" && sha256sum -c "$BASE_MANIFEST" ) > "$OUT/26499_manifest_check.txt"
[[ "$(wc -l < "$BASE_MANIFEST")" -eq 865 ]] || fail "26499 manifest count mismatch"
cp -a "$BASE/app" "$CAND/app"
assert_no_artifacts(){ local d="$1"; local x; x="$(find "$d/app" -type f \( -name '*.orig' -o -name '*.rej' \) -print)"; [[ -z "$x" ]] || { printf '%s\n' "$x" >&2; fail "patch artifacts survived"; }; }
apply_patch(){ local name="$1" p="$2"; patch --dry-run --batch --forward --fuzz=0 --no-backup-if-mismatch -p1 -d "$CAND" < "$p" > "$OUT/${name}_dry.txt"; patch --batch --forward --fuzz=0 --no-backup-if-mismatch -p1 -d "$CAND" < "$p" > "$OUT/${name}_apply.txt"; assert_no_artifacts "$CAND"; }
apply_patch 26501 "$PATCH_26501"
cp "$CAND/app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_contribute_26501.glsl" "$OUT/contribute_pre_v6.glsl"
apply_patch 26501_v6 "$V6_PATCH"
python3 - "$OUT/contribute_pre_v6.glsl" "$CAND/app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_contribute_26501.glsl" <<'PY'
from pathlib import Path
import sys
b=Path(sys.argv[1]).read_text(); a=Path(sys.argv[2]).read_text(); r=a.replace('ownedPixel','sample').replace('precisionMatrix','precision').replace('packedCoord','packed')
assert r==b,'V6 changed more than reserved GLSL identifiers'; print('PASS: V6 portability remains identifier-only')
PY
python3 "$VALIDATOR_26501" "$CAND" --base "$BASE" | tee "$OUT/26501_validator.txt"
apply_patch 26502 "$PATCH_26502"
python3 "$VALIDATOR_26502" "$CAND" --patch "$PATCH_26502" | tee "$OUT/26502_validator.txt"
# APK-proven runtime assets from the actually tested 26502 file.
[[ "$(sha "$CAND/app/src/main/assets/shaders/motionv2/short_highlight_bayer_recover.glsl")" == "$BASE_SHORT_SHA" ]] || fail "26502 Short source != tested APK"
[[ "$(sha "$CAND/app/src/main/assets/shaders/motionv2/display_exposure.glsl")" == "$BASE_DISPLAY_SHA" ]] || fail "26502 display source != tested APK"
[[ "$(sha "$CAND/app/src/main/assets/shaders/motionv2/render.glsl")" == "$BASE_RENDER_SHA" ]] || fail "26502 render source != tested APK"
[[ "$(sha "$CAND/app/src/main/assets/shaders/motionv2/color_transform.glsl")" == "$BASE_COLOR_SHA" ]] || fail "26502 color source != tested APK"
[[ "$(sha "$CAND/app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_normalize_26501.glsl")" == "$BASE_NORMALIZE_SHA" ]] || fail "26502 normalizer source != tested APK"
[[ "$(sha "$CAND/app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_contribute_26501.glsl")" == "$BASE_CONTRIB_SHA" ]] || fail "26502 contributor source != tested APK"
python3 - "$CAND/app/version.properties" <<'PY'
from pathlib import Path
import re,sys
p=Path(sys.argv[1]); s=p.read_text(); s=re.sub(r'^VERSION_NAME=.*$','VERSION_NAME=0.9726502',s,flags=re.M); s=re.sub(r'^VERSION_BUILD=.*$','VERSION_BUILD=26502',s,flags=re.M); p.write_text(s)
PY
cp -a "$CAND/app/." "$PRE/app/"
python3 - "$PRE/app" "$OUT/26502_exact_runtime_snapshot.json" <<'PY'
from pathlib import Path
import hashlib,json,sys
r=Path(sys.argv[1]); d={p.relative_to(r).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in r.rglob('*') if p.is_file()}; assert len(d)==869,len(d); Path(sys.argv[2]).write_text(json.dumps(d,sort_keys=True,indent=2)); print('PASS: exact tested 26502 frozen: 869 files including version')
PY
# Required pre-change rollback/audit patch exists BEFORE any 26503 transform.
set +e; git diff --no-index --binary "$BASE/app" "$PRE/app" > "$OUT/26503_V2_PRECHANGE_EXACT_TESTED_26502.patch"; rc=$?; set -e
[[ "$rc" -eq 1 && -s "$OUT/26503_V2_PRECHANGE_EXACT_TESTED_26502.patch" ]] || fail "pre-change 26502 patch creation failed"
sha256sum "$OUT/26503_V2_PRECHANGE_EXACT_TESTED_26502.patch" > "$OUT/26503_V2_PRECHANGE_EXACT_TESTED_26502.patch.sha256"
pass "GATE 2 exact tested 26502 reconstructed; pre-change patch emitted before 26503 modification"

echo "=== GATE 3: CANONICALIZE TESTED 26502 INTO app/src/main ==="
root_matches_26502(){ python3 - "$PRE" "$ROOT" <<'PY'
from pathlib import Path
import hashlib,sys

def collect(root):
 root=Path(root); out={}
 for p in (root/'app/src/main').rglob('*'):
  if p.is_file(): out[p.relative_to(root/'app').as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
 p=root/'app/version.properties'
 if p.is_file(): out[p.relative_to(root/'app').as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
 return out
raise SystemExit(0 if collect(sys.argv[1])==collect(sys.argv[2]) else 1)
PY
}
if root_matches_26502; then
  pass "repository app/src/main is already exact canonical tested 26502"
else
  [[ ! -s "$OUT/runtime_diff_before_canonicalization.txt" ]] || { cat "$OUT/runtime_diff_before_canonicalization.txt" >&2; fail "runtime drift exists and is not exact canonical 26502; refusing overwrite"; }
  [[ -f app/build.gradle ]] || fail "app module shell missing"
  find app -maxdepth 1 -type f ! -name version.properties -print0 | sort -z | xargs -0 sha256sum > "$OUT/app_shell_before.sha256"
  rm -rf app/src/main; cp -a "$PRE/app/src/main" app/src/main; cp "$PRE/app/version.properties" app/version.properties
  find app -maxdepth 1 -type f ! -name version.properties -print0 | sort -z | xargs -0 sha256sum > "$OUT/app_shell_after.sha256"
  diff -u "$OUT/app_shell_before.sha256" "$OUT/app_shell_after.sha256" >/dev/null || fail "Android module shell changed during canonicalization"
  root_matches_26502 || fail "canonicalized root does not equal exact tested 26502"
  git config user.name "Photon 26503 Guarded Build"
  git config user.email "actions@users.noreply.github.com"
  git add app/src/main app/version.properties
  git commit -m "Canonicalize tested 26502 V4 runtime source [skip ci]"
  CANONICAL_HEAD="$(git rev-parse HEAD)"
  git fetch origin "$EXPECTED_BRANCH"
  [[ "$(git rev-parse origin/$EXPECTED_BRANCH)" == "$START_HEAD" ]] || fail "remote branch moved during 26502 canonicalization; refusing push"
  git push origin "HEAD:$EXPECTED_BRANCH"
  pass "tested 26502 is now canonical app/src/main on experimental branch: $CANONICAL_HEAD"
fi
CANONICAL_HEAD="$(git rev-parse HEAD)"

echo "=== GATE 4: BUILD 26503 DIRECTLY FROM CANONICAL 26502 ==="
cp -a "$PRE/app/." "$AFTER/app/"
# Reuse the already-audited conservative C/D seed against exact 26502, then deterministic A/B/E/speed transforms; tested-26502 EXIF remains frozen.
patch --dry-run --batch --forward --fuzz=0 --no-backup-if-mismatch -p1 -d "$AFTER" < "$SEED_26503" > "$OUT/26503_seed_dry.txt"
patch --batch --forward --fuzz=0 --no-backup-if-mismatch -p1 -d "$AFTER" < "$SEED_26503" > "$OUT/26503_seed_apply.txt"
assert_no_artifacts "$AFTER"
python3 "$APPLY_26503" "$AFTER" | tee "$OUT/26503_apply_transform.txt"
assert_no_artifacts "$AFTER"
# Exact direct delta patch from latest tested canonical base.
set +e; git diff --no-index --binary "$PRE/app" "$AFTER/app" > "$OUT/26503_V2_EXACT_RUNTIME_DELTA_FROM_26502.patch"; rc=$?; set -e
[[ "$rc" -eq 1 && -s "$OUT/26503_V2_EXACT_RUNTIME_DELTA_FROM_26502.patch" ]] || fail "26503 exact delta patch generation failed"
sha256sum "$OUT/26503_V2_EXACT_RUNTIME_DELTA_FROM_26502.patch" > "$OUT/26503_V2_EXACT_RUNTIME_DELTA_FROM_26502.patch.sha256"
python3 "$VALIDATOR_26503" "$AFTER" --base-root "$PRE" --seed-validator "$SEED_VALIDATOR" | tee "$OUT/26503_v2_validator.txt"
pass "GATE 4 26503 is a direct exact seven-file delta from canonical tested 26502"

echo "=== GATE 5: REAL GLSL / JAVA / OWNER PREFLIGHT ==="
command -v glslangValidator >/dev/null 2>&1 || fail "glslangValidator missing"
glslangValidator --version | head -1 | grep -F '16.5.0' >/dev/null || fail "glslangValidator is not pinned 16.5.0"
python3 - "$AFTER" "$OUT" <<'PY'
from pathlib import Path
import re,subprocess,sys
root=Path(sys.argv[1]); out=Path(sys.argv[2]); items=[
('app/src/main/assets/shaders/motionv2/short_highlight_bayer_recover.glsl','comp'),('app/src/main/assets/shaders/motionv2/display_exposure.glsl','frag'),('app/src/main/assets/shaders/motionv2/render.glsl','frag'),('app/src/main/assets/shaders/motionv2/color_transform.glsl','frag'),('app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_chroma_guide_26501.glsl','frag'),('app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_contribute_26501.glsl','frag'),('app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_normalize_26501.glsl','frag'),('app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_short_weight_26501.glsl','comp'),('app/src/main/assets/shaders/motionv2/shadow_aux_bayer_fuse.glsl','comp'),('app/src/main/assets/shaders/motionv2/mfsr_mgc_covariance.glsl','comp')]
reserved={'sample','precision','packed','common','partition','active','asm','class','union','enum','typedef','template','this','resource','goto','inline','noinline','public','static','extern','external','interface','long','short','half','fixed','unsigned','superp','input','output','hvec2','hvec3','hvec4','fvec2','fvec3','fvec4','sampler3DRect','filter','sizeof','cast','namespace','using','row_major'}
type_re=r'(?:bool|int|uint|float|double|vec[234]|ivec[234]|uvec[234]|bvec[234]|dvec[234]|mat[234](?:x[234])?|dmat[234](?:x[234])?|[iu]?sampler\w+|[iu]?image\w+)'; logs=[]
for i,(rel,stage) in enumerate(items):
 src=(root/rel).read_text(); clean=re.sub(r'/\*.*?\*/',' ',src,flags=re.S); clean=re.sub(r'//.*',' ',clean); hits=[]
 for m in re.finditer(r'\b'+type_re+r'\s+([A-Za-z_]\w*)',clean):
  if m.group(1) in reserved:hits.append((clean.count('\n',0,m.start())+1,m.group(1)))
 if hits:raise SystemExit(f'{rel}: reserved GLSL identifier {hits}')
 cs=src
 if stage=='comp':
  if not cs.startswith('#define LAYOUT //'):raise SystemExit(rel+' missing Photon LAYOUT')
  cs=cs.replace('#define LAYOUT //','#define LAYOUT layout(local_size_x=8, local_size_y=8, local_size_z=1) in;',1)
 tmp=out/f'glsl_{i}.{stage}'; tmp.write_text('#version 310 es\n'+cs); cp=subprocess.run(['glslangValidator','-S',stage,str(tmp)],capture_output=True,text=True); logs.append(rel+' rc='+str(cp.returncode)+'\n'+cp.stdout+cp.stderr)
 if cp.returncode: (out/'26503_glsl.log').write_text('\n'.join(logs)); raise SystemExit('GLSL compile failed '+rel)
(out/'26503_glsl.log').write_text('\n'.join(logs)); print('PASS: ten active/changed shaders compile with Khronos glslang 16.5.0')
PY
mkdir -p "$WORK/javac_parse"
javac -proc:none -Xmaxerrs 10000 -d "$WORK/javac_parse" \
 "$AFTER/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2Merger.java" \
 "$AFTER/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java" \
 "$AFTER/app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java" > "$OUT/26503_javac_parse.log" 2>&1 || true
python3 - "$OUT/26503_javac_parse.log" <<'PY'
from pathlib import Path
import sys
s=Path(sys.argv[1]).read_text(errors='replace'); pats=['; expected','illegal start of','reached end of file while parsing',"')' expected","'}' expected",'not a statement','class, interface, enum, or record expected','unclosed']; bad=[x for x in s.splitlines() if any(p in x for p in pats)]; assert not bad,bad[:30]; print('PASS: changed Java owners contain no syntax/parse diagnostics')
PY
[[ "$(grep '^VERSION_NAME=' "$AFTER/app/version.properties" | cut -d= -f2)" == "0.9726502" ]] || fail "version changed before safety proof"
[[ "$(grep '^VERSION_BUILD=' "$AFTER/app/version.properties" | cut -d= -f2)" == "26502" ]] || fail "build changed before safety proof"
echo "PRE-BUILD SAFETY PROOF PASSED"
echo "  A frozen capture scene-key single display exposure authority PASS"
echo "  B evidence-based true-floor shadow recovery PASS"
echo "  C extended-range hue-preserving highlight/gamut PASS"
echo "  D boundary-anchored Short-A observability PASS"
echo "  E pixel-local effective-stack shadow permission PASS"
echo "  F border-bar proof gate/no band-aid PASS"
echo "  G exact 26502 architecture firewall PASS"
echo "  Speed diagnostic-only GPU readback disable PASS"
echo "  EXIF tested-26502 Photon ISO100 normalization FROZEN PASS"

echo "=== GATE 6: VERSION 0.9726503 / 26503 + BUILD IN SAME GUARDED BLOCK ==="
python3 - "$AFTER/app/version.properties" <<'PY'
from pathlib import Path
import re,sys
p=Path(sys.argv[1]); s=p.read_text(); s=re.sub(r'^VERSION_NAME=.*$','VERSION_NAME=0.9726503',s,flags=re.M); s=re.sub(r'^VERSION_BUILD=.*$','VERSION_BUILD=26503',s,flags=re.M); p.write_text(s)
PY
find app -maxdepth 1 -type f ! -name version.properties -print0 | sort -z | xargs -0 sha256sum > "$OUT/app_shell_pre_26503_overlay.sha256"
rm -rf app/src/main; cp -a "$AFTER/app/src/main" app/src/main; cp "$AFTER/app/version.properties" app/version.properties
find app -maxdepth 1 -type f ! -name version.properties -print0 | sort -z | xargs -0 sha256sum > "$OUT/app_shell_post_26503_overlay.sha256"
diff -u "$OUT/app_shell_pre_26503_overlay.sha256" "$OUT/app_shell_post_26503_overlay.sha256" >/dev/null || fail "module shell changed"
python3 "$INTEGRITY" snapshot "$ROOT/app" "$OUT/26503_pre_gradle_manifest.json"
chmod +x ./gradlew
./gradlew clean :app:assembleDebug --stacktrace
python3 "$INTEGRITY" verify "$ROOT/app" "$OUT/26503_pre_gradle_manifest.json" | tee "$OUT/26503_post_gradle_integrity.txt"
mapfile -t APKS < <(find app/build -type f -name '*.apk' | sort); [[ "${#APKS[@]}" -eq 1 ]] || fail "expected exactly one APK, found ${#APKS[@]}"
[[ "$(basename "${APKS[0]}")" == "IrisCamera-0.9726503-26503-debug.apk" ]] || fail "unexpected APK identity $(basename "${APKS[0]}")"
FINAL="$ROOT/IrisCamera-0.9726503-26503-canonical-scene-faithful-debug.apk"; rm -f "$ROOT"/*.apk; cp "${APKS[0]}" "$FINAL"; sha256sum "$FINAL" > "$OUT/26503_apk.sha256"
python3 - "$FINAL" "$AFTER" <<'PY'
from pathlib import Path
from zipfile import ZipFile
import hashlib,sys
apk=Path(sys.argv[1]); root=Path(sys.argv[2]); assets=['short_highlight_bayer_recover.glsl','display_exposure.glsl','render.glsl','color_transform.glsl','mfsr_spatial_rgb_normalize_26501.glsl','mfsr_spatial_rgb_contribute_26501.glsl']
h=lambda b:hashlib.sha256(b).hexdigest()
with ZipFile(apk) as z:
 for n in assets:
  p='assets/shaders/motionv2/'+n; want=h((root/'app/src/main/assets/shaders/motionv2'/n).read_bytes()); got=h(z.read(p)); assert got==want,(n,got,want)
 dex=b''.join(z.read(n) for n in z.namelist() if n.startswith('classes') and n.endswith('.dex'))
 for m in [b'IRIS_26503_FROZEN_CAPTURE_SCENE_KEY_GAIN',b'IRIS_26503_SINGLE_EXPOSURE_SHADOW_AUTHORITY',b'IRIS_26503_DISABLE_HEAVY_PROVENANCE_READBACK']:
  assert m in dex,m
print('PASS: APK/source shader parity + required 26503 Java markers in DEX')
PY
pass "GATE 6 exactly one 26503 APK built from direct canonical-26502 delta"

echo "=== GATE 7: SUCCESSFUL SOURCE CHECKPOINT / OPTIONAL POST-TEST PROMOTION ==="
( cd "$AFTER" && tar --sort=name --mtime='UTC 2026-08-18 00:00:00' --owner=0 --group=0 --numeric-owner -czf "$OUT/26503_successful_app_source.tar.gz" app/src/main app/version.properties )
( cd "$AFTER" && { find app/src/main -type f -print; echo app/version.properties; } | LC_ALL=C sort | while read -r f; do sha256sum "$f"; done ) > "$OUT/26503_successful_after.sha256"
[[ "$(wc -l < "$OUT/26503_successful_after.sha256")" -eq 869 ]] || fail "26503 source manifest count mismatch"
cat > "$OUT/26503_build_report.txt" <<EOF
26503 V2 Canonical Scene-Faithful Motion
Canonical direct base: tested 26502 V4
Canonical 26502 commit: $CANONICAL_HEAD
Version/build: 0.9726503 / 26503
APK: $(basename "$FINAL")
APK SHA256: $(sha "$FINAL")
NewBackupBranch=false
A=Frozen selected-reference CaptureResult scene key replaces fixed darkness-is-error display targets; low-EV darkness stays dark; high-EV shadow-dominated HDR gets global over-lift protection; no live AE feedback.
B=True floor + scalar local shadow recovery only.
C=Camera2 matrix frozen; render white painting removed; hue-preserving extended-range gamut fit.
D=Strict 26502 Tier1 Short-A first; boundary Tier2 only when Tier1 unobservable.
E=True local frame-equivalent support carried in RGB alpha to the one display node; weak local stack gets less shadow lift.
F=No border mask/desaturation; semantic support-count proof did not authorize reconstruction band-aid.
G=Exact seven-file delta from tested 26502; all other runtime bytes frozen, including ParseExif.java.
Speed=Diagnostic-only full direct-RGB support and heavy per-phase provenance GPU readbacks disabled; real effective-support readback retained.
EXIF=Tested-26502 Photon ISO100-normalized convention preserved byte-for-byte; getMPY remains unchanged.
Promote26503Requested=$PROMOTE_26503_SOURCE
EOF
if [[ "$PROMOTE_26503_SOURCE" == "true" ]]; then
  # This path is intentionally for a SECOND manual run only after the user has tested/accepted 26503.
  git add app/src/main app/version.properties
  git commit -m "26503 V2: canonical scene-faithful Motion recovery [skip ci]"
  PROMOTE_HEAD="$(git rev-parse HEAD)"
  git fetch origin "$EXPECTED_BRANCH"
  [[ "$(git rev-parse origin/$EXPECTED_BRANCH)" == "$CANONICAL_HEAD" ]] || fail "remote moved since canonical 26502; refusing 26503 promotion"
  git push origin "HEAD:$EXPECTED_BRANCH"
  echo "PASS: accepted 26503 source promoted to canonical app/src/main: $PROMOTE_HEAD"
else
  echo "PASS: 26503 source intentionally NOT promoted before on-device acceptance; tested 26502 remains canonical"
fi
pass "clean 869-file 26503 successful-source checkpoint emitted"
echo "PASS: 26503 V2 CANONICAL A-G BUILD COMPLETE: $FINAL"
