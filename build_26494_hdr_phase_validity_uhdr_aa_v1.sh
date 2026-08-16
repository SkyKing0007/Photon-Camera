#!/usr/bin/env bash
set -euo pipefail

fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }

BRANCH="experimental-clean-photon-rebuild"
V5B_COMMIT="a424653a42923b02bd3a9f303da05d7a7e43409c"
REJECTED_26493_V3="4aedd435f72f68b268cbbbe65470260827a9f7f5"
V5B_BACKUP_BRANCH="backup-26492-v5b-before-26494-hdr-phase-validity-uhdr-aa"
EXPECTED_APP_BASE="8233415edf738bf35c0fe1c4907f5dfe51de31a4"
BASELINE_BUNDLE="26492_successful_app_source.tar.gz"
BASELINE_BUNDLE_SHA="4636f22d1ea417b9b3c5380025abc502971c3f334c78b3f7c199570ad72d98a9"
BASELINE_MANIFEST="26492_successful_after.sha256"
BASELINE_MANIFEST_SHA="dc19b4eba0fbeab493476383f5b148d9258103ab7d9e3d71e4e9e2915d149bef"
TRANSFORM="transform_26494_hdr_phase_validity_uhdr_aa_v1.py"
TRANSFORM_SHA="f3848c111943624a4699c077083f31b3c8190f22a370f61d383549dc1eb39773"
NEW_VERSION="0.9726494"
NEW_BUILD="26494"
APK_NAME="IrisCamera-${NEW_VERSION}-${NEW_BUILD}-hdr-phase-validity-uhdr-footprint-aa-debug.apk"
REPO="$(pwd)"
OUTDIR="build_26494_outputs"
WORK="${RUNNER_TEMP:-/tmp}/photon_26494_work_$$"
PREPATCH="$OUTDIR/26494_pre_edit_exact_26492_v5b_complete_binary.patch"
FINALPATCH="$OUTDIR/26494_successful_complete_binary.patch"
NEXTBUNDLE="$OUTDIR/26494_successful_app_source.tar.gz"
AFTERHASH="$OUTDIR/26494_successful_after.sha256"
BUILDLOG="$OUTDIR/26494_build.log"
REPORT="$OUTDIR/26494_build_report.txt"

rm -rf "$OUTDIR" "$WORK"
mkdir -p "$OUTDIR"

echo "=== 26494 HDR PHASE VALIDITY + UHDR MATCHED-FOOTPRINT AA ==="
date -Iseconds

# Gate 0: exact lineage and package identities.
[[ "$(git branch --show-current)" == "$BRANCH" ]] || fail "wrong branch"
git cat-file -e "$V5B_COMMIT^{commit}" || fail "tested V5B commit unavailable"
git cat-file -e "$REJECTED_26493_V3^{commit}" || fail "26493 V3 checkpoint unavailable"
git cat-file -e "$EXPECTED_APP_BASE^{commit}" || fail "protected app base unavailable"
git merge-base --is-ancestor "$V5B_COMMIT" HEAD || fail "HEAD must descend from tested V5B"
git merge-base --is-ancestor "$REJECTED_26493_V3" HEAD || fail "HEAD must descend from rejected 26493 V3 infrastructure checkpoint"
remote_backup="$(git ls-remote origin "refs/heads/$V5B_BACKUP_BRANCH" | awk '{print $1}')"
[[ "$remote_backup" == "$V5B_COMMIT" ]] || fail "26494 V5B backup branch missing/moved: $remote_backup"
[[ -f "$BASELINE_BUNDLE" && "$(sha "$BASELINE_BUNDLE")" == "$BASELINE_BUNDLE_SHA" ]] || fail "complete V5B source bundle identity mismatch"
[[ -f "$BASELINE_MANIFEST" && "$(sha "$BASELINE_MANIFEST")" == "$BASELINE_MANIFEST_SHA" ]] || fail "V5B manifest identity mismatch"
[[ -f "$TRANSFORM" && "$(sha "$TRANSFORM")" == "$TRANSFORM_SHA" ]] || fail "26494 transform identity mismatch"
python3 -m py_compile "$REPO/$TRANSFORM" || fail "transform Python syntax"
python3 "$REPO/$TRANSFORM" --self-test || fail "26494 model self-test"
pass "lineage + backup + canonical V5B inputs + transform identity"

# Gate 1: reconstruct the exact tested 26492 V5B app source.
git worktree add --detach "$WORK" "$EXPECTED_APP_BASE" >/dev/null
trap 'git worktree remove --force "$WORK" >/dev/null 2>&1 || true; rm -rf "$WORK"' EXIT
rm -rf "$WORK/app/src/main"
rm -f "$WORK/app/version.properties"
( cd "$WORK" && tar -xzf "$REPO/$BASELINE_BUNDLE" ) || fail "extract V5B bundle"
python3 - "$WORK" "$REPO/$BASELINE_MANIFEST" <<'PY_BASE'
from pathlib import Path
import hashlib,sys
root=Path(sys.argv[1]); manifest=Path(sys.argv[2])
expected={}
for line in manifest.read_text().splitlines():
    if line.strip():
        h,rel=line.split(None,1); expected[rel.strip()]=h
actual=sorted([str(p.relative_to(root)) for p in (root/'app/src/main').rglob('*') if p.is_file()] + ['app/version.properties'])
want=sorted(expected)
if actual!=want:
    raise SystemExit('V5B file-set mismatch missing='+repr(sorted(set(want)-set(actual))[:20])+' extra='+repr(sorted(set(actual)-set(want))[:20]))
for rel,h in expected.items():
    a=hashlib.sha256((root/rel).read_bytes()).hexdigest()
    if a!=h: raise SystemExit('V5B hash mismatch '+rel+' expected='+h+' actual='+a)
print('26494 BASELINE PASS files=856 hashes=856 exactTested26492V5B=true')
PY_BASE
pass "exact 26492 V5B source reconstructed"

# Required backup patch BEFORE any application-source modification.
(
  cd "$WORK"
  git add -N app/src/main app/version.properties
  git diff --binary "$EXPECTED_APP_BASE" -- app/src/main app/version.properties
  git reset -q -- app/src/main app/version.properties
) > "$REPO/$PREPATCH"
[[ -s "$PREPATCH" ]] || fail "pre-edit V5B binary patch empty"
grep -q 'new file mode' "$PREPATCH" || fail "pre-edit patch missing historical new files"
sha256sum "$PREPATCH" > "$OUTDIR/26494_pre_edit_exact_26492_v5b_complete_binary.patch.sha256"
pass "pre-edit exact V5B complete binary patch created before modification"

# Gate 2: apply one integrated 26494 architecture transform.
python3 "$REPO/$TRANSFORM" "$WORK" || fail "26494 transform application"
python3 - "$WORK" "$REPO/$BASELINE_MANIFEST" <<'PY_SCOPE'
from pathlib import Path
import hashlib,sys
root=Path(sys.argv[1]); manifest=Path(sys.argv[2])
base={}
for line in manifest.read_text().splitlines():
    if line.strip():
        h,rel=line.split(None,1); base[rel.strip()]=h
changed=[]; missing=[]
for rel,h in base.items():
    p=root/rel
    if not p.is_file(): missing.append(rel)
    elif hashlib.sha256(p.read_bytes()).hexdigest()!=h: changed.append(rel)
if missing: raise SystemExit('files missing after transform '+repr(missing[:20]))
want={
'app/src/main/assets/shaders/motionv2/highlight_provenance_init.glsl',
'app/src/main/assets/shaders/motionv2/short_highlight_bayer_recover.glsl',
'app/src/main/assets/shaders/motionv2/rcd26489_populate.glsl',
'app/src/main/assets/shaders/motionv2/gainmap.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
}
if set(changed)!=want:
    raise SystemExit('26494 scope mismatch changed='+repr(sorted(changed))+' expected='+repr(sorted(want)))
print('26494 EXACT PREVERSION SCOPE PASS files=6')
PY_SCOPE
pass "V5B identity preserved outside six targeted architecture files"

# Gate 3: per-phase provenance/short/RCD ownership semantic audit.
PROV="$WORK/app/src/main/assets/shaders/motionv2/highlight_provenance_init.glsl"
SHORT="$WORK/app/src/main/assets/shaders/motionv2/short_highlight_bayer_recover.glsl"
POP="$WORK/app/src/main/assets/shaders/motionv2/rcd26489_populate.glsl"
GAIN="$WORK/app/src/main/assets/shaders/motionv2/gainmap.glsl"
RECON="$WORK/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java"
RENDER="$WORK/app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java"
RCDHOST="$WORK/app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2RcdDemosaic.java"

grep -q 'layout(r32f, binding = 0).*outProvenance' "$PROV" || fail "provenance init must preserve R32F bridge"
grep -q 'encodePhaseStates' "$PROV" || fail "base-3 per-phase encoder missing"
grep -q 'vec4 state = step(vec4(physicalClipThreshold), sensor);' "$PROV" || fail "per-phase physical clip classification missing"
grep -q 'layout(r32f, binding = 1).*outProvenance' "$SHORT" || fail "short provenance must preserve R32F bridge"
grep -q 'vec4 recoverMask = clipMask \* shortSafe(shortCenter);' "$SHORT" || fail "short recovery not phase-selective"
grep -q 'vec4 recovered = normal;' "$SHORT" || fail "normal measured phase preservation missing"
grep -q 'state\[i\] = PROVENANCE_SHORT_VALIDATED;' "$SHORT" || fail "per-phase short state missing"
grep -q 'IRIS_26494_RCD_PER_PHASE_PROVENANCE_CONSUMER' "$POP" || fail "RCD per-phase consumer missing"
grep -q 'float code = texelFetch(HighlightProvenance, p >> 1, 0).r;' "$POP" || fail "RCD base-3 provenance fetch missing"
grep -q 'return mod(digit, 3.0);' "$POP" || fail "RCD base-3 phase decoder missing"
grep -q 'if (!isCensoredState(provenanceAt(p))) return measured;' "$POP" || fail "measured NORMAL/SHORT identity missing"
grep -q 'trustedSamePhaseBalanced' "$POP" || fail "same-CFA constrained evidence missing"
grep -q 'max(neutralLowerBound, meanH)' "$POP" || fail "censored lower-bound monotonicity missing"
grep -q 'IRIS_26494_PER_PHASE_HIGHLIGHT_PROVENANCE' "$RECON" || fail "phase diagnostics missing"
grep -q 'encoding=R32F_BASE3_PHASES' "$RECON" || fail "base-3 diagnostic encoding missing"
# 26493 rejected final-write cleanup must not be part of the V5B-derived 26494 image path.
! grep -Rqs 'IRIS_26493_PROVENANCE_BOUNDARY_CHROMA_STABILIZER' "$WORK/app/src/main" || fail "rejected 26493 final-RGB cleanup leaked into 26494"
pass "per-phase CFA authority in existing R32F bridge + per-phase short validation + unresolved-phase-only RCD semantics"

# Gate 4: UHDR is exact matched 4x4 HDR/SDR footprint integration, not point decimation or blind blur.
grep -q 'IRIS_26494_MATCHED_FOOTPRINT_UHDR_GAINMAP' "$GAIN" || fail "26494 UHDR marker missing"
grep -q 'const int FOOTPRINT = 4;' "$GAIN" || fail "UHDR footprint factor"
grep -q 'texelFetch(HdrBuffer, sp, 0)' "$GAIN" || fail "HDR footprint fetch missing"
grep -q 'texelFetch(SdrBuffer, sp, 0)' "$GAIN" || fail "SDR footprint fetch missing"
grep -q 'hdrMean = hdrSum / float(FOOTPRINT \* FOOTPRINT);' "$GAIN" || fail "HDR footprint integration missing"
grep -q 'sdrMean = sdrSum / float(FOOTPRINT \* FOOTPRINT);' "$GAIN" || fail "SDR footprint integration missing"
grep -q 'setVar("sourceSize", renderedSdrSize)' "$RENDER" || fail "UHDR source geometry host binding missing"
! grep -q 'SPIKE_SIGMA_MULT\|SAME_SURFACE_LOG_LUMA' "$GAIN" || fail "old point-sample spike limiter still active"
pass "UHDR matched-footprint anti-aliased decimation contract"

# Gate 5: Photon runtime binding parser and sampler/image binding types.
python3 - "$POP" "$RCDHOST" "$PROV" "$SHORT" <<'PY_LAYOUT'
from pathlib import Path
import re,sys
pop=Path(sys.argv[1]).read_text(); host=Path(sys.argv[2]).read_text(); prov=Path(sys.argv[3]).read_text(); short=Path(sys.argv[4]).read_text()
def parse(src):
    out={}
    for val in src.splitlines():
        if 'layout' not in val: continue
        d=val.replace('{','').split(' ')
        while d and d[-1]=='': d.pop()
        last=d[-1].replace(';','') if d else ''
        li=val.find('('); ri=val.rfind(')'); binding=0
        if li>=0 and ri>li:
            for x in val[li+1:ri].split(','):
                pv=x.replace(' ','').split('=')
                if len(pv)==2 and pv[0]=='binding': binding=int(pv[1])
        out[last]=binding
    return out
layouts=parse(pop)
want={'CfaBuf':0,'RedBuf':1,'GreenBuf':2,'BlueBuf':3}
actual={k:layouts.get(k) for k in want}
if actual!=want: raise SystemExit('Photon RCD parser mismatch '+repr(actual))
for n in want:
    if not re.search(r'setBufferCompute\(\s*"'+n+r'"',host): raise SystemExit('host missing '+n)
if not re.search(r'setTexture\(\s*"HighlightProvenance"',host): raise SystemExit('sampler must use setTexture')
if 'layout(r32f, binding = 0) uniform highp writeonly image2D outProvenance;' not in prov:
    raise SystemExit('provenance image layout mismatch')
if 'layout(r32f, binding = 1) uniform highp writeonly image2D outProvenance;' not in short:
    raise SystemExit('short provenance image layout mismatch')
print('26494 PHOTON BINDING PASS RCD_SSBO=0,1,2,3 HighlightProvenance=sampler R32F_BASE3=true')
PY_LAYOUT

# Gate 6: real GLSL compilers on all four modified shaders.
command -v glslangValidator >/dev/null 2>&1 || fail "glslangValidator missing"
preprocess_compute(){
  local src="$1" dst="$2"
  python3 - "$src" "$dst" <<'PY_COMP'
from pathlib import Path
import sys
src=Path(sys.argv[1]).read_text(); needle='#define LAYOUT //\nLAYOUT\n'
if src.count(needle)!=1: raise SystemExit('LAYOUT anchor mismatch '+sys.argv[1])
src=src.replace(needle,'#version 310 es\nlayout(local_size_x=8, local_size_y=8, local_size_z=1) in;\n',1)
Path(sys.argv[2]).write_text(src)
PY_COMP
}
preprocess_compute "$PROV" "$OUTDIR/highlight_provenance_init_26494.comp"
preprocess_compute "$SHORT" "$OUTDIR/short_highlight_bayer_recover_26494.comp"
preprocess_compute "$POP" "$OUTDIR/rcd26489_populate_26494.comp"
python3 - "$GAIN" "$OUTDIR/gainmap_26494.frag" <<'PY_FRAG'
from pathlib import Path
import sys
Path(sys.argv[2]).write_text('#version 300 es\n'+Path(sys.argv[1]).read_text())
PY_FRAG
for f in "$OUTDIR/highlight_provenance_init_26494.comp" "$OUTDIR/short_highlight_bayer_recover_26494.comp" "$OUTDIR/rcd26489_populate_26494.comp"; do
  glslangValidator -S comp "$f" >> "$OUTDIR/26494_shader_validation.txt" 2>&1 || { cat "$OUTDIR/26494_shader_validation.txt"; fail "compute shader compiler $f"; }
done
glslangValidator -S frag "$OUTDIR/gainmap_26494.frag" >> "$OUTDIR/26494_shader_validation.txt" 2>&1 || { cat "$OUTDIR/26494_shader_validation.txt"; fail "gainmap fragment compiler"; }
pass "all four changed shaders pass real glslang compilation"

# Unchanged native subsystem must begin clean.
GENERATED_DEPS=(
  "app/src/main/cpp/deps/archive.h"
  "app/src/main/cpp/deps/archive_entry.h"
  "app/src/main/cpp/deps/technicallyflac.h"
  "app/src/main/cpp/deps/tiny_dng_writer.h"
)
for rel in "${GENERATED_DEPS[@]}"; do [[ ! -e "$WORK/$rel" ]] || fail "generated native dep exists before build: $rel"; done
pass "unchanged native subsystem starts from clean canonical source"

# Gate 7: version increment AND APK build in one guarded command block.
(
  set -euo pipefail
  python3 - "$WORK/app/version.properties" "$NEW_VERSION" "$NEW_BUILD" <<'PY_VERSION'
from pathlib import Path
import sys
p=Path(sys.argv[1]); name=sys.argv[2]; build=sys.argv[3]; s=p.read_text()
if s.count('VERSION_NAME=0.9726492')!=1 or s.count('VERSION_BUILD=26492')!=1:
    raise SystemExit('exact V5B version anchors missing')
s=s.replace('VERSION_NAME=0.9726492','VERSION_NAME='+name,1)
s=s.replace('VERSION_BUILD=26492','VERSION_BUILD='+build,1)
p.write_text(s)
PY_VERSION
  cd "$WORK"
  ./gradlew clean assembleDebug --stacktrace
) > "$BUILDLOG" 2>&1 || { tail -300 "$BUILDLOG"; fail "26494 Gradle build"; }
pass "version increment + full APK build completed in one guarded block"

grep -q '^VERSION_NAME=0.9726494$' "$WORK/app/version.properties" || fail "final version name"
grep -q '^VERSION_BUILD=26494$' "$WORK/app/version.properties" || fail "final version build"

# Gate 8: exact final source delta is seven architecture files + version only.
python3 - "$WORK" "$REPO/$BASELINE_MANIFEST" <<'PY_FINAL'
from pathlib import Path
import hashlib,sys
root=Path(sys.argv[1]); manifest=Path(sys.argv[2]); base={}
for line in manifest.read_text().splitlines():
    if line.strip():
        h,rel=line.split(None,1); base[rel.strip()]=h
changed=[]
for rel,h in base.items():
    p=root/rel
    if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=h: changed.append(rel)
want={
'app/src/main/assets/shaders/motionv2/highlight_provenance_init.glsl',
'app/src/main/assets/shaders/motionv2/short_highlight_bayer_recover.glsl',
'app/src/main/assets/shaders/motionv2/rcd26489_populate.glsl',
'app/src/main/assets/shaders/motionv2/gainmap.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/version.properties'}
if set(changed)!=want: raise SystemExit('26494 final scope mismatch '+repr(sorted(changed)))
print('26494 FINAL SCOPE PASS files=7 including version')
PY_FINAL

APK_SRC="$(find "$WORK/app/build/outputs/apk/debug" -maxdepth 1 -type f -name '*.apk' -print | head -1)"
[[ -n "$APK_SRC" && -f "$APK_SRC" ]] || fail "APK output missing"
cp "$APK_SRC" "$APK_NAME"
APK_SHA="$(sha "$APK_NAME")"
sha256sum "$APK_NAME" > "$OUTDIR/${APK_NAME}.sha256"

for rel in "${GENERATED_DEPS[@]}"; do
  [[ -f "$WORK/$rel" ]] || fail "expected CMake-generated native dep missing after build: $rel"
  rm -f "$WORK/$rel"
done
pass "known generated native deps removed before canonical baseline output"

python3 - "$WORK" "$REPO/$BASELINE_MANIFEST" <<'PY_FILESET'
from pathlib import Path
import sys
root=Path(sys.argv[1]); manifest=Path(sys.argv[2])
want=sorted([line.split(None,1)[1].strip() for line in manifest.read_text().splitlines() if line.strip()])
actual=sorted([str(p.relative_to(root)) for p in (root/'app/src/main').rglob('*') if p.is_file()] + ['app/version.properties'])
if actual!=want:
    raise SystemExit('26494 final file-set mismatch missing='+repr(sorted(set(want)-set(actual))[:20])+' extra='+repr(sorted(set(actual)-set(want))[:20]))
print('26494 FINAL CANONICAL FILESET PASS files=856')
PY_FILESET

# Complete binary patch and complete next baseline bundle.
(
  cd "$WORK"
  git add -N app/src/main app/version.properties
  git diff --binary "$EXPECTED_APP_BASE" -- app/src/main app/version.properties
  git reset -q -- app/src/main app/version.properties
) > "$REPO/$FINALPATCH"
[[ -s "$FINALPATCH" ]] || fail "26494 complete binary patch empty"
(
  cd "$WORK"
  tar --sort=name --mtime='UTC 2026-08-16 00:00:00' --owner=0 --group=0 --numeric-owner \
      -czf "$REPO/$NEXTBUNDLE" app/src/main app/version.properties
  { find app/src/main -type f -print; echo app/version.properties; } | LC_ALL=C sort | while read -r f; do sha256sum "$f"; done
) > "$AFTERHASH"

cat > "$REPORT" <<EOF
26494 BUILD SUCCESS
Version: ${NEW_VERSION} / ${NEW_BUILD}
Baseline: exact tested 26492 V5B canonical source
Baseline checkpoint: ${V5B_COMMIT}
Required pre-edit backup branch: ${V5B_BACKUP_BRANCH}
Rejected 26493 V3 is not in the image path.
APK: ${APK_NAME}
APK SHA256: ${APK_SHA}

Architecture correction 1: per-phase physical CFA authority
- provenance keeps the existing R32F carrier; four R/G1/G2/B ternary states are packed exactly as one base-3 code
- an unsaturated normal phase remains measured even if another phase in the 2x2 pack clips
- no extra full-frame provenance texture/readback bandwidth is added
- short recovery changes only clipped phases that are individually short-safe and pass the existing observable correspondence gate
- unresolved clipped phases alone receive a neutral physical lower bound, optionally raised by coherent same-CFA measured evidence
- all nine existing RCD directional passes remain unchanged

Architecture correction 2: Ultra HDR matched-footprint anti-aliasing
- gain map remains 1/4 width and 1/4 height with existing orientation/max-ratio/JPEG ownership
- each gain sample integrates the exact corresponding 4x4 HDR and SDR source footprint before ratio formation
- no point decimation, no blind spatial blur, no post-aliased spike repair
- SDR remains full-resolution spatial-detail authority

New runtime diagnostics
- normal/censored/shortValidated counts are per physical CFA phase
- affected packed-cell histogram reports 0..4 affected phases
- censored and short counts are reported by packed CFA phase
- existing gain-map roughness/grid telemetry remains active

Protected unchanged by exact scope gate
- Wronski alignment/rejection/accumulator/frame ownership
- capture timing and no shutter top-up wait
- scene-body global display exposure authority
- Camera2 color transform
- tone/render exposure scale and UHDR attachment geometry
- MotionV2Denoise remains excluded
- sharpening remains excluded
EOF

mkdir -p "$OUTDIR/next_baseline_inputs"
cp "$NEXTBUNDLE" "$OUTDIR/next_baseline_inputs/26494_successful_app_source.tar.gz"
cp "$AFTERHASH" "$OUTDIR/next_baseline_inputs/26494_successful_after.sha256"
cp "$TRANSFORM" "$OUTDIR/next_baseline_inputs/"
sha256sum "$BASELINE_BUNDLE" "$BASELINE_MANIFEST" "$TRANSFORM" "$PREPATCH" "$FINALPATCH" "$NEXTBUNDLE" "$AFTERHASH" "$REPORT" "$APK_NAME" > "$OUTDIR/26494_artifact_hashes.sha256"

echo "=== 26494 BUILD SUCCESS ==="
cat "$REPORT"
