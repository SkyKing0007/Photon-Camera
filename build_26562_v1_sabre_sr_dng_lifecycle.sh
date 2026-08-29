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
exact_tree_equal(){ python3 - "$1" "$2" <<'PY'
from pathlib import Path
import hashlib,sys
def tree(root):
 root=Path(root); return {p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file() and '.git' not in p.parts}
a,b=tree(sys.argv[1]),tree(sys.argv[2])
if a!=b:
 bad=[k for k in sorted(set(a)|set(b)) if a.get(k)!=b.get(k)]
 raise SystemExit('tree mismatch: '+repr(bad[:40]))
PY
}

ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
BASE_SUCCESS_COMMIT="6e0618b13d4fd3f98c292cf275ba0a487068b66f"
BASE_RUN_ID="33268952022"
BASE_ARTIFACT_ID="9719538010"
BASE_ARTIFACT_NAME="photon-26561-v1-1-sabre-native-super-res-adaptive-color"
BASE_ARTIFACT_SHA="9a7e1fd2fbeb88b6da023cb5c54b259e3c1a1415d10ad54152a3a86ebc4d9b7d"
BASE_TAR_SHA="9e2a9a2cb2ca6306bd6f6535b4fe673ec69154ffdc9f98a5ae064b62c27f8249"
BASE_MANIFEST_SHA="1cda4a00406f83e42c1d6d66e6b1a7067514c645402dc4859bf21f0b7bd13f64"
CAND_MANIFEST_SHA="347c460657b48eb06182690353fbe1cfadd00c4bc7eb8b446d1e25c3a40c8809"
VENDOR_MANIFEST_SHA="7dbcc5ee5b9040965e431d79c45c5100f559c2b96c50970ca21987c684c825a8"
PROTECTED_CORE_SHA="19c981a126043e8820639a394269adaa206b6ef0acaea5ccc88dd7650f6454af"
PREWRITE_MANIFEST_SHA="966a85c57a2e4be9c6724cc72a53f361fda65dc074551b424d71e6ef4d8c8863"
CAND_CHANGED_MANIFEST_SHA="b6abb46aa6a37c841c8d9c93db08abaee7c27531a575ad716537a3ed6a05a0d1"
RUNTIME_PATHS_SHA="c421f004d1eb961835f2506f8db59bd9b067e9cd11c47349ee0519c30e29695b"
RUNTIME_GLSL_MANIFEST_SHA="7314081416156a9b2f50b6e96a90f0cc5478db241fb198172dc953184765361a"
FORWARD_SHA="ee889fb824a2e46b8dc408ae431e1273afb8bfac65630e45a9d94abf3b06f62e"
ROLLBACK_SHA="074a6e4d10a0daab1c8cd67d20eea39b3f1e7f67cda344e34a2cfdd2c38c0966"
GLSLANG_PKG_VERSION="15.1.0-2~ubuntu0.24.04.2"
BACKUP_BRANCH="backup-26561-v1-1-before-26562-sabre-sr-dng-lifecycle"
BACKUP_SHA_EXPECTED="$BASE_SUCCESS_COMMIT"
VERSION_NAME="0.9726562"
VERSION_BUILD="26562"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"

BASE_PIN="$ROOT/V1_26562_BASE_26561_V1_1_AUDITED_RUNTIME.sha256"
BASE_TAR_PIN="$ROOT/V1_26562_BASE_26561_V1_1_CANDIDATE_TAR.sha256"
CAND_PIN="$ROOT/V1_26562_EXPECTED_CANDIDATE_AUDITED_RUNTIME.sha256"
VENDOR_PIN="$ROOT/V1_26562_NATIVE_VENDOR_DEPENDENCIES.sha256"
RUNTIME_LIST="$ROOT/V1_26562_RUNTIME_CHANGED_PATHS.txt"
PREWRITE="$ROOT/V1_26562_PREWRITE_SOURCE_HASHES.sha256"
CAND_CHANGED="$ROOT/V1_26562_CANDIDATE_CHANGED_HASHES.sha256"
PROTECTED_CORE="$ROOT/V1_26562_PROTECTED_UNCHANGED_CORE.sha256"
RUNTIME_GLSL_PIN="$ROOT/V1_26562_RUNTIME_EXPANDED_GLSL.sha256"
FORWARD="$ROOT/V1_26562_RUNTIME_DELTA_FROM_26561_V1_1.patch"
ROLLBACK="$ROOT/V1_26562_RUNTIME_ROLLBACK_TO_26561_V1_1.patch"
TRANSFORM="$ROOT/transform_26562_v1_sabre_sr_dng_lifecycle.py"
VALIDATE="$ROOT/validate_26562_v1_sabre_sr_dng_lifecycle.py"
EXTRACT="$ROOT/extract_26562_runtime_glsl.py"
RESERVED="$ROOT/scan_glsl_reserved_identifiers_26562.py"
DNG_SELFTEST="$ROOT/selftest_26562_sabre_linearraw_dng.py"
HANDOFF_HASHES="$ROOT/V1_26562_HANDOFF_HASHES.sha256"
OUT="$ROOT/build_26562_v1_sabre_sr_dng_lifecycle_outputs"
WORK="$ROOT/.build_26562_v1_sabre_sr_dng_lifecycle_work"
ARTZIP="$WORK/26561_v1_1_artifact.zip"
ARTDIR="$WORK/artifact"
BASE="$WORK/exact_26561_v1_1_compiled_candidate"
AFTER="$WORK/candidate_26562"
GLSLOUT="$WORK/runtime_glsl"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-v1-sabre-sr-dng-lifecycle-debug.apk"
LOCAL_REPLAY_ARTIFACT=""
if [[ "${1:-}" == "--local-prebuild" ]]; then [[ -n "${2:-}" ]] || fail "--local-prebuild requires exact 26561 V1.1 artifact ZIP"; LOCAL_REPLAY_ARTIFACT="$2"; fi
mapfile -t RUNTIME_FILES < "$RUNTIME_LIST"
[[ "${#RUNTIME_FILES[@]}" -eq 18 ]] || fail "runtime changed-path inventory must contain exactly 18 paths"

rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR" "$BASE" "$AFTER" "$GLSLOUT"
cat > "$OUT/26562_V1_COMPILER_STATUS.txt" <<'EOF'
REAL GLSL COMPILE: NOT RUN YET
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
NATIVE/NDK COMPILE: NOT RUN YET (covered by full assemble)
FULL ANDROID ASSEMBLE: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
EOF
cat > "$OUT/26562_V1_STRICT_HANDOFF_REPORT.txt" <<'EOF'
RUNTIME OWNERSHIP: NOT RUN
EXACT PRIOR RUNTIME AUTHORITY: NOT RUN
BACKUP STATUS: NOT RUN
CHANGED RUNTIME SCOPE: NOT RUN
EXISTING SABRE SR MATH INVARIANCE: NOT RUN
MOTION SR 1X/2X CONTRACT: NOT RUN
NIGHT SR 1X/2X CONTRACT: NOT RUN
NIGHT SHADOW_LONG POLICY: NOT RUN
SABRE SR LINEAR_RAW DNG: NOT RUN
OLD SPATIAL SR DNG OWNER REMOVAL: NOT RUN
MOTION SR PUBLICATION RESILIENCE: NOT RUN
BACKGROUND FOREGROUND RESET: NOT RUN
EXACT USER ICONS: NOT RUN
PROTECTED UNRELATED INVARIANCE: NOT RUN
PREINSTALL VENDOR AUTHORITY ORDERING: NOT RUN
GLSL RESERVED-IDENTIFIER SCAN: NOT RUN
EXACT RUNTIME-EXPANDED GLSL: NOT RUN
DNG SERIALIZER SELFTEST: NOT RUN
REAL GLSL COMPILE: NOT RUN
REAL KOTLIN COMPILE: NOT RUN
REAL JAVA COMPILE: NOT RUN
NATIVE/NDK COMPILE: NOT RUN
FULL ANDROID ASSEMBLE: NOT RUN
FORWARD PATCH FUZZ=0: NOT RUN
ROLLBACK PATCH FUZZ=0: NOT RUN
POST-BUILD INVARIANCE: NOT RUN
CLEAN ARTIFACT SOURCE EXPORT: NOT RUN
TARGET VERSION/BUILD: 0.9726562 / 26562 V1
EOF
set_report(){
 local key="$1" val="$2" tmp="$OUT/.26562_report.tmp"
 awk -v key="$key:" -v val="$val" 'BEGIN{found=0} index($0,key)==1{print key" "val; found=1; next} {print} END{if(!found) exit 42}' "$OUT/26562_V1_STRICT_HANDOFF_REPORT.txt" > "$tmp" || { rm -f "$tmp"; fail "report key missing $key"; }
 mv "$tmp" "$OUT/26562_V1_STRICT_HANDOFF_REPORT.txt"
}

verify_package_and_pins(){
 sha256sum -c "$HANDOFF_HASHES"
 python3 -m py_compile "$TRANSFORM" "$VALIDATE" "$EXTRACT" "$RESERVED" "$DNG_SELFTEST"
 python3 "$EXTRACT" --self-test
 python3 "$RESERVED" --self-test
 bash -n "$0"
 [[ "$(wc -l < "$BASE_PIN")" -eq 927 && "$(sha "$BASE_PIN")" == "$BASE_MANIFEST_SHA" ]] || fail "base runtime manifest pin"
 [[ "$(wc -l < "$CAND_PIN")" -eq 927 && "$(sha "$CAND_PIN")" == "$CAND_MANIFEST_SHA" ]] || fail "candidate runtime manifest pin"
 [[ "$(wc -l < "$VENDOR_PIN")" -eq 778 && "$(sha "$VENDOR_PIN")" == "$VENDOR_MANIFEST_SHA" ]] || fail "vendor manifest pin"
 [[ "$(wc -l < "$PROTECTED_CORE")" -eq 11 && "$(sha "$PROTECTED_CORE")" == "$PROTECTED_CORE_SHA" ]] || fail "protected manifest pin"
 [[ "$(wc -l < "$PREWRITE")" -eq 17 && "$(sha "$PREWRITE")" == "$PREWRITE_MANIFEST_SHA" ]] || fail "prewrite manifest pin"
 ! grep -Eq '  /' "$PREWRITE" || fail "prewrite manifest contains absolute path (Actions checkout replay regression)"
 ! grep -Eq '  /' "$CAND_CHANGED" || fail "candidate changed manifest contains absolute path"
 [[ "$(wc -l < "$CAND_CHANGED")" -eq 17 && "$(sha "$CAND_CHANGED")" == "$CAND_CHANGED_MANIFEST_SHA" ]] || fail "candidate changed manifest pin"
 [[ "$(wc -l < "$RUNTIME_LIST")" -eq 18 && "$(sha "$RUNTIME_LIST")" == "$RUNTIME_PATHS_SHA" ]] || fail "runtime changed-path pin"
 [[ "$(wc -l < "$RUNTIME_GLSL_PIN")" -eq 7 && "$(sha "$RUNTIME_GLSL_PIN")" == "$RUNTIME_GLSL_MANIFEST_SHA" ]] || fail "runtime GLSL pin"
 [[ "$(sha "$FORWARD")" == "$FORWARD_SHA" && "$(sha "$ROLLBACK")" == "$ROLLBACK_SHA" ]] || fail "canonical patch SHA"
 grep -F "$BASE_TAR_SHA" "$BASE_TAR_PIN" >/dev/null || fail "base TAR pin drift"
}

verify_base_artifact_and_reconstruct(){
 local zip="$1"; [[ "$(sha "$zip")" == "$BASE_ARTIFACT_SHA" ]] || fail "26561 V1.1 artifact ZIP SHA mismatch"
 rm -rf "$ARTDIR"; mkdir -p "$ARTDIR"
 # The full prior artifact ZIP is already SHA-pinned above. Extract only its proof/source-export
 # directory; the 118 MB prior APK is not runtime source authority and need not be copied.
 unzip -q "$zip" 'build_26561_v1_1_sabre_native_super_res_adaptive_color_outputs/*' -d "$ARTDIR"
 local bo="$ARTDIR/build_26561_v1_1_sabre_native_super_res_adaptive_color_outputs"
 local bt="$bo/26561_V1_1_candidate_app_source.tar.gz" bm="$bo/26561_V1_1_candidate_source.sha256" bc="$bo/26561_V1_1_COMPILER_STATUS.txt" bv="$bo/26561_vendor_postbuild.sha256" ba="$bo/26561_V1_1_APK.sha256"
 for f in "$bt" "$bm" "$bc" "$bv" "$ba"; do [[ -f "$f" ]] || fail "base artifact missing $f"; done
 [[ "$(sha "$bt")" == "$BASE_TAR_SHA" && "$(sha "$bm")" == "$BASE_MANIFEST_SHA" ]] || fail "base TAR/manifest SHA mismatch"
 cmp "$bm" "$BASE_PIN" >/dev/null || fail "packaged base pin differs from successful 26561 V1.1"
 cmp "$bv" "$VENDOR_PIN" >/dev/null || fail "base vendor proof differs from pin"
 for status in 'REAL GLSL COMPILE: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS'; do grep -F "$status" "$bc" >/dev/null || fail "26561 compiler proof missing: $status"; done
 rm -rf "$BASE"; mkdir -p "$BASE"; tar -xzf "$bt" -C "$BASE"
 manifest_audited "$BASE" "$WORK/base_reconstructed.sha256"; cmp "$WORK/base_reconstructed.sha256" "$BASE_PIN" >/dev/null || fail "reconstructed 26561 runtime mismatch"
 vendor_manifest "$BASE" "$WORK/base_vendor_reconstructed.sha256"; cmp "$WORK/base_vendor_reconstructed.sha256" "$VENDOR_PIN" >/dev/null || fail "reconstructed 26561 vendor mismatch"
 set_report "EXACT PRIOR RUNTIME AUTHORITY" "PASS (run ${BASE_RUN_ID} artifact ${BASE_ARTIFACT_ID})"; pass "exact successful compiled 26561 V1.1 authority"
}

candidate_diff_paths(){ python3 - "$1" "$2" <<'PY'
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib,sys
def T(root):
 root=Path(root); paths=sorted(p for p in root.rglob('*') if p.is_file() and '.git' not in p.parts)
 def one(p):
  h=hashlib.sha256()
  with p.open('rb') as f:
   for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
  return p.relative_to(root).as_posix(),h.hexdigest()
 with ThreadPoolExecutor(max_workers=32) as pool: return dict(pool.map(one,paths))
a,b=T(sys.argv[1]),T(sys.argv[2]); print('\n'.join(sorted(k for k in set(a)|set(b) if a.get(k)!=b.get(k))))
PY
}

seed_scope(){ local source="$1" dest="$2"; rm -rf "$dest"; mkdir -p "$dest"; while read -r rel; do if [[ -f "$source/$rel" ]]; then mkdir -p "$dest/$(dirname "$rel")"; cp -a "$source/$rel" "$dest/$rel"; fi; done < "$RUNTIME_LIST"; }
apply_state_to_scope(){ local source="$1" dest="$2"; while read -r rel; do if [[ -f "$source/$rel" ]]; then mkdir -p "$dest/$(dirname "$rel")"; cp -a "$source/$rel" "$dest/$rel"; else rm -f "$dest/$rel"; fi; done < "$RUNTIME_LIST"; }

build_candidate_and_precompile_proof(){
 rm -rf "$AFTER"; mkdir -p "$AFTER"; cp -a "$BASE/." "$AFTER/"
 (cd "$AFTER" && sha256sum -c "$PREWRITE")
 python3 "$TRANSFORM" "$AFTER"
 manifest_audited "$AFTER" "$WORK/candidate_manifest.sha256"; cmp "$WORK/candidate_manifest.sha256" "$CAND_PIN" >/dev/null || fail "candidate manifest differs from pin"
 (cd "$AFTER" && sha256sum -c "$CAND_CHANGED")
 [[ ! -e "$AFTER/app/src/main/java/com/particlesdevs/photoncamera/processing/IrisMotionSuperResDngWriter.java" ]] || fail "obsolete Spatial SR DNG writer survived"
 mapfile -t got < <(candidate_diff_paths "$BASE" "$AFTER")
 mapfile -t want < <(LC_ALL=C sort "$RUNTIME_LIST")
 [[ "${got[*]}" == "${want[*]}" ]] || fail "exact 18-path candidate diff mismatch"
 python3 "$VALIDATE" "$BASE" "$AFTER" | tee "$OUT/26562_focused_architecture_validation.txt"
 python3 "$DNG_SELFTEST" --candidate "$AFTER" | tee "$OUT/26562_dng_serializer_selftest.txt"
 set_report "RUNTIME OWNERSHIP" "PASS (native Sabre remains structural/color authority; no Spatial/Wronski SR reconstruction)"
 set_report "CHANGED RUNTIME SCOPE" "PASS (exact 18 paths; 1 obsolete owner deleted, 1 Sabre DNG owner added)"
 set_report "EXISTING SABRE SR MATH INVARIANCE" "PASS (17/17 prior Sabre shader literals byte-identical; one DNG export shader added)"
 set_report "MOTION SR 1X/2X CONTRACT" "PASS"
 set_report "NIGHT SR 1X/2X CONTRACT" "PASS"
 set_report "NIGHT SHADOW_LONG POLICY" "PASS (native base yes; fine SR detail no)"
 set_report "SABRE SR LINEAR_RAW DNG" "PASS (RGB16 LinearRaw; 2x; no fake CFA/NoiseProfile)"
 set_report "OLD SPATIAL SR DNG OWNER REMOVAL" "PASS"
 set_report "MOTION SR PUBLICATION RESILIENCE" "PASS (2x attempt; native completed multiframe Sabre fallback only on publication failure)"
 set_report "BACKGROUND FOREGROUND RESET" "PASS (cold/true foreground reset Motion + physical 1x + SR OFF; processing defer)"
 set_report "EXACT USER ICONS" "PASS"
 set_report "PROTECTED UNRELATED INVARIANCE" "PASS (11 files byte-identical)"
 set_report "DNG SERIALIZER SELFTEST" "PASS"

 rm -rf "$GLSLOUT"; mkdir -p "$GLSLOUT"
 python3 "$EXTRACT" --root "$AFTER" --out "$GLSLOUT" | tee "$OUT/26562_runtime_glsl_extraction.txt"
 (cd "$GLSLOUT" && sha256sum -c "$RUNTIME_GLSL_PIN")
 python3 "$RESERVED" "$GLSLOUT"/* | tee "$OUT/26562_reserved_identifier_scan.txt"
 set_report "GLSL RESERVED-IDENTIFIER SCAN" "PASS (7 exact runtime-expanded files; coherent regression retained)"
 set_report "EXACT RUNTIME-EXPANDED GLSL" "PASS (7-file hash pin)"

 # Deterministic binary forward/rollback patches from two committed states in one exact
 # 18-path scope repo. Full candidate/vendor manifests prove every byte outside this scope.
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

 # Fuzz=0 application proof in both directions. Commit the forward-applied state before
 # applying rollback so git applies the rollback against the exact candidate state.
 local FP="$WORK/patchproof"
 seed_scope "$BASE" "$FP"
 (cd "$FP"; git init -q; git config user.name Photon; git config user.email photon@example.invalid; git add -A; git commit -qm base; git apply --check "$FORWARD"; git apply "$FORWARD"; sha256sum -c "$CAND_CHANGED"; [[ ! -e app/src/main/java/com/particlesdevs/photoncamera/processing/IrisMotionSuperResDngWriter.java ]]; git add -A; git commit -qm candidate-applied; git apply --check "$ROLLBACK"; git apply "$ROLLBACK"; sha256sum -c "$PREWRITE"; [[ ! -e app/src/main/java/com/particlesdevs/photoncamera/processing/IrisSabreSuperResDngWriter.java ]])
 set_report "FORWARD PATCH FUZZ=0" "PASS"; set_report "ROLLBACK PATCH FUZZ=0" "PASS"; pass "candidate semantics / DNG / exact GLSL / deterministic patches"
}

run_real_glsl(){
 if ! command -v glslangValidator >/dev/null 2>&1 || [[ "$(dpkg-query -W -f='${Version}' glslang-tools 2>/dev/null || true)" != "$GLSLANG_PKG_VERSION" ]]; then sudo apt-get update -qq; sudo apt-get install -y --no-install-recommends "glslang-tools=${GLSLANG_PKG_VERSION}"; fi
 [[ "$(dpkg-query -W -f='${Version}' glslang-tools)" == "$GLSLANG_PKG_VERSION" ]] || fail "wrong glslang package"
 glslangValidator --version | tee "$OUT/26562_glslang_version.txt"; grep -F 'Khronos. 15.1.0' "$OUT/26562_glslang_version.txt" >/dev/null || fail "glslang version not 15.1.0"
 glslangValidator -S vert "$GLSLOUT/sabre_super_res_detail_merge_26561.vert"; glslangValidator -S frag "$GLSLOUT/sabre_super_res_detail_merge_26561.frag"; glslangValidator -l "$GLSLOUT/sabre_super_res_detail_merge_26561.vert" "$GLSLOUT/sabre_super_res_detail_merge_26561.frag"
 glslangValidator -S vert "$GLSLOUT/sabre_super_res_detail_resolve_26561.vert"; glslangValidator -S frag "$GLSLOUT/sabre_super_res_detail_resolve_26561.frag"; glslangValidator -l "$GLSLOUT/sabre_super_res_detail_resolve_26561.vert" "$GLSLOUT/sabre_super_res_detail_resolve_26561.frag"
 glslangValidator -S vert "$GLSLOUT/sabre_super_res_linear_raw_26562.vert"; glslangValidator -S frag "$GLSLOUT/sabre_super_res_linear_raw_26562.frag"; glslangValidator -l "$GLSLOUT/sabre_super_res_linear_raw_26562.vert" "$GLSLOUT/sabre_super_res_linear_raw_26562.frag"
 glslangValidator -S comp "$GLSLOUT/universal_adaptive_color_26561.comp"
 python3 - "$OUT/26562_V1_COMPILER_STATUS.txt" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]); p.write_text(p.read_text().replace('REAL GLSL COMPILE: NOT RUN YET','REAL GLSL COMPILE: PASS'))
PY
 set_report "REAL GLSL COMPILE" "PASS (pinned 15.1.0 on exact 7 runtime-expanded files)"; pass "real GLSL compile"
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
 set_report "PREINSTALL VENDOR AUTHORITY ORDERING" "PASS (V1 failure regression retained; equality only after frozen candidate install)"; pass "permanent V1 vendor-authority regression"
}

if [[ -n "$LOCAL_REPLAY_ARTIFACT" ]]; then
 echo "=== 26562 LOCAL PREBUILD: package/pins ==="; verify_package_and_pins
 echo "=== 26562 LOCAL PREBUILD: exact 26561 V1.1 artifact ==="; verify_base_artifact_and_reconstruct "$LOCAL_REPLAY_ARTIFACT"
 echo "=== 26562 LOCAL PREBUILD: transform/audit/DNG/GLSL/patches ==="; build_candidate_and_precompile_proof
 echo "=== 26562 LOCAL PREBUILD: V1 vendor regression ==="; run_preinstall_vendor_authority_regression
 if command -v glslangValidator >/dev/null 2>&1 && command -v dpkg-query >/dev/null 2>&1 && [[ "$(dpkg-query -W -f='${Version}' glslang-tools 2>/dev/null || true)" == "$GLSLANG_PKG_VERSION" ]]; then run_real_glsl; else echo 'LOCAL REAL GLSL COMPILE: NOT RUN (pinned package unavailable locally)' | tee "$OUT/26562_V1_LOCAL_COMPILER_LIMIT.txt"; fi
 echo 'LOCAL REAL KOTLIN/JAVA/ASSEMBLE: NOT RUN (authoritative Actions gate)' | tee -a "$OUT/26562_V1_LOCAL_COMPILER_LIMIT.txt"; pass "26562 local prebuild replay complete"; exit 0
fi

# Actions authoritative sequence.
echo "=== 26562 GATE 0: sealed handoff / branch / direct lineage / architectural backup ==="
[[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch"
[[ "$(git rev-parse HEAD^)" == "$BASE_SUCCESS_COMMIT" ]] || fail "26562 handoff must be direct child of successful 26561 V1.1"
git diff --quiet "$BASE_SUCCESS_COMMIT..HEAD" -- app || fail "handoff directly changed repository app source"
[[ -n "$TOKEN" ]] || fail "GITHUB_TOKEN missing"; verify_package_and_pins
BACKUP_SHA="$(git ls-remote origin "refs/heads/${BACKUP_BRANCH}" | awk '{print $1}')"; [[ "$BACKUP_SHA" == "$BACKUP_SHA_EXPECTED" ]] || fail "backup missing/wrong"
set_report "BACKUP STATUS" "PASS (${BACKUP_BRANCH} @ ${BACKUP_SHA_EXPECTED})"
python3 - "$BASE_SUCCESS_COMMIT" <<'PY'
import subprocess,sys
base=sys.argv[1]
allowed={
'.github/workflows/build-26562-v1-sabre-sr-dng-lifecycle.yml','V1_26562_BASE_26561_V1_1_AUDITED_RUNTIME.sha256','V1_26562_BASE_26561_V1_1_CANDIDATE_TAR.sha256','V1_26562_BASE_PROVENANCE.txt','V1_26562_CANDIDATE_CHANGED_HASHES.sha256','V1_26562_EXPECTED_CANDIDATE_AUDITED_RUNTIME.sha256','V1_26562_HANDOFF_HASHES.sha256','V1_26562_LOCAL_VALIDATION.txt','V1_26562_NATIVE_VENDOR_DEPENDENCIES.sha256','V1_26562_PREWRITE_SOURCE_HASHES.sha256','V1_26562_PROTECTED_UNCHANGED_CORE.sha256','V1_26562_RUNTIME_DELTA_FROM_26561_V1_1.patch','V1_26562_RUNTIME_EXPANDED_GLSL.sha256','V1_26562_RUNTIME_CHANGED_PATHS.txt','V1_26562_RUNTIME_ROLLBACK_TO_26561_V1_1.patch','V1_26562_UPLOAD_INSTRUCTIONS.md','build_26562_v1_sabre_sr_dng_lifecycle.sh','extract_26562_runtime_glsl.py','scan_glsl_reserved_identifiers_26562.py','selftest_26562_sabre_linearraw_dng.py','transform_26562_v1_sabre_sr_dng_lifecycle.py','validate_26562_v1_sabre_sr_dng_lifecycle.py'}
actual=set(subprocess.check_output(['git','diff','--name-only',base+'..HEAD'],text=True).splitlines())
if actual!=allowed: raise SystemExit('handoff scope mismatch extra=%r missing=%r'%(sorted(actual-allowed),sorted(allowed-actual)))
if any(x.startswith('app/') for x in actual): raise SystemExit('handoff modified repository app source')
print('PASS exact 22-file 26562 handoff scope')
PY
pass "sealed 26562 package / lineage / backup"

echo "=== 26562 GATE 1: exact successful compiled 26561 V1.1 authority ==="
REPO_API="https://api.github.com/repos/${GITHUB_REPOSITORY:-SkyKing0007/Photon-Camera}"
curl --fail --location --silent --show-error --retry 5 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' -H 'X-GitHub-Api-Version: 2022-11-28' "$REPO_API/actions/runs/${BASE_RUN_ID}" -o "$WORK/base_run.json"
python3 - "$WORK/base_run.json" "$BASE_RUN_ID" "$BASE_SUCCESS_COMMIT" "$EXPECTED_BRANCH" <<'PY'
import json,sys
d=json.load(open(sys.argv[1])); assert str(d.get('id'))==sys.argv[2] and d.get('conclusion')=='success' and d.get('head_sha')==sys.argv[3] and d.get('head_branch')==sys.argv[4]; print('PASS exact successful 26561 V1.1 Actions run')
PY
curl --fail --location --silent --show-error --retry 5 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' -H 'X-GitHub-Api-Version: 2022-11-28' "$REPO_API/actions/artifacts/${BASE_ARTIFACT_ID}" -o "$WORK/base_artifact.json"
python3 - "$WORK/base_artifact.json" "$BASE_ARTIFACT_ID" "$BASE_ARTIFACT_NAME" "$BASE_ARTIFACT_SHA" <<'PY'
import json,sys
d=json.load(open(sys.argv[1])); assert str(d.get('id'))==sys.argv[2] and d.get('name')==sys.argv[3] and not d.get('expired') and d.get('digest')=='sha256:'+sys.argv[4]; print('PASS exact 26561 V1.1 artifact metadata/digest')
PY
curl --fail --location --silent --show-error --retry 5 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' -H 'X-GitHub-Api-Version: 2022-11-28' "$REPO_API/actions/artifacts/${BASE_ARTIFACT_ID}/zip" -o "$ARTZIP"
verify_base_artifact_and_reconstruct "$ARTZIP"

echo "=== 26562 GATE 2: candidate-first transform / audit / DNG / exact GLSL / patches ==="; build_candidate_and_precompile_proof
echo "=== 26562 GATE 3: pinned real glslangValidator ==="; run_real_glsl
echo "=== 26562 GATE 4: controlled live install / real Kotlin+Java / full assemble ==="
run_preinstall_vendor_authority_regression; install_frozen_candidate_into_live_root "$ROOT" repository
rm -rf "$ROOT/app/build/outputs/apk/debug"
./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace
python3 - "$OUT/26562_V1_COMPILER_STATUS.txt" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]); p.write_text(p.read_text().replace('REAL KOTLIN COMPILE: NOT RUN YET','REAL KOTLIN COMPILE: PASS').replace('REAL JAVA COMPILE: NOT RUN YET','REAL JAVA COMPILE: PASS'))
PY
set_report "REAL KOTLIN COMPILE" PASS; set_report "REAL JAVA COMPILE" PASS
./gradlew :app:assembleDebug --stacktrace
python3 - "$OUT/26562_V1_COMPILER_STATUS.txt" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]); p.write_text(p.read_text().replace('NATIVE/NDK COMPILE: NOT RUN YET (covered by full assemble)','NATIVE/NDK COMPILE: PASS (full assemble)').replace('FULL ANDROID ASSEMBLE: NOT RUN YET','FULL ANDROID ASSEMBLE: PASS'))
PY
set_report "NATIVE/NDK COMPILE" "PASS (full assemble)"; set_report "FULL ANDROID ASSEMBLE" PASS
mapfile -t APKS < <(find "$ROOT/app/build/outputs/apk/debug" -maxdepth 1 -type f -name '*.apk' -print); [[ "${#APKS[@]}" -eq 1 ]] || fail "expected exactly one debug APK, found ${#APKS[@]}"; mv "${APKS[0]}" "$FINAL"; [[ -s "$FINAL" ]] || fail "final APK missing"; [[ "$(find "$ROOT/app/build/outputs/apk/debug" -maxdepth 1 -type f -name '*.apk' | wc -l)" -eq 0 ]] || fail "duplicate APK remained"; sha256sum "$FINAL" > "$OUT/26562_V1_APK.sha256"; pass "real Kotlin/Java/NDK + full assemble + exactly one APK"

echo "=== 26562 GATE 5: post-build frozen candidate / protected / native/vendor / exact GLSL invariance ==="
manifest_audited "$ROOT" "$OUT/26562_postbuild_runtime.sha256"; cmp "$OUT/26562_postbuild_runtime.sha256" "$CAND_PIN" >/dev/null || fail "postbuild runtime changed"
manifest_audited "$AFTER" "$OUT/26562_frozen_candidate_postbuild.sha256"; cmp "$OUT/26562_frozen_candidate_postbuild.sha256" "$CAND_PIN" >/dev/null || fail "frozen candidate changed"
vendor_manifest "$ROOT" "$OUT/26562_vendor_postbuild.sha256"; cmp "$OUT/26562_vendor_postbuild.sha256" "$VENDOR_PIN" >/dev/null || fail "vendor changed during build"
(cd "$ROOT" && sha256sum -c "$PROTECTED_CORE")
rm -rf "$WORK/runtime_glsl_post"; mkdir -p "$WORK/runtime_glsl_post"; python3 "$EXTRACT" --root "$ROOT" --out "$WORK/runtime_glsl_post" >/dev/null; (cd "$WORK/runtime_glsl_post" && sha256sum -c "$RUNTIME_GLSL_PIN"); python3 "$RESERVED" "$WORK/runtime_glsl_post"/* > "$OUT/26562_postbuild_reserved_identifier_scan.txt"
python3 "$VALIDATE" "$BASE" "$ROOT" > "$OUT/26562_postbuild_focused_validation.txt"
python3 - "$OUT/26562_V1_COMPILER_STATUS.txt" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]); p.write_text(p.read_text().replace('POST-BUILD INVARIANCE: NOT RUN YET','POST-BUILD INVARIANCE: PASS'))
PY
set_report "POST-BUILD INVARIANCE" PASS; pass "post-build invariance"

echo "=== 26562 GATE 6: deterministic clean candidate source export ==="
tar --sort=name --mtime='UTC 2020-01-01' --owner=0 --group=0 --numeric-owner -czf "$OUT/26562_V1_candidate_app_source.tar.gz" -C "$AFTER" app
sha256sum "$OUT/26562_V1_candidate_app_source.tar.gz" > "$OUT/26562_V1_candidate_app_source.tar.gz.sha256"; cp "$CAND_PIN" "$OUT/26562_V1_candidate_source.sha256"; set_report "CLEAN ARTIFACT SOURCE EXPORT" PASS
pass "26562 V1 BUILD-PROVEN Actions output"
