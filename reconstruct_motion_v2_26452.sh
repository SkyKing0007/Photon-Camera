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

def _last_proof(patterns, body):
    hits = []
    for pattern in patterns:
        hits.extend(re.finditer(pattern, body, re.IGNORECASE | re.MULTILINE))
    if not hits:
        return None
    return max(hits, key=lambda m: m.end())

candidate_proof = _last_proof(
    (
        r"candidate/source\s+validation\s*:?\s*PASS",
        r"candidate[^\r\n]{0,120}validation[^\r\n]{0,80}\bPASS\b",
    ),
    text,
)
temporary_proof = _last_proof(
    (
        r"Temporary-copy\s+validation\s*:?\s*PASS",
        r"temporary[^\r\n]{0,120}validation[^\r\n]{0,80}\bPASS\b",
    ),
    text,
)

if candidate_proof is None:
    raise SystemExit(
        f"FAIL: historical {target_b} lacks a candidate validation PASS proof"
    )
if temporary_proof is None:
    raise SystemExit(
        f"FAIL: historical {target_b} lacks a temporary-copy validation PASS proof"
    )

proof_end = max(candidate_proof.end(), temporary_proof.end())

# Match any PowerShell statement containing a quoted === GATE ... === heading:
# Write-Host, Safety, Pass, or another logger.
gate_heading = re.compile(
    r"(?im)^[^\r\n]*[\"']===\s*GATE\s+[^\"'\r\n]*===[\"'][^\r\n]*$"
)

danger_tokens = (
    "APPLY",
    "REAL GLSL",
    "GLSLC",
    "JAVAC",
    "APK BUILD",
    "SOURCE WRITE",
    "REAL SOURCE",
    "GRADLE",
)
generic_build = re.compile(r"\bBUILD\b", re.IGNORECASE)

headings = list(gate_heading.finditer(text))
post_proof_headings = [m for m in headings if m.start() >= proof_end]

cut = None
cut_title = None

for m in post_proof_headings:
    title = m.group(0).upper()
    dangerous = any(token in title for token in danger_tokens)

    # Candidate construction may legitimately contain BUILD in a heading.
    if generic_build.search(title):
        if "CANDIDATE" not in title and "TEMPORARY" not in title:
            dangerous = True

    if dangerous:
        cut = m.start()
        cut_title = m.group(0).strip()
        break

if cut is None:
    diagnostic = [m.group(0).strip() for m in post_proof_headings[:12]]
    raise SystemExit(
        "FAIL: no safe post-candidate truncation gate found for historical "
        + str(target_b)
        + "; later gate headings="
        + repr(diagnostic)
    )

if cut <= proof_end:
    raise SystemExit(
        f"FAIL: historical {target_b} truncation does not follow both validation proofs"
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
    def last_proof(patterns, body):
        hits = []
        for pattern in patterns:
            hits.extend(re.finditer(pattern, body, re.IGNORECASE | re.MULTILINE))
        return max(hits, key=lambda m: m.end()) if hits else None

    candidate_proof = last_proof(
        (
            r"candidate/source\s+validation\s*:?\s*PASS",
            r"candidate[^\r\n]{0,120}validation[^\r\n]{0,80}\bPASS\b",
        ),
        text,
    )
    temporary_proof = last_proof(
        (
            r"Temporary-copy\s+validation\s*:?\s*PASS",
            r"temporary[^\r\n]{0,120}validation[^\r\n]{0,80}\bPASS\b",
        ),
        text,
    )

    if candidate_proof is None or temporary_proof is None:
        raise AssertionError(f"{target_b}: validation proof missing")

    proof_end = max(candidate_proof.end(), temporary_proof.end())

    gate_heading = re.compile(
        r"(?im)^[^\r\n]*[\"']===\s*GATE\s+[^\"'\r\n]*===[\"'][^\r\n]*$"
    )
    danger_tokens = (
        "APPLY", "REAL GLSL", "GLSLC", "JAVAC", "APK BUILD",
        "SOURCE WRITE", "REAL SOURCE", "GRADLE",
    )
    generic_build = re.compile(r"\bBUILD\b", re.IGNORECASE)

    for m in gate_heading.finditer(text):
        if m.start() < proof_end:
            continue

        title = m.group(0).upper()
        dangerous = any(token in title for token in danger_tokens)

        if generic_build.search(title):
            if "CANDIDATE" not in title and "TEMPORARY" not in title:
                dangerous = True

        if not dangerous:
            continue

        suffix = text[m.start():]
        if not re.search(
            r"(?i)(Copy-Item|Move-Item|Set-Content|WriteAllText|gradlew|assembleDebug|"
            r"compileDebugJavaWithJavac|glslc|JAVAC|SOURCE APPLY|APPLY EXACT)",
            suffix,
        ):
            raise AssertionError(f"{target_b}: no executable suffix evidence")

        return m.group(0).strip()

    raise AssertionError(f"{target_b}: no cut")

cases = {
    "26437": (
        'Write-Host "=== GATE 2: BUILD ALL 26437 TEMPORARY CANDIDATES ==="\n'
        'Write-Host "candidate/source validation PASS"\n'
        'Write-Host "Temporary-copy validation: PASS"\n'
        'Write-Host "=== GATE 3: REAL GLSL VALIDATION ==="\n'
        '& $glslc $Candidate\n'
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

# Delivered revision v2: 2026-08-12 semantic Gate 6B1 hardening.
