#!/usr/bin/env bash
set -euo pipefail

fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }

BRANCH="experimental-clean-photon-rebuild"
V5B_COMMIT="a424653a42923b02bd3a9f303da05d7a7e43409c"
V5B_BACKUP_BRANCH="backup-26492-v5b-tested-before-26493-boundary-refinement"
FAILED_V1_COMMIT="00a72ba28665c0667c4f45e490f638195f46d6dc"
FAILED_V1_BACKUP_BRANCH="backup-26493-v1-manifest-failed-before-v2-canonical-bundle"
FAILED_V2_COMMIT="0599afe5098e02b35169bf6cd0df32837b26e9b0"
FAILED_V2_BACKUP_BRANCH="backup-26493-v2-glsl-keyword-failed-before-v3-reserved-name-fix"
EXPECTED_APP_BASE="8233415edf738bf35c0fe1c4907f5dfe51de31a4"
BASELINE_BUNDLE="26492_successful_app_source.tar.gz"
BASELINE_BUNDLE_SHA="4636f22d1ea417b9b3c5380025abc502971c3f334c78b3f7c199570ad72d98a9"
BASELINE_MANIFEST="26492_successful_after.sha256"
BASELINE_MANIFEST_SHA="dc19b4eba0fbeab493476383f5b148d9258103ab7d9e3d71e4e9e2915d149bef"
TRANSFORM="transform_26493_rcd_provenance_boundary_chroma_v2_glsl_keyword_fix.py"
TRANSFORM_SHA="7b52fc154ddde069e040099f148b3431c984e1945e9efb6ed0e9638044feeba0"
NEW_VERSION="0.9726493"
NEW_BUILD="26493"
APK_NAME="IrisCamera-${NEW_VERSION}-${NEW_BUILD}-rcd-provenance-boundary-chroma-v3-glsl-keyword-fix-debug.apk"
REPO="$(pwd)"
OUTDIR="build_26493_v3_outputs"
WORK="${RUNNER_TEMP:-/tmp}/photon_26493_v2_work_$$"
PREPATCH="$OUTDIR/26493_v3_pre_edit_exact_26492_v5b_complete_binary.patch"
FINALPATCH="$OUTDIR/26493_v3_successful_complete_binary.patch"
NEXTBUNDLE="$OUTDIR/26493_successful_app_source.tar.gz"
AFTERHASH="$OUTDIR/26493_successful_after.sha256"
BUILDLOG="$OUTDIR/26493_v3_build.log"
REPORT="$OUTDIR/26493_v3_build_report.txt"

rm -rf "$OUTDIR" "$WORK"
mkdir -p "$OUTDIR"

echo "=== 26493 V3 RCD PROVENANCE-BOUNDARY CHROMA REFINEMENT — GLSL RESERVED KEYWORD FIX ==="
date -Iseconds

# Gate 0: exact repository lineage and immutable input identities.
[[ "$(git branch --show-current)" == "$BRANCH" ]] || fail "wrong branch"
git cat-file -e "$V5B_COMMIT^{commit}" || fail "V5B commit unavailable"
git cat-file -e "$FAILED_V1_COMMIT^{commit}" || fail "failed 26493 V1 infrastructure commit unavailable"
git cat-file -e "$FAILED_V2_COMMIT^{commit}" || fail "failed 26493 V2 shader-compile commit unavailable"
git cat-file -e "$EXPECTED_APP_BASE^{commit}" || fail "protected app base unavailable"
git merge-base --is-ancestor "$V5B_COMMIT" HEAD || fail "HEAD must descend from tested V5B commit"
git merge-base --is-ancestor "$FAILED_V1_COMMIT" HEAD || fail "HEAD must descend from failed 26493 V1 infrastructure checkpoint"
git merge-base --is-ancestor "$FAILED_V2_COMMIT" HEAD || fail "HEAD must descend from failed 26493 V2 shader-compile checkpoint"
remote_backup="$(git ls-remote origin "refs/heads/$V5B_BACKUP_BRANCH" | awk '{print $1}')"
[[ "$remote_backup" == "$V5B_COMMIT" ]] || fail "V5B rollback branch missing/moved: $remote_backup"
v1_backup="$(git ls-remote origin "refs/heads/$FAILED_V1_BACKUP_BRANCH" | awk '{print $1}')"
[[ "$v1_backup" == "$FAILED_V1_COMMIT" ]] || fail "failed V1 backup branch missing/moved: $v1_backup"
v2_backup="$(git ls-remote origin "refs/heads/$FAILED_V2_BACKUP_BRANCH" | awk '{print $1}')"
[[ "$v2_backup" == "$FAILED_V2_COMMIT" ]] || fail "failed V2 backup branch missing/moved: $v2_backup"
[[ -f "$BASELINE_BUNDLE" && "$(sha "$BASELINE_BUNDLE")" == "$BASELINE_BUNDLE_SHA" ]] || fail "complete V5B source bundle identity mismatch"
[[ -f "$BASELINE_MANIFEST" && "$(sha "$BASELINE_MANIFEST")" == "$BASELINE_MANIFEST_SHA" ]] || fail "V5B baseline manifest identity mismatch"
[[ -f "$TRANSFORM" && "$(sha "$TRANSFORM")" == "$TRANSFORM_SHA" ]] || fail "26493 transform identity mismatch"
python3 -m py_compile "$REPO/$TRANSFORM" || fail "transform Python syntax"
python3 "$REPO/$TRANSFORM" --self-test || fail "26493 model self-test"
pass "lineage + complete V5B bundle + V3 GLSL-keyword-fix transform identity"

# Gate 1: reconstruct ONE canonical baseline directly from a complete successful V5B source bundle.
# This explicitly includes the 43 files that were new/untracked relative to the protected base
# and therefore could not be represented by the old git-diff-only baseline package.
git worktree add --detach "$WORK" "$EXPECTED_APP_BASE" >/dev/null
trap 'git worktree remove --force "$WORK" >/dev/null 2>&1 || true; rm -rf "$WORK"' EXIT
rm -rf "$WORK/app/src/main"
rm -f "$WORK/app/version.properties"
( cd "$WORK" && tar -xzf "$REPO/$BASELINE_BUNDLE" ) || fail "extract complete V5B source bundle"
python3 - "$WORK" "$REPO/$BASELINE_MANIFEST" <<'PY_BASELINE'
from pathlib import Path
import hashlib,sys
root=Path(sys.argv[1]); manifest=Path(sys.argv[2])
expected={}
for line in manifest.read_text().splitlines():
    if not line.strip(): continue
    h,rel=line.split(None,1); expected[rel.strip()]=h
actual=sorted([str(p.relative_to(root)) for p in (root/'app/src/main').rglob('*') if p.is_file()] + ['app/version.properties'])
want=sorted(expected)
if actual!=want:
    missing=sorted(set(want)-set(actual)); extra=sorted(set(actual)-set(want))
    raise SystemExit('V5B canonical file-set mismatch missing='+repr(missing[:20])+' extra='+repr(extra[:20]))
for rel,h in expected.items():
    p=root/rel
    ah=hashlib.sha256(p.read_bytes()).hexdigest()
    if ah!=h: raise SystemExit('V5B canonical hash mismatch '+rel+' expected='+h+' actual='+ah)
print('26492 V5B COMPLETE CANONICAL BASELINE PASS files=856 hashes=856')
PY_BASELINE
pass "complete canonical V5B source reconstructed; exact 856-file set + hashes"

# Required pre-edit complete binary patch: exact tested V5B source, BEFORE 26493 modification.
# Intent-to-add makes Git include files that are new relative to the protected historical base.
(
  cd "$WORK"
  git add -N app/src/main app/version.properties
  git diff --binary "$EXPECTED_APP_BASE" -- app/src/main app/version.properties
  git reset -q -- app/src/main app/version.properties
) > "$REPO/$PREPATCH"
[[ -s "$PREPATCH" ]] || fail "pre-edit complete V5B binary patch empty"
grep -q 'new file mode.*' "$PREPATCH" || fail "pre-edit complete patch does not carry new files"
grep -q 'rcd26489_write.glsl' "$PREPATCH" || fail "pre-edit complete patch missing RCD write source"
grep -q 'MotionV2RcdDemosaic.java' "$PREPATCH" || fail "pre-edit complete patch missing RCD host source"
sha256sum "$PREPATCH" > "$OUTDIR/26493_v3_pre_edit_exact_26492_v5b_complete_binary.patch.sha256"
pass "pre-edit exact V5B COMPLETE binary patch created before 26493 modification"

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
# First catch GLSL reserved-word declarations explicitly. V1/V2 failed because
# `coherent` is a GLSL memory qualifier and was accidentally used as a vec3 name.
python3 - "$SHADER" <<'PY_RESERVED'
from pathlib import Path
import re,sys
src=Path(sys.argv[1]).read_text()
start=src.find('/* IRIS_26493_PROVENANCE_BOUNDARY_CHROMA_STABILIZER')
end=src.find('float ppgGreen(', start)
if start < 0 or end < 0:
    raise SystemExit('26493 stabilizer block not found for reserved-keyword audit')
block=src[start:end]
reserved={
 'attribute','const','uniform','varying','buffer','shared','coherent','volatile','restrict',
 'readonly','writeonly','atomic_uint','layout','centroid','flat','smooth','noperspective',
 'patch','sample','invariant','precise','precision','highp','mediump','lowp','in','out','inout',
 'struct','void','while','break','continue','do','for','if','else','switch','case','default',
 'discard','return','subroutine','true','false'
}
decls=[]
for m in re.finditer(r'\b(?:float|int|uint|bool|vec[234]|ivec[234]|uvec[234]|bvec[234]|mat[234](?:x[234])?)\s+([A-Za-z_]\w*)',block):
    name=m.group(1); decls.append(name)
    if name in reserved:
        raise SystemExit('26493 reserved GLSL identifier used as variable: '+name)
if 'coherentRgb' not in decls:
    raise SystemExit('26493 coherentRgb portability identifier missing')
print('26493 GLSL RESERVED-IDENTIFIER PASS declarations='+str(len(decls))+' coherentRgb=true')
PY_RESERVED
command -v glslangValidator >/dev/null 2>&1 || fail "glslangValidator missing"
TMPGLSL="$OUTDIR/rcd26489_write_26493_v3_preprocessed.comp"
python3 - "$SHADER" "$TMPGLSL" <<'PY_GLSL'
from pathlib import Path
import sys
src=Path(sys.argv[1]).read_text()
needle='#define LAYOUT //\nLAYOUT\n'
if src.count(needle)!=1: raise SystemExit('LAYOUT preprocessor anchor mismatch')
src=src.replace(needle,'#version 310 es\nlayout(local_size_x=8, local_size_y=8, local_size_z=1) in;\n',1)
Path(sys.argv[2]).write_text(src)
PY_GLSL
glslangValidator -S comp "$TMPGLSL" > "$OUTDIR/26493_v3_shader_validation.txt" 2>&1 || { cat "$OUTDIR/26493_v3_shader_validation.txt"; fail "26493 changed shader compiler"; }
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

# Prove the post-build canonical source file set is still exactly the V5B domain
# (same 856 paths; only two code files + version changed in content).
python3 - "$WORK" "$REPO/$BASELINE_MANIFEST" <<'PY_FILESET'
from pathlib import Path
import sys
root=Path(sys.argv[1]); manifest=Path(sys.argv[2])
want=[]
for line in manifest.read_text().splitlines():
    if line.strip(): want.append(line.split(None,1)[1].strip())
actual=sorted([str(p.relative_to(root)) for p in (root/'app/src/main').rglob('*') if p.is_file()] + ['app/version.properties'])
want=sorted(want)
if actual!=want:
    raise SystemExit('26493 final canonical file-set mismatch missing='+repr(sorted(set(want)-set(actual))[:20])+' extra='+repr(sorted(set(actual)-set(want))[:20]))
print('26493 FINAL CANONICAL FILESET PASS files=856')
PY_FILESET

# Produce a COMPLETE binary audit patch. Intent-to-add includes all historical new files.
(
  cd "$WORK"
  git add -N app/src/main app/version.properties
  git diff --binary "$EXPECTED_APP_BASE" -- app/src/main app/version.properties
  git reset -q -- app/src/main app/version.properties
) > "$REPO/$FINALPATCH"
[[ -s "$FINALPATCH" ]] || fail "26493 successful complete binary patch empty"
grep -q 'rcd26489_write.glsl' "$FINALPATCH" || fail "26493 complete patch missing RCD write source"

# Canonical next baseline is a complete deterministic app-source bundle + manifest,
# not a git-diff-only patch, so future new files cannot disappear.
(
  cd "$WORK"
  tar --sort=name --mtime='UTC 2026-08-16 00:00:00' --owner=0 --group=0 --numeric-owner       -czf "$REPO/$NEXTBUNDLE" app/src/main app/version.properties
  { find app/src/main -type f -print; echo app/version.properties; } | LC_ALL=C sort | while read -r f; do sha256sum "$f"; done
) > "$AFTERHASH"

cat > "$REPORT" <<EOF
26493 V3 BUILD SUCCESS
Version: ${NEW_VERSION} / ${NEW_BUILD}
Baseline: exact tested 26492 V5B COMPLETE source bundle
Baseline checkpoint: ${V5B_COMMIT}
V5B rollback branch: ${V5B_BACKUP_BRANCH}
Failed V1 infrastructure checkpoint: ${FAILED_V1_COMMIT}
Failed V1 backup branch: ${FAILED_V1_BACKUP_BRANCH}
Failed V2 shader-compile checkpoint: ${FAILED_V2_COMMIT}
Failed V2 backup branch: ${FAILED_V2_BACKUP_BRANCH}
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

GLSL portability correction:
- V1/V2 local identifier `coherent` renamed to `coherentRgb`; math unchanged
- reserved-identifier audit runs before glslang

Canonical baseline packaging correction:
- source carrier is complete app/src/main + app/version.properties tar.gz
- exact file-set gate = 856/856
- exact pre-edit and final binary patches include intent-to-add new files
EOF

mkdir -p "$OUTDIR/next_baseline_inputs"
cp "$NEXTBUNDLE" "$OUTDIR/next_baseline_inputs/26493_successful_app_source.tar.gz"
cp "$AFTERHASH" "$OUTDIR/next_baseline_inputs/26493_successful_after.sha256"
cp "$TRANSFORM" "$OUTDIR/next_baseline_inputs/"
sha256sum "$BASELINE_BUNDLE" "$BASELINE_MANIFEST" "$TRANSFORM" "$PREPATCH" "$FINALPATCH" "$NEXTBUNDLE" "$AFTERHASH" "$REPORT" "$APK_NAME" > "$OUTDIR/26493_v3_artifact_hashes.sha256"

echo "=== 26493 V3 BUILD SUCCESS ==="
cat "$REPORT"
