#!/usr/bin/env bash
set -euo pipefail
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }

ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
SUCCESSFUL_26513_HEAD="3601f39b8e4d7ebd4776edbcae6e56f4514eea54"
BACKUP_26513="backup-26513-success-before-26514-20260819"
SUCCESSFUL_26512_HEAD="0c44699978a5e719b67e541bc73bc2bdb8ff671c"
BACKUP_26512="backup-26512-success-before-26513-20260819"
BASE_BUILDER="$ROOT/build_26512_direct_26507_mgc1271_spatial_parity.sh"
BASE_BUILDER_SHA="e4cae018f5fa19be80016c44b153b6110e5a8de47b191a9aef44fadc1dc7ca87"
BASE_HANDOFF="$ROOT/26512_HANDOFF_HASHES.sha256"
HANDOFF_26513="$ROOT/26513_HANDOFF_HASHES.sha256"
APPLY_26513="$ROOT/apply_26513_mgc_native_detail_output_completion.py"
VALIDATE_26513="$ROOT/validate_26513_mgc_native_detail_output_completion.py"
APPLY_26514="$ROOT/apply_26514_iris_profiles_controls.py"
VALIDATE_26514="$ROOT/validate_26514_iris_profiles_controls.py"
OUT="$ROOT/build_26514_iris_profiles_controls_outputs"
PREOUT="$ROOT/.build_26514_handoff_preflight"
DERIVED="$ROOT/.build_26514_derived_from_exact_26512.sh"
VERSION_NAME="0.9726514"
VERSION_BUILD="26514"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-iris-profiles-controls-debug.apk"

rm -rf "$PREOUT"; mkdir -p "$PREOUT"
exec > >(tee "$PREOUT/26514_handoff_prebuild.log") 2>&1

echo "=== 26514 GATE 0: stable 26513 + one backup + exact handoff identities ==="
BRANCH="$(git branch --show-current)"; START_HEAD="$(git rev-parse HEAD)"
[[ "$BRANCH" == "$EXPECTED_BRANCH" && "$BRANCH" != "dev" ]] || fail "wrong/protected branch $BRANCH"
git merge-base --is-ancestor "$SUCCESSFUL_26513_HEAD" HEAD || fail "26514 handoff is not descended from successful 26513"
REMOTE_BACKUP="$(git ls-remote origin "refs/heads/$BACKUP_26513" | awk '{print $1}')"
[[ "$REMOTE_BACKUP" == "$SUCCESSFUL_26513_HEAD" ]] || fail "backup missing/wrong: $BACKUP_26513 -> ${REMOTE_BACKUP:-MISSING}; expected $SUCCESSFUL_26513_HEAD"
for f in "$BASE_BUILDER" "$BASE_HANDOFF" "$HANDOFF_26513" "$APPLY_26513" "$VALIDATE_26513" "$APPLY_26514" "$VALIDATE_26514"; do
  [[ -f "$f" ]] || fail "missing $(basename "$f")"
done
[[ "$(sha "$BASE_BUILDER")" == "$BASE_BUILDER_SHA" ]] || fail "successful 26512 builder hash drift"
sha256sum -c "$BASE_HANDOFF"
sha256sum -c "$HANDOFF_26513"
python3 -m py_compile "$APPLY_26513" "$VALIDATE_26513" "$APPLY_26514" "$VALIDATE_26514"

# Only handoff/build files may exist after the tested 26513 checkpoint; runtime/build infrastructure
# must still be the exact lineage that produced 26513.
RUNTIME_DRIFT="$PREOUT/26514_runtime_drift_after_successful_26513.txt"
git diff --name-only "$SUCCESSFUL_26513_HEAD"..HEAD -- app/src/main app/version.properties > "$RUNTIME_DRIFT"
[[ ! -s "$RUNTIME_DRIFT" ]] || { cat "$RUNTIME_DRIFT" >&2; fail "runtime source changed after successful 26513"; }
PROTECTED_DRIFT="$PREOUT/26514_protected_build_infrastructure_drift.txt"
git diff --name-only "$SUCCESSFUL_26513_HEAD"..HEAD -- \
  gradlew gradlew.bat gradle build.gradle settings.gradle gradle.properties \
  app/build.gradle app/proguard-rules.pro > "$PROTECTED_DRIFT"
[[ ! -s "$PROTECTED_DRIFT" ]] || { cat "$PROTECTED_DRIFT" >&2; fail "protected Gradle/build infrastructure changed after successful 26513"; }
pass "stable 26513 checkpoint, exact backup, no runtime drift, and prior audited handoffs verified"

echo "=== 26514 GATE 1: derive one build from exact 26512 constructor -> proven 26513 -> 26514 ==="
python3 - "$BASE_BUILDER" "$DERIVED" "$SUCCESSFUL_26512_HEAD" "$BACKUP_26512" \
  "$APPLY_26513" "$VALIDATE_26513" "$APPLY_26514" "$VALIDATE_26514" <<'PYDERIVE'
from pathlib import Path
import sys
src_path, dst_path = map(Path, sys.argv[1:3])
head, backup, apply13, validate13, apply14, validate14 = sys.argv[3:9]
s=src_path.read_text()

def one(old,new,label):
    global s
    n=s.count(old)
    if n != 1:
        raise SystemExit(f'{label}: expected exactly one anchor, found {n}')
    s=s.replace(old,new,1)

one('OUT="$ROOT/build_26512_direct_26507_mgc1271_spatial_parity_outputs"',
    'OUT="$ROOT/build_26514_iris_profiles_controls_outputs"','OUT path')
one('WORK="$ROOT/.build_26512_direct_26507_mgc1271_spatial_parity_work"',
    'WORK="$ROOT/.build_26514_iris_profiles_controls_work"','WORK path')
one('AFTER="$WORK/candidate26512"','AFTER="$WORK/candidate26514"','candidate path')
one('REJECTED_26511_HEAD="9d4fecd69a0b3549f3599f2efb07ad2c8fd740fe"',
    f'SUCCESSFUL_26512_HEAD="{head}"','base checkpoint')
one('BACKUP_BRANCH="backup-26511-rejected-before-26512-20260819"',
    f'BACKUP_BRANCH="{backup}"','constructor backup')
one('VERSION_NAME="0.9726512"','VERSION_NAME="0.9726514"','version name')
one('VERSION_BUILD="26512"','VERSION_BUILD="26514"','version build')
one('FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-mgc1271-spatial-parity-debug.apk"',
    'FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-iris-profiles-controls-debug.apk"','final APK')
one('exec > >(tee "$OUT/26512_build.log") 2>&1',
    'exec > >(tee "$OUT/26514_build.log") 2>&1','build log')
one('git merge-base --is-ancestor "$REJECTED_26511_HEAD" HEAD || fail "handoff is not descended from rejected 26511 checkpoint"',
    'git merge-base --is-ancestor "$SUCCESSFUL_26512_HEAD" HEAD || fail "handoff is not descended from successful 26512 checkpoint"','ancestor gate')
one('[[ "$REMOTE_BACKUP" == "$REJECTED_26511_HEAD" ]] || fail "backup missing/wrong: $BACKUP_BRANCH -> ${REMOTE_BACKUP:-MISSING}"',
    '[[ "$REMOTE_BACKUP" == "$SUCCESSFUL_26512_HEAD" ]] || fail "backup missing/wrong: $BACKUP_BRANCH -> ${REMOTE_BACKUP:-MISSING}"','backup gate')
one('git diff --name-only "$REJECTED_26511_HEAD"..HEAD --',
    'git diff --name-only "$SUCCESSFUL_26512_HEAD"..HEAD --','protected drift base')
one('pass "GATE 1 exact rejected-26511 backup + direct successful-26507 identities"',
    'pass "GATE 1 successful-26512 constructor identities retained for exact MGC reconstruction"','gate1 label')

# Both post-26512 transforms are explicit build inputs.
anchor='for f in "$SOURCE_TAR" "$SOURCE_MANIFEST" "$DELTA_PATCH" "$VALIDATOR" "$IMPORTER" "$SHADER_PREFLIGHT" "$BJZHOU_NATIVE_MANIFEST" "$BJZHOU_COMMIT_FILE"; do'
one(anchor, anchor.replace('; do',' "$APPLY_26513" "$VALIDATE_26513" "$APPLY_26514" "$VALIDATE_26514"; do'), 'helper file gate')
one('SHADER_PREFLIGHT="$ROOT/preflight_mgc1271_embedded_shaders.py"',
    'SHADER_PREFLIGHT="$ROOT/preflight_mgc1271_embedded_shaders.py"\n'
    f'APPLY_26513="{apply13}"\nVALIDATE_26513="{validate13}"\n'
    f'APPLY_26514="{apply14}"\nVALIDATE_26514="{validate14}"',
    'helper vars')

inject='''pass "GATE 4 exact pinned 1.27.1 Spatial source/native closure imported"\n\necho "=== GATE 4.5: reproduce exact tested 26513 from golden 26512 ==="\nBASE26512="$WORK/golden26512"\nrm -rf "$BASE26512"; mkdir -p "$BASE26512"\ncp -a "$AFTER/." "$BASE26512/"\nPATCH26513="$OUT/26513_RUNTIME_DELTA_FROM_GOLDEN_26512.patch"\nPATCH26513_SHA="$OUT/26513_RUNTIME_DELTA_FROM_GOLDEN_26512.patch.sha256"\npython3 "$APPLY_26513" "$AFTER" --patch-out "$PATCH26513" --patch-sha-out "$PATCH26513_SHA"\n( cd "$OUT" && sha256sum -c "$(basename "$PATCH26513_SHA")" )\npython3 "$VALIDATE_26513" --base "$BASE26512" --candidate "$AFTER" --apply-script "$APPLY_26513"\npass "GATE 4.5 exact tested 26513 candidate reconstructed"\n\necho "=== GATE 4.6: apply only 26514 Iris profile/denoise/presentation controls ==="\nBASE26513="$WORK/golden26513"\nrm -rf "$BASE26513"; mkdir -p "$BASE26513"\ncp -a "$AFTER/." "$BASE26513/"\nPATCH26514="$OUT/26514_RUNTIME_DELTA_FROM_GOLDEN_26513.patch"\nPATCH26514_SHA="$OUT/26514_RUNTIME_DELTA_FROM_GOLDEN_26513.patch.sha256"\npython3 "$APPLY_26514" "$AFTER" --patch-out "$PATCH26514" --patch-sha-out "$PATCH26514_SHA"\n( cd "$OUT" && sha256sum -c "$(basename "$PATCH26514_SHA")" )\npython3 "$VALIDATE_26514" --base "$BASE26513" --candidate "$AFTER" --apply-script "$APPLY_26514"\n# Compile the new standalone Iris fragment shader under the same pinned validator.\n{ echo '#version 300 es'; cat "$AFTER/app/src/main/assets/shaders/motionv2/iris_tone_controls.glsl"; } > "$WORK/iris26514_tone.frag"\nglslangValidator -S frag "$WORK/iris26514_tone.frag" > "$OUT/26514_iris_tone_glslang.txt"\npass "GATE 4.6 rollback patch existed before 26514 writes; exact golden-26513 delta validated"'''
one('pass "GATE 4 exact pinned 1.27.1 Spatial source/native closure imported"',inject,'26513 + 26514 gates')

# Include the new Kotlin source in the parser smoke; Gradle remains the authoritative type check.
one('kotlinc "$AFTER/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt" -d "$WORK/kotlin-smoke.jar"',
    'kotlinc "$AFTER/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt" "$AFTER/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNoiseProfileStore.kt" -d "$WORK/kotlin-smoke.jar"',
    'Kotlin smoke inputs')

for old,new in (
 ('26512_pre_gradle_audited_runtime.sha256','26514_pre_gradle_audited_runtime.sha256'),
 ('26512_post_gradle_audited_runtime.sha256','26514_post_gradle_audited_runtime.sha256'),
 ('26512_gradle_runtime_source_diff.txt','26514_gradle_runtime_source_diff.txt'),
 ('Gradle preserved audited 26512 runtime source','Gradle preserved audited 26514 runtime source'),
 ('26512_arm64_mgc_symbols.txt','26514_arm64_mgc_symbols.txt'),
 ('26512_armv7_stub_symbols.txt','26514_armv7_stub_symbols.txt'),
 ('26512_APK.sha256','26514_APK.sha256'),
 ('26512_successful_app_source.tar.gz','26514_candidate_app_source.tar.gz'),
 ('26512_successful_source.sha256','26514_candidate_source.sha256'),
 ('GATE 6 exactly one 26512 APK built from successful 26507 + exact pinned MGC 1.27.1 owner',
  'GATE 6 exactly one 26514 APK built from exact tested 26513 + Iris controls'),
 ('26512 complete: exact 1.27.1 MGC Fusion/Spatial RGB/Bento/Long/noise/default-denoise owner inside unchanged 26507 capture/post shell',
  '26514 complete: exact tested 26513 image architecture + strict Iris noise profiles/denoise/presentation controls'),
):
    s=s.replace(old,new)

post_anchor='sha256sum "$FINAL" > "$OUT/26514_APK.sha256"'
post='''python3 - "$FINAL" <<'PYAPK26514'\nimport sys,zipfile\nwith zipfile.ZipFile(sys.argv[1]) as z:\n    names=set(z.namelist())\n    dex=b''.join(z.read(n) for n in sorted(names) if n.endswith('.dex'))\n    for marker in (\n        b'IRIS_26512_MGC1271_PARITY_VALID',\n        b'IRIS_26513_JPEG_COMPLETION_AFTER_SAVE',\n        b'IRIS_26514_NOISE_AUTHORITY',\n        b'IRIS_26514_DENOISE',\n        b'IRIS_26514_PRESENTATION',\n        b'pref_iris_custom_noise_model',\n        b'pref_iris_exposure_ev',\n    ):\n        assert marker in dex,('missing 26514 DEX marker',marker)\n    for bad in (b'IRIS_26509_',b'IRIS_26510_',b'IRIS_26511_'):\n        assert bad not in dex,bad\nprint('PASS: APK proves 26512/26513 lineage plus 26514 strict controls')\nPYAPK26514\n'''+post_anchor
one(post_anchor,post,'26514 APK proof')

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
 'VERSION_NAME="0.9726514"', 'VERSION_BUILD="26514"',
 'GATE 4.5: reproduce exact tested 26513 from golden 26512',
 'GATE 4.6: apply only 26514 Iris profile/denoise/presentation controls',
 '26514_RUNTIME_DELTA_FROM_GOLDEN_26513.patch',
 'python3 "$VALIDATE_26514" --base "$BASE26513" --candidate "$AFTER" --apply-script "$APPLY_26514"',
):
    assert token in s, token
for bad in ('VERSION_NAME="0.9726512"','VERSION_BUILD="26512"','REJECTED_26511_HEAD='):
    assert bad not in s,bad
print('PASS: derived 26514 builder identities/version/lineage gates are correct')
PYPROOF
sha256sum "$DERIVED" > "$PREOUT/26514_DERIVED_BUILDER.sha256"
pass "one constructor now reproduces tested 26513 then applies only validated 26514 delta"

echo "=== 26514 GATE 2: version increment + build in the same guarded constructor ==="
"$DERIVED"
[[ -f "$FINAL" ]] || fail "expected 26514 APK missing: $FINAL"
mkdir -p "$OUT"
cp "$PREOUT/26514_handoff_prebuild.log" "$OUT/26514_handoff_prebuild.log"
cp "$PREOUT/26514_runtime_drift_after_successful_26513.txt" "$OUT/26514_runtime_drift_after_successful_26513.txt"
cp "$PREOUT/26514_protected_build_infrastructure_drift.txt" "$OUT/26514_protected_build_infrastructure_drift.txt"
cp "$PREOUT/26514_DERIVED_BUILDER.sha256" "$OUT/26514_DERIVED_BUILDER.sha256"
sha256sum "$FINAL" > "$OUT/26514_FINAL_APK.sha256"
echo "=== 26514 SUCCESS ==="
echo "APK: $(basename "$FINAL")"
echo "APK SHA256: $(sha "$FINAL")"
echo "START_HEAD=$START_HEAD"
echo "SUCCESSFUL_26513_HEAD=$SUCCESSFUL_26513_HEAD"
pass "26514 handoff/build complete"
