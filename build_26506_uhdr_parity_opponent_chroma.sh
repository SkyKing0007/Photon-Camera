#!/usr/bin/env bash
set -euo pipefail
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }

ROOT="$(pwd)"
OUT="$ROOT/build_26506_uhdr_parity_opponent_chroma_outputs"
WORK="$ROOT/.build_26506_uhdr_parity_opponent_chroma_work"
PRE="$WORK/canonical26502"
BEFORE="$WORK/tested26505"
AFTER="$WORK/candidate26506"

EXPECTED_BRANCH="experimental-clean-photon-rebuild"
CANONICAL_26502_HEAD="6118984523296945a0910e55ddaa4d3126184059"
HANDOFF_26505_HEAD="782bcee12188399d877080d4e4f2c1f14e252d97"
BACKUP_BRANCH="backup-26505-tested-before-26506-20260818"

SEED_26503="$ROOT/26503_v2_seed_safe_highlight_shadow_runtime.patch"
APPLY_26504="$ROOT/apply_26504_integrated.py"
VALIDATOR_26504="$ROOT/validate_26504_integrated.py"
APPLY_26505="$ROOT/apply_26505_bjzhou_consistency.py"
VALIDATOR_26505="$ROOT/validate_26505_bjzhou_consistency.py"
APPLY_26506="$ROOT/apply_26506_uhdr_parity_opponent_chroma.py"
VALIDATOR_26506="$ROOT/validate_26506_uhdr_parity_opponent_chroma.py"
INTEGRITY="$ROOT/verify_26501_source_integrity.py"

SEED_26503_SHA="c5d4e13e6f8a59243eedac8c2beab9d737444a231f21411bf7dec1636dca5a1e"
APPLY_26504_SHA="96f44374c564231abf13e219362add26c4a3ff1be1e1bbd793b3cd4af3ef6348"
VALIDATOR_26504_SHA="c071526c04b36a5c8d19525c1485b01c5eea4befe89abc7443b24fef4f4d28f3"
APPLY_26505_SHA="2a718c5972ab4a8f518c3f25d769e9ac37e87050989e85dcb1f747272e6bd9bf"
VALIDATOR_26505_SHA="703df94241c2a4effcf088eb757809dbc9da141b0c295a46aaf40e93ec8a0345"
BASE_SHORT_SHA="9664e51a34427bd525a2000bdb01ade2be4f0e6754d388e8079eb04d57403b47"
BASE_DISPLAY_SHA="a68be9b3e4658fdfcab3a322a5c1b918863c27c581b468d2e29b16bea23a39f8"
BASE_RENDER_SHA="94373581342acd722a6778843a0d95f90d8aaefe7cba30d6b8b0800f74132bd7"
BASE_COLOR_SHA="4b14131a59e2358a9b8b18ded4c167f15cc0af5e0ab3d380768625017d7a81ac"
BASE_NORMALIZE_SHA="c3c5cfea45deba08415e4255dca934127edc878ca5fba73856ab8306a6cd958d"
BASE_CONTRIB_SHA="35fcbcce4138f29b4ee83703f6dc9f99452861917daca5e9dec6655c2de5174b"

rm -rf "$OUT" "$WORK"
mkdir -p "$OUT" "$PRE" "$BEFORE" "$AFTER"
exec > >(tee "$OUT/26506_build.log") 2>&1

BRANCH="$(git branch --show-current)"
START_HEAD="$(git rev-parse HEAD)"
[[ "$BRANCH" == "$EXPECTED_BRANCH" ]] || fail "branch=$BRANCH expected=$EXPECTED_BRANCH"
[[ "$BRANCH" != "dev" ]] || fail "refusing dev"
git merge-base --is-ancestor "$HANDOFF_26505_HEAD" HEAD || fail "tested 26505 handoff is not an ancestor"
git merge-base --is-ancestor "$CANONICAL_26502_HEAD" HEAD || fail "canonical 26502 missing"

RUNTIME_DRIFT="$OUT/runtime_diff_from_canonical_26502.txt"
git diff --name-only "$CANONICAL_26502_HEAD"..HEAD -- app/src/main app/version.properties > "$RUNTIME_DRIFT"
[[ ! -s "$RUNTIME_DRIFT" ]] || { cat "$RUNTIME_DRIFT" >&2; fail "runtime drift exists after canonical 26502"; }

REMOTE_BACKUP="$(git ls-remote origin "refs/heads/$BACKUP_BRANCH" | awk '{print $1}')"
[[ "$REMOTE_BACKUP" == "$HANDOFF_26505_HEAD" ]] || fail "required backup missing/wrong: $BACKUP_BRANCH -> ${REMOTE_BACKUP:-MISSING}"

for f in "$SEED_26503" "$APPLY_26504" "$VALIDATOR_26504" "$APPLY_26505" "$VALIDATOR_26505" "$APPLY_26506" "$VALIDATOR_26506" "$INTEGRITY"; do
  [[ -f "$f" ]] || fail "missing dependency $(basename "$f")"
done
[[ "$(sha "$SEED_26503")" == "$SEED_26503_SHA" ]] || fail "26503 seed patch hash mismatch"
[[ "$(sha "$APPLY_26504")" == "$APPLY_26504_SHA" ]] || fail "26504 apply hash mismatch"
[[ "$(sha "$VALIDATOR_26504")" == "$VALIDATOR_26504_SHA" ]] || fail "26504 validator hash mismatch"
[[ "$(sha "$APPLY_26505")" == "$APPLY_26505_SHA" ]] || fail "26505 apply hash mismatch"
[[ "$(sha "$VALIDATOR_26505")" == "$VALIDATOR_26505_SHA" ]] || fail "26505 validator hash mismatch"
pass "GATE 1 branch/lineage/runtime + exact tested-26505 backup verified"

echo "=== GATE 2: RECONSTRUCT AND FREEZE TESTED 26505 BEFORE 26506 MODIFICATION ==="
git archive "$CANONICAL_26502_HEAD" app/src/main app/version.properties | tar -x -C "$PRE"
python3 - "$PRE" "$ROOT" "$OUT/26502_canonical_runtime_snapshot.json" <<'PYBASE'
from pathlib import Path
import hashlib,json,sys
pre=Path(sys.argv[1]); root=Path(sys.argv[2]); out=Path(sys.argv[3])
def collect(base):
    app=base/'app'; d={}
    for p in (app/'src/main').rglob('*'):
        if p.is_file(): d[p.relative_to(app).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
    vp=app/'version.properties'; d[vp.relative_to(app).as_posix()]=hashlib.sha256(vp.read_bytes()).hexdigest()
    return d
p=collect(pre); r=collect(root)
assert p==r, 'working runtime is not byte-identical to canonical tested 26502'
assert len(p)==869, len(p)
out.write_text(json.dumps(p,sort_keys=True,indent=2))
print('PASS: canonical tested 26502 frozen directly: 869/869 files')
PYBASE

[[ "$(sha "$PRE/app/src/main/assets/shaders/motionv2/short_highlight_bayer_recover.glsl")" == "$BASE_SHORT_SHA" ]] || fail "Short-A hash mismatch"
[[ "$(sha "$PRE/app/src/main/assets/shaders/motionv2/display_exposure.glsl")" == "$BASE_DISPLAY_SHA" ]] || fail "display hash mismatch"
[[ "$(sha "$PRE/app/src/main/assets/shaders/motionv2/render.glsl")" == "$BASE_RENDER_SHA" ]] || fail "render hash mismatch"
[[ "$(sha "$PRE/app/src/main/assets/shaders/motionv2/color_transform.glsl")" == "$BASE_COLOR_SHA" ]] || fail "color hash mismatch"
[[ "$(sha "$PRE/app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_normalize_26501.glsl")" == "$BASE_NORMALIZE_SHA" ]] || fail "normalizer hash mismatch"
[[ "$(sha "$PRE/app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_contribute_26501.glsl")" == "$BASE_CONTRIB_SHA" ]] || fail "contributor hash mismatch"

cp -a "$PRE/app/." "$BEFORE/app/"
patch --dry-run --batch --forward --fuzz=0 --no-backup-if-mismatch -p1 -d "$BEFORE" < "$SEED_26503" > "$OUT/26503_seed_dry.txt"
patch --batch --forward --fuzz=0 --no-backup-if-mismatch -p1 -d "$BEFORE" < "$SEED_26503" > "$OUT/26503_seed_apply.txt"
python3 "$APPLY_26504" "$BEFORE" | tee "$OUT/26504_apply_transform.txt"
python3 "$VALIDATOR_26504" "$BEFORE" --base-root "$PRE" | tee "$OUT/26504_validator.txt"
python3 "$APPLY_26505" "$BEFORE" | tee "$OUT/26505_apply_transform.txt"
python3 "$VALIDATOR_26505" "$BEFORE" --base-root "$PRE" | tee "$OUT/26505_validator.txt"

set +e
git diff --no-index --binary "$PRE/app" "$BEFORE/app" > "$OUT/26506_PRECHANGE_TESTED_26505_RUNTIME.patch"
rc=$?
set -e
[[ "$rc" -eq 1 && -s "$OUT/26506_PRECHANGE_TESTED_26505_RUNTIME.patch" ]] || fail "tested 26505 prechange patch generation failed"
sha256sum "$OUT/26506_PRECHANGE_TESTED_26505_RUNTIME.patch" > "$OUT/26506_PRECHANGE_TESTED_26505_RUNTIME.patch.sha256"
( cd "$BEFORE" && tar --sort=name --mtime='UTC 2026-08-18 00:00:00' --owner=0 --group=0 --numeric-owner -czf "$OUT/26506_PRECHANGE_TESTED_26505_RUNTIME.tar.gz" app/src/main app/version.properties )
( cd "$BEFORE" && { find app/src/main -type f -print; echo app/version.properties; } | LC_ALL=C sort | while read -r f; do sha256sum "$f"; done ) > "$OUT/26506_prechange_tested_26505.sha256"
[[ "$(wc -l < "$OUT/26506_prechange_tested_26505.sha256")" -eq 870 ]] || fail "tested 26505 source manifest count mismatch"
pass "GATE 2 exact tested 26505 reconstructed; pre-change patch/archive frozen before 26506 modification"

echo "=== GATE 3: APPLY INTEGRATED 26506 PARITY + NORMAL/SHORT/LONG CHROMA COHERENCE ==="
cp -a "$BEFORE/app/." "$AFTER/app/"
python3 "$APPLY_26506" "$AFTER" | tee "$OUT/26506_apply_transform.txt"
python3 "$VALIDATOR_26506" "$AFTER" --base-root "$PRE" | tee "$OUT/26506_validator.txt"

python3 - "$BEFORE" "$AFTER" <<'PYDELTA'
from pathlib import Path
import hashlib,sys
before=Path(sys.argv[1]); after=Path(sys.argv[2])
def collect(root):
    out={}
    for p in (root/'app/src/main').rglob('*'):
        if p.is_file(): out[p.relative_to(root).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
    return out
b=collect(before); a=collect(after)
changed={k for k in set(a)|set(b) if a.get(k)!=b.get(k)}
expected={
'app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_normalize_26501.glsl',
'app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_short_weight_26501.glsl',
'app/src/main/assets/shaders/motionv2/shadow_aux_bayer_fuse.glsl',
'app/src/main/assets/shaders/motionv2/short_highlight_bayer_recover.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java',
}
assert changed==expected,(sorted(changed),sorted(expected))
print('PASS: 26506 modifies exactly six files relative to tested 26505')
PYDELTA

set +e
git diff --no-index --binary "$BEFORE/app" "$AFTER/app" > "$OUT/26506_EXACT_DELTA_FROM_TESTED_26505.patch"
rc=$?
set -e
[[ "$rc" -eq 1 && -s "$OUT/26506_EXACT_DELTA_FROM_TESTED_26505.patch" ]] || fail "26506 delta-from-26505 generation failed"
sha256sum "$OUT/26506_EXACT_DELTA_FROM_TESTED_26505.patch" > "$OUT/26506_EXACT_DELTA_FROM_TESTED_26505.patch.sha256"
set +e
git diff --no-index --binary "$PRE/app" "$AFTER/app" > "$OUT/26506_EXACT_RUNTIME_FROM_26502.patch"
rc=$?
set -e
[[ "$rc" -eq 1 && -s "$OUT/26506_EXACT_RUNTIME_FROM_26502.patch" ]] || fail "26506 runtime-from-26502 generation failed"
sha256sum "$OUT/26506_EXACT_RUNTIME_FROM_26502.patch" > "$OUT/26506_EXACT_RUNTIME_FROM_26502.patch.sha256"
pass "GATE 3 exact six-file 26506 delta + full runtime candidate produced"

echo "=== GATE 4: REAL GLSL / JAVA / OWNER PREFLIGHT ==="
command -v glslangValidator >/dev/null 2>&1 || fail "glslangValidator missing"
VERSION_OUTPUT="$(glslangValidator --version)"
VERSION_LINE="${VERSION_OUTPUT%%$'\n'*}"
grep -F '16.5.0' <<<"$VERSION_LINE" >/dev/null || fail "glslangValidator is not pinned 16.5.0"

python3 - "$AFTER" "$OUT" <<'PYGLSL'
from pathlib import Path
import re,subprocess,sys
root=Path(sys.argv[1]); out=Path(sys.argv[2])
items=[
('app/src/main/assets/shaders/motionv2/short_highlight_bayer_recover.glsl','comp'),
('app/src/main/assets/shaders/motionv2/display_exposure.glsl','frag'),
('app/src/main/assets/shaders/motionv2/low_support_ppg_reference_26505.glsl','frag'),
('app/src/main/assets/shaders/motionv2/render.glsl','frag'),
('app/src/main/assets/shaders/motionv2/gainmap.glsl','frag'),
('app/src/main/assets/shaders/motionv2/color_transform.glsl','frag'),
('app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_chroma_guide_26501.glsl','frag'),
('app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_contribute_26501.glsl','frag'),
('app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_normalize_26501.glsl','frag'),
('app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_short_weight_26501.glsl','comp'),
('app/src/main/assets/shaders/motionv2/shadow_aux_bayer_fuse.glsl','comp'),
('app/src/main/assets/shaders/motionv2/mfsr_mgc_covariance.glsl','comp')]
reserved={'sample','precision','packed','common','partition','active','asm','class','union','enum','typedef','template','this','resource','goto','inline','noinline','public','static','extern','external','interface','long','short','half','fixed','unsigned','superp','input','output','hvec2','hvec3','hvec4','fvec2','fvec3','fvec4','sampler3DRect','filter','sizeof','cast','namespace','using','row_major'}
type_re=r'(?:bool|int|uint|float|double|vec[234]|ivec[234]|uvec[234]|bvec[234]|dvec[234]|mat[234](?:x[234])?|dmat[234](?:x[234])?|[iu]?sampler\w+|[iu]?image\w+)'
logs=[]
for i,(rel,stage) in enumerate(items):
    src=(root/rel).read_text()
    clean=re.sub(r'/\*.*?\*/',' ',src,flags=re.S); clean=re.sub(r'//.*',' ',clean)
    hits=[]
    for m in re.finditer(r'\b'+type_re+r'\s+([A-Za-z_]\w*)',clean):
        if m.group(1) in reserved: hits.append((clean.count('\n',0,m.start())+1,m.group(1)))
    if hits: raise SystemExit(f'{rel}: reserved GLSL identifier {hits}')
    cs=src
    if stage=='comp':
        if not cs.startswith('#define LAYOUT //'): raise SystemExit(rel+' missing Photon LAYOUT')
        cs=cs.replace('#define LAYOUT //','#define LAYOUT layout(local_size_x=8, local_size_y=8, local_size_z=1) in;',1)
    tmp=out/f'glsl_{i}.{stage}'; tmp.write_text('#version 310 es\n'+cs)
    cp=subprocess.run(['glslangValidator','-S',stage,str(tmp)],capture_output=True,text=True)
    logs.append(rel+' rc='+str(cp.returncode)+'\n'+cp.stdout+cp.stderr)
    if cp.returncode:
        (out/'26506_glsl.log').write_text('\n'.join(logs)); raise SystemExit('GLSL compile failed '+rel)
(out/'26506_glsl.log').write_text('\n'.join(logs))
print('PASS: twelve active/changed HDR/CFA shaders compile with Khronos glslang 16.5.0')
PYGLSL

mkdir -p "$WORK/javac_parse"
javac -proc:none -Xmaxerrs 10000 -d "$WORK/javac_parse" \
 "$AFTER/app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java" \
 "$AFTER/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2Merger.java" \
 "$AFTER/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java" \
 "$AFTER/app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java" \
 "$AFTER/app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java" \
 > "$OUT/26506_javac_parse.log" 2>&1 || true
python3 - "$OUT/26506_javac_parse.log" <<'PYJAVA'
from pathlib import Path
import sys
s=Path(sys.argv[1]).read_text(errors='replace')
pats=['; expected','illegal start of','reached end of file while parsing',"')' expected","'}' expected",'not a statement','class, interface, enum, or record expected','unclosed']
bad=[x for x in s.splitlines() if any(p in x for p in pats)]
assert not bad,bad[:30]
print('PASS: changed Java owners contain no syntax/parse diagnostics')
PYJAVA

[[ "$(grep '^VERSION_NAME=' "$AFTER/app/version.properties" | cut -d= -f2)" == "0.9726502" ]] || fail "version changed before safety proof"
[[ "$(grep '^VERSION_BUILD=' "$AFTER/app/version.properties" | cut -d= -f2)" == "26502" ]] || fail "build changed before safety proof"

echo "PRE-BUILD SAFETY PROOF PASSED"
echo "  exact tested-26505 backup + reconstructed prechange patch/archive PASS"
echo "  exact six-file 26506 delta / twelve-file full runtime allowlist PASS"
echo "  Wronski normal stack and 15-frame accumulator unchanged PASS"
echo "  Short-A + intentional +2.5 EV Long-A capture/metadata ownership unchanged PASS"
echo "  tested SDR primary 0.80 preserved; independent UHDR target 1.00 (+0.322 EV nominal body recovery) PASS"
echo "  full-resolution gain map now encodes HDR/SDR rendition separation; highlight shoulder unchanged PASS"
echo "  moderate-support fallback changes R-G/B-G chroma only; temporal green detail preserved PASS"
echo "  brightness alone cannot override physically validated Short-A color PASS"
echo "  26504 coherent clipping / EXIF / no-heavy-readback invariants PASS"

echo "=== GATE 5: VERSION 0.9726506 / 26506 + BUILD IN SAME GUARDED BLOCK ==="
python3 - "$AFTER/app/version.properties" <<'PYVER'
from pathlib import Path
import re,sys
p=Path(sys.argv[1]); s=p.read_text()
s=re.sub(r'^VERSION_NAME=.*$','VERSION_NAME=0.9726506',s,flags=re.M)
s=re.sub(r'^VERSION_BUILD=.*$','VERSION_BUILD=26506',s,flags=re.M)
p.write_text(s)
PYVER

find app -maxdepth 1 -type f ! -name version.properties -print0 | sort -z | xargs -0 sha256sum > "$OUT/app_shell_pre_26506_overlay.sha256"
rm -rf app/src/main
cp -a "$AFTER/app/src/main" app/src/main
cp "$AFTER/app/version.properties" app/version.properties
find app -maxdepth 1 -type f ! -name version.properties -print0 | sort -z | xargs -0 sha256sum > "$OUT/app_shell_post_26506_overlay.sha256"
diff -u "$OUT/app_shell_pre_26506_overlay.sha256" "$OUT/app_shell_post_26506_overlay.sha256" >/dev/null || fail "module shell changed"

python3 "$INTEGRITY" snapshot "$ROOT/app" "$OUT/26506_pre_gradle_manifest.json"
chmod +x ./gradlew
./gradlew clean :app:assembleDebug --stacktrace
python3 "$INTEGRITY" verify "$ROOT/app" "$OUT/26506_pre_gradle_manifest.json" | tee "$OUT/26506_post_gradle_integrity.txt"

mapfile -t APKS < <(find app/build -type f -name '*.apk' | sort)
[[ "${#APKS[@]}" -eq 1 ]] || fail "expected exactly one APK, found ${#APKS[@]}"
[[ "$(basename "${APKS[0]}")" == "IrisCamera-0.9726506-26506-debug.apk" ]] || fail "unexpected APK identity $(basename "${APKS[0]}")"

FINAL="$ROOT/IrisCamera-0.9726506-26506-integrated-hdr-chroma-consistency-debug.apk"
rm -f "$ROOT"/*.apk
cp "${APKS[0]}" "$FINAL"
sha256sum "$FINAL" > "$OUT/26506_apk.sha256"

python3 - "$FINAL" "$AFTER" <<'PYAPK'
from pathlib import Path
from zipfile import ZipFile
import hashlib,sys
apk=Path(sys.argv[1]); root=Path(sys.argv[2]); h=lambda b:hashlib.sha256(b).hexdigest()
assets=['short_highlight_bayer_recover.glsl','display_exposure.glsl','render.glsl','gainmap.glsl','color_transform.glsl','mfsr_spatial_rgb_normalize_26501.glsl','mfsr_spatial_rgb_contribute_26501.glsl','mfsr_spatial_rgb_short_weight_26501.glsl','shadow_aux_bayer_fuse.glsl','low_support_ppg_reference_26505.glsl']
with ZipFile(apk) as z:
    for n in assets:
        p='assets/shaders/motionv2/'+n
        want=h((root/'app/src/main/assets/shaders/motionv2'/n).read_bytes()); got=h(z.read(p))
        assert got==want,(n,got,want)
    normalizer=z.read('assets/shaders/motionv2/mfsr_spatial_rgb_normalize_26501.glsl')
    short_weight=z.read('assets/shaders/motionv2/mfsr_spatial_rgb_short_weight_26501.glsl')
    shadow=z.read('assets/shaders/motionv2/shadow_aux_bayer_fuse.glsl')
    short_recover=z.read('assets/shaders/motionv2/short_highlight_bayer_recover.glsl')
    render=z.read('assets/shaders/motionv2/render.glsl')
    assert b'IRIS_26506_OPPONENT_CONFIDENCE_REFERENCE_CHROMA' in normalizer
    assert b'IRIS_26506_SHORT_A_SPATIAL_PROVENANCE_COHERENCE' in short_weight
    assert b'IRIS_26506_LONG_A_QUAD_COHERENT_CHROMA_AUTHORITY' in shadow
    assert b'IRIS_26506_SHORT_A_PACK_COHERENCE_DIAGNOSTICS' in short_recover
    dex=b''.join(z.read(n) for n in z.namelist() if n.startswith('classes') and n.endswith('.dex'))
    for m in [b'IRIS_26504_COMPOSITION_BOUNDED_DISPLAY_GAIN',b'IRIS_26504_SINGLE_EXPOSURE_LOCAL_SUPPORT',b'IRIS_26505_PHYSICAL_LONG_BRACKET',b'IRIS_26506_SEPARATE_SDR_HDR_EXPOSURE_TARGETS']:
        assert m in dex,m
cfa=(root/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java').read_bytes()
assert b'IRIS_26504_DISABLE_HEAVY_PROVENANCE_READBACK' in cfa
cap=(root/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_bytes()
assert b'IRIS_26505_PHYSICAL_LONG_BRACKET' in cap
print('PASS: APK/source shader parity + 26505 bracket + 26506 Normal/Short/Long chroma-coherence markers')
PYAPK
pass "GATE 5 exactly one 26506 APK built"

echo "=== GATE 6: SUCCESSFUL SOURCE CHECKPOINT — NO PROMOTION ==="
( cd "$AFTER" && tar --sort=name --mtime='UTC 2026-08-18 00:00:00' --owner=0 --group=0 --numeric-owner -czf "$OUT/26506_successful_app_source.tar.gz" app/src/main app/version.properties )
( cd "$AFTER" && { find app/src/main -type f -print; echo app/version.properties; } | LC_ALL=C sort | while read -r f; do sha256sum "$f"; done ) > "$OUT/26506_successful_after.sha256"
[[ "$(wc -l < "$OUT/26506_successful_after.sha256")" -eq 870 ]] || fail "26506 source manifest count mismatch"

cat > "$OUT/26506_build_report.txt" <<EOF
26506 Integrated HDR / Chroma Consistency
Start infrastructure HEAD: $START_HEAD
Protected tested-26505 backup: $BACKUP_BRANCH -> $HANDOFF_26505_HEAD
Canonical runtime base: tested 26502 $CANONICAL_26502_HEAD
Version/build: 0.9726506 / 26506
APK: $(basename "$FINAL")
APK SHA256: $(sha "$FINAL")
Capture: tested 26505 Wronski normal + optional Short-A + intentional Long-A timing/metadata unchanged.
Brightness: tested SDR primary remains 0.80; Ultra HDR target is 1.00, so the gain map restores a nominal 1.25x (+0.322 EV) body signal at full HDR while preserving the SDR rendition.
Chroma: Normal uses support-discontinuity + R-G/B-G confidence; Short-A mixed/censored packs keep physical luminance but cannot inject isolated semantic chroma; Long-A semantic RGB requires all four Bayer phases with one common minimum weight. Valid Short-A color overrides generic Normal fallback.
Highlight safety: tested 26504 coherent clipping remains final authority; Short-A acceptance thresholds are not globally relaxed.
Learned HDR: NOT implemented in 26506.
Promotion: NONE until on-device acceptance.
EOF

pass "clean 870-file 26506 successful-source checkpoint emitted"
echo "PASS: 26506 INTEGRATED HDR / CHROMA CONSISTENCY BUILD COMPLETE: $FINAL"
