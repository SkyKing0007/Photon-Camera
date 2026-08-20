#!/usr/bin/env bash
set -euo pipefail
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }

ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
SUCCESSFUL_26514_HANDOFF_HEAD="e9855a3af7a79801a762ec3f99b441474926f009"
BACKUP_26514="backup-26514-before-26515-short-bento-fix-20260820"
BASE_26514_BUILDER="$ROOT/build_26514_iris_profiles_controls.sh"
BASE_26514_BUILDER_SHA="0402e9b2a6793cd8a81161f4e4e380adf5c79c0b4309d8a873912c387ee8fbf4"
BASE_26514_HANDOFF="$ROOT/26514_HANDOFF_HASHES.sha256"
APPLY_26515="$ROOT/apply_26515_short_bento_exposure_domain.py"
VALIDATE_26515="$ROOT/validate_26515_short_bento_exposure_domain.py"
PATCH_DERIVED="$ROOT/patch_26515_derived_builder.py"
HANDOFF_26515="$ROOT/26515_HANDOFF_HASHES.sha256"
OUT="$ROOT/build_26515_short_bento_exposure_domain_outputs"
PREOUT="$ROOT/.build_26515_short_bento_preflight"
OUTER="$ROOT/.build_26515_outer_from_exact_26514_handoff.sh"
VERSION_NAME="0.9726515"
VERSION_BUILD="26515"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-short-bento-domain-fix-debug.apk"

rm -rf "$PREOUT"; mkdir -p "$PREOUT"
exec > >(tee "$PREOUT/26515_handoff_prebuild.log") 2>&1

echo "=== 26515 GATE 0: exact 26514 handoff checkpoint + backup + no runtime drift ==="
BRANCH="$(git branch --show-current)"; START_HEAD="$(git rev-parse HEAD)"
[[ "$BRANCH" == "$EXPECTED_BRANCH" && "$BRANCH" != "dev" ]] || fail "wrong/protected branch $BRANCH"
git merge-base --is-ancestor "$SUCCESSFUL_26514_HANDOFF_HEAD" HEAD || fail "26515 handoff is not descended from exact 26514 handoff HEAD"
REMOTE_BACKUP="$(git ls-remote origin "refs/heads/$BACKUP_26514" | awk '{print $1}')"
[[ "$REMOTE_BACKUP" == "$SUCCESSFUL_26514_HANDOFF_HEAD" ]] || fail "backup missing/wrong: $BACKUP_26514 -> ${REMOTE_BACKUP:-MISSING}; expected $SUCCESSFUL_26514_HANDOFF_HEAD"
for f in "$BASE_26514_BUILDER" "$BASE_26514_HANDOFF" "$APPLY_26515" "$VALIDATE_26515" "$PATCH_DERIVED" "$HANDOFF_26515"; do
  [[ -f "$f" ]] || fail "missing $(basename "$f")"
done
[[ "$(sha "$BASE_26514_BUILDER")" == "$BASE_26514_BUILDER_SHA" ]] || fail "26514 builder hash drift"
sha256sum -c "$BASE_26514_HANDOFF"
sha256sum -c "$HANDOFF_26515"
python3 -m py_compile "$APPLY_26515" "$VALIDATE_26515" "$PATCH_DERIVED"

# This commit may contain only the 26515 handoff package. Runtime source is reconstructed and
# modified only inside the disposable audited candidate during this build.
DRIFT="$PREOUT/26515_committed_drift_after_26514_handoff.txt"
git diff --name-only "$SUCCESSFUL_26514_HANDOFF_HEAD"..HEAD > "$DRIFT"
python3 - "$DRIFT" <<'PYDRIFT'
from pathlib import Path
import sys
allowed={
 'apply_26515_short_bento_exposure_domain.py',
 'validate_26515_short_bento_exposure_domain.py',
 'patch_26515_derived_builder.py',
 'build_26515_short_bento_exposure_domain.sh',
 '26515_BASE_26514_COMMIT.txt',
 '26515_README_UPLOAD.txt',
 '26515_HANDOFF_HASHES.sha256',
 '.github/workflows/build-26515-short-bento-domain.yml',
}
seen={x.strip() for x in Path(sys.argv[1]).read_text().splitlines() if x.strip()}
extra=seen-allowed
if extra: raise SystemExit('unexpected committed drift after 26514: '+', '.join(sorted(extra)))
print('PASS: committed delta after 26514 is handoff-only')
PYDRIFT
pass "exact 26514 handoff HEAD, exact backup and no committed runtime drift verified"

echo "=== 26515 GATE 1: derive exact 26514 constructor, then insert one validated 26515 delta before its only Gradle build ==="
cp "$BASE_26514_BUILDER" "$OUTER"
python3 - "$OUTER" "$PATCH_DERIVED" <<'PYOUTER'
from pathlib import Path
import sys
p=Path(sys.argv[1]); patcher=Path(sys.argv[2]).resolve(); s=p.read_text()

def one(old,new,label):
    global s
    n=s.count(old)
    if n!=1: raise SystemExit(f'{label}: expected one anchor, found {n}')
    s=s.replace(old,new,1)

one('OUT="$ROOT/build_26514_iris_profiles_controls_outputs"',
    'OUT="$ROOT/build_26515_short_bento_exposure_domain_outputs"','outer OUT')
one('PREOUT="$ROOT/.build_26514_handoff_preflight"',
    'PREOUT="$ROOT/.build_26515_short_bento_preflight"','outer PREOUT')
one('DERIVED="$ROOT/.build_26514_derived_from_exact_26512.sh"',
    'DERIVED="$ROOT/.build_26515_derived_from_exact_26512.sh"','outer DERIVED')
one('VERSION_NAME="0.9726514"','VERSION_NAME="0.9726515"','outer version name')
one('VERSION_BUILD="26514"','VERSION_BUILD="26515"','outer version build')
one('FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-iris-profiles-controls-debug.apk"',
    'FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-short-bento-domain-fix-debug.apk"','outer final')
# Patch the already-proved inner 26514 constructor only after its built-in lineage proof, then run it once.
one('\n"$DERIVED"\n',
    '\npython3 "'+str(patcher)+'" "$DERIVED"\nbash -n "$DERIVED"\nsha256sum "$DERIVED" > "$PREOUT/26515_EXECUTED_DERIVED_BUILDER.sha256"\n"$DERIVED"\n',
    'outer execution hook')
one('[[ -f "$FINAL" ]] || fail "expected 26514 APK missing: $FINAL"',
    '[[ -f "$FINAL" ]] || fail "expected 26515 APK missing: $FINAL"','outer final check')
one('sha256sum "$FINAL" > "$OUT/26514_FINAL_APK.sha256"',
    'sha256sum "$FINAL" > "$OUT/26515_FINAL_APK.sha256"','outer final SHA')
one('echo "=== 26514 SUCCESS ==="','echo "=== 26515 SUCCESS ==="','outer success label')
one('pass "26514 handoff/build complete"','pass "26515 Short/Bento exposure-domain fix build complete"','outer final pass')
p.write_text(s)
PYOUTER
chmod +x "$OUTER"
bash -n "$OUTER"
sha256sum "$OUTER" > "$PREOUT/26515_OUTER_CONSTRUCTOR.sha256"
pass "26515 outer constructor derived without modifying repository runtime source"

echo "=== 26515 GATE 2: version increment + single APK build in the same guarded command ==="
"$OUTER"
[[ -f "$FINAL" ]] || fail "expected 26515 APK missing: $FINAL"
mkdir -p "$OUT"
cp "$PREOUT/26515_handoff_prebuild.log" "$OUT/26515_handoff_prebuild.log"
cp "$PREOUT/26515_committed_drift_after_26514_handoff.txt" "$OUT/26515_committed_drift_after_26514_handoff.txt"
cp "$PREOUT/26515_OUTER_CONSTRUCTOR.sha256" "$OUT/26515_OUTER_CONSTRUCTOR.sha256"
[[ -f "$PREOUT/26515_EXECUTED_DERIVED_BUILDER.sha256" ]] && cp "$PREOUT/26515_EXECUTED_DERIVED_BUILDER.sha256" "$OUT/26515_EXECUTED_DERIVED_BUILDER.sha256"
sha256sum "$FINAL" > "$OUT/26515_FINAL_APK.sha256"
cat > "$OUT/26515_SHORT_BENTO_FIX_PROOF.txt" <<EOF
START_HEAD=$START_HEAD
BASE_26514_HANDOFF_HEAD=$SUCCESSFUL_26514_HANDOFF_HEAD
BACKUP_26514=$BACKUP_26514
VERSION_NAME=$VERSION_NAME
VERSION_BUILD=$VERSION_BUILD
APK=$(basename "$FINAL")
APK_SHA256=$(sha "$FINAL")
FIX=accepted Short retained; MGC BaselineExposure restored as source-domain gain after MGC denoise; Photon display/sceneWhite authority remains reference-only; prior UHDR gain-map ceiling preserved
EOF

echo "=== 26515 HANDOFF SUCCESS ==="
echo "APK: $(basename "$FINAL")"
echo "APK SHA256: $(sha "$FINAL")"
pass "26515 direct corrective build complete"
