#!/usr/bin/env bash
set -euo pipefail

fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }

BRANCH="experimental-clean-photon-rebuild"
V5B_COMMIT="a424653a42923b02bd3a9f303da05d7a7e43409c"
V5B_BACKUP_BRANCH="backup-26492-v5b-tested-before-26493-boundary-refinement"
EXPECTED_APP_BASE="8233415edf738bf35c0fe1c4907f5dfe51de31a4"
BASELINE_PATCH="26492_successful_source.patch"
BASELINE_PATCH_SHA="1c4f948df5ac0ffd2b956d4890f051af936b34457fcff932d54027832f67f75f"
BASELINE_MANIFEST="26492_successful_after.sha256"
BASELINE_MANIFEST_SHA="dc19b4eba0fbeab493476383f5b148d9258103ab7d9e3d71e4e9e2915d149bef"
TRANSFORM="transform_26493_rcd_provenance_boundary_chroma_v1.py"
TRANSFORM_SHA="6e981316abfc2d7951369def577c5ecde777aefb37c420f4bfe1f897cab6382f"
NEW_VERSION="0.9726493"
NEW_BUILD="26493"
APK_NAME="IrisCamera-${NEW_VERSION}-${NEW_BUILD}-rcd-provenance-boundary-chroma-v1-debug.apk"
REPO="$(pwd)"
OUTDIR="build_26493_outputs"
WORK="${RUNNER_TEMP:-/tmp}/photon_26493_work_$$"
PREPATCH="$OUTDIR/26493_pre_edit_exact_26492_v5b.patch"
FINALPATCH="$OUTDIR/26493_successful_source.patch"
AFTERHASH="$OUTDIR/26493_successful_after.sha256"
BUILDLOG="$OUTDIR/26493_build.log"
REPORT="$OUTDIR/26493_build_report.txt"

rm -rf "$OUTDIR" "$WORK"
mkdir -p "$OUTDIR"

echo "=== 26493 RCD PROVENANCE-BOUNDARY CHROMA REFINEMENT ==="
date -Iseconds

# Gate 0: exact repository lineage and immutable input identities.
[[ "$(git branch --show-current)" == "$BRANCH" ]] || fail "wrong branch"
git cat-file -e "$V5B_COMMIT^{commit}" || fail "V5B commit unavailable"
git cat-file -e "$EXPECTED_APP_BASE^{commit}" || fail "protected app base unavailable"
git merge-base --is-ancestor "$V5B_COMMIT" HEAD || fail "HEAD must descend from tested V5B commit"
remote_backup="$(git ls-remote origin "refs/heads/$V5B_BACKUP_BRANCH" | awk '{print $1}')"
[[ "$remote_backup" == "$V5B_COMMIT" ]] || fail "V5B rollback branch missing/moved: $remote_backup"
[[ -f "$BASELINE_PATCH" && "$(sha "$BASELINE_PATCH")" == "$BASELINE_PATCH_SHA" ]] || fail "V5B baseline patch identity mismatch"
[[ -f "$BASELINE_MANIFEST" && "$(sha "$BASELINE_MANIFEST")" == "$BASELINE_MANIFEST_SHA" ]] || fail "V5B baseline manifest identity mismatch"
[[ -f "$TRANSFORM" && "$(sha "$TRANSFORM")" == "$TRANSFORM_SHA" ]] || fail "26493 transform identity mismatch"
python3 -m py_compile "$REPO/$TRANSFORM" || fail "transform Python syntax"
python3 "$REPO/$TRANSFORM" --self-test || fail "26493 model self-test"
pass "lineage + exact V5B inputs + transform identity"

# Gate 1: reconstruct ONE canonical baseline directly from the successful V5B artifact.
# No 26490->26491->26492 transform replay remains.
git worktree add --detach "$WORK" "$EXPECTED_APP_BASE" >/dev/null
trap 'git worktree remove --force "$WORK" >/dev/null 2>&1 || true; rm -rf "$WORK"' EXIT
( cd "$WORK" && git apply --binary "$REPO/$BASELINE_PATCH" ) || fail "apply exact V5B baseline patch"
( cd "$WORK" && sha256sum -c "$REPO/$BASELINE_MANIFEST" >/dev/null ) || fail "exact V5B 856-file manifest"
pass "canonical V5B source reconstructed directly; 856-file manifest exact"

# Required pre-edit binary patch: exact tested V5B source, before 26493 modification.
cp "$BASELINE_PATCH" "$PREPATCH"
[[ "$(sha "$PREPATCH")" == "$BASELINE_PATCH_SHA" ]] || fail "pre-edit V5B patch copy mismatch"
sha256sum "$PREPATCH" > "$OUTDIR/26493_pre_edit_exact_26492_v5b.patch.sha256"
pass "pre-edit exact V5B binary patch preserved before modification"

# Gate 2: apply the only 26493 image-pipeline modification.
python3 "$REPO/$TRANSFORM" "$WORK" || fail "26493 transform application"

python3 - "$WORK" "$BASELINE_MANIFEST" <<'PY_SCOPE'
from pathlib import Path
import hashlib,sys
root=Path(sys.argv[1]); manifest=Path(sys.argv[2])
expected={}
for line in manifest.read_text().splitlines():
    if not line.strip(): continue
    h,rel=line.split(None,1); expected[rel.strip()]=h
changed=[]; missing=[]
for rel,h in expected.items():
    p=root/rel
    if not p.is_file(): missing.append(rel); continue
    if hashlib.sha256(p.read_bytes()).hexdigest()!=h: changed.append(rel)
if missing: raise SystemExit('baseline files missing after transform: '+repr(missing[:20]))
want={
 'app/src/main/assets/shaders/motionv2/rcd26489_write.glsl',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2RcdDemosaic.java',
}
if set(changed)!=want:
    raise SystemExit('26493 scope failure changed='+repr(sorted(changed))+' expected='+repr(sorted(want)))
print('26493 EXACT SCOPE PASS files=2')
PY_SCOPE
pass "V5B identity outside two targeted files"

# Gate 3: semantic invariants. Core RCD passes and all other architecture remain untouched.
SHADER="$WORK/app/src/main/assets/shaders/motionv2/rcd26489_write.glsl"
HOST="$WORK/app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2RcdDemosaic.java"
grep -q 'IRIS_26493_PROVENANCE_BOUNDARY_CHROMA_STABILIZER' "$SHADER" || fail "26493 shader marker"
grep -q 'IRIS_26493_PROVENANCE_BOUNDARY_CHROMA_STABILIZER_BINDING' "$HOST" || fail "26493 host marker"
grep -q 'uniform highp sampler2D HighlightProvenance;' "$SHADER" || fail "write shader provenance sampler"
grep -q 'setTexture("HighlightProvenance"' "$HOST" || fail "write-stage provenance host binding"
grep -q 'useAssetProgram("motionv2/rcd26489_green"' "$HOST" || fail "RCD green pass survived"
grep -q 'useAssetProgram("motionv2/rcd26489_diag_direction"' "$HOST" || fail "RCD diagonal pass survived"
grep -q 'useAssetProgram("motionv2/rcd26489_opposite"' "$HOST" || fail "RCD opposite-colour pass survived"
grep -q 'useAssetProgram("motionv2/rcd26489_green_rb"' "$HOST" || fail "RCD green-RB pass survived"
pass "nine-pass RCD owner preserved; correction final-write-only"

# Gate 4: Photon runtime layout parser + host names remain valid.
python3 - "$WORK" <<'PY_LAYOUT'
from pathlib import Path
import re,sys
root=Path(sys.argv[1])
shader=(root/'app/src/main/assets/shaders/motionv2/rcd26489_write.glsl').read_text()
host=(root/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2RcdDemosaic.java').read_text()
def jsplit(s):
    p=re.split(r' ',s)
    while p and p[-1]=='': p.pop()
    return p
def parse(src):
    out={}
    for val in src.splitlines():
        if 'layout' not in val: continue
        d=jsplit(val.replace('{','')); last=d[-1].replace(';','') if d else ''
        li=val.find('('); ri=val.rfind(')'); binding=0
        if li>=0 and ri>li:
            for x in val[li+1:ri].split(','):
                pv=x.replace(' ','').split('=')
                if len(pv)==2 and pv[0]=='binding': binding=int(pv[1])
        out[last]=binding
    return out
layouts=parse(shader)
want={'CfaBuf':0,'RedBuf':1,'GreenBuf':2,'BlueBuf':3,'OutputRgb':9}
actual={k:layouts.get(k) for k in want}
if actual!=want: raise SystemExit('Photon layout parser mismatch '+repr(actual))
for n in ('CfaBuf','RedBuf','GreenBuf','BlueBuf'):
    if not re.search(r'setBufferCompute\(\s*"'+n+r'"',host): raise SystemExit('host missing '+n)
if not re.search(r'setTextureCompute\(\s*"OutputRgb"',host): raise SystemExit('host missing OutputRgb')
if not re.search(r'setTexture\(\s*"HighlightProvenance"',host): raise SystemExit('host missing HighlightProvenance')
print('26493 PHOTON RUNTIME BINDING PASS CfaBuf=0 RedBuf=1 GreenBuf=2 BlueBuf=3 OutputRgb=9 HighlightProvenance=sampler')
PY_LAYOUT

# Gate 5: compile the changed compute shader as GLES 3.1.
command -v glslangValidator >/dev/null 2>&1 || fail "glslangValidator missing"
TMPGLSL="$OUTDIR/rcd26489_write_26493_preprocessed.comp"
python3 - "$SHADER" "$TMPGLSL" <<'PY_GLSL'
from pathlib import Path
import sys
src=Path(sys.argv[1]).read_text()
needle='#define LAYOUT //\nLAYOUT\n'
if src.count(needle)!=1: raise SystemExit('LAYOUT preprocessor anchor mismatch')
src=src.replace(needle,'#version 310 es\nlayout(local_size_x=8, local_size_y=8, local_size_z=1) in;\n',1)
Path(sys.argv[2]).write_text(src)
PY_GLSL
glslangValidator -S comp "$TMPGLSL" > "$OUTDIR/26493_shader_validation.txt" 2>&1 || { cat "$OUTDIR/26493_shader_validation.txt"; fail "26493 changed shader compiler"; }
pass "changed RCD write shader real glslang compile"

# Native dependency policy: unchanged subsystem, so only prove the exact V5B baseline
# starts clean and remove the same four CMake-generated headers after the APK build.
GENERATED_DEPS=(
  "app/src/main/cpp/deps/archive.h"
  "app/src/main/cpp/deps/archive_entry.h"
  "app/src/main/cpp/deps/technicallyflac.h"
  "app/src/main/cpp/deps/tiny_dng_writer.h"
)
for rel in "${GENERATED_DEPS[@]}"; do
  [[ ! -e "$WORK/$rel" ]] || fail "generated native dep unexpectedly exists before build: $rel"
done
pass "unchanged native subsystem begins from clean canonical source"

# Gate 6: version increment and APK build occur in the SAME guarded block.
(
  set -euo pipefail
  python3 - "$WORK/app/version.properties" "$NEW_VERSION" "$NEW_BUILD" <<'PY_VERSION'
from pathlib import Path
import re,sys
p=Path(sys.argv[1]); name=sys.argv[2]; build=sys.argv[3]
s=p.read_text()
if s.count('VERSION_NAME=0.9726492')!=1 or s.count('VERSION_BUILD=26492')!=1:
    raise SystemExit('V5B version anchors not exact')
s=s.replace('VERSION_NAME=0.9726492','VERSION_NAME='+name,1)
s=s.replace('VERSION_BUILD=26492','VERSION_BUILD='+build,1)
p.write_text(s)
PY_VERSION
  cd "$WORK"
  ./gradlew clean assembleDebug --stacktrace
) > "$BUILDLOG" 2>&1 || { tail -260 "$BUILDLOG"; fail "26493 Gradle build"; }
pass "version increment + full APK build in one guarded block"

grep -q '^VERSION_NAME=0.9726493$' "$WORK/app/version.properties" || fail "final version name"
grep -q '^VERSION_BUILD=26493$' "$WORK/app/version.properties" || fail "final version build"

# Gate 7: exact final scope is V5B + two code files + version only.
python3 - "$WORK" "$BASELINE_MANIFEST" <<'PY_FINAL_SCOPE'
from pathlib import Path
import hashlib,sys
root=Path(sys.argv[1]); manifest=Path(sys.argv[2])
base={}
for line in manifest.read_text().splitlines():
    if line.strip():
        h,rel=line.split(None,1); base[rel.strip()]=h
changed=[]
for rel,h in base.items():
    p=root/rel
    if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=h: changed.append(rel)
want={
 'app/src/main/assets/shaders/motionv2/rcd26489_write.glsl',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2RcdDemosaic.java',
 'app/version.properties',
}
if set(changed)!=want: raise SystemExit('final scope failure '+repr(sorted(changed)))
print('26493 FINAL SCOPE PASS files=3 including version')
PY_FINAL_SCOPE

APK_SRC="$(find "$WORK/app/build/outputs/apk/debug" -maxdepth 1 -type f -name '*.apk' -print | head -1)"
[[ -n "$APK_SRC" && -f "$APK_SRC" ]] || fail "APK output missing"
cp "$APK_SRC" "$APK_NAME"
APK_SHA="$(sha "$APK_NAME")"
sha256sum "$APK_NAME" > "$OUTDIR/${APK_NAME}.sha256"

# Known CMake downloads are build products, not canonical application source.
for rel in "${GENERATED_DEPS[@]}"; do
  [[ -f "$WORK/$rel" ]] || fail "expected CMake-generated native dep missing after build: $rel"
  rm -f "$WORK/$rel"
done
pass "known generated native deps removed before canonical delta/manifest"

# Produce the one-file canonical baseline for the next iteration.
( cd "$WORK" && git diff --binary "$EXPECTED_APP_BASE" -- app/src/main app/version.properties ) > "$FINALPATCH"
[[ -s "$FINALPATCH" ]] || fail "26493 successful source patch empty"
(
  cd "$WORK"
  { find app/src/main -type f -print; echo app/version.properties; } | LC_ALL=C sort | while read -r f; do sha256sum "$f"; done
) > "$AFTERHASH"

cat > "$REPORT" <<EOF
26493 BUILD SUCCESS
Version: ${NEW_VERSION} / ${NEW_BUILD}
Baseline: exact tested 26492 V5B successful artifact
Baseline commit/package checkpoint: ${V5B_COMMIT}
Rollback branch: ${V5B_BACKUP_BRANCH}
APK: ${APK_NAME}
APK SHA256: ${APK_SHA}

Functional delta from V5B: exactly 2 source files + version.
- rcd26489_write.glsl: final-write-only provenance-boundary chroma stabilization
- MotionV2RcdDemosaic.java: read-only HighlightProvenance binding for final write

Hard identity conditions:
- no nearby CENSORED+trusted provenance boundary => V5B output
- not high luminance => V5B output
- no sign-reversing opponent chroma => V5B output
- incoherent neighbor pair => V5B output
- true photo border PPG path unchanged

Protected unchanged by exact manifest scope:
- Wronski alignment/accumulator/rejection/frame ownership
- 26492 provenance classification and short validation
- scene-body global display exposure authority
- Camera2 color transform
- render/UHDR
- MotionV2Denoise remains excluded
- sharpening remains excluded
- all nine existing RCD reconstruction passes remain active
EOF

mkdir -p "$OUTDIR/next_baseline_inputs"
cp "$FINALPATCH" "$OUTDIR/next_baseline_inputs/26493_successful_source.patch"
cp "$AFTERHASH" "$OUTDIR/next_baseline_inputs/26493_successful_after.sha256"
cp "$TRANSFORM" "$OUTDIR/next_baseline_inputs/"
sha256sum "$BASELINE_PATCH" "$BASELINE_MANIFEST" "$TRANSFORM" "$PREPATCH" "$FINALPATCH" "$AFTERHASH" "$REPORT" "$APK_NAME" > "$OUTDIR/26493_artifact_hashes.sha256"

echo "=== 26493 BUILD SUCCESS ==="
cat "$REPORT"
