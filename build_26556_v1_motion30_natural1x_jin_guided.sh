#!/usr/bin/env bash
set -euo pipefail
fail(){ echo "ERROR: $*" >&2; exit 1; }
pass(){ echo "PASS: $*"; }
sha(){ sha256sum "$1" | awk '{print $1}'; }
manifest_audited(){ local root="$1" out="$2"; (cd "$root" && { find app/src/main -type f ! -path 'app/src/main/cpp/third_party_26507/*' ! -path 'app/src/main/cpp/deps/*' -print; [[ -f app/src/main/cpp/deps/.gitignore ]] && echo app/src/main/cpp/deps/.gitignore; echo app/version.properties; echo app/build.gradle; } | LC_ALL=C sort | while read -r f; do sha256sum "$f"; done) > "$out"; }
vendor_manifest(){ local root="$1" out="$2"; (cd "$root" && { [[ -d app/src/main/cpp/third_party_26507 ]] && find app/src/main/cpp/third_party_26507 -type f -print; [[ -d app/src/main/cpp/deps ]] && find app/src/main/cpp/deps -type f -print; } | LC_ALL=C sort | while read -r f; do sha256sum "$f"; done) > "$out"; }
exact_tree_equal(){ python3 - "$1" "$2" <<'PY'
from pathlib import Path
import hashlib,sys
def m(root):
 root=Path(root); return {p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file() and '.git' not in p.parts}
a,b=m(sys.argv[1]),m(sys.argv[2])
if a!=b:
 bad=[k for k in sorted(set(a)|set(b)) if a.get(k)!=b.get(k)]
 raise SystemExit('tree mismatch: '+repr(bad[:30]))
PY
}
ROOT="$(pwd)"
EXPECTED_BRANCH="experimental-clean-photon-rebuild"
BASE_SUCCESS_COMMIT="45baab3044b95be7c60638b5404c53f02966128f"
BACKUP_BRANCH="backup-26555-v1-before-26556-frames-zoom-jin-guidance"
BASE_RUN_ID="33205216686"
BASE_ARTIFACT_ID="9699482627"
BASE_ARTIFACT_NAME="photon-26555-v1-jin-reference-preview-recovery"
BASE_ARTIFACT_SHA="622a3b163f41ad2f2b95a87955fe2ddad8296504aab15f17efecbd17f7f78220"
BASE_TAR_SHA="7ed49f3cdccb7076b1ca25c480fcc80752f820633b3ba9dd1954d2bb1b63ca98"
BASE_MANIFEST_SHA="fac620a2decc10bc23d22531236a0eef589d8f9778f6be3bec529c8c48b8339f"
CAND_MANIFEST_SHA="aa0a28cbe2cb7a71943e35f8ba715190b6011e34e07c74cd08cc6bd034ccd500"
BASE_APK_SHA="9735c38022925d9221f4cfd536710aa5d05964531bd60a3b5407d2768d27c37f"
VENDOR_MANIFEST_SHA="7dbcc5ee5b9040965e431d79c45c5100f559c2b96c50970ca21987c684c825a8"
VERSION_NAME="0.9726556"
VERSION_BUILD="26556"
TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"
BASE_PIN="$ROOT/V1_26556_BASE_26555_V1_AUDITED_RUNTIME.sha256"
BASE_TAR_PIN="$ROOT/V1_26556_BASE_26555_V1_CANDIDATE_TAR.sha256"
CAND_PIN="$ROOT/V1_26556_EXPECTED_CANDIDATE_AUDITED_RUNTIME.sha256"
VENDOR_PIN="$ROOT/V1_26556_NATIVE_VENDOR_DEPENDENCIES.sha256"
RUNTIME_LIST="$ROOT/V1_26556_RUNTIME_FILES.txt"
PREWRITE="$ROOT/V1_26556_PREWRITE_SOURCE_HASHES.sha256"
CAND_CHANGED="$ROOT/V1_26556_CANDIDATE_CHANGED_HASHES.sha256"
FORWARD="$ROOT/V1_26556_RUNTIME_DELTA_FROM_26555_V1.patch"
ROLLBACK="$ROOT/V1_26556_RUNTIME_ROLLBACK_TO_26555_V1.patch"
VALIDATE="$ROOT/validate_26556_v1_motion30_natural1x_jin_guided.py"
GLSL_PIN="$ROOT/V1_26556_PROTECTED_ALL_GLSL.sha256"
HANDOFF_HASHES="$ROOT/V1_26556_HANDOFF_HASHES.sha256"
OUT="$ROOT/build_26556_v1_motion30_natural1x_jin_guided_outputs"
WORK="$ROOT/.build_26556_v1_motion30_natural1x_jin_guided_work"
ARTZIP="$WORK/26555_v1_artifact.zip"; ARTDIR="$WORK/artifact"; BASE="$WORK/exact_26555_compiled_candidate"; AFTER="$WORK/candidate_26556"; PATCHREPO="$WORK/patchrepo"
FINAL="$ROOT/IrisCamera-${VERSION_NAME}-${VERSION_BUILD}-v1-motion30-natural1x-jin-guided-debug.apk"
mapfile -t RUNTIME_FILES < "$RUNTIME_LIST"
[[ "${#RUNTIME_FILES[@]}" -eq 7 ]] || fail "runtime inventory must contain exactly 7 files"
rm -rf "$OUT" "$WORK"; rm -f "$FINAL"; mkdir -p "$OUT" "$WORK" "$ARTDIR" "$BASE" "$AFTER"
cat > "$OUT/26556_V1_COMPILER_STATUS.txt" <<'EOF'
REAL GLSL COMPILE: PASS INHERITED (no GLSL modified; exact successful 26555 bytes required)
REAL KOTLIN COMPILE: NOT RUN YET
REAL JAVA COMPILE: NOT RUN YET
FULL ANDROID ASSEMBLE: NOT RUN YET
NATIVE/NDK COMPILE: NOT RUN YET (covered by full assemble)
POST-BUILD INVARIANCE: NOT RUN YET
EOF
cat > "$OUT/26556_V1_STRICT_HANDOFF_REPORT.txt" <<'EOF'
RUNTIME OWNERSHIP: NOT RUN
DORMANT-OWNER REJECTION: NOT RUN
EXACT PRIOR RUNTIME AUTHORITY: NOT RUN
CHANGED RUNTIME SCOPE: NOT RUN
MOTION FRAME CAP 30 / PRE-SHUTTER ZSL: NOT RUN
NIGHT 2-50 FRAME ROUTING INVARIANCE: NOT RUN
GLOBAL SLIDER OPTION B: NOT RUN
MOTION+NIGHT NATURAL 1.0X: NOT RUN
POST-STARTUP MOTION ZOOM INVARIANCE: NOT RUN
JIN MODEL/INFERENCE SEMANTICS: NOT RUN
JIN SMOOTH EXACT-BILINEAR INVARIANT: NOT RUN
JIN SEGMENTED-EDGE REGRESSION: NOT RUN
PROTECTED SABRE/VGN/UHDR/NIGHT: NOT RUN
GLSL/KOTLIN BYTE INVARIANCE: NOT RUN
REAL GLSL COMPILE: PASS INHERITED (no GLSL modified)
REAL KOTLIN COMPILE: NOT RUN
REAL JAVA COMPILE: NOT RUN
NATIVE/NDK COMPILE: NOT RUN
FULL ANDROID ASSEMBLE: NOT RUN
FORWARD PATCH FUZZ=0: NOT RUN
ROLLBACK PATCH FUZZ=0: NOT RUN
POST-BUILD INVARIANCE: NOT RUN
CLEAN ARTIFACT SOURCE EXPORT: NOT RUN
BACKUP BRANCH: NOT RUN
TARGET VERSION/BUILD: 0.9726556 / 26556 V1
EOF
set_report(){ python3 - "$OUT/26556_V1_STRICT_HANDOFF_REPORT.txt" "$1" "$2" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]); key=sys.argv[2]; val=sys.argv[3]; lines=p.read_text().splitlines()
for i,x in enumerate(lines):
 if x.startswith(key+':'): lines[i]=key+': '+val; break
else: raise SystemExit('missing report key '+key)
p.write_text('\n'.join(lines)+'\n')
PY
}

echo "=== 26556 GATE 0: sealed handoff / branch / lineage ==="
[[ "$(git branch --show-current)" == "$EXPECTED_BRANCH" ]] || fail "wrong branch"
[[ "$(git rev-parse HEAD^)" == "$BASE_SUCCESS_COMMIT" ]] || fail "handoff commit parent is not exact successful 26555 commit"
[[ -n "$TOKEN" ]] || fail "GitHub token unavailable"
sha256sum -c "$HANDOFF_HASHES"
python3 -m py_compile "$VALIDATE"
python3 "$VALIDATE" --self-test
bash -n "$0"
[[ "$(sha "$BASE_PIN")" == "$BASE_MANIFEST_SHA" ]] || fail "base manifest SHA drift"
[[ "$(wc -l < "$BASE_PIN")" -eq 970 ]] || fail "base manifest line count"
[[ "$(sha "$CAND_PIN")" == "$CAND_MANIFEST_SHA" ]] || fail "candidate manifest SHA drift"
[[ "$(wc -l < "$CAND_PIN")" -eq 970 ]] || fail "candidate manifest line count"
[[ "$(sha "$VENDOR_PIN")" == "$VENDOR_MANIFEST_SHA" ]] || fail "vendor manifest SHA drift"
[[ "$(wc -l < "$VENDOR_PIN")" -eq 778 ]] || fail "vendor manifest line count"
grep -F "$BASE_TAR_SHA" "$BASE_TAR_PIN" >/dev/null || fail "base TAR pin drift"
# 26553 permanent regression: all handoff SHA paths must be portable; exact /mnt/data absolute path must be rejected.
python3 - "$RUNTIME_LIST" <<'PY'
from pathlib import Path,PurePosixPath
import re,sys
runtime=[x.strip() for x in Path(sys.argv[1]).read_text().splitlines() if x.strip()]
def bad(x): return x.startswith('/') or x.startswith('\\') or re.match(r'^[A-Za-z]:[\\/]',x) or '\\' in x or '..' in PurePosixPath(x).parts
assert bad('/mnt/data/26553_base/app/version.properties')
for p in Path('.').glob('V1_26556_*.sha256'):
 for n,line in enumerate(p.read_text().splitlines(),1):
  if not line.strip(): continue
  parts=line.split(maxsplit=1)
  if len(parts)!=2 or not re.fullmatch(r'[0-9a-fA-F]{64}',parts[0]): raise SystemExit(f'{p}:{n}: malformed SHA line')
  entry=parts[1].lstrip('*')
  if bad(entry): raise SystemExit(f'{p}:{n}: nonportable path {entry!r}')
pre=[x.split(maxsplit=1)[1].lstrip('*') for x in Path('V1_26556_PREWRITE_SOURCE_HASHES.sha256').read_text().splitlines() if x.strip()]
if pre!=runtime: raise SystemExit('prewrite paths != runtime inventory')
print('PASS portable SHA manifests and 26553 absolute-path regression')
PY
# Repository handoff scope itself must contain no direct app source writes.
python3 - "$BASE_SUCCESS_COMMIT" <<'PY'
import subprocess,sys
base=sys.argv[1]
allowed={
'.github/workflows/build-26556-v1-motion30-natural1x-jin-guided.yml',
'V1_26556_BASE_26555_V1_AUDITED_RUNTIME.sha256','V1_26556_BASE_26555_V1_CANDIDATE_TAR.sha256',
'V1_26556_BASE_PROVENANCE.txt','V1_26556_CANDIDATE_CHANGED_HASHES.sha256',
'V1_26556_EXPECTED_CANDIDATE_AUDITED_RUNTIME.sha256','V1_26556_HANDOFF_HASHES.sha256',
'V1_26556_LOCAL_VALIDATION.txt','V1_26556_NATIVE_VENDOR_DEPENDENCIES.sha256',
'V1_26556_PREWRITE_SOURCE_HASHES.sha256','V1_26556_PROTECTED_ALL_GLSL.sha256',
'V1_26556_RUNTIME_DELTA_FROM_26555_V1.patch','V1_26556_RUNTIME_FILES.txt',
'V1_26556_RUNTIME_ROLLBACK_TO_26555_V1.patch','V1_26556_UPLOAD_INSTRUCTIONS.md',
'build_26556_v1_motion30_natural1x_jin_guided.sh','validate_26556_v1_motion30_natural1x_jin_guided.py'}
actual=set(subprocess.check_output(['git','diff','--name-only',base+'..HEAD'],text=True).splitlines())
if actual!=allowed: raise SystemExit('handoff scope mismatch extra=%r missing=%r'%(sorted(actual-allowed),sorted(allowed-actual)))
if any(x.startswith('app/') for x in actual): raise SystemExit('handoff directly modified repository app source')
print('PASS exact 17-file handoff scope; repository app source untouched')
PY
pass "sealed handoff lineage"

echo "=== 26556 GATE 1: exact successful compiled 26555 runtime authority ==="
REPO_API="https://api.github.com/repos/${GITHUB_REPOSITORY:-SkyKing0007/Photon-Camera}"
curl --fail --location --silent --show-error --retry 5 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "$REPO_API/actions/runs/${BASE_RUN_ID}" -o "$WORK/base_run.json"
python3 - "$WORK/base_run.json" "$BASE_RUN_ID" "$BASE_SUCCESS_COMMIT" "$EXPECTED_BRANCH" <<'PY'
import json,sys
d=json.load(open(sys.argv[1])); assert str(d.get('id'))==sys.argv[2]; assert d.get('conclusion')=='success'; assert d.get('head_sha')==sys.argv[3]; assert d.get('head_branch')==sys.argv[4]
print('PASS exact successful 26555 run')
PY
git fetch origin "$BACKUP_BRANCH" --quiet
git show-ref --verify --quiet "refs/remotes/origin/${BACKUP_BRANCH}" || fail "backup branch missing"
[[ "$(git rev-parse "origin/${BACKUP_BRANCH}")" == "$BASE_SUCCESS_COMMIT" ]] || fail "backup branch wrong commit"
set_report "BACKUP BRANCH" "PASS (${BACKUP_BRANCH} @ ${BASE_SUCCESS_COMMIT})"
curl --fail --location --silent --show-error --retry 5 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "$REPO_API/actions/artifacts/${BASE_ARTIFACT_ID}" -o "$WORK/base_artifact.json"
python3 - "$WORK/base_artifact.json" "$BASE_ARTIFACT_ID" "$BASE_ARTIFACT_NAME" <<'PY'
import json,sys
d=json.load(open(sys.argv[1])); assert str(d.get('id'))==sys.argv[2]; assert d.get('name')==sys.argv[3]; assert not d.get('expired'); print('PASS exact 26555 artifact metadata')
PY
curl --fail --location --silent --show-error --retry 5 -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "$REPO_API/actions/artifacts/${BASE_ARTIFACT_ID}/zip" -o "$ARTZIP"
[[ "$(sha "$ARTZIP")" == "$BASE_ARTIFACT_SHA" ]] || fail "26555 artifact ZIP SHA mismatch"
unzip -q "$ARTZIP" -d "$ARTDIR"
BASE_OUT="$ARTDIR/build_26555_v1_jin_reference_preview_recovery_outputs"
BASE_TAR="$BASE_OUT/26555_V1_candidate_app_source.tar.gz"
BASE_AUDITED="$BASE_OUT/26555_V1_candidate_source.sha256"
BASE_COMPILER="$BASE_OUT/26555_V1_COMPILER_STATUS.txt"
BASE_REPORT="$BASE_OUT/26555_V1_STRICT_HANDOFF_REPORT.txt"
BASE_APK="$ARTDIR/IrisCamera-0.9726555-26555-v1-jin-reference-preview-recovery-debug.apk"
for f in "$BASE_TAR" "$BASE_AUDITED" "$BASE_COMPILER" "$BASE_REPORT" "$BASE_APK"; do [[ -f "$f" ]] || fail "base artifact missing $f"; done
[[ "$(sha "$BASE_TAR")" == "$BASE_TAR_SHA" ]] || fail "base candidate TAR SHA mismatch"
[[ "$(sha "$BASE_APK")" == "$BASE_APK_SHA" ]] || fail "base APK SHA mismatch"
for x in 'REAL GLSL COMPILE: PASS' 'REAL KOTLIN COMPILE: PASS' 'REAL JAVA COMPILE: PASS' 'FULL ANDROID ASSEMBLE: PASS' 'POST-BUILD INVARIANCE: PASS'; do grep -F "$x" "$BASE_COMPILER" >/dev/null || fail "base compiler proof missing $x"; done
cmp "$BASE_AUDITED" "$BASE_PIN" >/dev/null || fail "packaged 26555 candidate manifest differs from handoff base pin"
[[ "$(sha "$BASE_AUDITED")" == "$BASE_MANIFEST_SHA" ]] || fail "base artifact manifest SHA mismatch"
[[ "$(wc -l < "$BASE_AUDITED")" -eq 970 ]] || fail "base artifact manifest line count"
tar -xzf "$BASE_TAR" -C "$BASE"
manifest_audited "$BASE" "$OUT/26555_reconstructed_runtime.sha256"
cmp "$OUT/26555_reconstructed_runtime.sha256" "$BASE_PIN" >/dev/null || fail "reconstructed 26555 source not exact"
vendor_manifest "$BASE" "$OUT/26555_vendor_base.sha256"
cmp "$OUT/26555_vendor_base.sha256" "$VENDOR_PIN" >/dev/null || fail "base vendor manifest mismatch"
set_report "EXACT PRIOR RUNTIME AUTHORITY" "PASS (run ${BASE_RUN_ID} artifact ${BASE_ARTIFACT_ID})"
pass "exact successful compiled 26555 authority"

echo "=== 26556 GATE 2: candidate-first transform + semantic/ownership proof ==="
# Exact base hashes before any transform.
(cd "$BASE" && sha256sum -c "$PREWRITE")
cp -a "$BASE/." "$AFTER/"
# Apply canonical forward patch to temporary candidate only.
(cd "$AFTER" && git init -q && git config user.email audit@example.invalid && git config user.name PhotonAudit && git add -A && git commit -q -m base26555 && git apply --check "$FORWARD" && git apply "$FORWARD")
python3 "$VALIDATE" --base "$BASE" --candidate "$AFTER" | tee "$OUT/26556_runtime_contract.txt"
manifest_audited "$AFTER" "$OUT/26556_candidate_runtime.sha256"
cmp "$OUT/26556_candidate_runtime.sha256" "$CAND_PIN" >/dev/null || fail "candidate manifest mismatch"
[[ "$(sha "$OUT/26556_candidate_runtime.sha256")" == "$CAND_MANIFEST_SHA" ]] || fail "candidate manifest SHA mismatch"
[[ "$(wc -l < "$OUT/26556_candidate_runtime.sha256")" -eq 970 ]] || fail "candidate manifest count"
vendor_manifest "$AFTER" "$OUT/26556_vendor_candidate.sha256"
cmp "$OUT/26556_vendor_candidate.sha256" "$VENDOR_PIN" >/dev/null || fail "candidate vendor drift"
(cd "$AFTER" && sha256sum -c "$CAND_CHANGED")
# Exact seven-file allowlist, independent of validator.
python3 - "$BASE" "$AFTER" "$RUNTIME_LIST" <<'PY'
from pathlib import Path
import hashlib,sys
b,c=Path(sys.argv[1]),Path(sys.argv[2]); expected=[x.strip() for x in Path(sys.argv[3]).read_text().splitlines() if x.strip()]
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
B={p.relative_to(b).as_posix():h(p) for p in b.rglob('*') if p.is_file() and '.git' not in p.parts}; C={p.relative_to(c).as_posix():h(p) for p in c.rglob('*') if p.is_file() and '.git' not in p.parts}
actual=sorted(k for k in set(B)|set(C) if B.get(k)!=C.get(k))
if actual!=sorted(expected): raise SystemExit('runtime scope '+repr(actual))
print('PASS exact seven-file runtime/version scope')
PY
# All GLSL must be exact successful 26555 bytes. No runtime-expanded GLSL changed, so successful 26555 real compiler proof is inherited.
(cd "$AFTER" && sha256sum -c "$GLSL_PIN") > "$OUT/26556_all_glsl_byte_invariance.txt"
set_report "CHANGED RUNTIME SCOPE" "PASS (7 files including version.properties)"
set_report "RUNTIME OWNERSHIP" "PASS"
set_report "DORMANT-OWNER REJECTION" "PASS"
set_report "MOTION FRAME CAP 30 / PRE-SHUTTER ZSL" "PASS"
set_report "NIGHT 2-50 FRAME ROUTING INVARIANCE" "PASS"
set_report "GLOBAL SLIDER OPTION B" "PASS"
set_report "MOTION+NIGHT NATURAL 1.0X" "PASS"
set_report "POST-STARTUP MOTION ZOOM INVARIANCE" "PASS"
set_report "JIN MODEL/INFERENCE SEMANTICS" "PASS"
set_report "JIN SMOOTH EXACT-BILINEAR INVARIANT" "PASS"
set_report "JIN SEGMENTED-EDGE REGRESSION" "PASS"
set_report "PROTECTED SABRE/VGN/UHDR/NIGHT" "PASS"
set_report "GLSL/KOTLIN BYTE INVARIANCE" "PASS"
pass "candidate ownership/contracts"

echo "=== 26556 GATE 3: canonical deterministic patch proof ==="
rm -rf "$PATCHREPO"; cp -a "$BASE" "$PATCHREPO"; cd "$PATCHREPO"
git init -q; git config user.email audit@example.invalid; git config user.name PhotonAudit; git add -A; git commit -q -m base
B=$(git rev-parse HEAD); rm -rf app; cp -a "$AFTER/app" ./app; git add -A; git diff --cached --check; git commit -q -m candidate; C=$(git rev-parse HEAD)
for ab in 7 12 40; do
 git -c core.abbrev=$ab diff --binary --full-index --no-ext-diff "$B" "$C" > "$WORK/fwd_${ab}.patch"
 git -c core.abbrev=$ab diff --binary --full-index --no-ext-diff "$C" "$B" > "$WORK/rbk_${ab}.patch"
done
cmp "$WORK/fwd_7.patch" "$WORK/fwd_12.patch" >/dev/null; cmp "$WORK/fwd_7.patch" "$WORK/fwd_40.patch" >/dev/null
cmp "$WORK/rbk_7.patch" "$WORK/rbk_12.patch" >/dev/null; cmp "$WORK/rbk_7.patch" "$WORK/rbk_40.patch" >/dev/null
cmp "$WORK/fwd_40.patch" "$FORWARD" >/dev/null || fail "forward patch not canonical regenerated bytes"
cmp "$WORK/rbk_40.patch" "$ROLLBACK" >/dev/null || fail "rollback patch not canonical regenerated bytes"
# Forward exact recreation from base.
rm -rf "$WORK/fwd_replay"; cp -a "$BASE" "$WORK/fwd_replay"; (cd "$WORK/fwd_replay" && git init -q && git config user.email audit@example.invalid && git config user.name PhotonAudit && git add -A && git commit -q -m base && git apply --check "$FORWARD" && git apply "$FORWARD")
exact_tree_equal "$WORK/fwd_replay" "$AFTER"
# Rollback exact recreation; --whitespace=nowarn only suppresses one historical 26555 baseline trailing-space warning restored by rollback.
rm -rf "$WORK/rbk_replay"; cp -a "$AFTER" "$WORK/rbk_replay"; (cd "$WORK/rbk_replay" && git init -q && git config user.email audit@example.invalid && git config user.name PhotonAudit && git add -A && git commit -q -m cand && git apply --check --whitespace=nowarn "$ROLLBACK" && git apply --whitespace=nowarn "$ROLLBACK")
exact_tree_equal "$WORK/rbk_replay" "$BASE"
set_report "FORWARD PATCH FUZZ=0" "PASS"
set_report "ROLLBACK PATCH FUZZ=0" "PASS"
cd "$ROOT"
pass "canonical patches deterministic and exact"

echo "=== 26556 GATE 4: controlled live install + version/compiler sequence ==="
# Record repository source hashes immediately before the only live source write.
: > "$OUT/26556_repository_prewrite_source_hashes.sha256"
for f in "${RUNTIME_FILES[@]}"; do [[ -f "$ROOT/$f" ]] && sha256sum "$ROOT/$f" >> "$OUT/26556_repository_prewrite_source_hashes.sha256" || true; done
rm -rf "$ROOT/app/src"
cp -a "$AFTER/app/src" "$ROOT/app/src"
cp "$AFTER/app/version.properties" "$ROOT/app/version.properties"
cp "$AFTER/app/build.gradle" "$ROOT/app/build.gradle"
manifest_audited "$ROOT" "$OUT/26556_installed_precompiler.sha256"
cmp "$OUT/26556_installed_precompiler.sha256" "$CAND_PIN" >/dev/null || fail "installed candidate differs before compiler"
vendor_manifest "$ROOT" "$OUT/26556_vendor_precompiler.sha256"
cmp "$OUT/26556_vendor_precompiler.sha256" "$VENDOR_PIN" >/dev/null || fail "vendor drift before compiler"
python3 "$VALIDATE" --base "$BASE" --candidate "$AFTER" > "$OUT/26556_precompiler_contract.txt"
grep -F 'VERSION_NAME=0.9726556' "$ROOT/app/version.properties" >/dev/null || fail "version name"
grep -F 'VERSION_BUILD=26556' "$ROOT/app/version.properties" >/dev/null || fail "version build"
chmod +x ./gradlew
./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace
python3 - "$OUT/26556_V1_COMPILER_STATUS.txt" <<'PY'
from pathlib import Path
p=Path(__import__('sys').argv[1]);s=p.read_text().replace('REAL KOTLIN COMPILE: NOT RUN YET','REAL KOTLIN COMPILE: PASS').replace('REAL JAVA COMPILE: NOT RUN YET','REAL JAVA COMPILE: PASS');p.write_text(s)
PY
set_report "REAL KOTLIN COMPILE" "PASS"
set_report "REAL JAVA COMPILE" "PASS"
./gradlew :app:assembleDebug --stacktrace
python3 - "$OUT/26556_V1_COMPILER_STATUS.txt" <<'PY'
from pathlib import Path
p=Path(__import__('sys').argv[1]);s=p.read_text().replace('FULL ANDROID ASSEMBLE: NOT RUN YET','FULL ANDROID ASSEMBLE: PASS').replace('NATIVE/NDK COMPILE: NOT RUN YET (covered by full assemble)','NATIVE/NDK COMPILE: PASS (full assemble)');p.write_text(s)
PY
set_report "NATIVE/NDK COMPILE" "PASS (full assemble)"
set_report "FULL ANDROID ASSEMBLE" "PASS"
mapfile -t APKS < <(find "$ROOT/app/build/outputs/apk/debug" -maxdepth 1 -type f -name '*.apk' -print)
[[ "${#APKS[@]}" -eq 1 ]] || fail "expected exactly one debug APK, got ${#APKS[@]}"
cp "${APKS[0]}" "$FINAL"
pass "real project compilers and full assemble"

echo "=== 26556 GATE 5: post-build frozen-candidate/protected/native/vendor invariance ==="
manifest_audited "$ROOT" "$OUT/26556_postbuild_runtime.sha256"
cmp "$OUT/26556_postbuild_runtime.sha256" "$CAND_PIN" >/dev/null || fail "runtime source changed during build"
manifest_audited "$AFTER" "$OUT/26556_frozen_candidate_postbuild.sha256"
cmp "$OUT/26556_frozen_candidate_postbuild.sha256" "$CAND_PIN" >/dev/null || fail "frozen candidate changed during build"
vendor_manifest "$ROOT" "$OUT/26556_vendor_postbuild.sha256"
cmp "$OUT/26556_vendor_postbuild.sha256" "$VENDOR_PIN" >/dev/null || fail "vendor changed during build"
(cd "$ROOT" && sha256sum -c "$GLSL_PIN") > "$OUT/26556_postbuild_glsl_invariance.txt"
python3 "$VALIDATE" --base "$BASE" --candidate "$AFTER" > "$OUT/26556_postbuild_contract.txt"
# Exactly one handoff APK at repository root.
mapfile -t ROOT_APKS < <(find "$ROOT" -maxdepth 1 -type f -name 'IrisCamera-*-debug.apk' -print)
[[ "${#ROOT_APKS[@]}" -eq 1 && "${ROOT_APKS[0]}" == "$FINAL" ]] || fail "root APK uniqueness"
sha256sum "$FINAL" > "$OUT/26556_V1_APK.sha256"
python3 - "$OUT/26556_V1_COMPILER_STATUS.txt" <<'PY'
from pathlib import Path
p=Path(__import__('sys').argv[1]);p.write_text(p.read_text().replace('POST-BUILD INVARIANCE: NOT RUN YET','POST-BUILD INVARIANCE: PASS'))
PY
set_report "POST-BUILD INVARIANCE" "PASS"
pass "post-build invariance"

echo "=== 26556 GATE 6: clean candidate source export proof ==="
EXPORT="$WORK/export_source"; rm -rf "$EXPORT"; mkdir -p "$EXPORT/app"
cp -a "$AFTER/app/src" "$EXPORT/app/src"; cp "$AFTER/app/version.properties" "$EXPORT/app/version.properties"; cp "$AFTER/app/build.gradle" "$EXPORT/app/build.gradle"
manifest_audited "$EXPORT" "$OUT/26556_V1_candidate_source.sha256"
cmp "$OUT/26556_V1_candidate_source.sha256" "$CAND_PIN" >/dev/null || fail "export manifest mismatch"
tar -C "$EXPORT" -czf "$OUT/26556_V1_candidate_app_source.tar.gz" app
sha256sum "$OUT/26556_V1_candidate_app_source.tar.gz" > "$OUT/26556_V1_candidate_app_source.tar.gz.sha256"
set_report "CLEAN ARTIFACT SOURCE EXPORT" "PASS"
# Final report must not contain an unpassed applicable compiler/build gate.
! grep -E 'REAL (KOTLIN|JAVA) COMPILE: NOT RUN|NATIVE/NDK COMPILE: NOT RUN|FULL ANDROID ASSEMBLE: NOT RUN' "$OUT/26556_V1_STRICT_HANDOFF_REPORT.txt"
pass "26556 V1 BUILD-PROVEN handoff output"
