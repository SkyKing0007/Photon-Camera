#!/usr/bin/env bash
set -euo pipefail
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
ROOT="$(pwd)"
OUT="$ROOT/build_26509_direct_26507_root_correction_outputs"
WORK="$ROOT/.build_26509_direct_26507_root_correction_work"
BASE="$WORK/successful26507"
AFTER="$WORK/candidate26509"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
BASE_HANDOFF_26507_HEAD="c4f99d7f3212ac82b0976b41621c8b5bb917d31b"
REJECTED_26508_V3_HEAD="33f26df7daafaa956b578233d1e94de57d5c84a3"
BACKUP_BRANCH="backup-26508-v3-rejected-before-26509-root-correction-20260819"
SOURCE_TAR="$ROOT/26507_successful_app_source.tar.gz"
SOURCE_TAR_SHA="3165a63224fc99652504113c312827b4af823eb643567f3678bfd938ad2c0082"
SOURCE_MANIFEST="$ROOT/26507_SUCCESSFUL_SOURCE.sha256"
DELTA_PATCH="$ROOT/26509_EXACT_DELTA_FROM_SUCCESSFUL_26507.patch"
DELTA_PATCH_SHA="b454171597e95c5a36eccd8491abb7bb7cc7be107c9b3d6459383a6e2ab44bf7"
APPLY="$ROOT/apply_26509_root_correction.py"
VALIDATOR="$ROOT/validate_26509_root_correction.py"
BJZHOU_HEAD="09c76e57e8f01a5a8fc536ab41fc80ba642d4042"
BJZHOU_MANIFEST="$ROOT/26507_BJZHOU_NATIVE_DEPENDENCIES.sha256"
BJZHOU_COMMIT_FILE="$ROOT/26507_BJZHOU_DEPENDENCY_COMMIT.txt"
VERSION_NAME="0.9726509"
VERSION_BUILD="26509"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-direct-26507-root-correction-debug.apk"
rm -rf "$OUT" "$WORK"; mkdir -p "$OUT" "$BASE" "$AFTER"
exec > >(tee "$OUT/26509_build.log") 2>&1

BRANCH="$(git branch --show-current)"; START_HEAD="$(git rev-parse HEAD)"
[[ "$BRANCH" == "$EXPECTED_BRANCH" && "$BRANCH" != "dev" ]] || fail "wrong/protected branch $BRANCH"
git merge-base --is-ancestor "$BASE_HANDOFF_26507_HEAD" HEAD || fail "26507 handoff missing from lineage"
git merge-base --is-ancestor "$REJECTED_26508_V3_HEAD" HEAD || fail "verified pre-26509 handoff missing from lineage"
REMOTE_BACKUP="$(git ls-remote origin "refs/heads/$BACKUP_BRANCH" | awk '{print $1}')"
[[ "$REMOTE_BACKUP" == "$REJECTED_26508_V3_HEAD" ]] || fail "backup missing/wrong: $BACKUP_BRANCH -> ${REMOTE_BACKUP:-MISSING}"
# Root Gradle/build infrastructure must remain the same as the successful 26507 handoff.
PROTECTED_DRIFT="$OUT/protected_build_infrastructure_drift.txt"
git diff --name-only "$BASE_HANDOFF_26507_HEAD"..HEAD -- \
  gradlew gradlew.bat gradle build.gradle settings.gradle gradle.properties \
  app/build.gradle app/proguard-rules.pro > "$PROTECTED_DRIFT"
[[ ! -s "$PROTECTED_DRIFT" ]] || { cat "$PROTECTED_DRIFT" >&2; fail "protected build infrastructure drifted after 26507"; }
for f in "$SOURCE_TAR" "$SOURCE_MANIFEST" "$DELTA_PATCH" "$APPLY" "$VALIDATOR" "$BJZHOU_MANIFEST" "$BJZHOU_COMMIT_FILE"; do [[ -f "$f" ]] || fail "missing $(basename "$f")"; done
[[ "$(sha "$SOURCE_TAR")" == "$SOURCE_TAR_SHA" ]] || fail "successful 26507 source archive hash mismatch"
[[ "$(sha "$DELTA_PATCH")" == "$DELTA_PATCH_SHA" ]] || fail "26509 exact delta patch hash mismatch"
[[ "$(tr -d '\r\n' < "$BJZHOU_COMMIT_FILE")" == "$BJZHOU_HEAD" ]] || fail "26507 bjzhou dependency commit proof mismatch"
python3 -m py_compile "$APPLY" "$VALIDATOR"
pass "GATE 1 branch/backup/protected-build/source-archive identities"

echo "=== GATE 2: exact successful 26507 source is the only runtime base ==="
tar -xzf "$SOURCE_TAR" -C "$BASE"
( cd "$BASE" && sha256sum -c "$SOURCE_MANIFEST" ) > "$OUT/26507_successful_source_manifest_check.txt"
[[ "$(grep '^VERSION_NAME=' "$BASE/app/version.properties" | cut -d= -f2)" == "0.9726507" ]] || fail "source archive is not 26507 version"
[[ "$(grep '^VERSION_BUILD=' "$BASE/app/version.properties" | cut -d= -f2)" == "26507" ]] || fail "source archive is not 26507 build"
[[ ! -d "$BASE/app/src/main/cpp/third_party_26507" ]] || fail "compact successful source unexpectedly contains fetched third-party tree"
cp "$SOURCE_TAR" "$OUT/26509_PRECHANGE_EXACT_SUCCESSFUL_26507_SOURCE.tar.gz"
sha256sum "$OUT/26509_PRECHANGE_EXACT_SUCCESSFUL_26507_SOURCE.tar.gz" > "$OUT/26509_PRECHANGE_EXACT_SUCCESSFUL_26507_SOURCE.tar.gz.sha256"
pass "GATE 2 exact successful 26507 source verified directly; no historical runtime replay"

echo "=== GATE 3: apply 26509 once and prove exact direct delta ==="
cp -a "$BASE/app" "$AFTER/app"
python3 "$APPLY" "$AFTER" | tee "$OUT/26509_apply.txt"
python3 "$VALIDATOR" "$AFTER" --base-root "$BASE" | tee "$OUT/26509_validate.txt"
set +e
( cd "$WORK" && git diff --no-index --binary successful26507/app candidate26509/app ) > "$OUT/26509_EXACT_DELTA_RUNTIME.patch"
rc=$?
set -e
[[ "$rc" -eq 1 && -s "$OUT/26509_EXACT_DELTA_RUNTIME.patch" ]] || fail "runtime direct delta patch generation failed"
cmp -s "$OUT/26509_EXACT_DELTA_RUNTIME.patch" "$DELTA_PATCH" || fail "runtime direct delta differs from audited handoff patch"
[[ "$(sha "$OUT/26509_EXACT_DELTA_RUNTIME.patch")" == "$DELTA_PATCH_SHA" ]] || fail "runtime direct delta hash mismatch"
[[ "$(grep '^VERSION_NAME=' "$AFTER/app/version.properties" | cut -d= -f2)" == "0.9726507" ]] || fail "version changed before guarded build block"
[[ "$(grep '^VERSION_BUILD=' "$AFTER/app/version.properties" | cut -d= -f2)" == "26507" ]] || fail "build changed before guarded build block"
# Parse changed Java with the JDK parser only; Android type resolution is left to Gradle.
cat > "$WORK/ParseJava.java" <<'JAVA'
import java.nio.charset.StandardCharsets;import java.util.*;import javax.tools.*;import com.sun.source.util.*;
public class ParseJava{public static void main(String[]a)throws Exception{JavaCompiler c=ToolProvider.getSystemJavaCompiler();if(c==null)throw new RuntimeException("no javac");DiagnosticCollector<JavaFileObject> dc=new DiagnosticCollector<>();StandardJavaFileManager fm=c.getStandardFileManager(dc,null,StandardCharsets.UTF_8);Iterable<? extends JavaFileObject> f=fm.getJavaFileObjectsFromStrings(Arrays.asList(a));JavacTask t=(JavacTask)c.getTask(null,fm,dc,List.of("-proc:none"),null,f);t.parse();long errors=dc.getDiagnostics().stream().filter(d->d.getKind()==Diagnostic.Kind.ERROR).count();for(Diagnostic<? extends JavaFileObject>d:dc.getDiagnostics())if(d.getKind()==Diagnostic.Kind.ERROR)System.err.println(d);fm.close();if(errors!=0)throw new RuntimeException("Java parse errors="+errors);System.out.println("PASS: Java parser accepted "+a.length+" changed sources with zero syntax errors");}}
JAVA
javac "$WORK/ParseJava.java"
JAVA_ROOT="$AFTER/app/src/main/java/com/particlesdevs/photoncamera"
java -cp "$WORK" ParseJava \
 "$JAVA_ROOT/processing/MotionBatch.java" \
 "$JAVA_ROOT/capture/CaptureController.java" \
 "$JAVA_ROOT/processing/processor/MotionV2WronskiAlignment.java" \
 "$JAVA_ROOT/processing/processor/MotionV2CfaReconstruction.java" \
 "$JAVA_ROOT/processing/processor/HdrxProcessor.java" | tee "$OUT/26509_java_parse.txt"
# Permanent lexical portability gate for all changed/new 26509 shaders.
python3 - "$AFTER" <<'PYLEX'
from pathlib import Path
import re,sys
root=Path(sys.argv[1])/'app/src/main/assets/shaders/motionv2'
names=['mfsr_flow_expand.glsl','mfsr_bjzhou_rejection_base.glsl','mfsr_spatial_rgb_contribute_26501.glsl','shadow_aux_bayer_fuse.glsl','mfsr_spatial_rgb_normalize_26501.glsl','short_highlight_bayer_recover.glsl','mfsr_spatial_rgb_short_weight_26501.glsl','mfsr_bridge_flow_compose_26509.glsl','mfsr_short_region_seed_26509.glsl','mfsr_short_region_propagate_26509.glsl','mfsr_short_region_finalize_26509.glsl','mfsr_support_diag_26509.glsl']
reserved=set('attribute const uniform varying buffer shared coherent volatile restrict readonly writeonly atomic_uint layout centroid flat smooth noperspective patch sample break continue do for while switch case default if else subroutine in out inout float double int void bool true false invariant precise discard return mat2 mat3 mat4 vec2 vec3 vec4 ivec2 ivec3 ivec4 bvec2 bvec3 bvec4 uint uvec2 uvec3 uvec4 lowp mediump highp precision sampler1D sampler2D sampler3D samplerCube isampler2D usampler2D image2D uimage2D struct common partition active asm class union enum typedef template this resource goto inline noinline public static extern external interface long short half fixed unsigned superp input output hvec2 hvec3 hvec4 fvec2 fvec3 fvec4 sampler3DRect filter sizeof cast namespace using row_major'.split())
for n in names:
 s=(root/n).read_text(); x=re.sub(r'/\*.*?\*/',' ',s,flags=re.S); x=re.sub(r'//.*',' ',x)
 assert '__' not in x,(n,'double underscore')
 decl=re.compile(r'\b(?:bool|int|uint|float|vec[234]|ivec[234]|uvec[234]|mat[234]|sampler2D|usampler2D|image2D|uimage2D)\s+([A-Za-z_]\w*)')
 bad=sorted({m.group(1) for m in decl.finditer(x) if m.group(1) in reserved}); assert not bad,(n,bad)
 for a,b in [('(',')'),('{','}'),('[',']')]: assert x.count(a)==x.count(b),(n,a,b,x.count(a),x.count(b))
print('PASS: GLSL reserved-identifier/delimiter preflight for 12 changed/new shaders')
PYLEX
pass "GATE 3 exact 17-file direct delta + Java/GLSL static preflight"

echo "=== GATE 4: exact 26507 native dependencies + glslang 16.5.0 + binding proof ==="
BJ="$WORK/bjzhou-$BJZHOU_HEAD"; rm -rf "$BJ"; git init -q "$BJ"; git -C "$BJ" remote add origin https://github.com/bjzhou/PhotonCamera.git
git -C "$BJ" config core.sparseCheckout true
mkdir -p "$BJ/.git/info"; printf '%s\n' '/app/src/main/cpp/libjpeg-turbo/' '/app/src/main/cpp/libultrahdr/' > "$BJ/.git/info/sparse-checkout"
git -C "$BJ" fetch --depth=1 origin "$BJZHOU_HEAD"; git -C "$BJ" checkout -q --detach FETCH_HEAD
[[ "$(git -C "$BJ" rev-parse HEAD)" == "$BJZHOU_HEAD" ]] || fail "bjzhou dependency checkout drift"
THIRD="$AFTER/app/src/main/cpp/third_party_26507"; mkdir -p "$THIRD"
cp -a "$BJ/app/src/main/cpp/libjpeg-turbo" "$THIRD/libjpeg-turbo"
cp -a "$BJ/app/src/main/cpp/libultrahdr" "$THIRD/libultrahdr"
[[ -f "$THIRD/libjpeg-turbo/CMakeLists.txt" && -f "$THIRD/libjpeg-turbo/src/turbojpeg.h" ]] || fail "pinned libjpeg-turbo layout missing"
[[ -f "$THIRD/libultrahdr/ultrahdr_api.h" && -f "$THIRD/libultrahdr/lib/src/ultrahdr_api.cpp" && -d "$THIRD/libultrahdr/lib/include/ultrahdr" ]] || fail "pinned libultrahdr layout missing"
[[ ! -e "$THIRD/libultrahdr/lib/include/ultrahdr_api.h" ]] || fail "obsolete libultrahdr include layout appeared"
( cd "$THIRD" && sha256sum -c "$BJZHOU_MANIFEST" ) > "$OUT/26509_bjzhou_native_manifest_check.txt"
echo "$BJZHOU_HEAD" > "$OUT/26509_bjzhou_dependency_commit.txt"
command -v glslangValidator >/dev/null || fail "glslangValidator missing"
grep -F '16.5.0' <<<"$(glslangValidator --version | head -1)" >/dev/null || fail "wrong glslangValidator"
python3 - "$AFTER" "$WORK" "$OUT" <<'PYGLSL'
from pathlib import Path
import subprocess,sys
root,work,out=map(Path,sys.argv[1:])
items=[
 ('mfsr_flow_expand.glsl','comp'),('mfsr_bjzhou_rejection_base.glsl','comp'),
 ('mfsr_spatial_rgb_contribute_26501.glsl','frag'),('shadow_aux_bayer_fuse.glsl','comp'),
 ('mfsr_spatial_rgb_normalize_26501.glsl','frag'),('short_highlight_bayer_recover.glsl','comp'),
 ('mfsr_spatial_rgb_short_weight_26501.glsl','comp'),('mfsr_bridge_flow_compose_26509.glsl','comp'),
 ('mfsr_short_region_seed_26509.glsl','comp'),('mfsr_short_region_propagate_26509.glsl','comp'),
 ('mfsr_short_region_finalize_26509.glsl','comp'),('mfsr_support_diag_26509.glsl','comp')]
for name,stage in items:
 src=(root/'app/src/main/assets/shaders/motionv2'/name).read_text()
 if stage=='comp':
  src=src.replace('#define LAYOUT //','',1).replace('LAYOUT','layout(local_size_x=8,local_size_y=8,local_size_z=1) in;',1)
 tmp=work/(name+'.'+stage); tmp.write_text('#version 310 es\n'+src)
 cp=subprocess.run(['glslangValidator','-S',stage,str(tmp)],capture_output=True,text=True)
 (out/(name+'.glslang.txt')).write_text(cp.stdout+cp.stderr)
 if cp.returncode: raise SystemExit('GLSL failed '+name+'\n'+cp.stdout+cp.stderr)
print('PASS: all 12 changed/new shaders compile with glslang 16.5.0')
PYGLSL
python3 - "$AFTER" <<'PYBIND'
from pathlib import Path
import sys
h=(Path(sys.argv[1])/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java').read_text()
checks=[
 'setTexture("referenceToBridgeFlow"','setTexture("bridgeToShortFlow"','setTextureCompute("outFlow"',
 'setTexture("candidateProvenance"','setTexture("mgcWeight"','setTextureCompute("outRegion"',
 'setTexture("regionIn"','setTexture("regionTexture"','setTextureCompute("outCfa"','setTextureCompute("outProvenance"',
 'setTexture("semanticAccumulator"','setTexture("opponentWeightAccumulator"','setBufferCompute("SupportDiagBuf"',
 'setBufferCompute("GeometryDiagBuf"']
for c in checks: assert c in h,'missing host binding '+c
# IRIS_26509_V2_BINDING_PROOF_REGION_TEXTURE
# Cross-check the exact finalizer sampler name against the generated shader so this proof
# cannot drift to a stale invented name such as the V1-only 'regionMask'.
shader=(Path(sys.argv[1])/'app/src/main/assets/shaders/motionv2/mfsr_short_region_finalize_26509.glsl').read_text()
assert 'uniform highp sampler2D regionTexture;' in shader, 'finalizer shader regionTexture sampler missing'
assert 'setTexture("regionTexture",iris26509RegionRead)' in h, 'finalizer host regionTexture binding missing'
assert 'regionMask' not in shader, 'stale regionMask sampler unexpectedly present in finalizer shader'
assert h.count('setBufferCompute("GeometryDiagBuf",iris26509GeometryDiag)')==3
print('PASS: type-aware 26509 host binding proof + exact finalizer regionTexture contract')
PYBIND
# Protected runtime invariants that were not supposed to change.
grep -F 'IRIS_26507_MGC_RAW_HALF_GUIDE_PARITY' "$AFTER/app/src/main/assets/shaders/motionv2/mfsr_bjzhou_guide.glsl" >/dev/null
grep -F 'IRIS_26507_MGC_RAW_HALF_COVARIANCE_PARITY' "$AFTER/app/src/main/assets/shaders/motionv2/mfsr_mgc_covariance.glsl" >/dev/null
grep -F 'IRIS_26507_FULL_HDR_DISPLAY_CAPACITY_PARITY' "$AFTER/app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java" >/dev/null
grep -F 'IRIS_26507_TRUE_JPEG444_JPEGR' "$AFTER/app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java" >/dev/null
grep -F 'TJSAMP_444' "$AFTER/app/src/main/cpp/motionv2_jpeg444_jni.cpp" >/dev/null
if grep -F 'IRIS_26508_SHARED_NORMAL_LONG_MGC_FUSION_OWNER' "$AFTER/app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java" >/dev/null; then fail "rejected 26508 unrestricted Long fusion survived"; fi
echo "PRE-BUILD SAFETY PROOF PASSED"
pass "GATE 4 native layout + 12-shader compiler + binding/non-regression proof"

echo "=== GATE 5: VERSION ${VERSION_NAME} / ${VERSION_BUILD} + BUILD IN SAME GUARDED BLOCK ==="
python3 - "$AFTER/app/version.properties" "$VERSION_NAME" "$VERSION_BUILD" <<'PYVER'
from pathlib import Path
import sys
p=Path(sys.argv[1]); vn=sys.argv[2]; vb=sys.argv[3]; s=p.read_text()
assert 'VERSION_NAME=0.9726507' in s and 'VERSION_BUILD=26507' in s
s=s.replace('VERSION_NAME=0.9726507','VERSION_NAME='+vn).replace('VERSION_BUILD=26507','VERSION_BUILD='+vb)
p.write_text(s); t=p.read_text(); assert 'VERSION_NAME='+vn in t and 'VERSION_BUILD='+vb in t
PYVER
# Overlay only the audited direct candidate. No historical source transforms are run here.
rm -rf app/src/main
cp -a "$AFTER/app/src/main" app/src/main
cp "$AFTER/app/version.properties" app/version.properties
# IRIS_26509_V4_AUDITED_RUNTIME_EXCLUDES_ONLY_KNOWN_BUILD_GENERATED_DEPS
# Two source-tree locations have independent build-dependency authority and are not
# canonical Photon runtime source:
#   1) third_party_26507: pinned bjzhou native tree, authenticated above by commit + manifest.
#   2) cpp/deps generated headers: Photon CMakeLists.txt itself downloads exactly four
#      headers during CMake configure.  Their *names/location* are proved here; hashes are
#      emitted after Gradle.  CMakeLists.txt itself remains inside the immutable manifest.
CMAKE_SRC="app/src/main/cpp/CMakeLists.txt"
for needle in   'deps/tiny_dng_writer.h'   'deps/technicallyflac.h'   'deps/archive.h'   'deps/archive_entry.h'; do
  grep -F "$needle" "$CMAKE_SRC" >/dev/null || fail "CMake generated-dependency contract missing: $needle"
done

assert_cpp_deps_exact(){
  local phase="$1" expected actual
  if [[ "$phase" == "pre" ]]; then
    expected=$'.gitignore'
  else
    expected=$'.gitignore\narchive.h\narchive_entry.h\ntechnicallyflac.h\ntiny_dng_writer.h'
  fi
  actual="$(find app/src/main/cpp/deps -mindepth 1 -maxdepth 1 -type f -printf '%f\n' | LC_ALL=C sort)"
  [[ "$actual" == "$expected" ]] || {
    printf 'Expected cpp/deps (%s):\n%s\nActual:\n%s\n' "$phase" "$expected" "$actual" >&2
    fail "unexpected app/src/main/cpp/deps contents during $phase-build proof"
  }
}

# Successful 26507 source has only the tracked .gitignore before CMake runs.
assert_cpp_deps_exact pre

audited_runtime_manifest(){
  {
    find app/src/main -type f       ! -path 'app/src/main/cpp/third_party_26507/*'       ! -path 'app/src/main/cpp/deps/*' -print
    # Keep the tracked deps sentinel under immutable authority while excluding only
    # the four CMake-downloaded headers.
    echo app/src/main/cpp/deps/.gitignore
    echo app/version.properties
  } | LC_ALL=C sort | while read -r f; do sha256sum "$f"; done
}
audited_runtime_manifest > "$OUT/26509_pre_gradle_audited_runtime.sha256"
chmod +x ./gradlew
./gradlew clean :app:assembleDebug --stacktrace

# IRIS_26509_V4_GENERATED_CPP_DEPS_EXACT_ALLOWLIST
# After a successful native configure/build, only these four CMake-declared generated
# headers may have appeared beside the tracked .gitignore.  Any additional path fails.
assert_cpp_deps_exact post
(
  cd app/src/main/cpp/deps
  sha256sum .gitignore archive.h archive_entry.h technicallyflac.h tiny_dng_writer.h
) > "$OUT/26509_post_gradle_generated_cpp_deps.sha256"

audited_runtime_manifest > "$OUT/26509_post_gradle_audited_runtime.sha256"
if ! cmp -s "$OUT/26509_pre_gradle_audited_runtime.sha256" "$OUT/26509_post_gradle_audited_runtime.sha256"; then
  # IRIS_26509_V4_SOURCE_DIFF_DIAGNOSTIC
  diff -u "$OUT/26509_pre_gradle_audited_runtime.sha256" "$OUT/26509_post_gradle_audited_runtime.sha256" \
    | tee "$OUT/26509_gradle_runtime_source_diff.txt" >&2 || true
  fail "Gradle mutated audited Photon runtime source; see 26509_gradle_runtime_source_diff.txt"
fi
pass "Gradle preserved audited Photon runtime; only exact CMake-declared cpp/deps headers were generated"
mapfile -t APKS < <(find app/build -type f -name '*.apk' | sort)
[[ "${#APKS[@]}" -eq 1 ]] || fail "expected exactly one APK, found ${#APKS[@]}"
[[ "$(basename "${APKS[0]}")" == "IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-debug.apk" ]] || fail "unexpected APK identity $(basename "${APKS[0]}")"
rm -f "$FINAL"; cp "${APKS[0]}" "$FINAL"
python3 - "$FINAL" "$AFTER" <<'PYAPK'
from pathlib import Path
import hashlib,sys,zipfile
apk=Path(sys.argv[1]); src=Path(sys.argv[2])
with zipfile.ZipFile(apk) as z:
 names=set(z.namelist()); libs=sorted(n for n in names if n.endswith('/libmotionv2jpeg.so')); assert libs,'libmotionv2jpeg.so missing'
 dex_names=sorted(n for n in names if n.endswith('.dex')); assert dex_names,'no DEX'; dex=b''.join(z.read(n) for n in dex_names)
 runtime=[b'IRIS_26509_GEOMETRY_RESULT',b'IRIS_26509_SUPPORT_RESULT',b'IRIS_26509_SHORT_ARCHITECTURAL_RESULT',b'IRIS_26509_LONG_BUCKET_RESULT',b'IRIS_26509_NORMAL_EXPOSURE_BIAS',b'IRIS_26509_ASYNC_JPEGR_OUTPUT_COMPLETE',b'IRIS_26507_JPEG444']
 for m in runtime: assert m in dex,b'missing runtime DEX marker '+m
 shaders=['mfsr_flow_expand.glsl','mfsr_bjzhou_rejection_base.glsl','mfsr_spatial_rgb_contribute_26501.glsl','shadow_aux_bayer_fuse.glsl','mfsr_spatial_rgb_normalize_26501.glsl','short_highlight_bayer_recover.glsl','mfsr_spatial_rgb_short_weight_26501.glsl','mfsr_bridge_flow_compose_26509.glsl','mfsr_short_region_seed_26509.glsl','mfsr_short_region_propagate_26509.glsl','mfsr_short_region_finalize_26509.glsl','mfsr_support_diag_26509.glsl']
 for n in shaders:
  suffix='assets/shaders/motionv2/'+n; matches=[x for x in names if x.endswith(suffix)]; assert len(matches)==1,(n,matches)
  a=z.read(matches[0]); b=(src/'app/src/main/assets/shaders/motionv2'/n).read_bytes(); assert hashlib.sha256(a).digest()==hashlib.sha256(b).digest(),n+' packaged shader differs from source'
print('PASS: APK typed proof: 26509 DEX telemetry + exact packaged shaders + libmotionv2jpeg.so')
PYAPK
sha256sum "$FINAL" > "$OUT/26509_APK.sha256"
# Compact next-build source checkpoint: preserve exact built source but exclude fetched native tree, whose commit/manifest are separately proven.
rm -rf "$AFTER/app/src/main/cpp/third_party_26507"
( cd "$AFTER" && tar --sort=name --mtime='UTC 2026-08-19 00:00:00' --owner=0 --group=0 --numeric-owner -czf "$OUT/26509_successful_app_source.tar.gz" app/src/main app/version.properties )
( cd "$AFTER" && { find app/src/main -type f -print; echo app/version.properties; } | LC_ALL=C sort | while read -r f; do sha256sum "$f"; done ) > "$OUT/26509_successful_source.sha256"
pass "GATE 5 exactly one 26509 APK built from direct successful-26507 source"

echo "=== GATE 6: SUCCESS ==="
echo "APK: $(basename "$FINAL")"
echo "APK SHA256: $(sha "$FINAL")"
echo "START_HEAD=$START_HEAD"
echo "SOURCE_26507_SHA=$SOURCE_TAR_SHA"
echo "BJZHOU_HEAD=$BJZHOU_HEAD"
pass "26509 direct root correction complete: continuous geometry + physical borders + balanced chroma support + physical-Normal Short + shadow-only Long + RAW-signal Normal exposure + smooth endpoint + async JPEG_R"
