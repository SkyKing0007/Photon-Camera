#!/usr/bin/env bash
set -euo pipefail
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }

ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
SUCCESSFUL_26512_HEAD="0c44699978a5e719b67e541bc73bc2bdb8ff671c"
BACKUP_BRANCH="backup-26512-success-before-26513-20260819"
BASE_BUILDER="$ROOT/build_26512_direct_26507_mgc1271_spatial_parity.sh"
BASE_BUILDER_SHA="e4cae018f5fa19be80016c44b153b6110e5a8de47b191a9aef44fadc1dc7ca87"
BASE_HANDOFF="$ROOT/26512_HANDOFF_HASHES.sha256"
APPLY_26513="$ROOT/apply_26513_mgc_native_detail_output_completion.py"
VALIDATE_26513="$ROOT/validate_26513_mgc_native_detail_output_completion.py"
OUT="$ROOT/build_26513_mgc_native_detail_output_completion_outputs"
PREOUT="$ROOT/.build_26513_handoff_preflight"
DERIVED="$ROOT/.build_26513_derived_from_exact_26512.sh"
VERSION_NAME="0.9726513"
VERSION_BUILD="26513"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-mgc-native-detail-output-completion-debug.apk"

rm -rf "$PREOUT"; mkdir -p "$PREOUT"
exec > >(tee "$PREOUT/26513_handoff_prebuild.log") 2>&1

echo "=== 26513 GATE 0: successful-26512 checkpoint / backup / handoff identities ==="
BRANCH="$(git branch --show-current)"; START_HEAD="$(git rev-parse HEAD)"
[[ "$BRANCH" == "$EXPECTED_BRANCH" && "$BRANCH" != "dev" ]] || fail "wrong/protected branch $BRANCH"
git merge-base --is-ancestor "$SUCCESSFUL_26512_HEAD" HEAD || fail "26513 handoff is not descended from successful 26512"
REMOTE_BACKUP="$(git ls-remote origin "refs/heads/$BACKUP_BRANCH" | awk '{print $1}')"
[[ "$REMOTE_BACKUP" == "$SUCCESSFUL_26512_HEAD" ]] || fail "backup missing/wrong: $BACKUP_BRANCH -> ${REMOTE_BACKUP:-MISSING}; expected $SUCCESSFUL_26512_HEAD"
for f in "$BASE_BUILDER" "$BASE_HANDOFF" "$APPLY_26513" "$VALIDATE_26513"; do
  [[ -f "$f" ]] || fail "missing $(basename "$f")"
done
[[ "$(sha "$BASE_BUILDER")" == "$BASE_BUILDER_SHA" ]] || fail "successful 26512 builder hash drift"
sha256sum -c "$BASE_HANDOFF"
python3 -m py_compile "$APPLY_26513" "$VALIDATE_26513"

PROTECTED_DRIFT="$PREOUT/26513_protected_build_infrastructure_drift.txt"
git diff --name-only "$SUCCESSFUL_26512_HEAD"..HEAD -- \
  gradlew gradlew.bat gradle build.gradle settings.gradle gradle.properties \
  app/build.gradle app/proguard-rules.pro > "$PROTECTED_DRIFT"
[[ ! -s "$PROTECTED_DRIFT" ]] || { cat "$PROTECTED_DRIFT" >&2; fail "protected Gradle/build infrastructure drifted after successful 26512"; }
pass "successful 26512 checkpoint + one backup + exact 26512 handoff verified"

echo "=== 26513 GATE 1: derive build only from the exact successful 26512 constructor ==="
python3 - "$BASE_BUILDER" "$DERIVED" "$SUCCESSFUL_26512_HEAD" "$BACKUP_BRANCH" "$APPLY_26513" "$VALIDATE_26513" <<'PYDERIVE'
from pathlib import Path
import sys
src_path, dst_path, head, backup, apply_script, validate_script = map(Path, sys.argv[1:])
# head/backup are Path only to preserve argv count; stringify immediately.
head=str(head); backup=str(backup); apply_script=str(apply_script); validate_script=str(validate_script)
s=src_path.read_text()

def one(old,new,label):
    global s
    n=s.count(old)
    if n != 1:
        raise SystemExit(f'{label}: expected exactly one anchor, found {n}')
    s=s.replace(old,new,1)

one('OUT="$ROOT/build_26512_direct_26507_mgc1271_spatial_parity_outputs"',
    'OUT="$ROOT/build_26513_mgc_native_detail_output_completion_outputs"','OUT path')
one('WORK="$ROOT/.build_26512_direct_26507_mgc1271_spatial_parity_work"',
    'WORK="$ROOT/.build_26513_mgc_native_detail_output_completion_work"','WORK path')
one('AFTER="$WORK/candidate26512"','AFTER="$WORK/candidate26513"','candidate path')
one('REJECTED_26511_HEAD="9d4fecd69a0b3549f3599f2efb07ad2c8fd740fe"',
    f'SUCCESSFUL_26512_HEAD="{head}"','base checkpoint')
one('BACKUP_BRANCH="backup-26511-rejected-before-26512-20260819"',
    f'BACKUP_BRANCH="{backup}"','backup branch')
one('VERSION_NAME="0.9726512"','VERSION_NAME="0.9726513"','version name')
one('VERSION_BUILD="26512"','VERSION_BUILD="26513"','version build')
one('FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-mgc1271-spatial-parity-debug.apk"',
    'FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-mgc-native-detail-output-completion-debug.apk"','final APK')
one('exec > >(tee "$OUT/26512_build.log") 2>&1',
    'exec > >(tee "$OUT/26513_build.log") 2>&1','build log')
one('git merge-base --is-ancestor "$REJECTED_26511_HEAD" HEAD || fail "handoff is not descended from rejected 26511 checkpoint"',
    'git merge-base --is-ancestor "$SUCCESSFUL_26512_HEAD" HEAD || fail "handoff is not descended from successful 26512 checkpoint"','ancestor gate')
one('[[ "$REMOTE_BACKUP" == "$REJECTED_26511_HEAD" ]] || fail "backup missing/wrong: $BACKUP_BRANCH -> ${REMOTE_BACKUP:-MISSING}"',
    '[[ "$REMOTE_BACKUP" == "$SUCCESSFUL_26512_HEAD" ]] || fail "backup missing/wrong: $BACKUP_BRANCH -> ${REMOTE_BACKUP:-MISSING}"','backup gate')
one('git diff --name-only "$REJECTED_26511_HEAD"..HEAD --',
    'git diff --name-only "$SUCCESSFUL_26512_HEAD"..HEAD --','protected drift base')
one('pass "GATE 1 exact rejected-26511 backup + direct successful-26507 identities"',
    'pass "GATE 1 successful-26512 backup proven; exact 26507 + pinned-MGC constructor retained"','gate1 label')

# Add the 26513 deterministic transform/validator to the exact-file gate.
anchor='for f in "$SOURCE_TAR" "$SOURCE_MANIFEST" "$DELTA_PATCH" "$VALIDATOR" "$IMPORTER" "$SHADER_PREFLIGHT" "$BJZHOU_NATIVE_MANIFEST" "$BJZHOU_COMMIT_FILE"; do'
one(anchor,
    anchor.replace('; do',' "$APPLY_26513" "$VALIDATE_26513"; do'),
    '26513 helper file gate')
# Inject variables beside the exact 26512 importer/validator ownership.
one('SHADER_PREFLIGHT="$ROOT/preflight_mgc1271_embedded_shaders.py"',
    'SHADER_PREFLIGHT="$ROOT/preflight_mgc1271_embedded_shaders.py"\nAPPLY_26513="'+apply_script+'"\nVALIDATE_26513="'+validate_script+'"',
    '26513 helper vars')

inject='''pass "GATE 4 exact pinned 1.27.1 Spatial source/native closure imported"\n\necho "=== GATE 4.5: derive 26513 from the now-proven successful-26512 runtime ==="\nBASE26512="$WORK/golden26512"\nrm -rf "$BASE26512"; mkdir -p "$BASE26512"\ncp -a "$AFTER/." "$BASE26512/"\nPATCH26513="$OUT/26513_RUNTIME_DELTA_FROM_GOLDEN_26512.patch"\nPATCH26513_SHA="$OUT/26513_RUNTIME_DELTA_FROM_GOLDEN_26512.patch.sha256"\npython3 "$APPLY_26513" "$AFTER" --patch-out "$PATCH26513" --patch-sha-out "$PATCH26513_SHA"\n( cd "$OUT" && sha256sum -c "$(basename "$PATCH26513_SHA")" )\npython3 "$VALIDATE_26513" --base "$BASE26512" --candidate "$AFTER" --apply-script "$APPLY_26513"\npass "GATE 4.5 golden 26512 -> exact four-path 26513 transform; rollback patch existed before writes"'''
one('pass "GATE 4 exact pinned 1.27.1 Spatial source/native closure imported"',inject,'26513 gate 4.5')

# Rename only derived-build proof outputs that otherwise misleadingly say 26512.
for old,new in (
 ('26512_pre_gradle_audited_runtime.sha256','26513_pre_gradle_audited_runtime.sha256'),
 ('26512_post_gradle_audited_runtime.sha256','26513_post_gradle_audited_runtime.sha256'),
 ('26512_gradle_runtime_source_diff.txt','26513_gradle_runtime_source_diff.txt'),
 ('Gradle preserved audited 26512 runtime source','Gradle preserved audited 26513 runtime source'),
 ('26512_arm64_mgc_symbols.txt','26513_arm64_mgc_symbols.txt'),
 ('26512_armv7_stub_symbols.txt','26513_armv7_stub_symbols.txt'),
 ('26512_APK.sha256','26513_APK.sha256'),
 ('26512_successful_app_source.tar.gz','26513_candidate_app_source.tar.gz'),
 ('26512_successful_source.sha256','26513_candidate_source.sha256'),
 ('GATE 6 exactly one 26512 APK built from successful 26507 + exact pinned MGC 1.27.1 owner',
  'GATE 6 exactly one 26513 APK built from golden 26512 with bounded detail/output transform'),
 ('26512 complete: exact 1.27.1 MGC Fusion/Spatial RGB/Bento/Long/noise/default-denoise owner inside unchanged 26507 capture/post shell',
  '26513 complete: golden 26512 MGC/color/highlight/UHDR architecture retained; bounded RGB footprint + Motion output completion only'),
):
    s=s.replace(old,new)

# Add post-build proof that the actual DEX contains the two user-visible runtime changes.
post_anchor='sha256sum "$FINAL" > "$OUT/26513_APK.sha256"'
post='''python3 - "$FINAL" <<'PYAPK26513'\nimport sys,zipfile\nwith zipfile.ZipFile(sys.argv[1]) as z:\n    names=set(z.namelist())\n    dex=b''.join(z.read(n) for n in sorted(names) if n.endswith('.dex'))\n    for marker in (b'IRIS_26513_JPEG_COMPLETION_AFTER_SAVE',b'roughnessSampling=12x8_local_neighbors',b'fullImageRoughnessScan=false'):\n        assert marker in dex,('missing 26513 DEX marker',marker)\n    assert b'IRIS_26512_MGC1271_PARITY_VALID' in dex\n    assert b'SPATIAL_DEFAULT' in dex\n    assert b'IRIS_26509_' not in dex and b'IRIS_26510_' not in dex and b'IRIS_26511_' not in dex\nprint('PASS: APK proves 26513 completion/diagnostic runtime while retaining 26512 MGC owner')\nPYAPK26513\n'''+post_anchor
one(post_anchor,post,'26513 APK proof')

dst_path.write_text(s)
PYDERIVE
chmod +x "$DERIVED"
bash -n "$DERIVED"
python3 - "$DERIVED" <<'PYPROOF'
from pathlib import Path
import sys
s=Path(sys.argv[1]).read_text()
for token in (
 'SUCCESSFUL_26512_HEAD="0c44699978a5e719b67e541bc73bc2bdb8ff671c"',
 'BACKUP_BRANCH="backup-26512-success-before-26513-20260819"',
 'VERSION_NAME="0.9726513"', 'VERSION_BUILD="26513"',
 'GATE 4.5: derive 26513 from the now-proven successful-26512 runtime',
 '26513_RUNTIME_DELTA_FROM_GOLDEN_26512.patch',
 'python3 "$VALIDATE_26513" --base "$BASE26512" --candidate "$AFTER" --apply-script "$APPLY_26513"',
):
    assert token in s, token
for bad in ('VERSION_NAME="0.9726512"','VERSION_BUILD="26512"','REJECTED_26511_HEAD='):
    assert bad not in s,bad
print('PASS: derived builder identities/version/golden-base gates are correct')
PYPROOF
sha256sum "$DERIVED" > "$PREOUT/26513_DERIVED_BUILDER.sha256"
pass "exact 26512 constructor transformed deterministically for 26513"

echo "=== 26513 GATE 2: execute version increment + build in the same guarded constructor ==="
"$DERIVED"
[[ -f "$FINAL" ]] || fail "expected 26513 APK missing: $FINAL"
mkdir -p "$OUT"
cp "$PREOUT/26513_handoff_prebuild.log" "$OUT/26513_handoff_prebuild.log"
cp "$PREOUT/26513_protected_build_infrastructure_drift.txt" "$OUT/26513_protected_build_infrastructure_drift.txt"
cp "$PREOUT/26513_DERIVED_BUILDER.sha256" "$OUT/26513_DERIVED_BUILDER.sha256"
sha256sum "$FINAL" > "$OUT/26513_FINAL_APK.sha256"
echo "=== 26513 SUCCESS ==="
echo "APK: $(basename "$FINAL")"
echo "APK SHA256: $(sha "$FINAL")"
echo "START_HEAD=$START_HEAD"
echo "GOLDEN_26512_HEAD=$SUCCESSFUL_26512_HEAD"
pass "26513 handoff/build complete"
