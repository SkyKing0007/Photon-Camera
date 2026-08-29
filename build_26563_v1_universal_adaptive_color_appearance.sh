#!/usr/bin/env bash
set -euo pipefail
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
manifest_audited(){
 python3 - "$1" "$2" <<'PY'
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib,sys
root=Path(sys.argv[1]); out=Path(sys.argv[2]); rels=[]
m=root/'app/src/main'
for p in m.rglob('*'):
 if not p.is_file(): continue
 rel=p.relative_to(root).as_posix()
 if rel.startswith('app/src/main/cpp/third_party_26507/') or rel.startswith('app/src/main/cpp/deps/'): continue
 rels.append(rel)
gi=root/'app/src/main/cpp/deps/.gitignore'
if gi.is_file(): rels.append(gi.relative_to(root).as_posix())
rels.extend(('app/version.properties','app/build.gradle')); rels=sorted(set(rels))
def one(rel):
 h=hashlib.sha256()
 with (root/rel).open('rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
 return f'{h.hexdigest()}  {rel}'
with ThreadPoolExecutor(max_workers=32) as pool: lines=list(pool.map(one,rels))
out.write_text('\n'.join(lines)+'\n')
PY
}
vendor_manifest(){
 python3 - "$1" "$2" <<'PY'
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib,sys
root=Path(sys.argv[1]); out=Path(sys.argv[2]); rels=[]
for base in ('app/src/main/cpp/third_party_26507','app/src/main/cpp/deps'):
 p=root/base
 if p.is_dir(): rels.extend(x.relative_to(root).as_posix() for x in p.rglob('*') if x.is_file())
rels=sorted(rels)
def one(rel):
 h=hashlib.sha256()
 with (root/rel).open('rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
 return f'{h.hexdigest()}  {rel}'
with ThreadPoolExecutor(max_workers=32) as pool: lines=list(pool.map(one,rels))
out.write_text('\n'.join(lines)+'\n')
PY
}

ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
BASE_SUCCESS_COMMIT="3a7f9c192eecd4ecefc53491e0acfb928478c21e"
BASE_RUN_ID="33275727405"
BASE_ARTIFACT_ID="9721461694"
BASE_ARTIFACT_NAME="photon-26562-v1-1-sabre-sr-dng-lifecycle"
BASE_ARTIFACT_SHA="7943c16ae154922123060d27b6cd7a35802e800f098ee2fa8bbed5fb13599700"
BASE_TAR_SHA="e9ae4395a5df906eb34a1ec1feeeb6c6b6a944f349ab66686adcfa8b6a6baea0"
BASE_MANIFEST_SHA="347c460657b48eb06182690353fbe1cfadd00c4bc7eb8b446d1e25c3a40c8809"
CAND_MANIFEST_SHA="c1fae8c6691b3d900c25c249f1c96abefa761dd828b18e8b27bf8def53afcae4"
VENDOR_MANIFEST_SHA="7dbcc5ee5b9040965e431d79c45c5100f559c2b96c50970ca21987c684c825a8"
PROTECTED_CORE_SHA="c9fe8ac660520165c40dbc68e1071f4ba88bc99f102b2a5f20a06710a6ccd2a8"
PREWRITE_MANIFEST_SHA="d89fe26d2d3914c22b3c3c86da4545fd044f09b09f7d2be05f66296f412f91bb"
CAND_CHANGED_MANIFEST_SHA="4ab57944c7097729d3acb66461d89e9fd29c24a5c2796112c61759018687936d"
RUNTIME_PATHS_SHA="d07149649c1cc38cfd2bf5c5ad2c661833029c269115b21d471a11267c45948c"
RUNTIME_GLSL_MANIFEST_SHA="0b441171bcffcc7e68d38705e68184b358680a6300ae9462aba30875d1c90b3f"
FORWARD_SHA="52f15d5c46e1e9eccfcfcb6b8aa6448c903f1164a00be13c952d165cfa189b61"
ROLLBACK_SHA="9521402c32794f9793a4d8f1aa3401492b05a416d058fb598c6fad2e997c3e57"
GLSLANG_PKG_VERSION="15.1.0-2~ubuntu0.24.04.2"
BACKUP_BRANCH="backup-26562-v1-1-before-26563-universal-adaptive-color-appearance"
BACKUP_SHA_EXPECTED="$BASE_SUCCESS_COMMIT"
VERSION_NAME="0.9726563"
VERSION_BUILD="26563"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"

BASE_PIN="$ROOT/V1_26563_BASE_26562_V1_1_AUDITED_RUNTIME.sha256"
BASE_TAR_PIN="$ROOT/V1_26563_BASE_26562_V1_1_CANDIDATE_TAR.sha256"
CAND_PIN="$ROOT/V1_26563_EXPECTED_CANDIDATE_AUDITED_RUNTIME.sha256"
VENDOR_PIN="$ROOT/V1_26563_NATIVE_VENDOR_DEPENDENCIES.sha256"
RUNTIME_LIST="$ROOT/V1_26563_RUNTIME_CHANGED_PATHS.txt"
PREWRITE="$ROOT/V1_26563_PREWRITE_SOURCE_HASHES.sha256"
CAND_CHANGED="$ROOT/V1_26563_CANDIDATE_CHANGED_HASHES.sha256"
PROTECTED_CORE="$ROOT/V1_26563_PROTECTED_UNCHANGED_CORE.sha256"
RUNTIME_GLSL_PIN="$ROOT/V1_26563_RUNTIME_EXPANDED_GLSL.sha256"
FORWARD="$ROOT/V1_26563_RUNTIME_DELTA_FROM_26562_V1_1.patch"
ROLLBACK="$ROOT/V1_26563_RUNTIME_ROLLBACK_TO_26562_V1_1.patch"
TRANSFORM="$ROOT/transform_26563_v1_universal_adaptive_color_appearance.py"
VALIDATE="$ROOT/validate_26563_v1_universal_adaptive_color_appearance.py"
EXTRACT="$ROOT/extract_26563_runtime_glsl.py"
RESERVED="$ROOT/scan_glsl_reserved_identifiers_26563.py"
HANDOFF_HASHES="$ROOT/V1_26563_HANDOFF_HASHES.sha256"
OUT="$ROOT/build_26563_v1_universal_adaptive_color_appearance_outputs"
WORK="$ROOT/.build_26563_v1_universal_adaptive_color_appearance_work"
ARTZIP="$WORK/26562_v1_1_artifact.zip"
ARTDIR="$WORK/artifact"
BASE="$WORK/exact_26562_v1_1_compiled_candidate"
AFTER="$WORK/candidate_26563"
GLSLOUT="$WORK/runtime_glsl"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-v1-universal-adaptive-color-appearance-debug.apk"
LOCAL_REPLAY_ARTIFACT=""
if [[ "${1:-}" == "--local-prebuild" ]]; then [[ -n "${2:-}" ]] || fail "--local-prebuild requires exact 26562 V1.1 artifact ZIP"; LOCAL_REPLAY_ARTIFACT="$2"; fi
mapfile -t RUNTIME_FILES < "$RUNTIME_LIST"
[[ "${#RUNTIME_FILES[@]}" -eq 4 ]] || fail "runtime changed-path inventory must contain exactly 4 paths"

rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR" "$BASE" "$AFTER" "$GLSLOUT"
cat > "$OUT/26563_V1_COMPILER_STATUS.txt" <<'EOF'
REAL GLSL COMPILE: NOT RUN YET
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
NATIVE/NDK COMPILE: NOT RUN YET (covered by full assemble)
FULL ANDROID ASSEMBLE: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
EOF
cat > "$OUT/26563_V1_STRICT_HANDOFF_REPORT.txt" <<'EOF'
RUNTIME OWNERSHIP: NOT RUN
EXACT PRIOR RUNTIME AUTHORITY: NOT RUN
BACKUP STATUS: NOT RUN
CHANGED RUNTIME SCOPE: NOT RUN
26561 CHROMA CLEANUP SEPARATION: NOT RUN
COMMON LINEAR RGB INSERTION: NOT RUN
MOTION/NIGHT X SR COVERAGE: NOT RUN
POSITIVE SATURATION BOOST SEMANTIC: NOT RUN
ANTI-OVERSATURATION: NOT RUN
HUE/LUMINANCE PRESERVATION: NOT RUN
HIGHLIGHT/CLIPPED BORDER SAFETY: NOT RUN
CHROMA NOISE/EDGE SAFETY: NOT RUN
NO MANUFACTURER-SPECIFIC TUNING: NOT RUN
DNG/SABRE/SR/LIFECYCLE INVARIANCE: NOT RUN
PREINSTALL VENDOR AUTHORITY ORDERING: NOT RUN
LIVE REPOSITORY EXTRAS SCOPE REGRESSION: NOT RUN
GLSL RESERVED-IDENTIFIER SCAN: NOT RUN
EXACT RUNTIME-EXPANDED GLSL: NOT RUN
REAL GLSL COMPILE: NOT RUN
REAL KOTLIN COMPILE: NOT RUN
REAL JAVA COMPILE: NOT RUN
NATIVE/NDK COMPILE: NOT RUN
FULL ANDROID ASSEMBLE: NOT RUN
FORWARD PATCH FUZZ=0: NOT RUN
ROLLBACK PATCH FUZZ=0: NOT RUN
POST-BUILD INVARIANCE: NOT RUN
CLEAN ARTIFACT SOURCE EXPORT: NOT RUN
TARGET VERSION/BUILD: 0.9726563 / 26563 V1
EOF
set_report(){
 local key="$1" val="$2" tmp="$OUT/.26563_report.tmp"
 awk -v key="$key:" -v val="$val" 'BEGIN{found=0} index($0,key)==1{print key" "val; found=1; next} {print} END{if(!found) exit 42}' "$OUT/26563_V1_STRICT_HANDOFF_REPORT.txt" > "$tmp" || { rm -f "$tmp"; fail "report key missing $key"; }
 mv "$tmp" "$OUT/26563_V1_STRICT_HANDOFF_REPORT.txt"
}

verify_package_and_pins(){
 sha256sum -c "$HANDOFF_HASHES"
 python3 -m py_compile "$TRANSFORM" "$VALIDATE" "$EXTRACT" "$RESERVED"
 python3 "$VALIDATE" --self-test
 python3 "$EXTRACT" --self-test
 python3 "$RESERVED" --self-test
 bash -n "$0"
 [[ "$(wc -l < "$BASE_PIN")" -eq 927 && "$(sha "$BASE_PIN")" == "$BASE_MANIFEST_SHA" ]] || fail "base runtime manifest pin"
 [[ "$(wc -l < "$CAND_PIN")" -eq 929 && "$(sha "$CAND_PIN")" == "$CAND_MANIFEST_SHA" ]] || fail "candidate runtime manifest pin"
 [[ "$(wc -l < "$VENDOR_PIN")" -eq 778 && "$(sha "$VENDOR_PIN")" == "$VENDOR_MANIFEST_SHA" ]] || fail "vendor manifest pin"
 [[ "$(wc -l < "$PROTECTED_CORE")" -eq 18 && "$(sha "$PROTECTED_CORE")" == "$PROTECTED_CORE_SHA" ]] || fail "protected manifest pin"
 [[ "$(wc -l < "$PREWRITE")" -eq 2 && "$(sha "$PREWRITE")" == "$PREWRITE_MANIFEST_SHA" ]] || fail "prewrite manifest pin"
 ! grep -Eq '  /' "$PREWRITE" || fail "prewrite manifest contains absolute path"
 ! grep -Eq '  /' "$CAND_CHANGED" || fail "candidate changed manifest contains absolute path"
 [[ "$(wc -l < "$CAND_CHANGED")" -eq 4 && "$(sha "$CAND_CHANGED")" == "$CAND_CHANGED_MANIFEST_SHA" ]] || fail "candidate changed manifest pin"
 [[ "$(wc -l < "$RUNTIME_LIST")" -eq 4 && "$(sha "$RUNTIME_LIST")" == "$RUNTIME_PATHS_SHA" ]] || fail "runtime changed-path pin"
 [[ "$(wc -l < "$RUNTIME_GLSL_PIN")" -eq 2 && "$(sha "$RUNTIME_GLSL_PIN")" == "$RUNTIME_GLSL_MANIFEST_SHA" ]] || fail "runtime GLSL pin"
 [[ "$(sha "$FORWARD")" == "$FORWARD_SHA" && "$(sha "$ROLLBACK")" == "$ROLLBACK_SHA" ]] || fail "canonical patch SHA"
 grep -F "$BASE_TAR_SHA" "$BASE_TAR_PIN" >/dev/null || fail "base TAR pin drift"
}

verify_base_artifact_and_reconstruct(){
 local zip="$1"; [[ "$(sha "$zip")" == "$BASE_ARTIFACT_SHA" ]] || fail "26562 V1.1 artifact ZIP SHA mismatch"
 rm -rf "$ARTDIR"; mkdir -p "$ARTDIR"
 unzip -q "$zip" 'build_26562_v1_sabre_sr_dng_lifecycle_outputs/*' -d "$ARTDIR"
 local bo="$ARTDIR/build_26562_v1_sabre_sr_dng_lifecycle_outputs"
 local bt="$bo/26562_V1_candidate_app_source.tar.gz" bm="$bo/26562_V1_candidate_source.sha256" bc="$bo/26562_V1_COMPILER_STATUS.txt" bv="$bo/26562_vendor_postbuild.sha256" ba="$bo/26562_V1_APK.sha256"
 for f in "$bt" "$bm" "$bc" "$bv" "$ba"; do [[ -f "$f" ]] || fail "base artifact missing $f"; done
 [[ "$(sha "$bt")" == "$BASE_TAR_SHA" && "$(sha "$bm")" == "$BASE_MANIFEST_SHA" ]] || fail "base TAR/manifest SHA mismatch"
 cmp "$bm" "$BASE_PIN" >/dev/null || fail "packaged base pin differs from successful 26562 V1.1"
 cmp "$bv" "$VENDOR_PIN" >/dev/null || fail "base vendor proof differs from pin"
 for status in 'REAL GLSL COMPILE: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS'; do grep -F "$status" "$bc" >/dev/null || fail "26562 compiler proof missing: $status"; done
 rm -rf "$BASE"; mkdir -p "$BASE"; tar -xzf "$bt" -C "$BASE"
 manifest_audited "$BASE" "$WORK/base_reconstructed.sha256"; cmp "$WORK/base_reconstructed.sha256" "$BASE_PIN" >/dev/null || fail "reconstructed 26562 runtime mismatch"
 vendor_manifest "$BASE" "$WORK/base_vendor_reconstructed.sha256"; cmp "$WORK/base_vendor_reconstructed.sha256" "$VENDOR_PIN" >/dev/null || fail "reconstructed 26562 vendor mismatch"
 set_report "EXACT PRIOR RUNTIME AUTHORITY" "PASS (run ${BASE_RUN_ID} artifact ${BASE_ARTIFACT_ID})"; pass "exact successful compiled 26562 V1.1 authority"
}

candidate_diff_paths(){ python3 - "$1" "$2" <<'PY'
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib,sys
def T(root):
 root=Path(root); paths=sorted(p for p in (root/'app').rglob('*') if p.is_file())
 def one(p):
  h=hashlib.sha256()
  with p.open('rb') as f:
   for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
  return p.relative_to(root).as_posix(),h.hexdigest()
 with ThreadPoolExecutor(max_workers=32) as pool: return dict(pool.map(one,paths))
a,b=T(Path(sys.argv[1])),T(Path(sys.argv[2])); print('\n'.join(sorted(k for k in set(a)|set(b) if a.get(k)!=b.get(k))))
PY
}
seed_scope(){ local source="$1" dest="$2"; rm -rf "$dest"; mkdir -p "$dest"; while read -r rel; do if [[ -f "$source/$rel" ]]; then mkdir -p "$dest/$(dirname "$rel")"; cp -a "$source/$rel" "$dest/$rel"; fi; done < "$RUNTIME_LIST"; }
apply_state_to_scope(){ local source="$1" dest="$2"; while read -r rel; do if [[ -f "$source/$rel" ]]; then mkdir -p "$dest/$(dirname "$rel")"; cp -a "$source/$rel" "$dest/$rel"; else rm -f "$dest/$rel"; fi; done < "$RUNTIME_LIST"; }

build_candidate_and_precompile_proof(){
 rm -rf "$AFTER"; mkdir -p "$AFTER"; cp -a "$BASE/." "$AFTER/"
 (cd "$AFTER" && sha256sum -c "$PREWRITE")
 [[ ! -e "$AFTER/app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2AdaptiveColorAppearance.java" ]] || fail "26563 node unexpectedly exists before transform"
 [[ ! -e "$AFTER/app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl" ]] || fail "26563 shader unexpectedly exists before transform"
 python3 "$TRANSFORM" "$AFTER"
 manifest_audited "$AFTER" "$WORK/candidate_manifest.sha256"; cmp "$WORK/candidate_manifest.sha256" "$CAND_PIN" >/dev/null || fail "candidate manifest differs from pin"
 (cd "$AFTER" && sha256sum -c "$CAND_CHANGED")
 mapfile -t got < <(candidate_diff_paths "$BASE" "$AFTER")
 mapfile -t want < <(LC_ALL=C sort "$RUNTIME_LIST")
 [[ "${got[*]}" == "${want[*]}" ]] || fail "exact 4-path candidate diff mismatch got=${got[*]} want=${want[*]}"
 python3 "$VALIDATE" "$BASE" "$AFTER" | tee "$OUT/26563_focused_architecture_validation.txt"
 (cd "$AFTER" && sha256sum -c "$PROTECTED_CORE")
 set_report "RUNTIME OWNERSHIP" "PASS (common-linear-sRGB appearance only; Sabre/DNG ownership unchanged)"
 set_report "CHANGED RUNTIME SCOPE" "PASS (exact 4 paths; one new Java node + one new shader + post graph + version)"
 set_report "26561 CHROMA CLEANUP SEPARATION" "PASS (byte-identical; remains never-boosts-saturation cleanup)"
 set_report "COMMON LINEAR RGB INSERTION" "PASS (after device profile transform/exposure solve; before display gain/tone/highlight/gamut)"
 set_report "MOTION/NIGHT X SR COVERAGE" "PASS (Motion/Night, SR OFF/ON, exactly once; DNG bypasses appearance stage)"
 set_report "POSITIVE SATURATION BOOST SEMANTIC" "PASS (weak legitimate chroma_out > chroma_in; >15% regression)"
 set_report "ANTI-OVERSATURATION" "PASS (max 1.22 weak gain; medium rolloff; strong chroma ~1x)"
 set_report "HUE/LUMINANCE PRESERVATION" "PASS (single chroma-axis scalar around Rec.709 linear luminance)"
 set_report "HIGHLIGHT/CLIPPED BORDER SAFETY" "PASS (highlight rolloff; projected/input clipping hard 1x; gamut bound)"
 set_report "CHROMA NOISE/EDGE SAFETY" "PASS (local coherence/agreement/edge gates; neighbors never mixed into output)"
 set_report "NO MANUFACTURER-SPECIFIC TUNING" "PASS"
 set_report "DNG/SABRE/SR/LIFECYCLE INVARIANCE" "PASS (18 focused files byte-identical)"

 rm -rf "$GLSLOUT"; mkdir -p "$GLSLOUT"
 python3 "$EXTRACT" --root "$AFTER" --out "$GLSLOUT" | tee "$OUT/26563_runtime_glsl_extraction.txt"
 (cd "$GLSLOUT" && sha256sum -c "$RUNTIME_GLSL_PIN")
 python3 "$RESERVED" "$GLSLOUT"/* | tee "$OUT/26563_reserved_identifier_scan.txt"
 set_report "GLSL RESERVED-IDENTIFIER SCAN" "PASS (exact runtime vertex+fragment; coherent+sample regressions retained)"
 set_report "EXACT RUNTIME-EXPANDED GLSL" "PASS (2-file hash pin)"

 local P="$WORK/patchscope"
 seed_scope "$BASE" "$P"
 (cd "$P"; git init -q; git config user.name Photon; git config user.email photon@example.invalid; git add -A; git commit -qm base)
 local BASE_PATCH_COMMIT; BASE_PATCH_COMMIT="$(cd "$P" && git rev-parse HEAD)"
 apply_state_to_scope "$AFTER" "$P"
 (cd "$P"; git add -A; git commit -qm candidate)
 local CAND_PATCH_COMMIT; CAND_PATCH_COMMIT="$(cd "$P" && git rev-parse HEAD)"
 for ab in 7 12 40; do
  (cd "$P" && git -c core.abbrev="$ab" diff --binary --full-index --no-ext-diff "$BASE_PATCH_COMMIT" "$CAND_PATCH_COMMIT") > "$WORK/forward.$ab.patch"
  (cd "$P" && git -c core.abbrev="$ab" diff --binary --full-index --no-ext-diff "$CAND_PATCH_COMMIT" "$BASE_PATCH_COMMIT") > "$WORK/rollback.$ab.patch"
 done
 cmp "$WORK/forward.7.patch" "$WORK/forward.12.patch"; cmp "$WORK/forward.7.patch" "$WORK/forward.40.patch"; cmp "$WORK/forward.40.patch" "$FORWARD"
 cmp "$WORK/rollback.7.patch" "$WORK/rollback.12.patch"; cmp "$WORK/rollback.7.patch" "$WORK/rollback.40.patch"; cmp "$WORK/rollback.40.patch" "$ROLLBACK"
 local FP="$WORK/patchproof"
 seed_scope "$BASE" "$FP"
 (cd "$FP"; git init -q; git config user.name Photon; git config user.email photon@example.invalid; git add -A; git commit -qm base; git apply --check "$FORWARD"; git apply "$FORWARD"; sha256sum -c "$CAND_CHANGED"; git add -A; git commit -qm candidate-applied; git apply --check "$ROLLBACK"; git apply "$ROLLBACK"; sha256sum -c "$PREWRITE"; [[ ! -e app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2AdaptiveColorAppearance.java ]]; [[ ! -e app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl ]])
 set_report "FORWARD PATCH FUZZ=0" "PASS"; set_report "ROLLBACK PATCH FUZZ=0" "PASS"; pass "candidate semantics / exact GLSL / deterministic patches"
}

run_real_glsl(){
 if ! command -v glslangValidator >/dev/null 2>&1 || [[ "$(dpkg-query -W -f='${Version}' glslang-tools 2>/dev/null || true)" != "$GLSLANG_PKG_VERSION" ]]; then sudo apt-get update -qq; sudo apt-get install -y --no-install-recommends "glslang-tools=${GLSLANG_PKG_VERSION}"; fi
 [[ "$(dpkg-query -W -f='${Version}' glslang-tools)" == "$GLSLANG_PKG_VERSION" ]] || fail "wrong glslang package"
 glslangValidator --version | tee "$OUT/26563_glslang_version.txt"; grep -F 'Khronos. 15.1.0' "$OUT/26563_glslang_version.txt" >/dev/null || fail "glslang version not 15.1.0"
 glslangValidator -S vert "$GLSLOUT/adaptive_color_appearance_26563.vert"
 glslangValidator -S frag "$GLSLOUT/adaptive_color_appearance_26563.frag"
 glslangValidator -l "$GLSLOUT/adaptive_color_appearance_26563.vert" "$GLSLOUT/adaptive_color_appearance_26563.frag"
 python3 - "$OUT/26563_V1_COMPILER_STATUS.txt" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]); p.write_text(p.read_text().replace('REAL GLSL COMPILE: NOT RUN YET','REAL GLSL COMPILE: PASS'))
PY
 set_report "REAL GLSL COMPILE" "PASS (pinned 15.1.0 exact runtime-expanded 26563 vertex+fragment)"; pass "real GLSL compile"
}

install_frozen_candidate_into_live_root(){
 local live="$1" label="$2"; [[ -d "$live/app" ]] || fail "live fixture missing app"
 manifest_audited "$live" "$WORK/${label}_preinstall_runtime.sha256"; vendor_manifest "$live" "$WORK/${label}_preinstall_vendor.sha256"
 rm -rf "$live/app/src/main" "$live/app/version.properties" "$live/app/build.gradle"; mkdir -p "$live/app/src"; cp -a "$AFTER/app/src/main" "$live/app/src/"; cp "$AFTER/app/version.properties" "$live/app/version.properties"; cp "$AFTER/app/build.gradle" "$live/app/build.gradle"
 manifest_audited "$live" "$WORK/${label}_installed_runtime.sha256"; cmp "$WORK/${label}_installed_runtime.sha256" "$CAND_PIN" >/dev/null || fail "installed runtime != candidate"
 vendor_manifest "$live" "$WORK/${label}_installed_vendor.sha256"; cmp "$WORK/${label}_installed_vendor.sha256" "$VENDOR_PIN" >/dev/null || fail "installed vendor != successful authority"
 python3 "$VALIDATE" "$BASE" "$live" > "$OUT/${label}_installed_contract.txt"
}
run_preinstall_vendor_authority_regression(){
 local f="$WORK/stale_checkout"; rm -rf "$f"; mkdir -p "$f/app/src/main/cpp/third_party_26507" "$f/app/src/main/cpp/deps"; printf 'stale\n' > "$f/app/src/main/cpp/third_party_26507/stale.txt"; printf 'VERSION_NAME=stale\nVERSION_BUILD=0\n' > "$f/app/version.properties"; printf '// stale\n' > "$f/app/build.gradle"
 vendor_manifest "$f" "$WORK/stale_vendor.sha256"; ! cmp -s "$WORK/stale_vendor.sha256" "$VENDOR_PIN" || fail "stale fixture invalid"; install_frozen_candidate_into_live_root "$f" regression
 set_report "PREINSTALL VENDOR AUTHORITY ORDERING" "PASS (stale checkout allowed only before frozen candidate install; exact vendor equality after install)"; pass "permanent vendor-authority regression"
}
run_live_repository_extras_scope_regression(){
 local f="$WORK/live_repository_extras_scope_regression"
 rm -rf "$f"; mkdir -p "$f"; cp -a "$AFTER/app" "$f/app"
 local extras=(
  '.gitignore' 'SupportedList.txt' 'proguard-rules.pro'
  'src/androidTest/java/com/particlesdevs/photoncamera/gallery/adapters/DepthPageTransformerTest.java'
  'src/test/java/android/util/Log.java'
  'src/test/java/com/particlesdevs/photoncamera/capture/CaptureControllerTest.java'
  'src/test/java/com/particlesdevs/photoncamera/debugclient/DebugClientTest.java'
  'src/test/java/com/particlesdevs/photoncamera/processing/render/ColorCorrectionTransformTest.java'
  'src/test/java/com/particlesdevs/photoncamera/ui/camera/CustomOrientationEventListenerTest.java'
  'src/test/java/com/particlesdevs/photoncamera/ui/camera/TestSwitchToMode.java'
  'src/test/java/com/particlesdevs/photoncamera/ui/camera/TestSwitchToModeTest.java'
  'src/test/java/com/particlesdevs/photoncamera/util/RANSACTest.java'
  'src/test/java/com/particlesdevs/photoncamera/util/UtilitiesTest.java'
 )
 for rel in "${extras[@]}"; do mkdir -p "$(dirname "$f/app/$rel")"; printf '26562 V1 exact Actions extras-scope regression\n' > "$f/app/$rel"; done
 python3 "$VALIDATE" "$BASE" "$f" > "$OUT/live_repository_extras_scope_regression.txt"
 grep -F 'PASS exact 4-file 26563 runtime allowlist' "$OUT/live_repository_extras_scope_regression.txt" >/dev/null || fail "live repository extras-scope regression did not reach allowlist PASS"
 set_report "LIVE REPOSITORY EXTRAS SCOPE REGRESSION" "PASS (exact 13 paths from 26562 V1 Actions failure ignored outside audited runtime scope)"
 pass "permanent 26562 V1 live-repository extras-scope regression"
}

if [[ -n "$LOCAL_REPLAY_ARTIFACT" ]]; then
 echo "=== 26563 LOCAL PREBUILD: package/pins ==="; verify_package_and_pins
 echo "=== 26563 LOCAL PREBUILD: exact 26562 V1.1 artifact ==="; verify_base_artifact_and_reconstruct "$LOCAL_REPLAY_ARTIFACT"
 echo "=== 26563 LOCAL PREBUILD: transform/audit/semantic/GLSL/patches ==="; build_candidate_and_precompile_proof
 echo "=== 26563 LOCAL PREBUILD: vendor regression ==="; run_preinstall_vendor_authority_regression
 echo "=== 26563 LOCAL PREBUILD: live-repository extras-scope regression ==="; run_live_repository_extras_scope_regression
 if command -v glslangValidator >/dev/null 2>&1 && command -v dpkg-query >/dev/null 2>&1 && [[ "$(dpkg-query -W -f='${Version}' glslang-tools 2>/dev/null || true)" == "$GLSLANG_PKG_VERSION" ]]; then run_real_glsl; else echo 'LOCAL REAL GLSL COMPILE: NOT RUN (pinned package unavailable locally)' | tee "$OUT/26563_V1_LOCAL_COMPILER_LIMIT.txt"; fi
 echo 'LOCAL REAL KOTLIN/JAVA/ASSEMBLE: NOT RUN (authoritative Actions gate)' | tee -a "$OUT/26563_V1_LOCAL_COMPILER_LIMIT.txt"; pass "26563 local prebuild replay complete"; exit 0
fi

# Actions authoritative sequence, matching successful 26562 V1.1 comparison/install semantics.
echo "=== 26563 GATE 0: sealed handoff / direct lineage / architectural backup ==="
[[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch"
[[ "$(git rev-parse HEAD^)" == "$BASE_SUCCESS_COMMIT" ]] || fail "26563 handoff must be direct child of successful 26562 V1.1"
git diff --quiet "$BASE_SUCCESS_COMMIT..HEAD" -- app || fail "handoff directly changed repository app source"
[[ -n "$TOKEN" ]] || fail "GITHUB_TOKEN missing"; verify_package_and_pins
BACKUP_SHA="$(git ls-remote origin "refs/heads/${BACKUP_BRANCH}" | awk '{print $1}')"; [[ "$BACKUP_SHA" == "$BACKUP_SHA_EXPECTED" ]] || fail "backup missing/wrong"
set_report "BACKUP STATUS" "PASS (${BACKUP_BRANCH} @ ${BACKUP_SHA_EXPECTED})"
python3 - "$BASE_SUCCESS_COMMIT" <<'PY'
import subprocess,sys
base=sys.argv[1]
allowed={
'.github/workflows/build-26563-v1-universal-adaptive-color-appearance.yml',
'V1_26563_BASE_26562_V1_1_AUDITED_RUNTIME.sha256','V1_26563_BASE_26562_V1_1_CANDIDATE_TAR.sha256','V1_26563_BASE_PROVENANCE.txt',
'V1_26563_CANDIDATE_CHANGED_HASHES.sha256','V1_26563_EXPECTED_CANDIDATE_AUDITED_RUNTIME.sha256','V1_26563_HANDOFF_HASHES.sha256',
'V1_26563_LOCAL_VALIDATION.txt','V1_26563_NATIVE_VENDOR_DEPENDENCIES.sha256','V1_26563_PREWRITE_SOURCE_HASHES.sha256',
'V1_26563_PROTECTED_UNCHANGED_CORE.sha256','V1_26563_RUNTIME_DELTA_FROM_26562_V1_1.patch','V1_26563_RUNTIME_EXPANDED_GLSL.sha256',
'V1_26563_RUNTIME_CHANGED_PATHS.txt','V1_26563_RUNTIME_ROLLBACK_TO_26562_V1_1.patch','V1_26563_UPLOAD_INSTRUCTIONS.md',
'build_26563_v1_universal_adaptive_color_appearance.sh','extract_26563_runtime_glsl.py','scan_glsl_reserved_identifiers_26563.py',
'transform_26563_v1_universal_adaptive_color_appearance.py','validate_26563_v1_universal_adaptive_color_appearance.py'}
actual=set(subprocess.check_output(['git','diff','--name-only',base+'..HEAD'],text=True).splitlines())
if actual!=allowed: raise SystemExit('handoff scope mismatch extra=%r missing=%r'%(sorted(actual-allowed),sorted(allowed-actual)))
if any(x.startswith('app/') for x in actual): raise SystemExit('handoff modified repository app source')
print('PASS exact 21-file 26563 handoff scope')
PY
pass "sealed 26563 package / lineage / backup"

echo "=== 26563 GATE 1: exact successful compiled 26562 V1.1 authority ==="
REPO_API="https://api.github.com/repos/${GITHUB_REPOSITORY:-SkyKing0007/Photon-Camera}"
curl --fail --location --silent --show-error --retry 5 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' -H 'X-GitHub-Api-Version: 2022-11-28' "$REPO_API/actions/runs/${BASE_RUN_ID}" -o "$WORK/base_run.json"
python3 - "$WORK/base_run.json" "$BASE_RUN_ID" "$BASE_SUCCESS_COMMIT" "$EXPECTED_BRANCH" <<'PY'
import json,sys
d=json.load(open(sys.argv[1])); assert str(d.get('id'))==sys.argv[2] and d.get('conclusion')=='success' and d.get('head_sha')==sys.argv[3] and d.get('head_branch')==sys.argv[4]; print('PASS exact successful 26562 V1.1 Actions run')
PY
curl --fail --location --silent --show-error --retry 5 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' -H 'X-GitHub-Api-Version: 2022-11-28' "$REPO_API/actions/artifacts/${BASE_ARTIFACT_ID}" -o "$WORK/base_artifact.json"
python3 - "$WORK/base_artifact.json" "$BASE_ARTIFACT_ID" "$BASE_ARTIFACT_NAME" "$BASE_ARTIFACT_SHA" <<'PY'
import json,sys
d=json.load(open(sys.argv[1])); assert str(d.get('id'))==sys.argv[2] and d.get('name')==sys.argv[3] and not d.get('expired') and d.get('digest')=='sha256:'+sys.argv[4]; print('PASS exact 26562 V1.1 artifact metadata/digest')
PY
curl --fail --location --silent --show-error --retry 5 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' -H 'X-GitHub-Api-Version: 2022-11-28' "$REPO_API/actions/artifacts/${BASE_ARTIFACT_ID}/zip" -o "$ARTZIP"
verify_base_artifact_and_reconstruct "$ARTZIP"

echo "=== 26563 GATE 2: candidate-first transform / color semantics / exact GLSL / patches ==="; build_candidate_and_precompile_proof
echo "=== 26563 GATE 3: pinned real glslangValidator ==="; run_real_glsl
echo "=== 26563 GATE 4: controlled live install / exact regressions / real Kotlin+Java / full assemble ==="
run_preinstall_vendor_authority_regression; run_live_repository_extras_scope_regression; install_frozen_candidate_into_live_root "$ROOT" repository
rm -rf "$ROOT/app/build/outputs/apk/debug"
./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace
python3 - "$OUT/26563_V1_COMPILER_STATUS.txt" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]); p.write_text(p.read_text().replace('REAL KOTLIN COMPILE: NOT RUN YET','REAL KOTLIN COMPILE: PASS').replace('REAL JAVA COMPILE: NOT RUN YET','REAL JAVA COMPILE: PASS'))
PY
set_report "REAL KOTLIN COMPILE" PASS; set_report "REAL JAVA COMPILE" PASS
./gradlew :app:assembleDebug --stacktrace
python3 - "$OUT/26563_V1_COMPILER_STATUS.txt" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]); p.write_text(p.read_text().replace('NATIVE/NDK COMPILE: NOT RUN YET (covered by full assemble)','NATIVE/NDK COMPILE: PASS (full assemble)').replace('FULL ANDROID ASSEMBLE: NOT RUN YET','FULL ANDROID ASSEMBLE: PASS'))
PY
set_report "NATIVE/NDK COMPILE" "PASS (full assemble)"; set_report "FULL ANDROID ASSEMBLE" PASS
mapfile -t APKS < <(find "$ROOT/app/build/outputs/apk/debug" -maxdepth 1 -type f -name '*.apk' -print); [[ "${#APKS[@]}" -eq 1 ]] || fail "expected exactly one debug APK, found ${#APKS[@]}"; mv "${APKS[0]}" "$FINAL"; [[ -s "$FINAL" ]] || fail "final APK missing"; [[ "$(find "$ROOT/app/build/outputs/apk/debug" -maxdepth 1 -type f -name '*.apk' | wc -l)" -eq 0 ]] || fail "duplicate APK remained"; sha256sum "$FINAL" > "$OUT/26563_V1_APK.sha256"; pass "real Kotlin/Java/NDK + full assemble + exactly one APK"

echo "=== 26563 GATE 5: post-build frozen candidate / protected / native/vendor / exact GLSL invariance ==="
manifest_audited "$ROOT" "$OUT/26563_postbuild_runtime.sha256"; cmp "$OUT/26563_postbuild_runtime.sha256" "$CAND_PIN" >/dev/null || fail "postbuild runtime changed"
manifest_audited "$AFTER" "$OUT/26563_frozen_candidate_postbuild.sha256"; cmp "$OUT/26563_frozen_candidate_postbuild.sha256" "$CAND_PIN" >/dev/null || fail "frozen candidate changed"
vendor_manifest "$ROOT" "$OUT/26563_vendor_postbuild.sha256"; cmp "$OUT/26563_vendor_postbuild.sha256" "$VENDOR_PIN" >/dev/null || fail "vendor changed during build"
(cd "$ROOT" && sha256sum -c "$PROTECTED_CORE")
rm -rf "$WORK/runtime_glsl_post"; mkdir -p "$WORK/runtime_glsl_post"; python3 "$EXTRACT" --root "$ROOT" --out "$WORK/runtime_glsl_post" >/dev/null; (cd "$WORK/runtime_glsl_post" && sha256sum -c "$RUNTIME_GLSL_PIN"); python3 "$RESERVED" "$WORK/runtime_glsl_post"/* > "$OUT/26563_postbuild_reserved_identifier_scan.txt"
python3 "$VALIDATE" "$BASE" "$ROOT" > "$OUT/26563_postbuild_focused_validation.txt"
python3 - "$OUT/26563_V1_COMPILER_STATUS.txt" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]); p.write_text(p.read_text().replace('POST-BUILD INVARIANCE: NOT RUN YET','POST-BUILD INVARIANCE: PASS'))
PY
set_report "POST-BUILD INVARIANCE" PASS; pass "post-build invariance"

echo "=== 26563 GATE 6: deterministic clean candidate source export ==="
tar --sort=name --mtime='UTC 2020-01-01' --owner=0 --group=0 --numeric-owner -czf "$OUT/26563_V1_candidate_app_source.tar.gz" -C "$AFTER" app
sha256sum "$OUT/26563_V1_candidate_app_source.tar.gz" > "$OUT/26563_V1_candidate_app_source.tar.gz.sha256"; cp "$CAND_PIN" "$OUT/26563_V1_candidate_source.sha256"; set_report "CLEAN ARTIFACT SOURCE EXPORT" PASS
pass "26563 V1 BUILD-PROVEN Actions output"
