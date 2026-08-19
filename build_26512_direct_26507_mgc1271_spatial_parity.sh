#!/usr/bin/env bash
set -euo pipefail
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
ROOT="$(pwd)"
OUT="$ROOT/build_26512_direct_26507_mgc1271_spatial_parity_outputs"
WORK="$ROOT/.build_26512_direct_26507_mgc1271_spatial_parity_work"
BASE="$WORK/successful26507"
AFTER="$WORK/candidate26512"
BJ="$WORK/bjzhou1271"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
REJECTED_26511_HEAD="9d4fecd69a0b3549f3599f2efb07ad2c8fd740fe"
BACKUP_BRANCH="backup-26511-rejected-before-26512-20260819"
SOURCE_TAR="$ROOT/26507_successful_app_source.tar.gz"
SOURCE_TAR_SHA="3165a63224fc99652504113c312827b4af823eb643567f3678bfd938ad2c0082"
SOURCE_MANIFEST="$ROOT/26507_SUCCESSFUL_SOURCE.sha256"
DELTA_PATCH="$ROOT/26512_EXACT_ADAPTER_DELTA_FROM_SUCCESSFUL_26507.patch"
DELTA_PATCH_SHA="ee22bb4fea4662e16cf8718e8bbba5d454a654f3c2cb8b028a07a0904261dc5e"
VALIDATOR="$ROOT/validate_26512_mgc1271_spatial_parity.py"
IMPORTER="$ROOT/import_bjzhou_1271_spatial_parity.py"
SHADER_PREFLIGHT="$ROOT/preflight_mgc1271_embedded_shaders.py"
BJZHOU_HEAD="09c76e57e8f01a5a8fc536ab41fc80ba642d4042"
BJZHOU_NATIVE_MANIFEST="$ROOT/26507_BJZHOU_NATIVE_DEPENDENCIES.sha256"
BJZHOU_COMMIT_FILE="$ROOT/26507_BJZHOU_DEPENDENCY_COMMIT.txt"
VERSION_NAME="0.9726512"
VERSION_BUILD="26512"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-mgc1271-spatial-parity-debug.apk"
rm -rf "$OUT" "$WORK"; mkdir -p "$OUT" "$BASE" "$AFTER"
exec > >(tee "$OUT/26512_build.log") 2>&1

echo "=== GATE 1: branch / backup / direct-source identities ==="
BRANCH="$(git branch --show-current)"; START_HEAD="$(git rev-parse HEAD)"
[[ "$BRANCH" == "$EXPECTED_BRANCH" && "$BRANCH" != "dev" ]] || fail "wrong/protected branch $BRANCH"
git merge-base --is-ancestor "$REJECTED_26511_HEAD" HEAD || fail "handoff is not descended from rejected 26511 checkpoint"
REMOTE_BACKUP="$(git ls-remote origin "refs/heads/$BACKUP_BRANCH" | awk '{print $1}')"
[[ "$REMOTE_BACKUP" == "$REJECTED_26511_HEAD" ]] || fail "backup missing/wrong: $BACKUP_BRANCH -> ${REMOTE_BACKUP:-MISSING}"
PROTECTED_DRIFT="$OUT/protected_build_infrastructure_drift.txt"
git diff --name-only "$REJECTED_26511_HEAD"..HEAD --   gradlew gradlew.bat gradle build.gradle settings.gradle gradle.properties   app/build.gradle app/proguard-rules.pro > "$PROTECTED_DRIFT"
[[ ! -s "$PROTECTED_DRIFT" ]] || { cat "$PROTECTED_DRIFT" >&2; fail "protected build infrastructure drifted after backup"; }
for f in "$SOURCE_TAR" "$SOURCE_MANIFEST" "$DELTA_PATCH" "$VALIDATOR" "$IMPORTER" "$SHADER_PREFLIGHT" "$BJZHOU_NATIVE_MANIFEST" "$BJZHOU_COMMIT_FILE"; do [[ -f "$f" ]] || fail "missing $(basename "$f")"; done
[[ "$(sha "$SOURCE_TAR")" == "$SOURCE_TAR_SHA" ]] || fail "successful 26507 source archive hash mismatch"
[[ "$(sha "$DELTA_PATCH")" == "$DELTA_PATCH_SHA" ]] || fail "26512 adapter patch hash mismatch"
[[ "$(tr -d '\r\n' < "$BJZHOU_COMMIT_FILE")" == "$BJZHOU_HEAD" ]] || fail "bjzhou dependency commit proof mismatch"
python3 -m py_compile "$VALIDATOR" "$IMPORTER" "$SHADER_PREFLIGHT"
pass "GATE 1 exact rejected-26511 backup + direct successful-26507 identities"

echo "=== GATE 2: exact successful 26507 is sole Photon runtime base ==="
tar -xzf "$SOURCE_TAR" -C "$BASE"
( cd "$BASE" && sha256sum -c "$SOURCE_MANIFEST" ) > "$OUT/26507_successful_source_manifest_check.txt"
[[ "$(grep '^VERSION_NAME=' "$BASE/app/version.properties" | cut -d= -f2)" == "0.9726507" ]] || fail "source archive is not version 26507"
[[ "$(grep '^VERSION_BUILD=' "$BASE/app/version.properties" | cut -d= -f2)" == "26507" ]] || fail "source archive is not build 26507"
cp -a "$BASE/." "$AFTER/"
cp "$SOURCE_TAR" "$OUT/26512_PRECHANGE_EXACT_SUCCESSFUL_26507_SOURCE.tar.gz"
sha256sum "$OUT/26512_PRECHANGE_EXACT_SUCCESSFUL_26507_SOURCE.tar.gz" > "$OUT/26512_PRECHANGE_EXACT_SUCCESSFUL_26507_SOURCE.tar.gz.sha256"
pass "GATE 2 exact successful 26507 recovered"

echo "=== GATE 3: apply only frozen Photon adapter delta ==="
patch -s -d "$AFTER" -p1 < "$DELTA_PATCH"
python3 "$VALIDATOR" --base "$BASE" --candidate "$AFTER" --importer "$IMPORTER"
pass "GATE 3 exact 15-path Photon adapter delta"

echo "=== GATE 4: fetch and import pinned bjzhou 1.27.1 owned MGC subsystem ==="
rm -rf "$BJ"; git init -q "$BJ"; git -C "$BJ" remote add origin https://github.com/bjzhou/PhotonCamera.git
git -C "$BJ" config core.sparseCheckout true
mkdir -p "$BJ/.git/info"
cat > "$BJ/.git/info/sparse-checkout" <<'SPARSE'
/app/src/main/java/com/hinnka/mycamera/processor/
/app/src/main/java/com/hinnka/mycamera/camera/MultiFrameConfig.kt
/app/src/main/java/com/hinnka/mycamera/raw/MgcSpatialStrengthMap.kt
/app/src/main/java/com/hinnka/mycamera/raw/MgcFullResolutionDenoise.kt
/app/src/main/assets/mgc_denoise/
/app/src/main/cpp/mgc_denoise_static/
/app/src/main/cpp/mgc_strength_map_scaler.cpp
/app/src/main/cpp/libjpeg-turbo/
/app/src/main/cpp/libultrahdr/
/LICENSE
SPARSE
git -C "$BJ" fetch --depth=1 origin "$BJZHOU_HEAD"
git -C "$BJ" checkout -q --detach FETCH_HEAD
[[ "$(git -C "$BJ" rev-parse HEAD)" == "$BJZHOU_HEAD" ]] || fail "bjzhou 1.27.1 checkout drift"
THIRD="$AFTER/app/src/main/cpp/third_party_26507"; mkdir -p "$THIRD"
cp -a "$BJ/app/src/main/cpp/libjpeg-turbo" "$THIRD/libjpeg-turbo"
cp -a "$BJ/app/src/main/cpp/libultrahdr" "$THIRD/libultrahdr"
( cd "$THIRD" && sha256sum -c "$BJZHOU_NATIVE_MANIFEST" ) > "$OUT/26512_bjzhou_jpeg_ultrahdr_manifest_check.txt"
python3 "$IMPORTER" --upstream "$BJ" --candidate "$AFTER" --manifest "$OUT/26512_bjzhou1271_imported_source.sha256"
python3 "$VALIDATOR" --base "$BASE" --candidate "$AFTER" --importer "$IMPORTER" --upstream "$BJ"
echo "$BJZHOU_HEAD" > "$OUT/26512_bjzhou_dependency_commit.txt"
pass "GATE 4 exact pinned 1.27.1 Spatial source/native closure imported"

echo "=== GATE 5: shader/native/adapter pre-build proof ==="
command -v glslangValidator >/dev/null || fail "glslangValidator missing"
glsl_ver="$(glslangValidator --version | head -1)"
grep -F '16.5.0' <<<"$glsl_ver" >/dev/null || fail "wrong glslangValidator: $glsl_ver"
python3 "$SHADER_PREFLIGHT" --root "$AFTER" --validator glslangValidator | tee "$OUT/26512_mgc1271_glslang_preflight.txt"
# Java parser: syntax only, independent of Android classpath.
cat > "$WORK/JavaSyntaxCheck.java" <<'JAVACHECK'
import java.nio.file.*; import java.util.*; import javax.tools.*; import com.sun.source.util.JavacTask;
public class JavaSyntaxCheck { public static void main(String[] a)throws Exception{ JavaCompiler c=ToolProvider.getSystemJavaCompiler(); for(String s:a){ JavaFileObject f=new SimpleJavaFileObject(Path.of(s).toUri(),JavaFileObject.Kind.SOURCE){ public CharSequence getCharContent(boolean x)throws java.io.IOException{return Files.readString(Path.of(s));}}; JavacTask t=(JavacTask)c.getTask(null,null,d-> {},List.of("-proc:none"),null,List.of(f)); t.parse(); System.out.println("PASS Java parse "+s); } } }
JAVACHECK
javac "$WORK/JavaSyntaxCheck.java"
java -cp "$WORK" JavaSyntaxCheck  "$AFTER/app/src/main/java/com/particlesdevs/photoncamera/app/PhotonCamera.java"  "$AFTER/app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java"  "$AFTER/app/src/main/java/com/particlesdevs/photoncamera/processing/ImageFrame.java"  "$AFTER/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java"
# Kotlin syntax smoke check: unresolved Android symbols are expected without Android classpath;
# parse errors are not. Gradle below is the authoritative type check.
KOUT="$OUT/26512_kotlin_syntax_smoke.txt"
if command -v kotlinc >/dev/null; then
  set +e
  kotlinc "$AFTER/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt" -d "$WORK/kotlin-smoke.jar" >"$KOUT" 2>&1
  KRC=$?
  set -e
  if grep -E '(^|: )error: (expecting|unexpected tokens|unclosed)' "$KOUT" >/dev/null; then cat "$KOUT"; fail "Kotlin syntax smoke found parser error"; fi
  echo "kotlinc exit=$KRC (unresolved Android/project symbols are expected in standalone smoke)" >> "$KOUT"
else
  echo "kotlinc CLI unavailable; authoritative Gradle Kotlin compile follows in guarded build block" > "$KOUT"
fi
# Exact native capsule hashes before CMake.
[[ "$(sha "$AFTER/app/src/main/cpp/mgc1271_upstream/mgc_denoise_static/mgc_full_resolution_denoise_capsule.bin")" == "3ee5c92d2b830448de6270ec0c71ac64a484885a6bd7440d1c53f8695afc55ec" ]] || fail "denoise capsule hash mismatch"
[[ "$(sha "$AFTER/app/src/main/cpp/mgc1271_upstream/mgc_denoise_static/mgc_demoire_capsule.bin")" == "769d656725b445c356b9f3e44341e101806bb201fcd2e5681c0ab92173a68c9a" ]] || fail "demoire capsule hash mismatch"
grep -F '/* updateMotionV2ExposureAuthority(result); intentionally dormant */' "$AFTER/app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java" >/dev/null
cmp -s "$BASE/app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLTexture.java" "$AFTER/app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLTexture.java" || fail "global GLTexture changed"
cmp -s "$BASE/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java" "$AFTER/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java" || fail "old Wronski/MGC owner changed rather than bypassed"
echo "PRE-BUILD SAFETY PROOF PASSED"
pass "GATE 5 exact upstream shaders/native + protected 26507 authority proof"

echo "=== GATE 6: VERSION ${VERSION_NAME}/${VERSION_BUILD} + BUILD IN SAME GUARDED BLOCK ==="
python3 - "$AFTER/app/version.properties" "$VERSION_NAME" "$VERSION_BUILD" <<'PYVER'
from pathlib import Path
import sys
p=Path(sys.argv[1]); vn=sys.argv[2]; vb=sys.argv[3]; s=p.read_text()
assert 'VERSION_NAME=0.9726507' in s and 'VERSION_BUILD=26507' in s
s=s.replace('VERSION_NAME=0.9726507','VERSION_NAME='+vn).replace('VERSION_BUILD=26507','VERSION_BUILD='+vb)
p.write_text(s); t=p.read_text(); assert 'VERSION_NAME='+vn in t and 'VERSION_BUILD='+vb in t
PYVER
# Overlay only audited candidate onto checkout. Current 26511 runtime source is not a base.
rm -rf app/src/main
cp -a "$AFTER/app/src/main" app/src/main
cp "$AFTER/app/version.properties" app/version.properties

assert_cpp_deps_exact(){
  local phase="$1" expected actual
  if [[ "$phase" == "pre" ]]; then expected=$'.gitignore';
  else expected=$'.gitignore\narchive.h\narchive_entry.h\ntechnicallyflac.h\ntiny_dng_writer.h'; fi
  actual="$(find app/src/main/cpp/deps -mindepth 1 -maxdepth 1 -type f -printf '%f\n' | LC_ALL=C sort)"
  [[ "$actual" == "$expected" ]] || { printf 'Expected cpp/deps (%s):\n%s\nActual:\n%s\n' "$phase" "$expected" "$actual" >&2; fail "unexpected app/src/main/cpp/deps contents"; }
}
audited_runtime_manifest(){
  { find app/src/main -type f ! -path 'app/src/main/cpp/third_party_26507/*' ! -path 'app/src/main/cpp/deps/*' -print; echo app/src/main/cpp/deps/.gitignore; echo app/version.properties; } |
    LC_ALL=C sort | while read -r f; do sha256sum "$f"; done
}
assert_cpp_deps_exact pre
audited_runtime_manifest > "$OUT/26512_pre_gradle_audited_runtime.sha256"
chmod +x ./gradlew
./gradlew clean :app:assembleDebug --stacktrace
assert_cpp_deps_exact post
audited_runtime_manifest > "$OUT/26512_post_gradle_audited_runtime.sha256"
cmp -s "$OUT/26512_pre_gradle_audited_runtime.sha256" "$OUT/26512_post_gradle_audited_runtime.sha256" || { diff -u "$OUT/26512_pre_gradle_audited_runtime.sha256" "$OUT/26512_post_gradle_audited_runtime.sha256" > "$OUT/26512_gradle_runtime_source_diff.txt" || true; fail "Gradle mutated audited runtime source"; }
pass "Gradle preserved audited 26512 runtime source"

mapfile -t APKS < <(find app/build -type f -name '*.apk' | sort)
[[ "${#APKS[@]}" -eq 1 ]] || fail "expected exactly one APK, found ${#APKS[@]}"
[[ "$(basename "${APKS[0]}")" == "IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-debug.apk" ]] || fail "unexpected APK identity $(basename "${APKS[0]}")"
rm -f "$FINAL"; cp "${APKS[0]}" "$FINAL"

APKX="$WORK/apkx"; rm -rf "$APKX"; mkdir -p "$APKX"; unzip -q "$FINAL" -d "$APKX"
[[ -f "$APKX/lib/arm64-v8a/libmy-native-lib.so" ]] || fail "arm64 MGC native library missing"
[[ -f "$APKX/lib/armeabi-v7a/libmy-native-lib.so" ]] || fail "armv7 packaging stub missing"
readelf -Ws "$APKX/lib/arm64-v8a/libmy-native-lib.so" > "$OUT/26512_arm64_mgc_symbols.txt"
grep -F 'Java_com_hinnka_mycamera_raw_MgcFullResolutionDenoise_nativeDenoiseRgba16f' "$OUT/26512_arm64_mgc_symbols.txt" >/dev/null || fail "MGC full-resolution denoise JNI symbol missing"
grep -F 'Java_com_hinnka_mycamera_processor_MgcSpatialStrengthMapGenerator_nativeCompute' "$OUT/26512_arm64_mgc_symbols.txt" >/dev/null || fail "MGC Spatial strength JNI symbol missing"
readelf -Ws "$APKX/lib/armeabi-v7a/libmy-native-lib.so" > "$OUT/26512_armv7_stub_symbols.txt"
if grep -F 'MgcFullResolutionDenoise_nativeDenoiseRgba16f' "$OUT/26512_armv7_stub_symbols.txt" >/dev/null; then fail "armv7 stub unexpectedly contains arm64 MGC AOT JNI"; fi
python3 - "$FINAL" <<'PYAPK'
from pathlib import Path
import sys,zipfile
apk=Path(sys.argv[1])
with zipfile.ZipFile(apk) as z:
    names=set(z.namelist()); dex=b''.join(z.read(n) for n in sorted(names) if n.endswith('.dex'))
    required=[b'IRIS_26512_MGC1271_PARITY_VALID',b'MGC PARITY ARCHITECTURE INVALID',b'GlesMgcRawFusion',b'GlesMgcRawSpatialStacker',b'MgcFullResolutionDenoise',b'SPATIAL_DEFAULT']
    for m in required: assert m in dex,('missing DEX marker',m)
    for bad in (b'IRIS_26509_',b'IRIS_26510_',b'IRIS_26511_'): assert bad not in dex,('rejected runtime marker',bad)
    for asset in ('luma_denoise_default.binarypb','sabre_luma_denoise.binarypb','chroma_denoise.binarypb'):
        assert any(n.endswith('assets/mgc_denoise/'+asset) for n in names),asset
print('PASS: APK DEX/native/assets prove owned MGC 1.27.1 parity route')
PYAPK
sha256sum "$FINAL" > "$OUT/26512_APK.sha256"

# Emit the actual built 26512 source for future direct incremental work.
rm -rf "$AFTER/app/src/main/cpp/third_party_26507"
( cd "$AFTER" && tar --sort=name --mtime='UTC 2026-08-19 00:00:00' --owner=0 --group=0 --numeric-owner -czf "$OUT/26512_successful_app_source.tar.gz" app/src/main app/version.properties )
( cd "$AFTER" && { find app/src/main -type f -print; echo app/version.properties; } | LC_ALL=C sort | while read -r f; do sha256sum "$f"; done ) > "$OUT/26512_successful_source.sha256"
pass "GATE 6 exactly one 26512 APK built from successful 26507 + exact pinned MGC 1.27.1 owner"

echo "=== GATE 7: SUCCESS ==="
echo "APK: $(basename "$FINAL")"
echo "APK SHA256: $(sha "$FINAL")"
echo "START_HEAD=$START_HEAD"
echo "SOURCE_26507_SHA=$SOURCE_TAR_SHA"
echo "BJZHOU_1_27_1_HEAD=$BJZHOU_HEAD"
pass "26512 complete: exact 1.27.1 MGC Fusion/Spatial RGB/Bento/Long/noise/default-denoise owner inside unchanged 26507 capture/post shell"
