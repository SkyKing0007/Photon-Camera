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
verify_state_manifest(){
 python3 - "$1" "$2" <<'PY'
from pathlib import Path
import hashlib,sys
root=Path(sys.argv[1])
for raw in Path(sys.argv[2]).read_text().splitlines():
 if not raw.strip(): continue
 want,rel=raw.split('  ',1); p=root/rel
 if want=='ABSENT':
  if p.exists(): raise SystemExit('expected absent '+rel)
 else:
  if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=want: raise SystemExit('hash mismatch '+rel)
print('PASS exact state manifest',Path(sys.argv[2]).name)
PY
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
seed_scope(){ local source="$1" dest="$2"; rm -rf "$dest"; mkdir -p "$dest"; while IFS= read -r rel; do if [[ -f "$source/$rel" ]]; then mkdir -p "$dest/$(dirname "$rel")"; cp -a "$source/$rel" "$dest/$rel"; fi; done < "$RUNTIME_LIST"; }
apply_state_to_scope(){ local source="$1" dest="$2"; while IFS= read -r rel; do if [[ -f "$source/$rel" ]]; then mkdir -p "$dest/$(dirname "$rel")"; cp -a "$source/$rel" "$dest/$rel"; else rm -f "$dest/$rel"; fi; done < "$RUNTIME_LIST"; }

ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
BASE_SUCCESS_COMMIT="d048338a8e303c11b2208d4c1b78c8c129ebc57b"
FAILED_V1_HANDOFF_COMMIT="82eafc66df2bd17885f3d8b44e22047abfda440e"
BASE_RUN_ID="33277777042"
BASE_ARTIFACT_ID="9722074240"
BASE_ARTIFACT_NAME="photon-26563-v1-universal-adaptive-color-appearance"
BASE_ARTIFACT_SHA="5861fb6cd33eb459fc1d9d3a571b65ceaba3525200df9b950597ae35b4579a7a"
BASE_TAR_SHA="07787003b70edfd6d7d3d50cf291a195484204205ad22c687088455710aa9594"
BASE_MANIFEST_SHA="c1fae8c6691b3d900c25c249f1c96abefa761dd828b18e8b27bf8def53afcae4"
CAND_MANIFEST_SHA="775562c45fc05556be22e7bf6c2942d607dfd35e94bd1daf9683f12fa0b6cc9c"
VENDOR_MANIFEST_SHA="7dbcc5ee5b9040965e431d79c45c5100f559c2b96c50970ca21987c684c825a8"
PROTECTED_CORE_SHA="434f29bbdb51b4b463c531bd287c17da1a86f700873700c41ac4ffd8af00e837"
PREWRITE_MANIFEST_SHA="cbb306837f514b85515cb7fae1c8bd08bd44f128fba6072d18f3efa583e742a6"
CAND_CHANGED_MANIFEST_SHA="b60b69675daeabb040061b79241f61fa60be2e15932e49568be3e2d768a6d20b"
RUNTIME_PATHS_SHA="eae7934b090d43f7a9a38239cf2bf7455a2d7b0e69bbcaa0f2521c6f7529376d"
RUNTIME_GLSL_MANIFEST_SHA="8d807071e335307f3ba332bd0d30b5546d19f7d700f658824e10a1a2f6e5737b"
FORWARD_SHA="3e1825305dd615535e692166017bcfc2520c3002d4dcb67e673ad7c8b0e3c3eb"
ROLLBACK_SHA="1cbd546840f6c687603f6a8241059ea4574759a072229324aeea1d5c87526bd4"
GLSLANG_PKG_VERSION="15.1.0-2~ubuntu0.24.04.2"
BACKUP_BRANCH="backup-26563-v1-before-26564-true-2x-sr"
BACKUP_SHA_EXPECTED="$BASE_SUCCESS_COMMIT"
VERSION_NAME="0.9726564"
VERSION_BUILD="26564"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"
BASE_PIN="$ROOT/V1_26564_BASE_26563_V1_AUDITED_RUNTIME.sha256"
BASE_TAR_PIN="$ROOT/V1_26564_BASE_26563_V1_CANDIDATE_TAR.sha256"
CAND_PIN="$ROOT/V1_26564_EXPECTED_CANDIDATE_AUDITED_RUNTIME.sha256"
VENDOR_PIN="$ROOT/V1_26564_NATIVE_VENDOR_DEPENDENCIES.sha256"
RUNTIME_LIST="$ROOT/V1_26564_RUNTIME_CHANGED_PATHS.txt"
PREWRITE="$ROOT/V1_26564_PREWRITE_SOURCE_HASHES.sha256"
CAND_CHANGED="$ROOT/V1_26564_CANDIDATE_CHANGED_HASHES.sha256"
PROTECTED_CORE="$ROOT/V1_26564_PROTECTED_UNCHANGED_CORE.sha256"
RUNTIME_GLSL_PIN="$ROOT/V1_26564_RUNTIME_EXPANDED_GLSL.sha256"
FORWARD="$ROOT/V1_26564_RUNTIME_DELTA_FROM_26563_V1.patch"
ROLLBACK="$ROOT/V1_26564_RUNTIME_ROLLBACK_TO_26563_V1.patch"
TRANSFORM="$ROOT/transform_26564_v1_true_2x_sr.py"
VALIDATE="$ROOT/validate_26564_v1_true_2x_sr.py"
MEMORY="$ROOT/validate_26564_true2x_memory.py"
PARITY="$ROOT/test_26564_true2x_cpu_gpu_numeric_parity.py"
EXTRACT="$ROOT/extract_26564_runtime_glsl.py"
RESERVED="$ROOT/scan_glsl_reserved_identifiers_26564.py"
HANDOFF_HASHES="$ROOT/V1_26564_HANDOFF_HASHES.sha256"
OUT="$ROOT/build_26564_v1_true_2x_sr_outputs"
WORK="$ROOT/.build_26564_v1_true_2x_sr_work"
ARTZIP="$WORK/26563_v1_artifact.zip"
ARTDIR="$WORK/artifact"
BASE="$WORK/exact_26563_v1_compiled_candidate"
AFTER="$WORK/candidate_26564"
GLSLOUT="$WORK/runtime_glsl"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-v1-1-true-2x-sr-debug.apk"
LOCAL_REPLAY_ARTIFACT=""
if [[ "${1:-}" == "--local-prebuild" ]]; then [[ -n "${2:-}" ]] || fail "--local-prebuild requires exact 26563 V1 artifact ZIP"; LOCAL_REPLAY_ARTIFACT="$2"; fi
mapfile -t RUNTIME_FILES < "$RUNTIME_LIST"
[[ "${#RUNTIME_FILES[@]}" -eq 15 ]] || fail "runtime changed-path inventory must contain exactly 15 paths"
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR" "$BASE" "$AFTER" "$GLSLOUT"
cat > "$OUT/26564_V1_COMPILER_STATUS.txt" <<'EOF'
REAL GLSL COMPILE: NOT RUN YET
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
NATIVE/NDK COMPILE: NOT RUN YET (covered by full assemble)
FULL ANDROID ASSEMBLE: NOT RUN YET
POST-BUILD INVARIANCE: NOT RUN YET
EOF
cat > "$OUT/26564_V1_STRICT_HANDOFF_REPORT.txt" <<'EOF'
RUNTIME AUTHORITY: NOT RUN
BACKUP STATUS: NOT RUN
CHANGED RUNTIME SCOPE: NOT RUN
TRUE 2X DIRECT CFA OWNERSHIP: NOT RUN
CPU/GPU EQUIVALENT SEMANTICS: NOT RUN
PHASE DIVERSITY: NOT RUN
BOUNDED MEMORY: NOT RUN
GPU FAILURE CPU FALLBACK: NOT RUN
LUMA ZERO CONTRACT: NOT RUN
26563 SATURATION/COLOR PROTECTION: NOT RUN
MOTION/NIGHT DNG/UHDR OWNERSHIP: NOT RUN
EXCEPTION CLEANUP: NOT RUN
OLD FAKE SR RETIRED: NOT RUN
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
TARGET VERSION/BUILD: 0.9726564 / 26564 V1.1
EOF
set_report(){ local key="$1" val="$2" tmp="$OUT/.report.tmp"; awk -v key="$key:" -v val="$val" 'BEGIN{f=0} index($0,key)==1{print key" "val;f=1;next}{print} END{if(!f)exit 42}' "$OUT/26564_V1_STRICT_HANDOFF_REPORT.txt" > "$tmp" || { rm -f "$tmp"; fail "report key missing $key"; }; mv "$tmp" "$OUT/26564_V1_STRICT_HANDOFF_REPORT.txt"; }

verify_package_and_pins(){
 sha256sum -c "$HANDOFF_HASHES"
 python3 -m py_compile "$TRANSFORM" "$VALIDATE" "$MEMORY" "$PARITY" "$EXTRACT" "$RESERVED"
 python3 "$EXTRACT" --self-test
 python3 "$RESERVED" --self-test
 bash -n "$0"
 python3 - "$HANDOFF_HASHES" <<'PY_SCOPE_SELFTEST'
from pathlib import Path
import sys
hf=Path(sys.argv[1])
raw=hf.read_text().splitlines()
allowed={line.split('  ',1)[1] for line in raw if line.strip()}
if len(allowed) != 28:
    raise SystemExit(f'handoff manifest payload count mismatch: {len(allowed)} != 28')
if any(('\n' in x or '\r' in x) for x in allowed):
    raise SystemExit('REGRESSION_26564_V1_HANDOFF_SCOPE_NEWLINE: parsed filename retained line ending')
# Exact historical failure fixture: old open(file) parsing retained '\n'; splitlines parsing must not.
fixture='a'*64+'  alpha.txt\n'+'b'*64+'  dir/beta.txt\n'
parsed={line.split('  ',1)[1] for line in fixture.splitlines() if line.strip()}
if parsed != {'alpha.txt','dir/beta.txt'}:
    raise SystemExit('REGRESSION_26564_V1_HANDOFF_SCOPE_NEWLINE fixture failed')
print('PASS permanent 26564 V1 handoff-scope newline regression')
PY_SCOPE_SELFTEST
 [[ "$(wc -l < "$BASE_PIN")" -eq 929 && "$(sha "$BASE_PIN")" == "$BASE_MANIFEST_SHA" ]] || fail "base runtime manifest pin"
 [[ "$(wc -l < "$CAND_PIN")" -eq 930 && "$(sha "$CAND_PIN")" == "$CAND_MANIFEST_SHA" ]] || fail "candidate runtime manifest pin"
 [[ "$(wc -l < "$VENDOR_PIN")" -eq 778 && "$(sha "$VENDOR_PIN")" == "$VENDOR_MANIFEST_SHA" ]] || fail "vendor manifest pin"
 [[ "$(wc -l < "$PROTECTED_CORE")" -eq 18 && "$(sha "$PROTECTED_CORE")" == "$PROTECTED_CORE_SHA" ]] || fail "protected core pin"
 [[ "$(wc -l < "$PREWRITE")" -eq 15 && "$(sha "$PREWRITE")" == "$PREWRITE_MANIFEST_SHA" ]] || fail "prewrite pin"
 [[ "$(wc -l < "$CAND_CHANGED")" -eq 15 && "$(sha "$CAND_CHANGED")" == "$CAND_CHANGED_MANIFEST_SHA" ]] || fail "candidate changed pin"
 [[ "$(wc -l < "$RUNTIME_LIST")" -eq 15 && "$(sha "$RUNTIME_LIST")" == "$RUNTIME_PATHS_SHA" ]] || fail "runtime list pin"
 [[ "$(wc -l < "$RUNTIME_GLSL_PIN")" -eq 4 && "$(sha "$RUNTIME_GLSL_PIN")" == "$RUNTIME_GLSL_MANIFEST_SHA" ]] || fail "runtime GLSL pin"
 [[ "$(sha "$FORWARD")" == "$FORWARD_SHA" && "$(sha "$ROLLBACK")" == "$ROLLBACK_SHA" ]] || fail "canonical patch SHA"
 grep -F "$BASE_TAR_SHA" "$BASE_TAR_PIN" >/dev/null || fail "base TAR pin drift"
 ! grep -Eq '  /' "$PREWRITE" || fail "prewrite contains absolute path"
 ! grep -Eq '  /' "$CAND_CHANGED" || fail "candidate changed contains absolute path"
 grep -F -- '--- /dev/null' "$FORWARD" >/dev/null || fail "new runtime file missing from forward patch"
 pass "sealed package/pins"
}

verify_base_artifact_and_reconstruct(){
 local zip="$1"; [[ "$(sha "$zip")" == "$BASE_ARTIFACT_SHA" ]] || fail "26563 V1 artifact ZIP SHA mismatch"
 rm -rf "$ARTDIR"; mkdir -p "$ARTDIR"; unzip -q "$zip" 'build_26563_v1_universal_adaptive_color_appearance_outputs/*' -d "$ARTDIR"
 local bo="$ARTDIR/build_26563_v1_universal_adaptive_color_appearance_outputs"
 local bt="$bo/26563_V1_candidate_app_source.tar.gz" bm="$bo/26563_V1_candidate_source.sha256" bc="$bo/26563_V1_COMPILER_STATUS.txt" bv="$bo/26563_vendor_postbuild.sha256" ba="$bo/26563_V1_APK.sha256" br="$bo/26563_V1_STRICT_HANDOFF_REPORT.txt"
 for f in "$bt" "$bm" "$bc" "$bv" "$ba" "$br"; do [[ -f "$f" ]] || fail "base artifact missing $f"; done
 [[ "$(sha "$bt")" == "$BASE_TAR_SHA" && "$(sha "$bm")" == "$BASE_MANIFEST_SHA" ]] || fail "base TAR/manifest SHA mismatch"
 cmp "$bm" "$BASE_PIN" >/dev/null || fail "packaged base pin differs from successful 26563"
 cmp "$bv" "$VENDOR_PIN" >/dev/null || fail "base vendor differs"
 for status in 'REAL GLSL COMPILE: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'NATIVE/NDK COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS'; do grep -F "$status" "$bc" >/dev/null || fail "26563 compiler proof missing: $status"; done
 grep -F 'CLEAN ARTIFACT SOURCE EXPORT: PASS' "$br" >/dev/null || fail "26563 strict report missing clean export"
 rm -rf "$BASE"; mkdir -p "$BASE"; tar -xzf "$bt" -C "$BASE"
 manifest_audited "$BASE" "$WORK/base_reconstructed.sha256"; cmp "$WORK/base_reconstructed.sha256" "$BASE_PIN" >/dev/null || fail "reconstructed 26563 runtime mismatch"
 vendor_manifest "$BASE" "$WORK/base_vendor_reconstructed.sha256"; cmp "$WORK/base_vendor_reconstructed.sha256" "$VENDOR_PIN" >/dev/null || fail "reconstructed vendor mismatch"
 set_report "RUNTIME AUTHORITY" "PASS (run ${BASE_RUN_ID} artifact ${BASE_ARTIFACT_ID}; exact compiled 26563)"; pass "exact successful compiled 26563 authority"
}

build_candidate_and_precompile_proof(){
 rm -rf "$AFTER"; mkdir -p "$AFTER"; cp -a "$BASE/." "$AFTER/"
 verify_state_manifest "$AFTER" "$PREWRITE"
 python3 "$TRANSFORM" --root "$AFTER" --patch "$FORWARD" --prewrite "$PREWRITE" --candidate "$CAND_CHANGED"
 manifest_audited "$AFTER" "$WORK/candidate_manifest.sha256"; cmp "$WORK/candidate_manifest.sha256" "$CAND_PIN" >/dev/null || fail "candidate manifest differs from pin"
 verify_state_manifest "$AFTER" "$CAND_CHANGED"
 mapfile -t got < <(candidate_diff_paths "$BASE" "$AFTER"); mapfile -t want < <(LC_ALL=C sort "$RUNTIME_LIST"); [[ "${got[*]}" == "${want[*]}" ]] || fail "exact 15-path diff mismatch"
 (cd "$AFTER" && sha256sum -c "$PROTECTED_CORE")
 grep -Fx 'VERSION_NAME=0.9726564' "$AFTER/app/version.properties" >/dev/null; grep -Fx 'VERSION_BUILD=26564' "$AFTER/app/version.properties" >/dev/null
 python3 "$VALIDATE" "$AFTER" "$BASE" | tee "$OUT/26564_true2x_semantic_validation.txt"; grep -F 'PASS TOTAL 45 / 45' "$OUT/26564_true2x_semantic_validation.txt" >/dev/null
 python3 "$MEMORY" "$AFTER" "$BASE" | tee "$OUT/26564_true2x_memory_validation.txt"; grep -F 'PASS TOTAL 12 / 12' "$OUT/26564_true2x_memory_validation.txt" >/dev/null
 python3 "$PARITY" | tee "$OUT/26564_true2x_cpu_gpu_numeric_parity.txt"; grep -F 'PASS synthetic CPU/GPU true2x parity' "$OUT/26564_true2x_cpu_gpu_numeric_parity.txt" >/dev/null
 set_report "CHANGED RUNTIME SCOPE" "PASS (exact 15 paths including one new JNI Java bridge + version)"
 set_report "TRUE 2X DIRECT CFA OWNERSHIP" "PASS (registered multiframe RAW/CFA -> direct 2x RGB; no native-RGB upscale/detail owner)"
 set_report "CPU/GPU EQUIVALENT SEMANTICS" "PASS (paired RBF equations + deterministic numeric parity fixture)"
 set_report "PHASE DIVERSITY" "PASS (four-bin independent occupancy separated from temporal support)"
 set_report "BOUNDED MEMORY" "PASS (CPU/GPU bounded tiles; disk-backed full RGB/gain staging)"
 set_report "GPU FAILURE CPU FALLBACK" "PASS (same estimator contract; GPU failure falls back to CPU)"
 set_report "LUMA ZERO CONTRACT" "PASS (luma=0 does not invoke luma/Pecan; both zero skips denoise)"
 set_report "26563 SATURATION/COLOR PROTECTION" "PASS (appearance GLSL/Java exact bytes + 18-file protected core)"
 set_report "MOTION/NIGHT DNG/UHDR OWNERSHIP" "PASS (pristine 2x LinearRaw; Motion 1:1 2x gain; Night post-Jin rebase)"
 set_report "EXCEPTION CLEANUP" "PASS (Motion/Night outer-finally true2x carriers)"
 set_report "OLD FAKE SR RETIRED" "PASS (legacy detail accumulator zero; definition-only old functions; native fallback only)"
 rm -rf "$GLSLOUT"; mkdir -p "$GLSLOUT"; python3 "$EXTRACT" --root "$AFTER" --out "$GLSLOUT" | tee "$OUT/26564_runtime_glsl_extraction.txt"
 (cd "$GLSLOUT" && sha256sum -c "$RUNTIME_GLSL_PIN")
 python3 "$RESERVED" "$GLSLOUT"/* | tee "$OUT/26564_reserved_identifier_scan.txt"
 set_report "GLSL RESERVED-IDENTIFIER SCAN" "PASS (all 4 exact runtime shaders; coherent/sample regressions)"; set_report "EXACT RUNTIME-EXPANDED GLSL" "PASS (4-file actual-runtime hash pin)"
 # Deterministic full-index patch regeneration at 7/12/40.
 local P="$WORK/patchscope"; seed_scope "$BASE" "$P"; (cd "$P"; git init -q; git config user.name Photon; git config user.email photon@example.invalid; git add -A; git commit -qm base)
 local BC; BC="$(cd "$P" && git rev-parse HEAD)"; apply_state_to_scope "$AFTER" "$P"; (cd "$P"; git add -A; git commit -qm candidate); local CC; CC="$(cd "$P" && git rev-parse HEAD)"
 for ab in 7 12 40; do (cd "$P" && git -c core.abbrev="$ab" diff --binary --full-index --no-ext-diff "$BC" "$CC") > "$WORK/forward.$ab.patch"; (cd "$P" && git -c core.abbrev="$ab" diff --binary --full-index --no-ext-diff "$CC" "$BC") > "$WORK/rollback.$ab.patch"; done
 cmp "$WORK/forward.7.patch" "$WORK/forward.12.patch"; cmp "$WORK/forward.7.patch" "$WORK/forward.40.patch"; cmp "$WORK/forward.40.patch" "$FORWARD"
 cmp "$WORK/rollback.7.patch" "$WORK/rollback.12.patch"; cmp "$WORK/rollback.7.patch" "$WORK/rollback.40.patch"; cmp "$WORK/rollback.40.patch" "$ROLLBACK"
 # Exact GNU patch fuzz=0 + git apply checks in independent scope directories.
 local FP="$WORK/forward_fuzz0"; seed_scope "$BASE" "$FP"; (cd "$FP"; git init -q; git apply --check "$FORWARD"; patch --batch --fuzz=0 -p1 < "$FORWARD" > "$OUT/26564_forward_patch_fuzz0.log"); verify_state_manifest "$FP" "$CAND_CHANGED"
 local RP="$WORK/rollback_fuzz0"; seed_scope "$AFTER" "$RP"; (cd "$RP"; git init -q; git apply --check "$ROLLBACK"; patch --batch --fuzz=0 -p1 < "$ROLLBACK" > "$OUT/26564_rollback_patch_fuzz0.log"); verify_state_manifest "$RP" "$PREWRITE"
 ! grep -Eqi 'fuzz|FAILED|reject' "$OUT/26564_forward_patch_fuzz0.log"; ! grep -Eqi 'fuzz|FAILED|reject' "$OUT/26564_rollback_patch_fuzz0.log"
 set_report "FORWARD PATCH FUZZ=0" PASS; set_report "ROLLBACK PATCH FUZZ=0" PASS; pass "candidate semantics/memory/parity/GLSL/patches"
}

run_real_glsl(){
 if ! command -v glslangValidator >/dev/null 2>&1 || [[ "$(dpkg-query -W -f='${Version}' glslang-tools 2>/dev/null || true)" != "$GLSLANG_PKG_VERSION" ]]; then sudo apt-get update -qq; sudo apt-get install -y --no-install-recommends "glslang-tools=${GLSLANG_PKG_VERSION}"; fi
 [[ "$(dpkg-query -W -f='${Version}' glslang-tools)" == "$GLSLANG_PKG_VERSION" ]] || fail "wrong glslang package"
 glslangValidator --version | tee "$OUT/26564_glslang_version.txt"; grep -F 'Khronos. 15.1.0' "$OUT/26564_glslang_version.txt" >/dev/null || fail "glslang version not 15.1.0"
 for s in "$GLSLOUT"/*.vert; do glslangValidator -S vert "$s"; done
 for s in "$GLSLOUT"/*.frag; do glslangValidator -S frag "$s"; done
 glslangValidator -l "$GLSLOUT/true2x_merge_26564.vert" "$GLSLOUT/true2x_merge_26564.frag"
 glslangValidator -l "$GLSLOUT/true2x_resolve_26564.vert" "$GLSLOUT/true2x_resolve_26564.frag"
 python3 - "$OUT/26564_V1_COMPILER_STATUS.txt" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]); p.write_text(p.read_text().replace('REAL GLSL COMPILE: NOT RUN YET','REAL GLSL COMPILE: PASS'))
PY
 set_report "REAL GLSL COMPILE" "PASS (pinned 15.1.0 exact runtime-expanded 4 shaders)"; pass "real GLSL compile"
}
install_frozen_candidate_into_live_root(){
 local live="$1" label="$2"; [[ -d "$live/app" ]] || fail "live fixture missing app"
 manifest_audited "$live" "$WORK/${label}_preinstall_runtime.sha256"; vendor_manifest "$live" "$WORK/${label}_preinstall_vendor.sha256"
 rm -rf "$live/app/src/main" "$live/app/version.properties" "$live/app/build.gradle"; mkdir -p "$live/app/src"; cp -a "$AFTER/app/src/main" "$live/app/src/"; cp "$AFTER/app/version.properties" "$live/app/version.properties"; cp "$AFTER/app/build.gradle" "$live/app/build.gradle"
 manifest_audited "$live" "$WORK/${label}_installed_runtime.sha256"; cmp "$WORK/${label}_installed_runtime.sha256" "$CAND_PIN" >/dev/null || fail "installed runtime != candidate"
 vendor_manifest "$live" "$WORK/${label}_installed_vendor.sha256"; cmp "$WORK/${label}_installed_vendor.sha256" "$VENDOR_PIN" >/dev/null || fail "installed vendor != authority"
 python3 "$VALIDATE" "$live" "$BASE" > "$OUT/${label}_installed_semantics.txt"; python3 "$MEMORY" "$live" "$BASE" > "$OUT/${label}_installed_memory.txt"
}
run_preinstall_vendor_authority_regression(){
 local f="$WORK/stale_checkout"; rm -rf "$f"; mkdir -p "$f/app/src/main/cpp/third_party_26507" "$f/app/src/main/cpp/deps"; printf 'stale\n' > "$f/app/src/main/cpp/third_party_26507/stale.txt"; printf 'VERSION_NAME=stale\nVERSION_BUILD=0\n' > "$f/app/version.properties"; printf '// stale\n' > "$f/app/build.gradle"
 vendor_manifest "$f" "$WORK/stale_vendor.sha256"; ! cmp -s "$WORK/stale_vendor.sha256" "$VENDOR_PIN" || fail "stale fixture invalid"; install_frozen_candidate_into_live_root "$f" regression
 set_report "PREINSTALL VENDOR AUTHORITY ORDERING" "PASS (stale checkout replaced by exact frozen candidate before compilation)"; pass "vendor-authority regression"
}
run_live_repository_extras_scope_regression(){
 local f="$WORK/live_repository_extras_scope_regression"; rm -rf "$f"; mkdir -p "$f"; cp -a "$AFTER/app" "$f/app"
 local extras=( '.gitignore' 'SupportedList.txt' 'proguard-rules.pro' 'src/androidTest/java/com/particlesdevs/photoncamera/gallery/adapters/DepthPageTransformerTest.java' 'src/test/java/android/util/Log.java' 'src/test/java/com/particlesdevs/photoncamera/capture/CaptureControllerTest.java' 'src/test/java/com/particlesdevs/photoncamera/debugclient/DebugClientTest.java' 'src/test/java/com/particlesdevs/photoncamera/processing/render/ColorCorrectionTransformTest.java' 'src/test/java/com/particlesdevs/photoncamera/ui/camera/CustomOrientationEventListenerTest.java' 'src/test/java/com/particlesdevs/photoncamera/ui/camera/TestSwitchToMode.java' 'src/test/java/com/particlesdevs/photoncamera/ui/camera/TestSwitchToModeTest.java' 'src/test/java/com/particlesdevs/photoncamera/util/RANSACTest.java' 'src/test/java/com/particlesdevs/photoncamera/util/UtilitiesTest.java' )
 for rel in "${extras[@]}"; do mkdir -p "$(dirname "$f/app/$rel")"; printf '26562 V1 exact Actions extras-scope regression retained by 26564\n' > "$f/app/$rel"; done
 python3 "$VALIDATE" "$f" "$BASE" > "$OUT/live_repository_extras_scope_regression.txt"; grep -F 'PASS TOTAL 45 / 45' "$OUT/live_repository_extras_scope_regression.txt" >/dev/null
 set_report "LIVE REPOSITORY EXTRAS SCOPE REGRESSION" "PASS (historical 13-path extras ignored outside audited runtime scope)"; pass "live repository extras-scope regression"
}

if [[ -n "$LOCAL_REPLAY_ARTIFACT" ]]; then
 echo "=== 26564 LOCAL PREBUILD 0: sealed package/pins ==="; verify_package_and_pins
 echo "=== 26564 LOCAL PREBUILD 1: exact successful 26563 artifact ==="; verify_base_artifact_and_reconstruct "$LOCAL_REPLAY_ARTIFACT"
 echo "=== 26564 LOCAL PREBUILD 2: candidate-first transform / true2x semantics / exact GLSL / patches ==="; build_candidate_and_precompile_proof
 echo "=== 26564 LOCAL PREBUILD 3: authority regressions ==="; run_preinstall_vendor_authority_regression; run_live_repository_extras_scope_regression
 if command -v glslangValidator >/dev/null 2>&1 && command -v dpkg-query >/dev/null 2>&1 && [[ "$(dpkg-query -W -f='${Version}' glslang-tools 2>/dev/null || true)" == "$GLSLANG_PKG_VERSION" ]]; then run_real_glsl; else echo 'LOCAL REAL GLSL COMPILE: NOT RUN (pinned glslang-tools package unavailable locally)' | tee "$OUT/26564_V1_LOCAL_COMPILER_LIMIT.txt"; fi
 echo 'LOCAL REAL KOTLIN/JAVA/NDK/ASSEMBLE: NOT RUN (authoritative Actions gate; Android SDK/project toolchain unavailable locally)' | tee -a "$OUT/26564_V1_LOCAL_COMPILER_LIMIT.txt"
 pass "26564 local prebuild replay complete"; exit 0
fi

echo "=== 26564 GATE 0: sealed handoff / direct lineage / architectural backup ==="
[[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch"
[[ "$(git rev-parse HEAD^)" == "$FAILED_V1_HANDOFF_COMMIT" ]] || fail "26564 V1.1 must be direct child of exact failed V1 handoff"
[[ "$(git rev-parse HEAD^^)" == "$BASE_SUCCESS_COMMIT" ]] || fail "failed V1 handoff must itself be direct child of successful 26563 V1"
git diff --quiet "$BASE_SUCCESS_COMMIT..HEAD" -- app || fail "V1/V1.1 handoffs directly changed repository app source"
[[ -n "$TOKEN" ]] || fail "GITHUB_TOKEN missing"; verify_package_and_pins
BACKUP_SHA="$(git ls-remote origin "refs/heads/${BACKUP_BRANCH}" | awk '{print $1}')"; [[ "$BACKUP_SHA" == "$BACKUP_SHA_EXPECTED" ]] || fail "backup missing/wrong"; set_report "BACKUP STATUS" "PASS (${BACKUP_BRANCH} @ ${BACKUP_SHA_EXPECTED})"
python3 - "$BASE_SUCCESS_COMMIT" "$HANDOFF_HASHES" <<'PY'
from pathlib import Path
import subprocess,sys
base=sys.argv[1]; hf=Path(sys.argv[2])
allowed={line.split('  ',1)[1] for line in hf.read_text().splitlines() if line.strip()}
allowed.add('V1_26564_HANDOFF_HASHES.sha256')
actual=set(subprocess.check_output(['git','diff','--name-only',base+'..HEAD'],text=True).splitlines())
if actual!=allowed: raise SystemExit('handoff scope mismatch extra=%r missing=%r'%(sorted(actual-allowed),sorted(allowed-actual)))
if any(x.startswith('app/') for x in actual): raise SystemExit('handoff modified repository app source')
if any(('\n' in x or '\r' in x) for x in allowed): raise SystemExit('REGRESSION_26564_V1_HANDOFF_SCOPE_NEWLINE')
print('PASS exact sealed 26564 V1.1 handoff scope',len(actual),'files')
PY
! grep -R -F 'V1_26564_' .github/workflows --exclude='build-26564-v1-true-2x-sr.yml' | grep -q . || fail "overlapping 26564 workflow trigger"
pass "sealed 26564 V1.1 package / failed-V1 lineage / backup"

echo "=== 26564 GATE 1: exact successful compiled 26563 authority ==="
REPO_API="https://api.github.com/repos/${GITHUB_REPOSITORY:-SkyKing0007/Photon-Camera}"
curl --fail --location --silent --show-error --retry 5 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' -H 'X-GitHub-Api-Version: 2022-11-28' "$REPO_API/actions/runs/${BASE_RUN_ID}" -o "$WORK/base_run.json"
python3 - "$WORK/base_run.json" "$BASE_RUN_ID" "$BASE_SUCCESS_COMMIT" "$EXPECTED_BRANCH" <<'PY'
import json,sys
d=json.load(open(sys.argv[1])); assert str(d.get('id'))==sys.argv[2] and d.get('conclusion')=='success' and d.get('head_sha')==sys.argv[3] and d.get('head_branch')==sys.argv[4]; print('PASS exact successful 26563 Actions run')
PY
curl --fail --location --silent --show-error --retry 5 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' -H 'X-GitHub-Api-Version: 2022-11-28' "$REPO_API/actions/artifacts/${BASE_ARTIFACT_ID}" -o "$WORK/base_artifact.json"
python3 - "$WORK/base_artifact.json" "$BASE_ARTIFACT_ID" "$BASE_ARTIFACT_NAME" "$BASE_ARTIFACT_SHA" <<'PY'
import json,sys
d=json.load(open(sys.argv[1])); assert str(d.get('id'))==sys.argv[2] and d.get('name')==sys.argv[3] and not d.get('expired') and d.get('digest')=='sha256:'+sys.argv[4]; print('PASS exact 26563 artifact metadata/digest')
PY
curl --fail --location --silent --show-error --retry 5 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' -H 'X-GitHub-Api-Version: 2022-11-28' "$REPO_API/actions/artifacts/${BASE_ARTIFACT_ID}/zip" -o "$ARTZIP"; verify_base_artifact_and_reconstruct "$ARTZIP"

echo "=== 26564 GATE 2: candidate-first true2x transform / semantic+memory+parity / exact GLSL / deterministic patches ==="; build_candidate_and_precompile_proof
echo "=== 26564 GATE 3: pinned real glslangValidator ==="; run_real_glsl
echo "=== 26564 GATE 4: controlled live install / authority regressions / real Kotlin+Java / full assemble ==="
run_preinstall_vendor_authority_regression; run_live_repository_extras_scope_regression; install_frozen_candidate_into_live_root "$ROOT" repository
rm -rf "$ROOT/app/build/outputs/apk/debug"
./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace
python3 - "$OUT/26564_V1_COMPILER_STATUS.txt" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]); p.write_text(p.read_text().replace('REAL KOTLIN COMPILE: NOT RUN YET','REAL KOTLIN COMPILE: PASS').replace('REAL JAVA COMPILE: NOT RUN YET','REAL JAVA COMPILE: PASS'))
PY
set_report "REAL KOTLIN COMPILE" PASS; set_report "REAL JAVA COMPILE" PASS
./gradlew :app:assembleDebug --stacktrace
python3 - "$OUT/26564_V1_COMPILER_STATUS.txt" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]); p.write_text(p.read_text().replace('NATIVE/NDK COMPILE: NOT RUN YET (covered by full assemble)','NATIVE/NDK COMPILE: PASS (full assemble)').replace('FULL ANDROID ASSEMBLE: NOT RUN YET','FULL ANDROID ASSEMBLE: PASS'))
PY
set_report "NATIVE/NDK COMPILE" "PASS (full assemble)"; set_report "FULL ANDROID ASSEMBLE" PASS
mapfile -t APKS < <(find "$ROOT/app/build/outputs/apk/debug" -maxdepth 1 -type f -name '*.apk' -print); [[ "${#APKS[@]}" -eq 1 ]] || fail "expected exactly one debug APK, found ${#APKS[@]}"; mv "${APKS[0]}" "$FINAL"; [[ -s "$FINAL" ]] || fail "final APK missing"; [[ "$(find "$ROOT/app/build/outputs/apk/debug" -maxdepth 1 -type f -name '*.apk' | wc -l)" -eq 0 ]] || fail "duplicate APK remained"; sha256sum "$FINAL" > "$OUT/26564_V1_APK.sha256"; pass "real Kotlin/Java/NDK + full assemble + exactly one APK"

echo "=== 26564 GATE 5: post-build frozen candidate / protected / vendor / shader invariance ==="
manifest_audited "$ROOT" "$OUT/26564_postbuild_runtime.sha256"; cmp "$OUT/26564_postbuild_runtime.sha256" "$CAND_PIN" >/dev/null || fail "postbuild runtime changed"
manifest_audited "$AFTER" "$OUT/26564_frozen_candidate_postbuild.sha256"; cmp "$OUT/26564_frozen_candidate_postbuild.sha256" "$CAND_PIN" >/dev/null || fail "frozen candidate changed"
vendor_manifest "$ROOT" "$OUT/26564_vendor_postbuild.sha256"; cmp "$OUT/26564_vendor_postbuild.sha256" "$VENDOR_PIN" >/dev/null || fail "vendor changed during build"
(cd "$ROOT" && sha256sum -c "$PROTECTED_CORE")
rm -rf "$WORK/runtime_glsl_post"; mkdir -p "$WORK/runtime_glsl_post"; python3 "$EXTRACT" --root "$ROOT" --out "$WORK/runtime_glsl_post" >/dev/null; (cd "$WORK/runtime_glsl_post" && sha256sum -c "$RUNTIME_GLSL_PIN"); python3 "$RESERVED" "$WORK/runtime_glsl_post"/* > "$OUT/26564_postbuild_reserved_identifier_scan.txt"
python3 "$VALIDATE" "$ROOT" "$BASE" > "$OUT/26564_postbuild_semantic_validation.txt"; python3 "$MEMORY" "$ROOT" "$BASE" > "$OUT/26564_postbuild_memory_validation.txt"
python3 - "$OUT/26564_V1_COMPILER_STATUS.txt" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]); p.write_text(p.read_text().replace('POST-BUILD INVARIANCE: NOT RUN YET','POST-BUILD INVARIANCE: PASS'))
PY
set_report "POST-BUILD INVARIANCE" PASS; pass "post-build invariance"

echo "=== 26564 GATE 6: deterministic clean candidate source export ==="
tar --sort=name --mtime='UTC 2020-01-01' --owner=0 --group=0 --numeric-owner -czf "$OUT/26564_V1_candidate_app_source.tar.gz" -C "$AFTER" app
sha256sum "$OUT/26564_V1_candidate_app_source.tar.gz" > "$OUT/26564_V1_candidate_app_source.tar.gz.sha256"; cp "$CAND_PIN" "$OUT/26564_V1_candidate_source.sha256"; set_report "CLEAN ARTIFACT SOURCE EXPORT" PASS
pass "26564 V1 BUILD-PROVEN Actions output"
