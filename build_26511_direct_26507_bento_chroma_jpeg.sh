#!/usr/bin/env bash
set -euo pipefail
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
ROOT="$(pwd)"
OUT="$ROOT/build_26511_direct_26507_bento_chroma_jpeg_outputs"
WORK="$ROOT/.build_26511_direct_26507_bento_chroma_jpeg_work"
BASE="$WORK/successful26507"
AFTER="$WORK/candidate26511"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
REJECTED_26510_HEAD="19b134a4716f877e25e9c2c8050208d25400e1c7"
BACKUP_BRANCH="backup-26510-rejected-before-26511-20260819"
SOURCE_TAR="$ROOT/26507_successful_app_source.tar.gz"
SOURCE_TAR_SHA="3165a63224fc99652504113c312827b4af823eb643567f3678bfd938ad2c0082"
SOURCE_MANIFEST="$ROOT/26507_SUCCESSFUL_SOURCE.sha256"
DELTA_PATCH="$ROOT/26511_EXACT_DELTA_FROM_SUCCESSFUL_26507.patch"
DELTA_PATCH_SHA="614f0cd987101da912e600fe039e16797584fb549d6c37d07812900f2c8da84c"
VALIDATOR="$ROOT/validate_26511_bento_chroma_jpeg.py"
BJZHOU_HEAD="09c76e57e8f01a5a8fc536ab41fc80ba642d4042"
BJZHOU_MANIFEST="$ROOT/26507_BJZHOU_NATIVE_DEPENDENCIES.sha256"
BJZHOU_COMMIT_FILE="$ROOT/26507_BJZHOU_DEPENDENCY_COMMIT.txt"
VERSION_NAME="0.9726511"
VERSION_BUILD="26511"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-bento-chroma-jpeg-debug.apk"
rm -rf "$OUT" "$WORK"; mkdir -p "$OUT" "$BASE" "$AFTER"
exec > >(tee "$OUT/26511_build.log") 2>&1

echo "=== GATE 1: branch / rejected-build backup / direct-source identities ==="
BRANCH="$(git branch --show-current)"; START_HEAD="$(git rev-parse HEAD)"
[[ "$BRANCH" == "$EXPECTED_BRANCH" && "$BRANCH" != "dev" ]] || fail "wrong/protected branch $BRANCH"
git merge-base --is-ancestor "$REJECTED_26510_HEAD" HEAD || fail "current handoff is not descended from rejected 26510 checkpoint"
REMOTE_BACKUP="$(git ls-remote origin "refs/heads/$BACKUP_BRANCH" | awk '{print $1}')"
[[ "$REMOTE_BACKUP" == "$REJECTED_26510_HEAD" ]] || fail "backup missing/wrong: $BACKUP_BRANCH -> ${REMOTE_BACKUP:-MISSING}"
PROTECTED_DRIFT="$OUT/protected_build_infrastructure_drift.txt"
git diff --name-only "$REJECTED_26510_HEAD"..HEAD -- \
  gradlew gradlew.bat gradle build.gradle settings.gradle gradle.properties \
  app/build.gradle app/proguard-rules.pro > "$PROTECTED_DRIFT"
[[ ! -s "$PROTECTED_DRIFT" ]] || { cat "$PROTECTED_DRIFT" >&2; fail "protected build infrastructure drifted after backup"; }
for f in "$SOURCE_TAR" "$SOURCE_MANIFEST" "$DELTA_PATCH" "$VALIDATOR" "$BJZHOU_MANIFEST" "$BJZHOU_COMMIT_FILE"; do [[ -f "$f" ]] || fail "missing $(basename "$f")"; done
[[ "$(sha "$SOURCE_TAR")" == "$SOURCE_TAR_SHA" ]] || fail "successful 26507 source archive hash mismatch"
[[ "$(sha "$DELTA_PATCH")" == "$DELTA_PATCH_SHA" ]] || fail "26511 exact delta patch hash mismatch"
[[ "$(tr -d '\r\n' < "$BJZHOU_COMMIT_FILE")" == "$BJZHOU_HEAD" ]] || fail "26507/1.27.1 bjzhou dependency commit proof mismatch"
python3 -m py_compile "$VALIDATOR"
pass "GATE 1 exact rejected-26510 backup + direct successful-26507 identities"

echo "=== GATE 2: exact successful 26507 is the only runtime base ==="
tar -xzf "$SOURCE_TAR" -C "$BASE"
( cd "$BASE" && sha256sum -c "$SOURCE_MANIFEST" ) > "$OUT/26507_successful_source_manifest_check.txt"
[[ "$(grep '^VERSION_NAME=' "$BASE/app/version.properties" | cut -d= -f2)" == "0.9726507" ]] || fail "source archive is not 26507 version"
[[ "$(grep '^VERSION_BUILD=' "$BASE/app/version.properties" | cut -d= -f2)" == "26507" ]] || fail "source archive is not 26507 build"
[[ ! -d "$BASE/app/src/main/cpp/third_party_26507" ]] || fail "successful source unexpectedly contains fetched third-party tree"
cp "$SOURCE_TAR" "$OUT/26511_PRECHANGE_EXACT_SUCCESSFUL_26507_SOURCE.tar.gz"
sha256sum "$OUT/26511_PRECHANGE_EXACT_SUCCESSFUL_26507_SOURCE.tar.gz" > "$OUT/26511_PRECHANGE_EXACT_SUCCESSFUL_26507_SOURCE.tar.gz.sha256"
pass "GATE 2 successful 26507 source verified; 26509/26510 runtime is not inherited"

echo "=== GATE 3: apply exact eight-path 26511 delta once ==="
cp -a "$BASE/app" "$AFTER/app"
patch -s -d "$AFTER" -p1 < "$DELTA_PATCH"
python3 "$VALIDATOR" "$AFTER" --base-root "$BASE" | tee "$OUT/26511_validate.txt"
[[ "$(grep '^VERSION_NAME=' "$AFTER/app/version.properties" | cut -d= -f2)" == "0.9726507" ]] || fail "version changed before guarded build block"
[[ "$(grep '^VERSION_BUILD=' "$AFTER/app/version.properties" | cut -d= -f2)" == "26507" ]] || fail "build changed before guarded build block"
( cd "$AFTER" && { find app/src/main -type f -print; echo app/version.properties; } | LC_ALL=C sort | while read -r f; do sha256sum "$f"; done ) > "$OUT/26511_prebuild_candidate_source.sha256"

cat > "$WORK/ParseJava.java" <<'JAVA'
import java.nio.charset.StandardCharsets;import java.util.*;import javax.tools.*;import com.sun.source.util.*;
public class ParseJava{public static void main(String[]a)throws Exception{JavaCompiler c=ToolProvider.getSystemJavaCompiler();if(c==null)throw new RuntimeException("no javac");DiagnosticCollector<JavaFileObject> dc=new DiagnosticCollector<>();StandardJavaFileManager fm=c.getStandardFileManager(dc,null,StandardCharsets.UTF_8);Iterable<? extends JavaFileObject> f=fm.getJavaFileObjectsFromStrings(Arrays.asList(a));JavacTask t=(JavacTask)c.getTask(null,fm,dc,List.of("-proc:none"),null,f);t.parse();long errors=dc.getDiagnostics().stream().filter(d->d.getKind()==Diagnostic.Kind.ERROR).count();for(Diagnostic<? extends JavaFileObject>d:dc.getDiagnostics())if(d.getKind()==Diagnostic.Kind.ERROR)System.err.println(d);fm.close();if(errors!=0)throw new RuntimeException("Java parse errors="+errors);System.out.println("PASS: Java parser accepted "+a.length+" changed sources with zero syntax errors");}}
JAVA
javac "$WORK/ParseJava.java"
JAVA_ROOT="$AFTER/app/src/main/java/com/particlesdevs/photoncamera"
java -cp "$WORK" ParseJava \
  "$JAVA_ROOT/processing/processor/HdrxProcessor.java" \
  "$JAVA_ROOT/processing/processor/MotionV2CfaReconstruction.java" \
  "$JAVA_ROOT/processing/ultrahdr/MotionV2Jpeg444Encoder.java" | tee "$OUT/26511_java_parse.txt"

python3 - "$AFTER" <<'PYLEX'
from pathlib import Path
import re,sys
root=Path(sys.argv[1])/'app/src/main/assets/shaders/motionv2'
names=['short_highlight_bayer_recover.glsl','mfsr_spatial_rgb_short_weight_26501.glsl','mfsr_spatial_rgb_normalize_26501.glsl']
reserved=set('attribute const uniform varying buffer shared coherent volatile restrict readonly writeonly atomic_uint layout centroid flat smooth noperspective patch sample break continue do for while switch case default if else subroutine in out inout float double int void bool true false invariant precise discard return mat2 mat3 mat4 vec2 vec3 vec4 ivec2 ivec3 ivec4 bvec2 bvec3 bvec4 uint uvec2 uvec3 uvec4 lowp mediump highp precision sampler1D sampler2D sampler3D samplerCube isampler2D usampler2D image2D uimage2D struct common partition active asm class union enum typedef template this resource goto inline noinline public static extern external interface long short half fixed unsigned superp input output hvec2 hvec3 hvec4 fvec2 fvec3 fvec4 sampler3DRect filter sizeof cast namespace using row_major'.split())
for n in names:
 s=(root/n).read_text(); x=re.sub(r'/\*.*?\*/',' ',s,flags=re.S); x=re.sub(r'//.*',' ',x)
 assert '__' not in x,(n,'double underscore')
 decl=re.compile(r'\b(?:bool|int|uint|float|vec[234]|ivec[234]|uvec[234]|mat[234]|sampler2D|usampler2D|image2D|uimage2D)\s+([A-Za-z_]\w*)')
 bad=sorted({m.group(1) for m in decl.finditer(x) if m.group(1) in reserved}); assert not bad,(n,bad)
 for a,b in [('(',')'),('{','}'),('[',']')]: assert x.count(a)==x.count(b),(n,a,b,x.count(a),x.count(b))
print('PASS: GLSL reserved-identifier/delimiter preflight for three changed shaders')
PYLEX
pass "GATE 3 exact eight-path delta + Java/GLSL static preflight"

echo "=== GATE 4: 1.27.1 pinned native dependencies + glslang 16.5.0 + binding/non-regression contracts ==="
BJ="$WORK/bjzhou-$BJZHOU_HEAD"; rm -rf "$BJ"; git init -q "$BJ"; git -C "$BJ" remote add origin https://github.com/bjzhou/PhotonCamera.git
git -C "$BJ" config core.sparseCheckout true
mkdir -p "$BJ/.git/info"; printf '%s\n' '/app/src/main/cpp/libjpeg-turbo/' '/app/src/main/cpp/libultrahdr/' > "$BJ/.git/info/sparse-checkout"
git -C "$BJ" fetch --depth=1 origin "$BJZHOU_HEAD"; git -C "$BJ" checkout -q --detach FETCH_HEAD
[[ "$(git -C "$BJ" rev-parse HEAD)" == "$BJZHOU_HEAD" ]] || fail "bjzhou 1.27.1 dependency checkout drift"
THIRD="$AFTER/app/src/main/cpp/third_party_26507"; mkdir -p "$THIRD"
cp -a "$BJ/app/src/main/cpp/libjpeg-turbo" "$THIRD/libjpeg-turbo"
cp -a "$BJ/app/src/main/cpp/libultrahdr" "$THIRD/libultrahdr"
[[ -f "$THIRD/libjpeg-turbo/CMakeLists.txt" && -f "$THIRD/libjpeg-turbo/src/turbojpeg.h" ]] || fail "pinned libjpeg-turbo layout missing"
[[ -f "$THIRD/libultrahdr/ultrahdr_api.h" && -f "$THIRD/libultrahdr/lib/src/ultrahdr_api.cpp" && -d "$THIRD/libultrahdr/lib/include/ultrahdr" ]] || fail "pinned libultrahdr layout missing"
[[ ! -e "$THIRD/libultrahdr/lib/include/ultrahdr_api.h" ]] || fail "obsolete libultrahdr include layout appeared"
( cd "$THIRD" && sha256sum -c "$BJZHOU_MANIFEST" ) > "$OUT/26511_bjzhou_native_manifest_check.txt"
echo "$BJZHOU_HEAD" > "$OUT/26511_bjzhou_dependency_commit.txt"

grep -F 'IRIS_26511_DEBUG_APK_JPEG_OPTIMIZATION_OWNER' "$AFTER/app/src/main/cpp/CMakeLists.txt" >/dev/null
grep -F 'target_compile_options(turbojpeg-static PRIVATE -O3)' "$AFTER/app/src/main/cpp/CMakeLists.txt" >/dev/null
grep -F 'target_compile_options(jpeg-static PRIVATE -O3)' "$AFTER/app/src/main/cpp/CMakeLists.txt" >/dev/null
grep -F 'target_compile_options(motionv2jpeg PRIVATE -O3)' "$AFTER/app/src/main/cpp/CMakeLists.txt" >/dev/null

command -v glslangValidator >/dev/null || fail "glslangValidator missing"
grep -F '16.5.0' <<<"$(glslangValidator --version | head -1)" >/dev/null || fail "wrong glslangValidator"
python3 - "$AFTER" "$WORK" "$OUT" <<'PYGLSL'
from pathlib import Path
import subprocess,sys
root,work,out=map(Path,sys.argv[1:])
items=[('short_highlight_bayer_recover.glsl','comp',True),('mfsr_spatial_rgb_short_weight_26501.glsl','comp',True),('mfsr_spatial_rgb_normalize_26501.glsl','frag',False)]
for name,stage,layout in items:
 src=(root/'app/src/main/assets/shaders/motionv2'/name).read_text()
 if layout:
  src=src.replace('#define LAYOUT //','',1).replace('LAYOUT','layout(local_size_x=8,local_size_y=8,local_size_z=1) in;',1)
 tmp=work/(name+'.'+stage); tmp.write_text('#version 310 es\n'+src)
 cp=subprocess.run(['glslangValidator','-S',stage,str(tmp)],capture_output=True,text=True)
 (out/(name+'.glslang.txt')).write_text(cp.stdout+cp.stderr)
 if cp.returncode: raise SystemExit('GLSL failed '+name+'\n'+cp.stdout+cp.stderr)
print('PASS: all three 26511 changed shaders compile with glslang 16.5.0')
PYGLSL

python3 - "$AFTER" <<'PYBIND'
from pathlib import Path
import sys
r=Path(sys.argv[1]); base=r/'app/src/main'; host=(base/'java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java').read_text()
short=(base/'assets/shaders/motionv2/short_highlight_bayer_recover.glsl').read_text()
weight=(base/'assets/shaders/motionv2/mfsr_spatial_rgb_short_weight_26501.glsl').read_text()
norm=(base/'assets/shaders/motionv2/mfsr_spatial_rgb_normalize_26501.glsl').read_text()
assert 'layout(r32f, binding = 3) uniform highp writeonly image2D outBentoCandidate;' in short
assert 'setTextureCompute("outBentoCandidate",iris26511ShortBentoCandidate,true)' in host
assert 'uniform highp sampler2D bentoCandidate;' in weight and 'uniform highp sampler2D flowTexture;' in weight
assert 'setTexture("bentoCandidate",iris26511ShortBentoCandidate)' in host
assert 'setTexture("flowTexture",iris26480ShortAlignment.flowTexture)' in host
assert 'layout(rgba32f,binding=0) uniform highp writeonly image2D outWeight;' in weight
assert 'setTextureCompute("outWeight",iris26501ShortWeight,true)' in host
assert 'layout(std430,binding=1) buffer ShortDiagBuf' in weight
assert 'setBufferCompute("ShortDiagBuf",iris26496ShortDiag)' in host
assert 'uniform highp sampler2D shortBentoWeightTexture;' in norm and 'uniform int useShortBentoMask;' in norm
assert 'setVar("useShortBentoMask",iris26501ShortWeight!=null?1:0)' in host
assert 'setTexture("shortBentoWeightTexture"' in host
print('PASS: exact 26511 Short Bento host/shader binding contracts')
PYBIND

# Explicit non-regression checks against successful 26507, not merely marker presence.
for f in \
 'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java' \
 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2WronskiAlignment.java' \
 'app/src/main/assets/shaders/motionv2/mfsr_flow_expand.glsl' \
 'app/src/main/java/com/particlesdevs/photoncamera/processing/MotionBatch.java' \
 'app/src/main/assets/shaders/motionv2/mfsr_bjzhou_rejection_base.glsl' \
 'app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_contribute_26501.glsl' \
 'app/src/main/assets/shaders/motionv2/shadow_aux_bayer_fuse.glsl' \
 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java' \
 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java' \
 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java' \
 'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java'; do
  cmp -s "$BASE/$f" "$AFTER/$f" || fail "protected successful-26507 authority drifted: $f"
done
grep -F '/* updateMotionV2ExposureAuthority(result); intentionally dormant */' "$AFTER/app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java" >/dev/null
if grep -R -F 'IRIS_26509_' "$AFTER/app/src/main" >/dev/null; then fail "rejected 26509 runtime marker survived"; fi
if grep -R -F 'IRIS_26510_' "$AFTER/app/src/main" >/dev/null; then fail "rejected/no-effect 26510 runtime marker survived"; fi
[[ ! -e "$AFTER/app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_vgn_chroma_26510.glsl" ]] || fail "rejected 26510 VGN shader survived"
echo "PRE-BUILD SAFETY PROOF PASSED"
pass "GATE 4 1.27.1 native + shader compiler + exact protected-authority proof"

echo "=== GATE 5: VERSION ${VERSION_NAME} / ${VERSION_BUILD} + BUILD IN SAME GUARDED BLOCK ==="
python3 - "$AFTER/app/version.properties" "$VERSION_NAME" "$VERSION_BUILD" <<'PYVER'
from pathlib import Path
import sys
p=Path(sys.argv[1]); vn=sys.argv[2]; vb=sys.argv[3]; s=p.read_text()
assert 'VERSION_NAME=0.9726507' in s and 'VERSION_BUILD=26507' in s
s=s.replace('VERSION_NAME=0.9726507','VERSION_NAME='+vn).replace('VERSION_BUILD=26507','VERSION_BUILD='+vb)
p.write_text(s); t=p.read_text(); assert 'VERSION_NAME='+vn in t and 'VERSION_BUILD='+vb in t
PYVER
# Overlay only the audited successful-26507 -> 26511 candidate. 26509/26510 runtime is never copied.
rm -rf app/src/main
cp -a "$AFTER/app/src/main" app/src/main
cp "$AFTER/app/version.properties" app/version.properties

# CMake creates exactly four headers under cpp/deps during the native build. Keep that generated
# dependency tree outside the immutable Photon-runtime manifest, but prove its exact contents.
CMAKE_SRC="app/src/main/cpp/CMakeLists.txt"
for needle in 'deps/tiny_dng_writer.h' 'deps/technicallyflac.h' 'deps/archive.h' 'deps/archive_entry.h'; do
  grep -F "$needle" "$CMAKE_SRC" >/dev/null || fail "CMake generated-dependency contract missing: $needle"
done
assert_cpp_deps_exact(){
  local phase="$1" expected actual
  if [[ "$phase" == "pre" ]]; then expected=$'.gitignore';
  else expected=$'.gitignore\narchive.h\narchive_entry.h\ntechnicallyflac.h\ntiny_dng_writer.h'; fi
  actual="$(find app/src/main/cpp/deps -mindepth 1 -maxdepth 1 -type f -printf '%f\n' | LC_ALL=C sort)"
  [[ "$actual" == "$expected" ]] || { printf 'Expected cpp/deps (%s):\n%s\nActual:\n%s\n' "$phase" "$expected" "$actual" >&2; fail "unexpected app/src/main/cpp/deps contents during $phase-build proof"; }
}
assert_cpp_deps_exact pre
audited_runtime_manifest(){
  {
    find app/src/main -type f ! -path 'app/src/main/cpp/third_party_26507/*' ! -path 'app/src/main/cpp/deps/*' -print
    echo app/src/main/cpp/deps/.gitignore
    echo app/version.properties
  } | LC_ALL=C sort | while read -r f; do sha256sum "$f"; done
}
audited_runtime_manifest > "$OUT/26511_pre_gradle_audited_runtime.sha256"
chmod +x ./gradlew
./gradlew clean :app:assembleDebug --stacktrace
assert_cpp_deps_exact post
( cd app/src/main/cpp/deps && sha256sum .gitignore archive.h archive_entry.h technicallyflac.h tiny_dng_writer.h ) > "$OUT/26511_post_gradle_generated_cpp_deps.sha256"
audited_runtime_manifest > "$OUT/26511_post_gradle_audited_runtime.sha256"
if ! cmp -s "$OUT/26511_pre_gradle_audited_runtime.sha256" "$OUT/26511_post_gradle_audited_runtime.sha256"; then
  diff -u "$OUT/26511_pre_gradle_audited_runtime.sha256" "$OUT/26511_post_gradle_audited_runtime.sha256" | tee "$OUT/26511_gradle_runtime_source_diff.txt" >&2 || true
  fail "Gradle mutated audited Photon runtime source; see 26511_gradle_runtime_source_diff.txt"
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
 runtime=[b'IRIS_26511_BENTO_COHERENT_RGB_REGION',b'IRIS_26511_CAPTURE_RELEASE_BEFORE_JPEGR_SAVE',b'IRIS_26511_ASYNC_JPEGR_OUTPUT_COMPLETE',b'IRIS_26511_JPEG444_PARALLEL_TIMING',b'IRIS_26507_JPEG444']
 for m in runtime: assert m in dex,b'missing runtime DEX marker '+m
 assert b'IRIS_26509_' not in dex,b'rejected 26509 runtime marker packaged in DEX'
 assert b'IRIS_26510_' not in dex,b'rejected 26510 runtime marker packaged in DEX'
 shaders=['short_highlight_bayer_recover.glsl','mfsr_spatial_rgb_short_weight_26501.glsl','mfsr_spatial_rgb_normalize_26501.glsl','mfsr_flow_expand.glsl','mfsr_bjzhou_rejection_base.glsl','mfsr_spatial_rgb_contribute_26501.glsl','shadow_aux_bayer_fuse.glsl']
 for n in shaders:
  suffix='assets/shaders/motionv2/'+n; matches=[x for x in names if x.endswith(suffix)]; assert len(matches)==1,(n,matches)
  a=z.read(matches[0]); b=(src/'app/src/main/assets/shaders/motionv2'/n).read_bytes(); assert hashlib.sha256(a).digest()==hashlib.sha256(b).digest(),n+' packaged shader differs from audited source'
 assert not any(x.endswith('assets/shaders/motionv2/mfsr_spatial_rgb_vgn_chroma_26510.glsl') for x in names),'rejected 26510 VGN shader packaged'
print('PASS: APK typed proof: 26511 DEX markers + exact protected/changed shaders + libmotionv2jpeg.so')
PYAPK
sha256sum "$FINAL" > "$OUT/26511_APK.sha256"

# Emit actual successful 26511 source for next incremental build if on-device test accepts it.
rm -rf "$AFTER/app/src/main/cpp/third_party_26507"
( cd "$AFTER" && tar --sort=name --mtime='UTC 2026-08-19 00:00:00' --owner=0 --group=0 --numeric-owner -czf "$OUT/26511_successful_app_source.tar.gz" app/src/main app/version.properties )
( cd "$AFTER" && { find app/src/main -type f -print; echo app/version.properties; } | LC_ALL=C sort | while read -r f; do sha256sum "$f"; done ) > "$OUT/26511_successful_source.sha256"
pass "GATE 5 exactly one 26511 APK built from direct successful-26507 source"

echo "=== GATE 6: SUCCESS ==="
echo "APK: $(basename "$FINAL")"
echo "APK SHA256: $(sha "$FINAL")"
echo "START_HEAD=$START_HEAD"
echo "SOURCE_26507_SHA=$SOURCE_TAR_SHA"
echo "BJZHOU_1_27_1_HEAD=$BJZHOU_HEAD"
pass "26511 complete: 26507 AE/Normal-Wronski protected + coherent Short Bento + chroma-only propagated-noise finish + parallel normal-priority JPEG_R encode"
