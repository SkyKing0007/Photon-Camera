#!/usr/bin/env bash
set -euo pipefail

EXPECTED_BRANCH="experimental-clean-photon-rebuild"
PROTECTED_HEAD="cd3aecad42726c3efe42de616762b1a778441b5e"
EXPECTED_APP_BASE="8233415edf738bf35c0fe1c4907f5dfe51de31a4"
BACKUP_BRANCH="backup-26475-v3-before-runtime-shader-portability"
BACKUP_TARGET="f6ec8a90f392a9c2374a2496b7b6b0c206750450"
PRECURSOR_SCRIPT="build_26475_wronski_source_fidelity_performance_v3.sh"
PRECURSOR_BLOB="727177946efe7ef96c25b3c44be304a998c1e1c8"

OLD_VERSION="0.9726475"
OLD_BUILD="26475"
NEW_VERSION="0.9726476"
NEW_BUILD="26476"
OUTDIR="build_26476_outputs"
APK_NAME="IrisCamera-${NEW_VERSION}-${NEW_BUILD}-wronski-runtime-shader-portability-debug.apk"

fail(){ echo "FAIL: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }

rm -rf "$OUTDIR"
mkdir -p "$OUTDIR"
AUDIT="$OUTDIR/26476_source_audit.txt"
REPORT="$OUTDIR/26476_build_report.txt"
PREPATCH="$OUTDIR/26476_pre_edit_binary.patch"
RECOVERY="$OUTDIR/26476_recovery_binary.patch"
SOURCEPATCH="$OUTDIR/26476_source.patch"
HASH_BEFORE="$OUTDIR/26476_before.sha256"
HASH_26475="$OUTDIR/26476_exact_26475.sha256"
HASH_AFTER="$OUTDIR/26476_after.sha256"
exec > >(tee "$AUDIT") 2>&1

echo "=== 26476 GUARDED WRONSKI RUNTIME SHADER PORTABILITY BUILD ==="
date -Iseconds || true

BRANCH="${GITHUB_REF_NAME:-$(git branch --show-current)}"
[[ "$BRANCH" == "$EXPECTED_BRANCH" ]] || fail "branch=$BRANCH expected=$EXPECTED_BRANCH"
pass "branch gate"

REMOTE_BACKUP="$(git ls-remote origin "refs/heads/$BACKUP_BRANCH" | awk '{print $1}')"
[[ "$REMOTE_BACKUP" == "$BACKUP_TARGET" ]] || fail "backup=$REMOTE_BACKUP expected=$BACKUP_TARGET"
pass "backup branch exact 26475 V3 infrastructure checkpoint"

git cat-file -e "$EXPECTED_APP_BASE^{commit}" || fail "missing verified app base"
git diff --quiet "$EXPECTED_APP_BASE" -- app/src/main app/version.properties || fail "app source changed before 26476"
pass "application source unchanged before 26476"

[[ -f "$PRECURSOR_SCRIPT" ]] || fail "missing $PRECURSOR_SCRIPT"
[[ "$(git hash-object "$PRECURSOR_SCRIPT")" == "$PRECURSOR_BLOB" ]] || fail "26475 V3 precursor blob mismatch"
pass "26475 V3 precursor exact"

# Required project safety rule: patch and hashes BEFORE any source modification.
git diff --binary "$EXPECTED_APP_BASE" -- app/src/main app/version.properties > "$PREPATCH"
find app/src/main -type f -print0 | sort -z | xargs -0 sha256sum > "$HASH_BEFORE"
sha256sum app/version.properties >> "$HASH_BEFORE"
pass "binary pre-edit patch created before source modification"
pass "initial protected hashes captured"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# Reproduce exact successful 26475 application transform, without Gradle.
PRECURSOR="$TMP/26475_transform_only.sh"
awk '/^rm -f \.\/\*\.apk$/ { exit } { print }' "$PRECURSOR_SCRIPT" > "$PRECURSOR"
python3 - "$PRECURSOR" "$TMP/26475_precursor_outputs" <<'PY_PRE'
from pathlib import Path
import sys
p=Path(sys.argv[1]); t=p.read_text()
old='OUTDIR="build_26475_outputs"'
new='OUTDIR="'+sys.argv[2]+'"'
if t.count(old)!=1:
    raise SystemExit("26475 precursor OUTDIR anchor count="+str(t.count(old)))
p.write_text(t.replace(old,new,1))
print("26475 precursor OUTDIR rewrite: PASS")
PY_PRE
chmod +x "$PRECURSOR"
bash -n "$PRECURSOR" || fail "26475 transform-only syntax"
bash "$PRECURSOR"

grep -q '^VERSION_NAME=0\.9726475$' app/version.properties || fail "26475 version name"
grep -q '^VERSION_BUILD=26475$' app/version.properties || fail "26475 version build"
for marker in \
 IRIS_26475_WRONSKI_BAYER_QUAD_ALIGNMENT_GUIDE \
 IRIS_26475_IPOL_ICA_FINE_ONLY_THREE_ITERATIONS \
 IRIS_26475_IPOL_ICA_REFERENCE_GRADIENT_PREP_ONCE \
 IRIS_26475_IPOL_ICA_REFERENCE_HESSIAN_PREP_ONCE \
 IRIS_26475_IPOL_RMAX8_REFERENCE_OWNERSHIP \
 IRIS_26475_IPOL_MC_EXACT_TABLE_CACHE \
 IRIS_26467_WRONSKI_REFERENCE_PREP_ONCE \
 IRIS_26472_WRONSKI_AUX_FIRST_ZERO_ACCUMULATOR \
 IRIS_26472_SDR_AUTHORITATIVE_UHDR_HEADROOM \
 IRIS_26470_UHDR_RENDER_GEOMETRY_AUTHORITY; do
  grep -Rqs "$marker" app/src/main || fail "26475 lineage missing $marker"
done
pass "exact successful 26475 V3 application lineage reproduced"

# Exact pre-26476 application snapshot: this is the authoritative protected
# comparison point for the narrow runtime portability modification.
find app/src/main -type f -print0 | sort -z | xargs -0 sha256sum > "$HASH_26475"
sha256sum app/version.properties >> "$HASH_26475"
pass "exact 26475 protected hashes captured before 26476 modification"

ALIGNJAVA="app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2WronskiAlignment.java"
GRAD="app/src/main/assets/shaders/motionv2/mfsr_ica_reference_gradient.glsl"
HESS="app/src/main/assets/shaders/motionv2/mfsr_ica_reference_hessian.glsl"
VERSION="app/version.properties"

mkdir -p "$TMP/candidate/$(dirname "$ALIGNJAVA")" "$TMP/candidate/$(dirname "$GRAD")" "$TMP/candidate/$(dirname "$VERSION")"
cp "$ALIGNJAVA" "$TMP/candidate/$ALIGNJAVA"
cp "$GRAD" "$TMP/candidate/$GRAD"
cp "$HESS" "$TMP/candidate/$HESS"
cp "$VERSION" "$TMP/candidate/$VERSION"

python3 - "$TMP/candidate" <<'PY_TRANSFORM'
from pathlib import Path
import sys
root=Path(sys.argv[1])

align=root/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2WronskiAlignment.java'
grad=root/'app/src/main/assets/shaders/motionv2/mfsr_ica_reference_gradient.glsl'
version=root/'app/version.properties'

a=align.read_text()
old='new GLFormat(GLFormat.DataType.FLOAT_32,2)'
new='new GLFormat(GLFormat.DataType.FLOAT_32,4)'
if a.count(old)!=1:
    raise SystemExit("26476 reference gradient Java carrier anchor count="+str(a.count(old)))
a=a.replace(old,new,1)
old_log='icaReferenceGradientPreparedOnce=true'
new_log='icaReferenceGradientPreparedOnce=true gradientCarrier=RGBA32F_RG_used'
if a.count(old_log)!=1:
    raise SystemExit("26476 reference gradient log anchor count="+str(a.count(old_log)))
a=a.replace(old_log,new_log,1)
align.write_text(a)

g=grad.read_text()
old_layout='layout(rg32f,binding=0) uniform highp writeonly image2D OutputGradient;'
new_layout='layout(rgba32f,binding=0) uniform highp writeonly image2D OutputGradient;'
if g.count(old_layout)!=1:
    raise SystemExit("26476 rg32f layout anchor count="+str(g.count(old_layout)))
g=g.replace(old_layout,new_layout,1)
marker='IRIS_26475_IPOL_ICA_REFERENCE_GRADIENT_PREP_ONCE'
if g.count(marker)!=1:
    raise SystemExit("26475 gradient marker count="+str(g.count(marker)))
g=g.replace(marker,
    marker + '\n * IRIS_26476_ADRENO_RGBA32F_GRADIENT_CARRIER_RG_ONLY',1)
grad.write_text(g)

v=version.read_text()
if v.count('VERSION_NAME=0.9726475')!=1 or v.count('VERSION_BUILD=26475')!=1:
    raise SystemExit("26475 version anchors not unique")
v=v.replace('VERSION_NAME=0.9726475','VERSION_NAME=0.9726476',1)
v=v.replace('VERSION_BUILD=26475','VERSION_BUILD=26476',1)
version.write_text(v)

print("26476 runtime shader portability transform: PASS")
PY_TRANSFORM

python3 - "$TMP/candidate" <<'PY_VALIDATE'
from pathlib import Path
import sys
root=Path(sys.argv[1])

align=(root/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2WronskiAlignment.java').read_text()
grad=(root/'app/src/main/assets/shaders/motionv2/mfsr_ica_reference_gradient.glsl').read_text()
hess=(root/'app/src/main/assets/shaders/motionv2/mfsr_ica_reference_hessian.glsl').read_text()
version=(root/'app/version.properties').read_text()

required=[
    ('align rgba carrier','new GLFormat(GLFormat.DataType.FLOAT_32,4)' in align),
    ('gradient rgba32f','layout(rgba32f,binding=0) uniform highp writeonly image2D OutputGradient;' in grad),
    ('runtime marker','IRIS_26476_ADRENO_RGBA32F_GRADIENT_CARRIER_RG_ONLY' in grad),
    ('gradient store unchanged','imageStore(OutputGradient,p,vec4(g,0.0,0.0));' in grad),
    ('hessian consumes rg','texelFetch(ReferenceGradient,p,0).rg' in hess),
    ('version name','VERSION_NAME=0.9726476' in version),
    ('version build','VERSION_BUILD=26476' in version),
]
for name,ok in required:
    if not ok: raise SystemExit("candidate validation failed: "+name)

if 'layout(rg32f' in grad:
    raise SystemExit("unsupported rg32f image carrier survived")
if 'new GLFormat(GLFormat.DataType.FLOAT_32,2)' in align:
    raise SystemExit("2-channel FLOAT32 gradient allocation survived")

# Exact math invariants: carrier padding only.
for invariant in [
    'refCircular(p+ivec2(1,0))-refCircular(p-ivec2(1,0))',
    'refCircular(p+ivec2(0,1))-refCircular(p-ivec2(0,1))',
]:
    if invariant not in grad:
        raise SystemExit("gradient math invariant missing: "+invariant)

print("candidate/source validation PASS")
print("Temporary-copy validation: PASS")
PY_VALIDATE

# Hard guard against the exact V2 Java-generation failure before real source is touched.
python3 - "$TMP/candidate/$ALIGNJAVA" <<'PY_JAVA_GUARD'
from pathlib import Path
import sys
t=Path(sys.argv[1]).read_text()
bad_patterns=[
    'icaReferenceGradientPreparedOnce=true + " gradientCarrier=',
    'gradientCarrier=RGBA32F_RG_used""',
]
for p in bad_patterns:
    if p in t:
        raise SystemExit("generated Java string syntax guard failed: "+p)
expected='" icaReferenceGradientPreparedOnce=true gradientCarrier=RGBA32F_RG_used"'
if expected not in t:
    raise SystemExit("generated Java log literal missing")
print("Generated Java log-string syntax guard: PASS")
PY_JAVA_GUARD

pass "candidate/source validation PASS"
pass "Temporary-copy validation: PASS"
pass "Generated Java log-string syntax guard PASS"

# Apply exact validated candidate only now.
cp "$TMP/candidate/$ALIGNJAVA" "$ALIGNJAVA"
cp "$TMP/candidate/$GRAD" "$GRAD"
cp "$TMP/candidate/$HESS" "$HESS"
cp "$TMP/candidate/$VERSION" "$VERSION"

grep -q 'IRIS_26476_ADRENO_RGBA32F_GRADIENT_CARRIER_RG_ONLY' "$GRAD" || fail "26476 portability marker missing"
grep -q 'layout(rgba32f,binding=0)' "$GRAD" || fail "rgba32f carrier missing"
! grep -q 'layout(rg32f' "$GRAD" || fail "rg32f carrier survived"
grep -q '^VERSION_NAME=0\.9726476$' "$VERSION" || fail "26476 version name"
grep -q '^VERSION_BUILD=26476$' "$VERSION" || fail "26476 version build"

# Protect every file except the three intentionally changed source/version files.
find app/src/main -type f -print0 | sort -z | xargs -0 sha256sum > "$HASH_AFTER"
sha256sum app/version.properties >> "$HASH_AFTER"

python3 - "$HASH_26475" "$HASH_AFTER" <<'PY_HASH'
from pathlib import Path
import sys

def read_hashes(path):
    out={}
    for line in Path(path).read_text().splitlines():
        if not line.strip():
            continue
        digest,name=line.split(None,1)
        out[name.strip()]=digest
    return out

before=read_hashes(sys.argv[1])
after=read_hashes(sys.argv[2])

expected_changed={
    'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2WronskiAlignment.java',
    'app/src/main/assets/shaders/motionv2/mfsr_ica_reference_gradient.glsl',
    'app/version.properties',
}

all_names=set(before)|set(after)
changed={name for name in all_names if before.get(name)!=after.get(name)}
if changed != expected_changed:
    raise SystemExit(
        "26476 protected hash scope mismatch; changed="
        + ",".join(sorted(changed))
        + " expected="
        + ",".join(sorted(expected_changed))
    )

# New Hessian shader is part of 26475 and must remain byte-identical.
hessian='app/src/main/assets/shaders/motionv2/mfsr_ica_reference_hessian.glsl'
if before.get(hessian) != after.get(hessian):
    raise SystemExit("26475 Hessian changed unexpectedly")

print("Protected-file hashes: PASS")
print("26476 exact narrow changed-file scope: PASS")
PY_HASH
pass "protected-file hashes PASS"
pass "26476 exact narrow changed-file scope PASS"

git diff --binary "$EXPECTED_APP_BASE" -- app/src/main app/version.properties > "$RECOVERY"
git diff "$EXPECTED_APP_BASE" -- app/src/main app/version.properties > "$SOURCEPATCH"

echo "PRE-BUILD SAFETY PROOF PASSED"
echo "  candidate/source validation PASS"
echo "  Temporary-copy validation: PASS"
echo "  exact 26475 V3 backup PASS"
echo "  exact 26475 V3 precursor PASS"
echo "  Wronski/IPOL gradient arithmetic unchanged PASS"
echo "  only carrier widened RG32F -> RGBA32F PASS"
echo "  Hessian/ICA consume .rg exactly as before PASS"
echo "  version/build increment in same script PASS"

cat > "$REPORT" <<EOF
26476 Wronski runtime shader portability
========================================
Protected checkpoint: $PROTECTED_HEAD
Backup: $BACKUP_BRANCH -> $BACKUP_TARGET
Build: $NEW_VERSION / $NEW_BUILD

Runtime failure addressed:
- new 26475 reference-gradient image carrier used RG32F.
- Adreno runtime shader creation failed before auxiliary processing.
- carrier is widened to RGBA32F; only R/G contain gx/gy.
- gradient arithmetic, Hessian arithmetic, ICA arithmetic and Wronski/IPOL
  constants remain unchanged.
EOF

rm -f ./*.apk
chmod +x ./gradlew
./gradlew assembleDebug --no-daemon

echo "BUILD SUCCESSFUL verified by Gradle return code" | tee -a "$REPORT"
mapfile -t apks < <(find app/build/outputs/apk/debug -maxdepth 1 -type f -name '*.apk' | sort)
[[ ${#apks[@]} -ge 1 ]] || fail "no debug APK found"
cp "${apks[0]}" "$APK_NAME"
[[ -s "$APK_NAME" ]] || fail "APK missing/empty"
sha="$(sha256sum "$APK_NAME" | awk '{print $1}')"
{
 echo "BUILD SUCCESS"
 echo "APK=$APK_NAME"
 echo "SHA256=$sha"
 echo "VERSION=$NEW_VERSION"
 echo "BUILD=$NEW_BUILD"
 echo "dev_untouched=true"
 echo "experimental_source_not_committed=true"
} | tee -a "$REPORT"
pass "26476 WRONSKI RUNTIME SHADER PORTABILITY BUILD SUCCESS"
