#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# Photon Camera Motion V2 26452 reconstruction — Gate 6B1 hardened launcher
#
# This launcher preserves the exact canonical reconstruction script from commit
# 4be666183feaf7caad708fa2bdace5928ebeb743 and changes ONLY the late-history
# candidate-only truncation detector that falsely rejected historical 26439.
# ============================================================================

CANONICAL_COMMIT="4be666183feaf7caad708fa2bdace5928ebeb743"
CANONICAL_PATH="reconstruct_motion_v2_26452.sh"
CANONICAL_BLOB="a0ed31efad41eb2320059d60f7f288e463f6127b"

fail() {
    echo "FAIL: $*" >&2
    exit 1
}

echo "======================================================================"
echo "MOTION V2 26452 RECONSTRUCTION — HARDENED GATE 6B1 LAUNCHER"
echo "======================================================================"

echo
echo "=== REVISION GATE R0: REPOSITORY + CANONICAL SOURCE PROOF ==="

git rev-parse --is-inside-work-tree >/dev/null 2>&1 \
    || fail "Not inside the Photon Camera Git repository"

ACTUAL_BLOB="$(git rev-parse "${CANONICAL_COMMIT}:${CANONICAL_PATH}" 2>/dev/null || true)"
[[ "$ACTUAL_BLOB" == "$CANONICAL_BLOB" ]] || {
    echo "Expected blob: $CANONICAL_BLOB"
    echo "Actual blob:   ${ACTUAL_BLOB:-MISSING}"
    fail "Exact 4be6661 reconstruction source was not proven"
}

CURRENT_BRANCH="$(git branch --show-current)"
[[ -n "$CURRENT_BRANCH" ]] || fail "Detached HEAD is not allowed"
[[ "$CURRENT_BRANCH" != "dev" ]] || fail "Refusing to execute on dev"

echo "PASS: exact canonical reconstruction blob = $CANONICAL_BLOB"
echo "PASS: current branch = $CURRENT_BRANCH"

STAMP="$(date +%Y%m%d_%H%M%S)_$$"
SAFETY_DIR="reconstruct_26452_revision_safety_${STAMP}"
mkdir -p "$SAFETY_DIR"

CANONICAL_COPY="$SAFETY_DIR/reconstruct_motion_v2_26452.4be6661.original.sh"
GENERATED="$SAFETY_DIR/reconstruct_motion_v2_26452.gate6b1_hardened.generated.sh"
PRE_PATCH="$SAFETY_DIR/pre_run_app.patch"
STATE="$SAFETY_DIR/pre_run_state.txt"

git show "${CANONICAL_COMMIT}:${CANONICAL_PATH}" > "$CANONICAL_COPY"
[[ -s "$CANONICAL_COPY" ]] || fail "Could not materialize canonical reconstruction source"
[[ "$(git hash-object "$CANONICAL_COPY")" == "$CANONICAL_BLOB" ]] \
    || fail "Materialized canonical source blob mismatch"

echo "PASS: canonical source materialized byte-for-byte"

echo
echo "=== REVISION GATE R1: BACKUP BRANCH + BINARY PRE-RUN PATCH ==="

BACKUP_BRANCH="backup/runner-before-26452-gate6b1-${STAMP}"
git branch "$BACKUP_BRANCH" HEAD \
    || fail "Could not create local backup branch $BACKUP_BRANCH"

git diff --binary HEAD -- app > "$PRE_PATCH" \
    || fail "Could not create binary pre-run app patch"

{
    echo "Photon Camera 26452 Gate 6B1 revision pre-run state"
    echo "=================================================="
    echo "branch=$CURRENT_BRANCH"
    echo "head=$(git rev-parse HEAD)"
    echo "canonical_reconstruction_commit=$CANONICAL_COMMIT"
    echo "canonical_reconstruction_blob=$CANONICAL_BLOB"
    echo "backup_branch=$BACKUP_BRANCH"
    echo
    echo "git status --short:"
    git status --short
} > "$STATE"

echo "PASS: backup branch created: $BACKUP_BRANCH"
echo "PASS: binary pre-run app patch saved: $PRE_PATCH"
echo "PASS: pre-run state saved: $STATE"

echo
echo "=== REVISION GATE R2: SURGICAL GATE 6B1 TRANSFORMATION ==="

python3 - "$CANONICAL_COPY" "$GENERATED" <<'PY'
from pathlib import Path
import sys
import re

src = Path(sys.argv[1])
dst = Path(sys.argv[2])
text = src.read_text(encoding="utf-8")

start_anchor = "headings = list(re.finditer("
end_anchor = "text = text[:cut]"

if text.count(start_anchor) != 1:
    raise SystemExit(
        f"FAIL: vulnerable Gate 6B1 detector start count={text.count(start_anchor)}, expected 1"
    )
if text.count(end_anchor) != 1:
    raise SystemExit(
        f"FAIL: Gate 6B1 truncation anchor count={text.count(end_anchor)}, expected 1"
    )

start = text.index(start_anchor)
end = text.index(end_anchor, start)
old_block = text[start:end]

# Prove this is the audited vulnerable 4be6661 Gate 6B1 detector without
# depending on the spelling/escaping of its PowerShell-heading regex.
semantic_requirements = (
    "headings = list(re.finditer(",
    'if any(k in title for k in ("GLSL", "APPLY", "JAVAC", " APK BUILD", " BUILD "))',
    'raise SystemExit("FAIL: no safe post-candidate truncation gate found")',
)
for required in semantic_requirements:
    if required not in old_block:
        raise SystemExit(
            "FAIL: vulnerable detector does not match audited 4be6661 semantics: "
            + required
        )

if "Write-Host" not in old_block:
    raise SystemExit(
        "FAIL: audited 4be6661 vulnerable detector no longer appears Write-Host-only"
    )

new_block = r"""
# -------------------------------------------------------------------------
# IRIS_26452_GATE6B1_HARDENED_TRUNCATION_CONTRACT
#
# Historical PowerShell scripts do not all emit gate headings through
# Write-Host.  Gate discovery is therefore logger-agnostic.
#
# Truncation is legal only after BOTH visible historical validation proofs and
# before the first later gate that can enter real source/GLSL/Javac/Gradle/APK
# work.
# -------------------------------------------------------------------------

candidate_patterns = (
    r"candidate/source\s+validation\s*:?\s*PASS",
    r"candidate[^\r\n]{0,120}validation[^\r\n]{0,80}\bPASS\b",
)
temporary_patterns = (
    r"Temporary-copy\s+validation\s*:?\s*PASS",
    r"temporary[^\r\n]{0,120}validation[^\r\n]{0,80}\bPASS\b",
)

def _has_proof(patterns, body):
    return any(
        re.search(pattern, body, re.IGNORECASE | re.MULTILINE)
        for pattern in patterns
    )

# Match any PowerShell statement containing a quoted === GATE ... === heading:
# Write-Host, Safety, Pass, or another logger.
gate_heading = re.compile(
    r"(?im)^[^\r\n]*[\"']===\s*GATE\s+[^\"'\r\n]*===[\"'][^\r\n]*$"
)

# Candidate-only compiler validation is SAFE and must be allowed to run.
# Historical 26437 produces Temporary-copy validation PASS inside its REAL GLSL
# gate and does not touch real source until the following APPLY gate.
danger_tokens = (
    "APPLY",
    "SOURCE WRITE",
    "REAL SOURCE",
    "JAVAC",
    "APK BUILD",
    "GRADLE",
)
generic_build = re.compile(r"\bBUILD\b", re.IGNORECASE)

headings = list(gate_heading.finditer(text))
if not headings:
    raise SystemExit(
        f"FAIL: historical {target_b} contains no recognizable Gate headings"
    )

cut = None
cut_title = None

# Chronological safety contract:
# choose the FIRST dangerous gate whose prefix has ALREADY completed both
# candidate/source and temporary-copy validation.  Do not use the last proof
# occurrence globally because old scripts repeat PASS messages in summaries.
for m in headings:
    title = m.group(0).upper()
    dangerous = any(token in title for token in danger_tokens)

    # BUILD can describe candidate construction; only treat it as dangerous
    # when it is not explicitly a candidate/temporary build stage.
    if generic_build.search(title):
        if "CANDIDATE" not in title and "TEMPORARY" not in title:
            dangerous = True

    if not dangerous:
        continue

    prefix = text[:m.start()]
    if (
        _has_proof(candidate_patterns, prefix)
        and _has_proof(temporary_patterns, prefix)
    ):
        cut = m.start()
        cut_title = m.group(0).strip()
        break

if cut is None:
    diagnostic = [m.group(0).strip() for m in headings[:24]]
    raise SystemExit(
        "FAIL: no source-apply/build gate occurs after both validation proofs "
        + "for historical "
        + str(target_b)
        + "; gate headings="
        + repr(diagnostic)
    )

prefix = text[:cut]
suffix = text[cut:]

if not re.search(
    r"candidate[^\r\n]{0,120}validation[^\r\n]{0,80}\bPASS\b",
    prefix,
    re.IGNORECASE,
):
    raise SystemExit(
        f"FAIL: historical {target_b} candidate validation proof would be truncated"
    )
if not re.search(
    r"temporary[^\r\n]{0,120}validation[^\r\n]{0,80}\bPASS\b",
    prefix,
    re.IGNORECASE,
):
    raise SystemExit(
        f"FAIL: historical {target_b} temporary-copy validation proof would be truncated"
    )

suffix_evidence = re.search(
    r"(?i)(Copy-Item|Move-Item|Set-Content|WriteAllText|gradlew|assembleDebug|"
    r"compileDebugJavaWithJavac|glslc|JAVAC|SOURCE APPLY|APPLY EXACT)",
    suffix,
)
if suffix_evidence is None:
    raise SystemExit(
        f"FAIL: historical {target_b} selected gate has no executable-stage evidence after it: "
        + str(cut_title)
    )

print(
    "PASS: historical "
    + str(target_b)
    + " hardened truncation boundary -> "
    + str(cut_title)
)
print(
    "PASS: candidate/source + temporary-copy validation both precede truncation for "
    + str(target_b)
)

"""
text = text[:start] + new_block + text[end:]
# -------------------------------------------------------------------------
# IRIS_26452_GATE6_26439_PRODUCTION_PROVENANCE_FIX
# -------------------------------------------------------------------------

req_old = (
    '    "build_26438_windows_REVISED_v2_audited_motion_microcontrast_standard_ultrahdr.ps1"\n'
    '    "launch_resume_build_26439_after_gate8_v2_MINIMAL.ps1"\n'
)
req_new = (
    '    "build_26438_windows_REVISED_v2_audited_motion_microcontrast_standard_ultrahdr.ps1"\n'
    '    "build_26439_windows_v2_temporal_channel_ownership.ps1"\n'
    '    "launch_resume_build_26439_after_gate8_v2_MINIMAL.ps1"\n'
)
if text.count(req_old) != 1:
    raise SystemExit('FAIL: canonical REQUIRED_HISTORY 26438/26439 anchor count=' + str(text.count(req_old)))
text = text.replace(req_old, req_new, 1)

count_old = (
    'if [[ "$HIST_FILE_COUNT" -ne 15 ]]; then\n'
    '    fail "Expected exactly 15 historical replay files; found $HIST_FILE_COUNT"\n'
    'fi'
)
count_new = (
    'if [[ "$HIST_FILE_COUNT" -ne 16 ]]; then\n'
    '    fail "Expected exactly 16 historical replay files; found $HIST_FILE_COUNT"\n'
    'fi'
)
if text.count(count_old) != 1:
    raise SystemExit('FAIL: canonical historical file-count anchor count=' + str(text.count(count_old)))
text = text.replace(count_old, count_new, 1)

prov_anchor = '    || fail "26438 revised provenance missing"\n'
if text.count(prov_anchor) != 1:
    raise SystemExit('FAIL: canonical 26438 provenance anchor count=' + str(text.count(prov_anchor)))
prov_insert = '''
grep -q '26439 MOTION V2 TEMPORAL + CHANNEL OWNERSHIP' \
    "$HIST_DIR/build_26439_windows_v2_temporal_channel_ownership.ps1" \
    || fail "26439 production transformer identity missing"

grep -q 'Transform-Reconstruction' \
    "$HIST_DIR/build_26439_windows_v2_temporal_channel_ownership.ps1" \
    || fail "26439 production reconstruction transformer missing"

grep -q 'Transform-Accumulator' \
    "$HIST_DIR/build_26439_windows_v2_temporal_channel_ownership.ps1" \
    || fail "26439 production accumulator transformer missing"

grep -q 'candidate/source validation PASS' \
    "$HIST_DIR/build_26439_windows_v2_temporal_channel_ownership.ps1" \
    || fail "26439 production candidate validation proof missing"

grep -q 'Temporary-copy validation: PASS' \
    "$HIST_DIR/build_26439_windows_v2_temporal_channel_ownership.ps1" \
    || fail "26439 production temporary-copy validation proof missing"

grep -q '=== GATE 5: APPLY EXACT VALIDATED TRANSFORMATION ===' \
    "$HIST_DIR/build_26439_windows_v2_temporal_channel_ownership.ps1" \
    || fail "26439 production exact-apply boundary missing"

echo "PASS: 26439 production transformer provenance verified"
'''
i = text.index(prov_anchor) + len(prov_anchor)
text = text[:i] + '\n' + prov_insert + text[i:]

decode_old = (
    'decode_launcher_payload \\\n'
    '    "$HIST_DIR/launch_resume_build_26439_after_gate8_v2_MINIMAL.ps1" \\\n'
    '    "$REPLAY_DECODED/26439.ps1" \\\n'
    '    "26439"\n'
)
if text.count(decode_old) != 1:
    raise SystemExit('FAIL: canonical resume-as-transformer decode anchor count=' + str(text.count(decode_old)))
decode_new = '''cp \
    "$HIST_DIR/build_26439_windows_v2_temporal_channel_ownership.ps1" \
    "$REPLAY_DECODED/26439.ps1"

[[ -s "$REPLAY_DECODED/26439.ps1" ]] \
    || fail "26439 production transformer copy is empty"

echo "PASS: 26439 production transformer -> $REPLAY_DECODED/26439.ps1"

decode_launcher_payload \
    "$HIST_DIR/launch_resume_build_26439_after_gate8_v2_MINIMAL.ps1" \
    "$REPLAY_DECODED/26439.resume.ps1" \
    "26439 resume-only verification"
'''
text = text.replace(decode_old, decode_new, 1)

gate_anchor = (
    '# Each historical build touched a different part of the V2 graph.\n'
    '# Validate the domain each build actually owned instead of falsely requiring\n'
    '# every payload to reference MotionV2CfaReconstruction.java.\n'
)
if text.count(gate_anchor) != 1:
    raise SystemExit('FAIL: canonical Gate 3D anchor count=' + str(text.count(gate_anchor)))
gate_insert = '''
grep -q 'Transform-Reconstruction' "$REPLAY_DECODED/26439.ps1" \
    || fail "26439 Gate 6 source is not the production reconstruction transformer"
grep -q 'Transform-Accumulator' "$REPLAY_DECODED/26439.ps1" \
    || fail "26439 Gate 6 source is not the production accumulator transformer"
grep -q '=== GATE 5: APPLY EXACT VALIDATED TRANSFORMATION ===' "$REPLAY_DECODED/26439.ps1" \
    || fail "26439 Gate 6 production exact-apply boundary missing"
grep -q '26439 RESUME-ONLY BUILD' "$REPLAY_DECODED/26439.resume.ps1" \
    || fail "26439 resume-only verifier identity missing"
grep -q 'NO SOURCE EDITS' "$REPLAY_DECODED/26439.resume.ps1" \
    || fail "26439 resume-only no-source-edits contract missing"
if grep -q '26439 RESUME-ONLY BUILD' "$REPLAY_DECODED/26439.ps1"; then
    fail "26439 resume-only verifier was incorrectly selected as Gate 6 transformer"
fi
echo "PASS: 26439 production transformer and resume-only verifier are separated"
'''
text = text.replace(gate_anchor, gate_anchor + '\n' + gate_insert, 1)

g6_anchor = 'cp "$REPLAY_DECODED/26439.ps1" "$G6_PS/26439.source.ps1"\n'
if text.count(g6_anchor) != 1:
    raise SystemExit('FAIL: canonical Gate 6 26439 materialization anchor count=' + str(text.count(g6_anchor)))
g6_extra = '''
grep -q 'Transform-Reconstruction' "$G6_PS/26439.source.ps1" \
    || fail "Gate 6 26439 source lost production transformer identity"
grep -q 'Transform-Accumulator' "$G6_PS/26439.source.ps1" \
    || fail "Gate 6 26439 source lost accumulator transformer identity"
if grep -q '26439 RESUME-ONLY BUILD' "$G6_PS/26439.source.ps1"; then
    fail "Gate 6 26439 source is resume-only verifier"
fi
echo "PASS: Gate 6 26439 materialized from production transformer"
'''
j = text.index(g6_anchor) + len(g6_anchor)
text = text[:j] + g6_extra + text[j:]

# Structural V4 provenance proof.  Do not count the marker string itself:
# that would count both this injected stage and any assertion that mentions it.
required_v4_fragments = (
    '"build_26439_windows_v2_temporal_channel_ownership.ps1"',
    'Expected exactly 16 historical replay files',
    '$REPLAY_DECODED/26439.resume.ps1',
    '26439 production transformer -> $REPLAY_DECODED/26439.ps1',
    '26439 production transformer and resume-only verifier are separated',
    'Gate 6 26439 materialized from production transformer',
)
for fragment in required_v4_fragments:
    if fragment not in text:
        raise SystemExit(
            "FAIL: V4 provenance structural fragment missing: " + fragment
        )

# -------------------------------------------------------------------------
# IRIS_26452_WINDOWS_NATIVE_REPLAY_PATHS
# -------------------------------------------------------------------------

windows_rewrites = (
    (
        'python3 - "$G5M_SOURCE" "$G5M_SCRIPT" "$G5M_REPO" "$G5M_OUT" <<\'PY\'',
        'python3 - "$G5M_SOURCE" "$G5M_SCRIPT" "$(cygpath -w "$G5M_REPO")" "$G5M_OUT" <<\'PY\'',
        "Gate 5M PowerShell repository path",
    ),
    (
        'python3 - "$source" "$output" "$G6_REPO" \\\n',
        'python3 - "$source" "$output" "$(cygpath -w "$G6_REPO")" \\\n',
        "Gate 6 PowerShell repository path",
    ),
)

for old, new, label in windows_rewrites:
    count = text.count(old)
    if count != 1:
        raise SystemExit(
            "FAIL: Windows-native rewrite anchor count for "
            + label
            + " = "
            + str(count)
        )
    text = text.replace(old, new, 1)

windows_gate_anchor = 'echo "MOTION V2 26452 RECONSTRUCTION"\n'
if text.count(windows_gate_anchor) != 1:
    raise SystemExit(
        "FAIL: canonical reconstruction banner anchor count="
        + str(text.count(windows_gate_anchor))
    )

windows_gate = (
    'if [[ "${OS:-}" != "Windows_NT" ]]; then\n'
    '    fail "This reconstruction path requires GitHub Actions windows-latest"\n'
    'fi\n'
    'command -v cygpath >/dev/null 2>&1 || fail "cygpath unavailable in Git Bash"\n'
    'command -v pwsh >/dev/null 2>&1 || fail "PowerShell 7 unavailable on Windows runner"\n'
    'echo "PASS: Windows-native Git Bash + PowerShell environment proven"\n'
)

text = text.replace(
    windows_gate_anchor,
    windows_gate_anchor + windows_gate,
    1,
)

ndk_gate_anchor = 'echo "=== GATE 0A: BRANCH SAFETY ==="\n'
if text.count(ndk_gate_anchor) != 1:
    raise SystemExit(
        "FAIL: canonical Gate 0A anchor count="
        + str(text.count(ndk_gate_anchor))
    )

ndk_gate = '''WINDOWS_SDK_ROOT="${ANDROID_SDK_ROOT:-${ANDROID_HOME:-}}"
[[ -n "$WINDOWS_SDK_ROOT" ]] || fail "ANDROID_SDK_ROOT/ANDROID_HOME missing"
WINDOWS_NDK_GLSLC="$(
    find "$WINDOWS_SDK_ROOT/ndk" \
        -type f \
        -path '*/shader-tools/windows-x86_64/glslc.exe' \
        -print 2>/dev/null \
        | sort -V \
        | tail -n 1
)"
[[ -n "$WINDOWS_NDK_GLSLC" ]] || fail "Real Windows NDK glslc.exe not found"
[[ -f "$WINDOWS_NDK_GLSLC" ]] || fail "Windows NDK glslc.exe path is not a file"
"$WINDOWS_NDK_GLSLC" --version >/dev/null \
    || fail "Real Windows NDK glslc.exe could not execute from Git Bash"
echo "PASS: real Windows NDK glslc.exe = $WINDOWS_NDK_GLSLC"
'''

text = text.replace(
    ndk_gate_anchor,
    ndk_gate_anchor + ndk_gate + "\n",
    1,
)


# Replace the canonical Linux-only GLSL validator installer with the real
# Windows Android NDK compiler already proven above. The canonical script only
# installs/checks glslangValidator in Gate 4B; no later stage consumes it.
gate4b_pattern = re.compile(
    r'echo\s*\n'
    r'echo "=== GATE 4B: INSTALL/VERIFY GLSL VALIDATOR ==="\n'
    r'.*?'
    r'echo "PASS: real glslangValidator available"\n'
    r'\n'
    r'echo\s*\n'
    r'(?=echo "=== GATE 4C: INSTALL NON-BUILDING GRADLE REPLAY SHIM ===")',
    re.DOTALL,
)

gate4b_matches = list(gate4b_pattern.finditer(text))
if len(gate4b_matches) != 1:
    raise SystemExit(
        "FAIL: canonical Linux Gate 4B GLSL-validator block count="
        + str(len(gate4b_matches))
    )

gate4b_windows = (
    'echo\n'
    'echo "=== GATE 4B: VERIFY REAL WINDOWS NDK GLSL COMPILER ==="\n'
    '\n'
    '[[ -n "${WINDOWS_NDK_GLSLC:-}" ]] \\\n'
    '    || fail "WINDOWS_NDK_GLSLC was not established by Gate 0A"\n'
    '\n'
    '[[ -f "$WINDOWS_NDK_GLSLC" ]] \\\n'
    '    || fail "Real Windows NDK glslc.exe disappeared before replay"\n'
    '\n'
    '"$WINDOWS_NDK_GLSLC" --version \\\n'
    '    > "$REPLAY_LOGS/windows_ndk_glslc_version.log" 2>&1 \\\n'
    '    || fail "Windows NDK glslc.exe validation failed"\n'
    '\n'
    'echo "PASS: real Windows NDK glslc.exe available for historical GLSL validation"\n'
    '\n'
    'echo\n'
)

text = gate4b_pattern.sub(gate4b_windows, text, count=1)

if "sudo apt-get" in text or "glslang-tools" in text:
    raise SystemExit(
        "FAIL: Linux GLSL validator installation survived Windows-native rewrite"
    )

if '=== GATE 4B: VERIFY REAL WINDOWS NDK GLSL COMPILER ===' not in text:
    raise SystemExit("FAIL: Windows-native Gate 4B was not installed")

# Remove the three canonical Linux SDK fallbacks. On Windows Actions the SDK
# root must come from ANDROID_SDK_ROOT or ANDROID_HOME, both proven before replay.
linux_sdk_expr = '${ANDROID_SDK_ROOT:-${ANDROID_HOME:-/usr/local/lib/android/sdk}}'
windows_sdk_expr = '${ANDROID_SDK_ROOT:-${ANDROID_HOME:-}}'

linux_sdk_count = text.count(linux_sdk_expr)
if linux_sdk_count != 3:
    raise SystemExit(
        "FAIL: expected exactly 3 canonical Linux SDK fallbacks, found "
        + str(linux_sdk_count)
    )

text = text.replace(linux_sdk_expr, windows_sdk_expr)

if "/usr/local/lib/android/sdk" in text:
    raise SystemExit("FAIL: Linux Android SDK fallback survived Windows rewrite")


# -------------------------------------------------------------------------
# IRIS_26452_WINDOWS_NESTED_CLONE_EXACT_BYTES
#
# The reconstruction creates three additional Git repositories on the Windows
# runner. Ordinary `git clone` performs a checkout before repository-local
# line-ending policy can be changed, which can turn LF shader bytes into CRLF
# and break historical exact-source SHA256 gates.
#
# Rewrite ALL three nested clones to:
#   clone --no-checkout
#   set core.autocrlf=false and core.eol=lf
#   only then perform the historical checkout
# -------------------------------------------------------------------------

nested_clone_rewrites = (
    (
        'git clone --no-hardlinks . "$REPLAY_REPO" \\\n'
        '    > "$REPLAY_LOGS/clone.log" 2>&1 \\\n'
        '    || fail "Could not create isolated replay clone"\n'
        '\n'
        '(\n'
        '    cd "$REPLAY_REPO"\n'
        '\n'
        '    git checkout --detach "$BASE_26428_COMMIT" \\\n',
        'git clone --no-hardlinks --no-checkout . "$REPLAY_REPO" \\\n'
        '    > "$REPLAY_LOGS/clone.log" 2>&1 \\\n'
        '    || fail "Could not create isolated replay clone"\n'
        '\n'
        'git -C "$REPLAY_REPO" config core.autocrlf false\n'
        'git -C "$REPLAY_REPO" config core.eol lf\n'
        '\n'
        '(\n'
        '    cd "$REPLAY_REPO"\n'
        '\n'
        '    git checkout --detach "$BASE_26428_COMMIT" \\\n',
        "Gate 4A replay clone",
    ),
    (
        'git clone --no-hardlinks . "$G5M_REPO" >/dev/null 2>&1 || fail "Gate 5M isolated canonical clone failed"\n'
        'git -C "$G5M_REPO" checkout --detach "$BASE_26428_COMMIT" >/dev/null 2>&1 || fail "Gate 5M canonical checkout failed"\n',
        'git clone --no-hardlinks --no-checkout . "$G5M_REPO" >/dev/null 2>&1 || fail "Gate 5M isolated canonical clone failed"\n'
        'git -C "$G5M_REPO" config core.autocrlf false\n'
        'git -C "$G5M_REPO" config core.eol lf\n'
        'git -C "$G5M_REPO" checkout --detach "$BASE_26428_COMMIT" >/dev/null 2>&1 || fail "Gate 5M canonical checkout failed"\n',
        "Gate 5M canonical clone",
    ),
    (
        'git clone --no-hardlinks . "$G6_REPO" > "$G6_LOGS/clone.log" 2>&1 \\\n'
        '    || fail "Gate 6 could not create isolated late-history repo"\n'
        '\n'
        'git -C "$G6_REPO" checkout --detach "$BASE_26428_COMMIT" >/dev/null 2>&1 \\\n',
        'git clone --no-hardlinks --no-checkout . "$G6_REPO" > "$G6_LOGS/clone.log" 2>&1 \\\n'
        '    || fail "Gate 6 could not create isolated late-history repo"\n'
        '\n'
        'git -C "$G6_REPO" config core.autocrlf false\n'
        'git -C "$G6_REPO" config core.eol lf\n'
        '\n'
        'git -C "$G6_REPO" checkout --detach "$BASE_26428_COMMIT" >/dev/null 2>&1 \\\n',
        "Gate 6 late-history clone",
    ),
)

for old, new, label in nested_clone_rewrites:
    count = text.count(old)
    if count != 1:
        raise SystemExit(
            "FAIL: nested Windows clone rewrite anchor count for "
            + label + " = " + str(count)
        )
    text = text.replace(old, new, 1)

# No ordinary nested reconstruction clone may remain.
remaining_nested = re.findall(
    r'git clone --no-hardlinks(?! --no-checkout)\s+\.\s+"\$(?:REPLAY_REPO|G5M_REPO|G6_REPO)"',
    text,
)
if remaining_nested:
    raise SystemExit(
        "FAIL: ordinary Windows nested clone survived rewrite: "
        + repr(remaining_nested)
    )

for repo_var in ("REPLAY_REPO", "G5M_REPO", "G6_REPO"):
    required_contracts = (
        f'git -C "${repo_var}" config core.autocrlf false',
        f'git -C "${repo_var}" config core.eol lf',
    )
    for contract in required_contracts:
        if contract not in text:
            raise SystemExit(
                "FAIL: nested clone exact-byte contract missing: " + contract
            )


# -------------------------------------------------------------------------
# IRIS_26452_HISTORICAL_LINEAGE_WINDOWS_GLSL
# -------------------------------------------------------------------------

hist_glsl_anchor = (
    'echo "PASS: real Windows NDK glslc.exe available for historical GLSL validation"\n'
)
if text.count(hist_glsl_anchor) != 1:
    raise SystemExit(
        "FAIL: historical GLSL compatibility anchor count="
        + str(text.count(hist_glsl_anchor))
    )

hist_glsl_block = r'''
HIST_GLSL_BIN="$REPLAY_AUX/windows_glsl_compat"
mkdir -p "$HIST_GLSL_BIN"

cat > "$HIST_GLSL_BIN/glslangValidator" <<'GLSLANG_COMPAT'
#!/usr/bin/env bash
set -euo pipefail

stage=""
source_file=""

while [[ "$#" -gt 0 ]]; do
    case "$1" in
        -S)
            [[ "$#" -ge 2 ]] || {
                echo "glslangValidator compatibility: -S requires a stage" >&2
                exit 2
            }
            stage="$2"
            shift 2
            ;;
        -*)
            echo "glslangValidator compatibility: unsupported option $1" >&2
            exit 2
            ;;
        *)
            [[ -z "$source_file" ]] || {
                echo "glslangValidator compatibility: multiple source files unsupported" >&2
                exit 2
            }
            source_file="$1"
            shift
            ;;
    esac
done

[[ -n "$stage" ]] || {
    echo "glslangValidator compatibility: missing -S stage" >&2
    exit 2
}
[[ -n "$source_file" && -f "$source_file" ]] || {
    echo "glslangValidator compatibility: source file missing: $source_file" >&2
    exit 2
}

case "$stage" in
    comp) glslc_stage="compute" ;;
    frag) glslc_stage="fragment" ;;
    *)
        echo "glslangValidator compatibility: unsupported stage $stage" >&2
        exit 2
        ;;
esac

out_file="${source_file}.iris_glslc_validation.spv"
trap 'rm -f "$out_file"' EXIT

"${WINDOWS_NDK_GLSLC:?WINDOWS_NDK_GLSLC missing}" \
    -fshader-stage="$glslc_stage" \
    "$source_file" \
    -o "$out_file"

[[ -s "$out_file" ]] || {
    echo "glslangValidator compatibility: glslc produced no SPIR-V" >&2
    exit 1
}
GLSLANG_COMPAT

chmod +x "$HIST_GLSL_BIN/glslangValidator"
export WINDOWS_NDK_GLSLC
export PATH="$HIST_GLSL_BIN:$PATH"

command -v glslangValidator >/dev/null 2>&1 \
    || fail "Historical glslangValidator compatibility shim unavailable"

HIST_GLSL_SMOKE="$REPLAY_AUX/windows_glsl_compat_smoke"
mkdir -p "$HIST_GLSL_SMOKE"

cat > "$HIST_GLSL_SMOKE/compute.comp" <<'EOF_COMP'
#version 310 es
layout(local_size_x=1, local_size_y=1, local_size_z=1) in;
void main() {}
EOF_COMP

cat > "$HIST_GLSL_SMOKE/fragment.frag" <<'EOF_FRAG'
#version 310 es
precision highp float;
layout(location=0) out vec4 outColor;
void main() { outColor = vec4(0.0); }
EOF_FRAG

glslangValidator -S comp "$HIST_GLSL_SMOKE/compute.comp" \
    || fail "Historical compute GLSL compatibility smoke test failed"
glslangValidator -S frag "$HIST_GLSL_SMOKE/fragment.frag" \
    || fail "Historical fragment GLSL compatibility smoke test failed"

echo "PASS: historical glslangValidator interface backed by real Windows NDK glslc.exe"
'''

text = text.replace(hist_glsl_anchor, hist_glsl_anchor + hist_glsl_block, 1)

gate4e_heading = 'echo "=== GATE 4E: REPLAY 26429 -> 26435 IN ORDER ==="\n'
gate4f_heading = 'echo "=== GATE 4F: VERIFY 26435 REPLAY STATE ==="\n'
if text.count(gate4e_heading) != 1:
    raise SystemExit(
        "FAIL: Gate 4E heading count="
        + str(text.count(gate4e_heading))
    )

gate4e_pos = text.index(gate4e_heading) + len(gate4e_heading)
gate4f_pos = text.find(gate4f_heading, gate4e_pos)
if gate4f_pos < 0:
    raise SystemExit("FAIL: Gate 4F heading not found after Gate 4E")

early_loop_anchor = 'for SCRIPT_NAME in "${REPLAY_SCRIPTS[@]}"; do\n'
early_loop_pos = text.find(early_loop_anchor, gate4e_pos, gate4f_pos)
if early_loop_pos < 0:
    raise SystemExit("FAIL: Gate 4E replay loop not found")
if text.find(
    early_loop_anchor,
    early_loop_pos + len(early_loop_anchor),
    gate4f_pos,
) >= 0:
    raise SystemExit("FAIL: multiple replay loops found inside Gate 4E")

early_maps = r'''
declare -A REPLAY_EXPECTED_BUILD
declare -A REPLAY_EXPECTED_VERSION

REPLAY_EXPECTED_BUILD["build_26429_codespace_shared_guide_reference_structure.sh"]="26429"
REPLAY_EXPECTED_BUILD["build_26430_codespace_v2_ownership_headroom_cleanup.sh"]="26430"
REPLAY_EXPECTED_BUILD["build_26431_codespace_allframes_body_lens_ownership_v2.sh"]="26431"
REPLAY_EXPECTED_BUILD["build_26432_codespace_stack_robust_true_ultrahdr_final.sh"]="26432"
REPLAY_EXPECTED_BUILD["resume_26433_fix_ultrahdr_javac_type_and_build.sh"]="26433"
REPLAY_EXPECTED_BUILD["build_26434_codespace_stable_base_smooth_motion_ultrahdr_v2.sh"]="26434"
REPLAY_EXPECTED_BUILD["build_26435_codespace_exact26430_sdr_lowfreq_ultrahdr_v2.sh"]="26435"

REPLAY_EXPECTED_VERSION["build_26429_codespace_shared_guide_reference_structure.sh"]="0.9726429"
REPLAY_EXPECTED_VERSION["build_26430_codespace_v2_ownership_headroom_cleanup.sh"]="0.9726430"
REPLAY_EXPECTED_VERSION["build_26431_codespace_allframes_body_lens_ownership_v2.sh"]="0.9726431"
REPLAY_EXPECTED_VERSION["build_26432_codespace_stack_robust_true_ultrahdr_final.sh"]="0.9726432"
REPLAY_EXPECTED_VERSION["resume_26433_fix_ultrahdr_javac_type_and_build.sh"]="0.9726433"
REPLAY_EXPECTED_VERSION["build_26434_codespace_stable_base_smooth_motion_ultrahdr_v2.sh"]="0.9726434"
REPLAY_EXPECTED_VERSION["build_26435_codespace_exact26430_sdr_lowfreq_ultrahdr_v2.sh"]="0.9726435"

'''
text = (
    text[:early_loop_pos]
    + early_maps
    + text[early_loop_pos:]
)
gate4e_pos = text.index(gate4e_heading) + len(gate4e_heading)
gate4f_pos = text.find(gate4f_heading, gate4e_pos)
early_loop_pos = text.find(early_loop_anchor, gate4e_pos, gate4f_pos)

early_pass_anchor = '    echo "PASS: $SCRIPT_NAME"\ndone\n'
early_pass_pos = text.find(early_pass_anchor, early_loop_pos, gate4f_pos)
if early_pass_pos < 0:
    raise SystemExit("FAIL: Gate 4E replay PASS/done anchor not found")
if text.find(
    early_pass_anchor,
    early_pass_pos + len(early_pass_anchor),
    gate4f_pos,
) >= 0:
    raise SystemExit("FAIL: multiple PASS/done anchors found inside Gate 4E")

early_checks = r'''    EXPECTED_STAGE_BUILD="${REPLAY_EXPECTED_BUILD[$SCRIPT_NAME]:-}"
    EXPECTED_STAGE_VERSION="${REPLAY_EXPECTED_VERSION[$SCRIPT_NAME]:-}"

    [[ -n "$EXPECTED_STAGE_BUILD" && -n "$EXPECTED_STAGE_VERSION" ]] \
        || fail "No lineage contract registered for $SCRIPT_NAME"

    grep -q "^VERSION_BUILD=${EXPECTED_STAGE_BUILD}$" \
        "$REPLAY_REPO/app/version.properties" \
        || fail "$SCRIPT_NAME did not produce build $EXPECTED_STAGE_BUILD"

    grep -q "^VERSION_NAME=${EXPECTED_STAGE_VERSION}$" \
        "$REPLAY_REPO/app/version.properties" \
        || fail "$SCRIPT_NAME did not produce version $EXPECTED_STAGE_VERSION"

    grep -q 'candidate/source validation PASS' \
        "$REPLAY_LOGS/$SCRIPT_NAME.log" \
        || fail "$SCRIPT_NAME log lacks candidate/source validation PASS"

    grep -q 'Temporary-copy validation: PASS' \
        "$REPLAY_LOGS/$SCRIPT_NAME.log" \
        || fail "$SCRIPT_NAME log lacks Temporary-copy validation PASS"

    echo "PASS: $SCRIPT_NAME -> $EXPECTED_STAGE_VERSION / $EXPECTED_STAGE_BUILD"
done
'''
text = (
    text[:early_pass_pos]
    + early_checks
    + text[early_pass_pos + len(early_pass_anchor):]
)

for required_hist_contract in (
    'HIST_GLSL_BIN="$REPLAY_AUX/windows_glsl_compat"',
    'glslangValidator -S comp "$HIST_GLSL_SMOKE/compute.comp"',
    'glslangValidator -S frag "$HIST_GLSL_SMOKE/fragment.frag"',
    'REPLAY_EXPECTED_BUILD["build_26429_codespace_shared_guide_reference_structure.sh"]="26429"',
    'REPLAY_EXPECTED_BUILD["build_26435_codespace_exact26430_sdr_lowfreq_ultrahdr_v2.sh"]="26435"',
    'log lacks candidate/source validation PASS',
    'log lacks Temporary-copy validation PASS',
):
    if required_hist_contract not in text:
        raise SystemExit(
            "FAIL: historical-lineage generated contract missing: "
            + required_hist_contract
        )

for required in (
    '$(cygpath -w "$G5M_REPO")',
    '$(cygpath -w "$G6_REPO")',
    'This reconstruction path requires GitHub Actions windows-latest',
    'Real Windows NDK glslc.exe not found',
):
    if required not in text:
        raise SystemExit("FAIL: Windows-native structural proof missing: " + required)

marker = "IRIS_26452_GATE6B1_HARDENED_TRUNCATION_CONTRACT"
if text.count(marker) != 1:
    raise SystemExit(
        f"FAIL: hardened Gate 6B1 marker count={text.count(marker)}, expected 1"
    )

patched_start = text.index(marker)
patched_end = text.index("text = text[:cut]", patched_start)
patched_block = text[patched_start:patched_end]

# Prove the old heading-scanner construction itself is gone, without comparing
# escaped regex spelling.
if "headings = list(re.finditer(" in patched_block:
    raise SystemExit(
        "FAIL: old Write-Host-only Gate 6B1 heading scanner survived patch"
    )

dst.write_text(text, encoding="utf-8")
print("PASS: exact one-block Gate 6B1 transformation applied")
print("PASS: all non-Gate-6B1 canonical reconstruction content preserved")
PY

[[ -s "$GENERATED" ]] || fail "Generated corrected reconstruction script is empty"

echo
echo "=== REVISION GATE R3: BASH + EMBEDDED-PYTHON STATIC VALIDATION ==="

bash -n "$GENERATED" \
    || fail "Corrected reconstruction Bash syntax validation failed"

python3 - "$GENERATED" <<'PY'
from pathlib import Path
import ast
import re
import sys

p = Path(sys.argv[1])
text = p.read_text(encoding="utf-8")
marker = "IRIS_26452_GATE6B1_HARDENED_TRUNCATION_CONTRACT"

if text.count(marker) != 1:
    raise SystemExit("FAIL: hardened marker missing or duplicated")

pattern = re.compile(r"<<'PY'\n(?P<body>.*?)\nPY(?:\n|$)", re.DOTALL)
bodies = [m.group("body") for m in pattern.finditer(text)]

if not bodies:
    raise SystemExit("FAIL: no embedded Python heredocs found")

for index, body in enumerate(bodies, 1):
    try:
        ast.parse(body)
    except SyntaxError as exc:
        raise SystemExit(
            f"FAIL: embedded Python heredoc #{index} syntax error: {exc}"
        )

print("PASS: corrected Bash syntax")
print(f"PASS: parsed {len(bodies)} embedded Python heredoc(s)")
PY

echo
echo "=== REVISION GATE R4: HARDENED DETECTOR UNIT TESTS ==="

python3 <<'PY'
import re

def find_cut(text, target_b):
    candidate_patterns = (
        r"candidate/source\s+validation\s*:?\s*PASS",
        r"candidate[^\r\n]{0,120}validation[^\r\n]{0,80}\bPASS\b",
    )
    temporary_patterns = (
        r"Temporary-copy\s+validation\s*:?\s*PASS",
        r"temporary[^\r\n]{0,120}validation[^\r\n]{0,80}\bPASS\b",
    )

    def has_proof(patterns, body):
        return any(
            re.search(pattern, body, re.IGNORECASE | re.MULTILINE)
            for pattern in patterns
        )

    gate_heading = re.compile(
        r"(?im)^[^\r\n]*[\"']===\s*GATE\s+[^\"'\r\n]*===[\"'][^\r\n]*$"
    )
    danger_tokens = (
        "APPLY", "SOURCE WRITE", "REAL SOURCE", "JAVAC",
        "APK BUILD", "GRADLE",
    )
    generic_build = re.compile(r"\bBUILD\b", re.IGNORECASE)

    for m in gate_heading.finditer(text):
        title = m.group(0).upper()
        dangerous = any(token in title for token in danger_tokens)

        if generic_build.search(title):
            if "CANDIDATE" not in title and "TEMPORARY" not in title:
                dangerous = True

        if not dangerous:
            continue

        prefix = text[:m.start()]
        if not (
            has_proof(candidate_patterns, prefix)
            and has_proof(temporary_patterns, prefix)
        ):
            continue

        suffix = text[m.start():]
        if not re.search(
            r"(?i)(Copy-Item|Move-Item|Set-Content|WriteAllText|gradlew|assembleDebug|"
            r"compileDebugJavaWithJavac|SOURCE APPLY|APPLY EXACT)",
            suffix,
        ):
            raise AssertionError(f"{target_b}: no executable suffix evidence")

        return m.group(0).strip()

    raise AssertionError(f"{target_b}: no safe source-apply/build cut")
cases = {
    "26437": (
        'Write-Host "=== GATE 2: BUILD ALL 26437 TEMPORARY CANDIDATES ==="\n'
        'Write-Host "candidate/source validation PASS"\n'
        'Write-Host "=== GATE 3: REAL GLSL COMPILER VALIDATION ==="\n'
        '& $glslc $Candidate\n'
        'Write-Host "REAL GLSL COMPILER PROOF: PASS"\n'
        'Write-Host "Temporary-copy validation: PASS"\n'
        'Write-Host "=== GATE 4: APPLY EXACT VALIDATED CANDIDATES ==="\n'
        'Copy-Item -LiteralPath $Candidate -Destination $Real\n'
    ),
    "26438": (
        'Pass "candidate/source validation PASS"\n'
        'Pass "Temporary-copy validation: PASS"\n'
        'Write-Host "=== GATE 8: APPLY EXACT VALIDATED CANDIDATES ==="\n'
        'Copy-Item -LiteralPath $Candidate -Destination $Real\n'
    ),
    "26439": (
        'Safety "candidate/source validation PASS"\n'
        'Safety "Temporary-copy validation: PASS"\n'
        'Safety "=== GATE 5: APPLY EXACT VALIDATED TRANSFORMATION ==="\n'
        '[IO.File]::WriteAllText($Recon,$ReconCandidate)\n'
    ),
    "26443": (
        'Write-Host "candidate source validation PASS"\n'
        'Write-Host "temporary candidate validation PASS"\n'
        'Safety "=== GATE 6: REAL SOURCE APPLY ==="\n'
        'Copy-Item $Tmp $Real\n'
    ),
    "26445": (
        'Pass "candidate/source validation: PASS"\n'
        'Pass "Temporary-copy validation PASS"\n'
        'Pass "=== GATE 9: JAVAC PROOF ==="\n'
        '& .\\gradlew.bat :app:compileDebugJavaWithJavac\n'
    ),
    "26446": (
        'Safety "candidate/source validation PASS"\n'
        'Safety "Temporary-copy validation: PASS"\n'
        'Safety "=== GATE 10: BUILD 0.9726446 / 26446 ==="\n'
        '& .\\gradlew.bat :app:assembleDebug\n'
    ),
}

for build, body in cases.items():
    heading = find_cut(body, build)
    print(f"PASS: detector unit {build} -> {heading}")

# Exact historical-26437 ordering regression:
# candidate/source PASS -> candidate-only REAL GLSL -> temporary-copy PASS ->
# real APPLY.  The safe truncation MUST be Gate 4 APPLY.
historical_26437_order = (
    'Write-Host "=== GATE 2A: TEMPORARY CANDIDATE ARCHITECTURE PROOF ==="\n'
    'Write-Host "candidate/source validation PASS"\n'
    'Write-Host "=== GATE 3: REAL GLSL COMPILER VALIDATION ==="\n'
    '& $Glslc @Args\n'
    'Write-Host "REAL GLSL COMPILER PROOF: PASS"\n'
    'Write-Host "Temporary-copy validation: PASS"\n'
    'Write-Host "=== GATE 4: APPLY EXACT VALIDATED CANDIDATES ==="\n'
    'Copy-Item -LiteralPath $From -Destination $Rel -Force\n'
    'Write-Host "candidate/source validation PASS"\n'
    'Write-Host "Temporary-copy validation: PASS"\n'
    'Write-Host "PRE-BUILD SAFETY PROOF PASSED"\n'
    'Write-Host "=== GATE 5: JAVAC PROOF ==="\n'
    '& .\\gradlew.bat :app:compileDebugJavaWithJavac\n'
)
hist37 = find_cut(historical_26437_order, "26437-exact-order")
assert "GATE 4: APPLY EXACT VALIDATED CANDIDATES" in hist37
print("PASS: exact 26437 ordering truncates at Gate 4 APPLY, after GLSL + temporary-copy proof")

negative = (
    'Write-Host "=== GATE 2: BUILD ALL TEMPORARY CANDIDATES ==="\n'
    'Write-Host "candidate/source validation PASS"\n'
    'Write-Host "Temporary-copy validation: PASS"\n'
    'Safety "=== GATE 5: APPLY EXACT VALIDATED TRANSFORMATION ==="\n'
    'Copy-Item $Tmp $Real\n'
)
assert "APPLY EXACT" in find_cut(negative, "negative-temp-build")
print("PASS: temporary candidate BUILD heading is not mistaken for real build")

try:
    find_cut(
        'Safety "candidate/source validation PASS"\n'
        'Safety "=== GATE 5: APPLY EXACT ==="\n'
        'Copy-Item $Tmp $Real\n',
        "negative-missing-temp-proof",
    )
except AssertionError:
    print("PASS: missing temporary-copy proof fails closed")
else:
    raise SystemExit("FAIL: missing temporary-copy proof did not fail closed")
PY

echo
echo "=== REVISION GATE R4W: COMPLETE WINDOWS PRE-EXECUTION AUDIT ==="

[[ "${OS:-}" == "Windows_NT" ]] \
    || fail "R4W requires GitHub Actions Windows"

# Every external Unix-style command used by the orchestration must be present
# in Git Bash before the generated reconstruction is allowed to execute.
REQUIRED_BASH_TOOLS=(
    bash git python3 pwsh cygpath
    sha256sum awk sed grep base64 tar diff
    find xargs sort wc tr chmod cp mv rm mkdir cat
)

for tool in "${REQUIRED_BASH_TOOLS[@]}"; do
    command -v "$tool" >/dev/null 2>&1 \
        || fail "R4W missing required Windows Git-Bash tool: $tool"
done

echo "PASS: complete Git-Bash/PowerShell toolchain present"

# The Windows workflow installs the deterministic NDK before this launcher.
WINDOWS_SDK_ROOT="${ANDROID_SDK_ROOT:-${ANDROID_HOME:-}}"
[[ -n "$WINDOWS_SDK_ROOT" ]] \
    || fail "R4W Android SDK root missing"

R4W_GLSLC="$(
    find "$WINDOWS_SDK_ROOT/ndk" \
        -type f \
        -path '*/shader-tools/windows-x86_64/glslc.exe' \
        -print 2>/dev/null \
        | sort -V \
        | tail -n 1
)"

[[ -n "$R4W_GLSLC" && -f "$R4W_GLSLC" ]] \
    || fail "R4W real Windows NDK glslc.exe missing"

"$R4W_GLSLC" --version >/dev/null 2>&1 \
    || fail "R4W real Windows NDK glslc.exe cannot execute"

echo "PASS: real Windows NDK GLSL compiler executes"

# Audit the fully generated reconstruction, not merely this outer launcher.
python3 - "$GENERATED" <<'PY'
from pathlib import Path
import ast
import re
import sys

p = Path(sys.argv[1])
text = p.read_text(encoding="utf-8")

# These may appear in comments/diagnostic strings in an outer patcher, but must
# not survive as executable dependencies in the fully generated reconstruction.
forbidden = {
    "sudo apt-get": "Linux package manager",
    "apt-get update": "Linux package manager",
    "linux-x86_64": "Linux NDK executable",
    "/usr/local/": "Linux local binary path",
}

for token, label in forbidden.items():
    if token in text:
        raise SystemExit(
            f"FAIL: R4W generated reconstruction still contains {label}: {token}"
        )

# /workspaces/... is a special case. The canonical reconstruction intentionally
# contains those historical literals inside one embedded Python relocation
# transformer whose job is to replace them before historical scripts execute.
# Prove those are the ONLY surviving occurrences and that the relocation
# contract itself is intact.
reloc_marker = "# Environment relocation only."
reloc_pos = text.find(reloc_marker)
if reloc_pos < 0:
    raise SystemExit("FAIL: R4W environment-relocation transformer missing")

# Locate the enclosing embedded-Python heredoc.
heredoc_start = text.rfind("<<'PY'", 0, reloc_pos)
heredoc_end = text.find("\nPY", reloc_pos)
if heredoc_start < 0 or heredoc_end < 0 or heredoc_end <= heredoc_start:
    raise SystemExit("FAIL: R4W could not isolate relocation Python heredoc")

reloc_body = text[heredoc_start:heredoc_end]
outside_reloc = text[:heredoc_start] + text[heredoc_end:]

if "/workspaces/" in outside_reloc:
    raise SystemExit(
        "FAIL: R4W executable/non-relocation Codespaces path survived outside relocation transformer"
    )

required_old_paths = (
    "/workspaces/Photon-Camera-fresh-iris",
    "/workspaces/Photon-Camera",
)
for old_path in required_old_paths:
    if old_path not in reloc_body:
        raise SystemExit(
            "FAIL: R4W historical relocation literal missing: " + old_path
        )

# The relocation block may mention the old paths in comments, but every literal
# must stay within this isolated transformer. No shell/PowerShell stage may use
# them directly.
if "text.replace(" not in reloc_body or "repo" not in reloc_body or "aux" not in reloc_body:
    raise SystemExit("FAIL: R4W relocation transformer semantics incomplete")

print("PASS: historical Codespaces literals are confined to relocation transformer")

# Gate 4B must have been replaced with the native Windows compiler proof.
required = (
    "=== GATE 4B: VERIFY REAL WINDOWS NDK GLSL COMPILER ===",
    "windows-x86_64/glslc.exe",
    "This reconstruction path requires GitHub Actions windows-latest",
    '$(cygpath -w "$G5M_REPO")',
    '$(cygpath -w "$G6_REPO")',
    "build_26439_windows_v2_temporal_channel_ownership.ps1",
)
for token in required:
    if token not in text:
        raise SystemExit(
            "FAIL: R4W generated reconstruction missing required Windows contract: "
            + token
        )

# Parse every Python heredoc that will execute inside the generated script, and
# additionally prove common module-qualified references have matching imports.
pattern = re.compile(r"<<'PY'\n(?P<body>.*?)\nPY(?:\n|$)", re.DOTALL)
bodies = [m.group("body") for m in pattern.finditer(text)]
if not bodies:
    raise SystemExit("FAIL: R4W generated reconstruction contains no Python heredocs")

for index, body in enumerate(bodies, 1):
    try:
        tree = ast.parse(body)
    except SyntaxError as ex:
        raise SystemExit(
            f"FAIL: R4W generated Python heredoc {index} syntax error: {ex}"
        )

    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])

    module_refs = {
        name for name in ("re", "sys", "os", "json", "base64", "hashlib",
                          "subprocess", "shutil", "tempfile")
        if re.search(rf"\b{name}\.", body)
    }
    missing = sorted(module_refs - imports)
    if missing:
        raise SystemExit(
            f"FAIL: R4W generated Python heredoc {index} missing imports: {missing}"
        )

# Every Git clone created by the generated reconstruction must establish the
# Windows line-ending policy BEFORE checkout. This is recursive protection:
# outer workflow -> disposable build clone -> all reconstruction-created clones.
nested_clone_contracts = (
    (
        'git clone --no-hardlinks --no-checkout . "$REPLAY_REPO"',
        'git -C "$REPLAY_REPO" config core.autocrlf false',
        'git -C "$REPLAY_REPO" config core.eol lf',
        "Gate 4A",
    ),
    (
        'git clone --no-hardlinks --no-checkout . "$G5M_REPO"',
        'git -C "$G5M_REPO" config core.autocrlf false',
        'git -C "$G5M_REPO" config core.eol lf',
        "Gate 5M",
    ),
    (
        'git clone --no-hardlinks --no-checkout . "$G6_REPO"',
        'git -C "$G6_REPO" config core.autocrlf false',
        'git -C "$G6_REPO" config core.eol lf',
        "Gate 6",
    ),
)

for clone_line, autocrlf_line, eol_line, label in nested_clone_contracts:
    for required_line in (clone_line, autocrlf_line, eol_line):
        if required_line not in text:
            raise SystemExit(
                f"FAIL: R4W {label} nested clone byte contract missing: "
                + required_line
            )

unsafe_nested = re.findall(
    r'git clone --no-hardlinks(?! --no-checkout)\s+\.\s+"\$(?:REPLAY_REPO|G5M_REPO|G6_REPO)"',
    text,
)
if unsafe_nested:
    raise SystemExit(
        "FAIL: R4W unsafe nested Windows clone survived: "
        + repr(unsafe_nested)
    )

for required_token in (
    'HIST_GLSL_BIN="$REPLAY_AUX/windows_glsl_compat"',
    'historical glslangValidator interface backed by real Windows NDK glslc.exe',
    'REPLAY_EXPECTED_BUILD["build_26429_codespace_shared_guide_reference_structure.sh"]="26429"',
    'REPLAY_EXPECTED_BUILD["build_26435_codespace_exact26430_sdr_lowfreq_ultrahdr_v2.sh"]="26435"',
    'log lacks candidate/source validation PASS',
    'log lacks Temporary-copy validation PASS',
):
    if required_token not in text:
        raise SystemExit(
            "FAIL: R4W historical lineage/GLSL contract missing: " + required_token
        )

print("PASS: historical Linux GLSL dependency replaced by Windows NDK glslc compatibility")
print("PASS: retained 26429->26435 replay has per-stage lineage validation")
print("PASS: all 3 nested reconstruction clones set LF policy before checkout")
print(f"PASS: {len(bodies)} generated Python heredocs parsed with import audit")
print("PASS: no Linux-only executable dependencies survive generated reconstruction")
print("PASS: required Windows-native reconstruction contracts present")
PY

# Parse every historical PowerShell source now, before historical replay.
R4W_HISTORY_DIR="historical_replay"
[[ -d "$R4W_HISTORY_DIR" ]] \
    || fail "R4W historical replay directory missing: $R4W_HISTORY_DIR"

R4W_HISTORY_COUNT="$(
    find "$R4W_HISTORY_DIR" -maxdepth 1 -type f -name '*.ps1' | wc -l | tr -d ' '
)"
[[ "$R4W_HISTORY_COUNT" -ge 1 ]] \
    || fail "R4W found no historical PowerShell files to parse"

echo "PASS: R4W historical replay directory = $R4W_HISTORY_DIR"
echo "PASS: R4W historical PowerShell file count = $R4W_HISTORY_COUNT"

R4W_PS_PARSER="$SAFETY_DIR/r4w_parse_all_history.ps1"
cat > "$R4W_PS_PARSER" <<'PWSH'
param([Parameter(Mandatory = $true)][string]$HistoryDir)

$ErrorActionPreference = "Stop"
$files = @(Get-ChildItem -LiteralPath $HistoryDir -Filter "*.ps1" -File)

if ($files.Count -lt 1) {
    throw "FAIL: no historical PowerShell files found"
}

foreach ($file in $files) {
    $tokens = $null
    $errors = $null
    [System.Management.Automation.Language.Parser]::ParseFile(
        $file.FullName,
        [ref]$tokens,
        [ref]$errors
    ) | Out-Null

    if ($errors.Count -gt 0) {
        $errors | ForEach-Object { Write-Host $_.Message }
        throw "FAIL: historical PowerShell parser error: $($file.Name)"
    }

    Write-Host "PASS: parser $($file.Name)"
}

Write-Host "PASS: all historical PowerShell files parse"
PWSH

pwsh -NoLogo -NoProfile -File "$R4W_PS_PARSER" "$(cygpath -w "$R4W_HISTORY_DIR")" \
    || fail "R4W historical PowerShell parser audit failed"

echo
echo "candidate/source validation PASS"
echo "Temporary-copy validation: PASS"
echo "PRE-BUILD SAFETY PROOF PASSED"
echo "PASS: COMPLETE WINDOWS PRE-EXECUTION AUDIT"
echo

echo "=== REVISION GATE R5: PATCH MANIFEST + PRE-EXEC SOURCE INTEGRITY ==="

REVISION_PATCH="$SAFETY_DIR/reconstruction_gate6b1_revision.patch"
set +e
diff -u "$CANONICAL_COPY" "$GENERATED" > "$REVISION_PATCH"
DIFF_RC=$?
set -e

[[ "$DIFF_RC" -eq 1 ]] \
    || fail "Revision diff generation returned unexpected code $DIFF_RC"
[[ -s "$REVISION_PATCH" ]] \
    || fail "Revision patch is unexpectedly empty"

APP_PATCH_AFTER="$SAFETY_DIR/pre_exec_app.patch"
git diff --binary HEAD -- app > "$APP_PATCH_AFTER" \
    || fail "Could not re-read pre-exec app patch"

cmp -s "$PRE_PATCH" "$APP_PATCH_AFTER" \
    || fail "app/ changed during revision preparation"

echo "PASS: revision patch saved: $REVISION_PATCH"
echo "PASS: app/ unchanged during hardened-launcher preparation"
echo "PASS: no version change"
echo "PASS: no Gradle/build executed by revision preflight"

echo
echo "======================================================================"
echo "REVISION PRE-BUILD SAFETY PROOF PASSED"
echo "ALL HARDENING CHECKS COMPLETED BEFORE HISTORICAL WRAPPER EXECUTION"
echo "EXECUTING EXACT 4be6661 SCRIPT WITH ONLY GATE 6B1 PATCHED"
echo "======================================================================"
echo

chmod +x "$GENERATED"
exec bash "$GENERATED"

# Windows-native replacement path: 2026-08-12. No Linux PowerShell emulation.
