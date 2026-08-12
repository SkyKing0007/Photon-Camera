#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# Photon Camera Motion V2 26452 historical recovery — V11 full-chain audit
#
# V11 always starts from the exact immutable V9 launcher committed at
# c156d3748f460e4499ade9c488828a47e96662f9.  It does NOT patch V10.
#
# V11 adds one semantic correction to V9:
#   historical glslangValidator calls use the real Khronos ESSL/GLSL front end,
#   while historical scripts that explicitly call Android NDK glslc keep glslc.
#
# Before any historical replay begins V11 also audits every retained replay
# file, every Bash script, every PowerShell wrapper, and every base64-decoded
# PowerShell payload.
# ============================================================================

V9_COMMIT="c156d3748f460e4499ade9c488828a47e96662f9"
V9_PATH="reconstruct_motion_v2_26452.sh"
V9_BLOB="f1062dc4f3aa8418af2f08c10ffc1463332c3149"
EXPECTED_BRANCH="experimental-mobile-26452-cfa-to-cfa"

fail() {
    echo "FAIL: $*" >&2
    exit 1
}

pass() {
    echo "PASS: $*"
}

echo "======================================================================"
echo "MOTION V2 26452 — V11 FULL-CHAIN HISTORICAL RECOVERY AUDIT"
echo "======================================================================"

# ---------------------------------------------------------------------------
# V11 GATE 0 — branch / immutable V9 provenance
# ---------------------------------------------------------------------------
echo
echo "=== V11 GATE 0: BRANCH + IMMUTABLE V9 PROVENANCE ==="

git rev-parse --is-inside-work-tree >/dev/null 2>&1 \
    || fail "Not inside Git repository"

CURRENT_BRANCH="$(git branch --show-current)"
[[ "$CURRENT_BRANCH" == "$EXPECTED_BRANCH" ]] \
    || fail "Expected branch $EXPECTED_BRANCH, actual $CURRENT_BRANCH"
[[ "$CURRENT_BRANCH" != "dev" ]] \
    || fail "Refusing dev"

ACTUAL_V9_BLOB="$(git rev-parse "${V9_COMMIT}:${V9_PATH}" 2>/dev/null || true)"
[[ "$ACTUAL_V9_BLOB" == "$V9_BLOB" ]] || {
    echo "Expected V9 blob: $V9_BLOB"
    echo "Actual V9 blob:   ${ACTUAL_V9_BLOB:-MISSING}"
    fail "Exact immutable V9 launcher unavailable"
}

pass "branch = $CURRENT_BRANCH"
pass "exact immutable V9 blob = $V9_BLOB"

STAMP="$(date +%Y%m%d_%H%M%S)_$$"
SAFETY_DIR="reconstruct_26452_v11_safety_${STAMP}"
DECODED_DIR="$SAFETY_DIR/decoded_payloads"
mkdir -p "$DECODED_DIR"

V9_COPY="$SAFETY_DIR/reconstruct_motion_v2_26452.v9.original.sh"
V11_GENERATED="$SAFETY_DIR/reconstruct_motion_v2_26452.v11.generated.sh"
PRE_PATCH="$SAFETY_DIR/pre_run_app.patch"
STATE="$SAFETY_DIR/pre_run_state.txt"
REVISION_PATCH="$SAFETY_DIR/v9_to_v11_harness.patch"

git show "${V9_COMMIT}:${V9_PATH}" > "$V9_COPY"
[[ "$(git hash-object --no-filters "$V9_COPY")" == "$V9_BLOB" ]] \
    || fail "Materialized V9 source is not byte-identical"

# ---------------------------------------------------------------------------
# V11 GATE 1 — mandatory backup branch + pre-run binary patch
# ---------------------------------------------------------------------------
echo
echo "=== V11 GATE 1: BACKUP BRANCH + BINARY PRE-RUN PATCH ==="

BACKUP_BRANCH="backup/runner-before-26452-v11-${STAMP}"
git branch "$BACKUP_BRANCH" HEAD \
    || fail "Could not create backup branch $BACKUP_BRANCH"

git diff --binary HEAD -- app > "$PRE_PATCH" \
    || fail "Could not create binary app pre-run patch"

{
    echo "Photon Camera 26452 V11 pre-run state"
    echo "branch=$CURRENT_BRANCH"
    echo "head=$(git rev-parse HEAD)"
    echo "v9_commit=$V9_COMMIT"
    echo "v9_blob=$V9_BLOB"
    echo "backup_branch=$BACKUP_BRANCH"
    echo
    git status --short
} > "$STATE"

pass "backup branch = $BACKUP_BRANCH"
pass "binary pre-run patch = $PRE_PATCH"

# ---------------------------------------------------------------------------
# V11 GATE 2 — exact 16-file history manifest + syntax audit
# ---------------------------------------------------------------------------
echo
echo "=== V11 GATE 2: COMPLETE 16-FILE HISTORY MANIFEST + SYNTAX AUDIT ==="

HISTORY_DIR="historical_replay"
[[ -d "$HISTORY_DIR" ]] || fail "historical_replay directory missing"

HISTORY_COUNT="$(find "$HISTORY_DIR" -maxdepth 1 -type f | wc -l | tr -d ' ')"
[[ "$HISTORY_COUNT" -eq 16 ]] \
    || fail "Expected exactly 16 historical replay files; found $HISTORY_COUNT"

declare -A HIST_BLOB
HIST_BLOB[build_26429_codespace_shared_guide_reference_structure.sh]="bc24300d1f006aceae7c08a517ba312f5da48e8a"
HIST_BLOB[build_26430_codespace_v2_ownership_headroom_cleanup.sh]="6d207118d6898781aebcc9201e8b231f3deb6a8d"
HIST_BLOB[build_26431_codespace_allframes_body_lens_ownership_v2.sh]="e76639f9fb46e90a4f54ffad765b604d53dadef4"
HIST_BLOB[build_26432_codespace_stack_robust_true_ultrahdr_final.sh]="480d0dffd265c6bc0974b78f80010455d2bdc314"
HIST_BLOB[resume_26433_fix_ultrahdr_javac_type_and_build.sh]="6c379a4c7a026ccd0e6afa1001c8b755bf5d00c5"
HIST_BLOB[build_26434_codespace_stable_base_smooth_motion_ultrahdr_v2.sh]="bd84bdcffdd7e2190413b41069e159f9d01da987"
HIST_BLOB[build_26435_codespace_exact26430_sdr_lowfreq_ultrahdr_v2.sh]="d005fa320771d02fb4dc266a7abaf1aed661d03d"
HIST_BLOB[build_26436_windows_integrated_motion_architecture.ps1]="bc8ff04e845ce06f47d5bc620f4b9995352affba"
HIST_BLOB[build_26437_windows_whitepoint_motion_detail_stable_uhdr.ps1]="5d43b57c4dd3205e67045b00062010f27426a5f8"
HIST_BLOB[build_26438_windows_REVISED_v2_audited_motion_microcontrast_standard_ultrahdr.ps1]="44c25ab8aece30de3d609398c07a07eabdb18093"
HIST_BLOB[build_26439_windows_v2_temporal_channel_ownership.ps1]="1db9e533703333001c96f244332c468c27482afe"
HIST_BLOB[launch_resume_build_26439_after_gate8_v2_MINIMAL.ps1]="c1ecd7f38a06634ecdb6e507b9a22c0092123185"
HIST_BLOB[launch_build_26443_reference_first_local_ownership.ps1]="1e64079bc537a30b0aae3fd1df69e96bfcda0edf"
HIST_BLOB[launch_build_26445_specular_channel_validity_v2.ps1]="68335b2c28a6118e040ea7281ac7c3a2bd0ca7b1"
HIST_BLOB[launch_build_26446_corrected_published_robustness_true_local_support.ps1]="f41d5f70876e973735e1b6119b7f11e78394496d"
HIST_BLOB[launch_build_26450_alias_aware_chroma_reference_dng_REVISED.ps1]="994258191c3ffcf58fdee7ee0cf03486d1e6079f"

[[ "${#HIST_BLOB[@]}" -eq 16 ]] || fail "Internal V11 history manifest is not 16 files"

for name in "${!HIST_BLOB[@]}"; do
    rel="$HISTORY_DIR/$name"
    [[ -f "$rel" ]] || fail "Historical file missing: $rel"
    committed="$(git rev-parse "HEAD:$rel")"
    worktree="$(git hash-object --no-filters "$rel")"
    expected="${HIST_BLOB[$name]}"
    [[ "$committed" == "$expected" ]] \
        || fail "Historical committed blob mismatch: $name expected=$expected actual=$committed"
    [[ "$worktree" == "$expected" ]] \
        || fail "Historical worktree blob mismatch: $name expected=$expected actual=$worktree"
done

pass "all 16 historical files match exact audited Git blobs"

SHELL_COUNT=0
while IFS= read -r -d '' shfile; do
    bash -n "$shfile" || fail "Historical Bash parse failed: $shfile"
    SHELL_COUNT=$((SHELL_COUNT + 1))
done < <(find "$HISTORY_DIR" -maxdepth 1 -type f -name '*.sh' -print0)
[[ "$SHELL_COUNT" -eq 7 ]] || fail "Expected 7 historical Bash scripts; parsed $SHELL_COUNT"
pass "all 7 historical Bash scripts parse"

PS_PARSER="$SAFETY_DIR/parse_powershell.ps1"
cat > "$PS_PARSER" <<'PWSH'
param(
    [Parameter(Mandatory=$true)][string]$Directory,
    [Parameter(Mandatory=$true)][string]$Label
)
$ErrorActionPreference = "Stop"
$files = @(Get-ChildItem -LiteralPath $Directory -Filter "*.ps1" -File)
if ($files.Count -lt 1) { throw "FAIL: no PowerShell files for $Label" }
foreach ($file in $files) {
    $tokens = $null
    $errors = $null
    [System.Management.Automation.Language.Parser]::ParseFile(
        $file.FullName,[ref]$tokens,[ref]$errors) | Out-Null
    if ($errors.Count -gt 0) {
        foreach ($e in $errors) {
            Write-Host ("PARSER ERROR " + $file.Name + " line " +
                $e.Extent.StartLineNumber + ": " + $e.Message)
        }
        throw "FAIL: PowerShell parser rejected $($file.Name)"
    }
    Write-Host ("PASS: parser " + $file.Name)
}
Write-Host ("PASS: PowerShell parser set complete: " + $Label +
    " count=" + $files.Count)
PWSH

pwsh -NoLogo -NoProfile -File "$PS_PARSER" "$(cygpath -w "$HISTORY_DIR")" "direct historical wrappers" \
    || fail "Direct historical PowerShell parser audit failed"

# ---------------------------------------------------------------------------
# V11 GATE 3 — decode every embedded launcher payload and parse the REAL script
# ---------------------------------------------------------------------------
echo
echo "=== V11 GATE 3: DECODE + PARSE ALL EMBEDDED POWERSHELL PAYLOADS ==="

python3 - "$HISTORY_DIR" "$DECODED_DIR" <<'PY'
from pathlib import Path
import base64
import re
import sys

history = Path(sys.argv[1])
out = Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)

expected = {
    "launch_resume_build_26439_after_gate8_v2_MINIMAL.ps1": "26439",
    "launch_build_26443_reference_first_local_ownership.ps1": "26443",
    "launch_build_26445_specular_channel_validity_v2.ps1": "26445",
    "launch_build_26446_corrected_published_robustness_true_local_support.ps1": "26446",
    "launch_build_26450_alias_aware_chroma_reference_dng_REVISED.ps1": "26450",
}

literal = re.compile(
    r'FromBase64String\(\s*"([A-Za-z0-9+/=]+)"\s*\)',
    re.DOTALL,
)

found = {}
for path in sorted(history.glob("*.ps1")):
    text = path.read_text(encoding="utf-8-sig", errors="strict")
    matches = literal.findall(text)
    if not matches:
        continue
    if len(matches) != 1:
        raise SystemExit(
            f"FAIL: {path.name} literal launcher payload count={len(matches)} expected=1"
        )
    try:
        raw = base64.b64decode(matches[0], validate=True)
        decoded = raw.decode("utf-8-sig")
    except Exception as exc:
        raise SystemExit(f"FAIL: cannot decode {path.name}: {exc}")

    build = expected.get(path.name)
    if build is None:
        raise SystemExit(
            f"FAIL: unexpected literal base64 PowerShell launcher: {path.name}"
        )
    if build not in decoded:
        raise SystemExit(
            f"FAIL: decoded {path.name} does not identify expected build {build}"
        )
    if "experimental-clean-photon-rebuild" not in decoded:
        raise SystemExit(
            f"FAIL: decoded {path.name} lost historical branch provenance"
        )
    if "C:\\Users\\nhann\\Documents\\GitHub\\Photon-Camera-clean-rebuild" not in decoded:
        raise SystemExit(
            f"FAIL: decoded {path.name} lost historical Windows-repo provenance"
        )

    target = out / (path.stem + ".decoded.ps1")
    target.write_text(decoded, encoding="utf-8", newline="\n")
    found[path.name] = target.name
    print(f"PASS: decoded {path.name} -> {target.name}")

if set(found) != set(expected):
    missing = sorted(set(expected) - set(found))
    extra = sorted(set(found) - set(expected))
    raise SystemExit(
        f"FAIL: decoded-launcher set mismatch missing={missing} extra={extra}"
    )

print("PASS: exactly five expected late-history/resume payloads decoded")
PY

DECODED_COUNT="$(find "$DECODED_DIR" -maxdepth 1 -type f -name '*.ps1' | wc -l | tr -d ' ')"
[[ "$DECODED_COUNT" -eq 5 ]] \
    || fail "Expected exactly 5 decoded PowerShell payloads; found $DECODED_COUNT"

pwsh -NoLogo -NoProfile -File "$PS_PARSER" "$(cygpath -w "$DECODED_DIR")" "decoded historical payloads" \
    || fail "Decoded historical PowerShell payload parser audit failed"

pass "all 5 decoded historical payloads parse"

# Explicit production/resume ownership proof.
grep -q 'Transform-Reconstruction' \
    "$HISTORY_DIR/build_26439_windows_v2_temporal_channel_ownership.ps1" \
    || fail "26439 production reconstruction transformer missing"
grep -q 'Transform-Accumulator' \
    "$HISTORY_DIR/build_26439_windows_v2_temporal_channel_ownership.ps1" \
    || fail "26439 production accumulator transformer missing"
pass "26439 production transformer ownership proven separately from resume helper"

# ---------------------------------------------------------------------------
# V11 GATE 4 — Windows toolchain and BOTH GLSL compiler semantics
# ---------------------------------------------------------------------------
echo
echo "=== V11 GATE 4: WINDOWS TOOLCHAIN + ESSL/GLSLC SEMANTIC SEPARATION ==="

[[ "${OS:-}" == "Windows_NT" ]] \
    || fail "V11 requires GitHub Actions Windows"

for tool in bash git python3 pwsh cygpath sha256sum awk sed grep base64 tar diff find xargs sort wc tr chmod cp mv rm mkdir cat; do
    command -v "$tool" >/dev/null 2>&1 \
        || fail "Missing required Git-Bash tool: $tool"
done
pass "complete Git-Bash/PowerShell toolchain present"

[[ -n "${REAL_GLSLANG_VALIDATOR:-}" ]] \
    || fail "REAL_GLSLANG_VALIDATOR missing from workflow"
[[ -f "$REAL_GLSLANG_VALIDATOR" ]] \
    || fail "Real Khronos glslangValidator missing: $REAL_GLSLANG_VALIDATOR"
"$REAL_GLSLANG_VALIDATOR" --version >/dev/null 2>&1 \
    || fail "Real Khronos glslangValidator cannot execute"

SDK_ROOT="${ANDROID_SDK_ROOT:-${ANDROID_HOME:-}}"
[[ -n "$SDK_ROOT" ]] || fail "Android SDK root missing"
WINDOWS_NDK_GLSLC="$(
    find "$SDK_ROOT/ndk" -type f \
        -path '*/shader-tools/windows-x86_64/glslc.exe' \
        -print 2>/dev/null | sort -V | tail -n 1
)"
[[ -n "$WINDOWS_NDK_GLSLC" && -f "$WINDOWS_NDK_GLSLC" ]] \
    || fail "Windows NDK glslc.exe missing"
"$WINDOWS_NDK_GLSLC" --version >/dev/null 2>&1 \
    || fail "Windows NDK glslc cannot execute"

# Real ESSL front-end test deliberately uses legal Photon-style standalone
# sampler/scalar/vector uniforms.  Do NOT use reserved/built-in identifiers.
ESSL_SMOKE="$SAFETY_DIR/essl_smoke"
mkdir -p "$ESSL_SMOKE"
cat > "$ESSL_SMOKE/legal_photon_style.comp" <<'GLSL'
#version 310 es
precision highp float;
precision highp image2D;
layout(local_size_x=1, local_size_y=1, local_size_z=1) in;
uniform sampler2D inputTexture;
uniform float exposureGain;
uniform vec2 irisImageExtent;
layout(rgba16f, binding=0) uniform highp writeonly image2D outImage;
void main() {
    ivec2 p=ivec2(gl_GlobalInvocationID.xy);
    vec2 uv=(vec2(p)+vec2(0.5))/max(irisImageExtent,vec2(1.0));
    float v=texture(inputTexture,uv).r*exposureGain;
    imageStore(outImage,p,vec4(v));
}
GLSL
"$REAL_GLSLANG_VALIDATOR" -S comp "$ESSL_SMOKE/legal_photon_style.comp" \
    || fail "Real ESSL validator rejected legal Photon-style compute shader"

cat > "$ESSL_SMOKE/invalid.comp" <<'GLSL'
#version 310 es
layout(local_size_x=1) in;
void main( {
GLSL
if "$REAL_GLSLANG_VALIDATOR" -S comp "$ESSL_SMOKE/invalid.comp" >/dev/null 2>&1; then
    fail "Real ESSL validator accepted intentionally invalid shader"
fi

pass "real Khronos ESSL front-end accepts legal Photon-style GLSL"
pass "real Khronos ESSL front-end rejects invalid GLSL"
pass "historical explicit NDK glslc remains independently available"

# ---------------------------------------------------------------------------
# V11 GATE 5 — semantic transformation of immutable V9 (no brittle V10 patch)
# ---------------------------------------------------------------------------
echo
echo "=== V11 GATE 5: SEMANTIC V9 -> V11 HARNESS TRANSFORMATION ==="

python3 - "$V9_COPY" "$V11_GENERATED" <<'PY'
from pathlib import Path
import re
import sys

src = Path(sys.argv[1])
dst = Path(sys.argv[2])
text = src.read_text(encoding="utf-8")

section_marker = "# IRIS_26452_HISTORICAL_LINEAGE_WINDOWS_GLSL"
if text.count(section_marker) != 1:
    raise SystemExit(
        f"FAIL: V9 GLSL section marker count={text.count(section_marker)} expected=1"
    )
section_start = text.index(section_marker)
section_end = text.find("gate4e_heading", section_start)
if section_end < 0:
    raise SystemExit("FAIL: semantic V9 Gate 4E variable boundary not found after GLSL section")
section = text[section_start:section_end]

# Match the assignment semantically inside the uniquely bounded section.
block_pattern = re.compile(
    r"hist_glsl_block\s*=\s*r'''(?P<body>.*?)'''\s*\n\s*"
    r"text\s*=\s*text\.replace\(hist_glsl_anchor,\s*"
    r"hist_glsl_anchor\s*\+\s*hist_glsl_block,\s*1\)",
    re.DOTALL,
)
matches = list(block_pattern.finditer(section))
if len(matches) != 1:
    raise SystemExit(
        f"FAIL: semantic V9 historical GLSL assignment count={len(matches)} expected=1"
    )
old_body = matches[0].group("body")
for token in (
    "WINDOWS_NDK_GLSLC",
    'glslc_stage="compute"',
    '.iris_glslc_validation.spv',
    "glslc produced no SPIR-V",
):
    if token not in old_body:
        raise SystemExit(
            "FAIL: semantic V9 validator provenance missing token: " + token
        )

new_assignment = r"""hist_glsl_block = r'''
# IRIS_26452_V11_REAL_ESSL_REFERENCE_VALIDATOR
[[ -n "${REAL_GLSLANG_VALIDATOR:-}" ]] \
    || fail "REAL_GLSLANG_VALIDATOR was not supplied by workflow"
[[ -f "$REAL_GLSLANG_VALIDATOR" ]] \
    || fail "Real Khronos glslangValidator.exe missing: $REAL_GLSLANG_VALIDATOR"
"$REAL_GLSLANG_VALIDATOR" --version \
    > "$REPLAY_LOGS/real_glslangValidator_version.log" 2>&1 \
    || fail "Real Khronos glslangValidator.exe could not execute"

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
            [[ "$#" -ge 2 ]] || { echo "missing stage" >&2; exit 2; }
            stage="$2"; shift 2 ;;
        -*)
            echo "unsupported historical glslangValidator option: $1" >&2
            exit 2 ;;
        *)
            [[ -z "$source_file" ]] || { echo "multiple sources unsupported" >&2; exit 2; }
            source_file="$1"; shift ;;
    esac
done
[[ "$stage" == "comp" || "$stage" == "frag" ]] || { echo "bad/missing stage" >&2; exit 2; }
[[ -n "$source_file" && -f "$source_file" ]] || { echo "source missing" >&2; exit 2; }
# GLSL/ESSL FRONT END ONLY. No -V, no -G, no SPIR-V output.
exec "${REAL_GLSLANG_VALIDATOR:?REAL_GLSLANG_VALIDATOR missing}" -S "$stage" "$source_file"
GLSLANG_COMPAT
chmod +x "$HIST_GLSL_BIN/glslangValidator"
export PATH="$HIST_GLSL_BIN:$PATH"

HIST_GLSL_SMOKE="$REPLAY_AUX/windows_glsl_compat_smoke"
mkdir -p "$HIST_GLSL_SMOKE"
cat > "$HIST_GLSL_SMOKE/compute.comp" <<'EOF_COMP'
#version 310 es
precision highp float;
layout(local_size_x=1, local_size_y=1, local_size_z=1) in;
uniform sampler2D inputTexture;
uniform float exposureGain;
uniform vec2 irisImageExtent;
void main() {
    vec2 uv=(vec2(gl_GlobalInvocationID.xy)+vec2(0.5))/max(irisImageExtent,vec2(1.0));
    float v=texture(inputTexture,uv).r*exposureGain;
    if(v < -1.0) return;
}
EOF_COMP
cat > "$HIST_GLSL_SMOKE/fragment.frag" <<'EOF_FRAG'
#version 310 es
precision highp float;
uniform sampler2D inputTexture;
uniform float exposureGain;
layout(location=0) out vec4 outColor;
void main(){ outColor=texture(inputTexture,vec2(0.5))*exposureGain; }
EOF_FRAG

glslangValidator -S comp "$HIST_GLSL_SMOKE/compute.comp" \
    || fail "Historical ESSL compute validation failed"
glslangValidator -S frag "$HIST_GLSL_SMOKE/fragment.frag" \
    || fail "Historical ESSL fragment validation failed"
echo "PASS: historical glslangValidator interface backed by real Khronos ESSL front end"
'''

text = text.replace(hist_glsl_anchor, hist_glsl_anchor + hist_glsl_block, 1)"""

absolute_start = section_start + matches[0].start()
absolute_end = section_start + matches[0].end()
text = text[:absolute_start] + new_assignment + text[absolute_end:]

# Update V9's own full generated-source audit to assert the corrected semantics.
old_required = (
    "    'historical glslangValidator interface backed by real Windows NDK glslc.exe',\n"
)
if text.count(old_required) != 1:
    raise SystemExit(
        f"FAIL: V9 R4W old GLSL semantic assertion count={text.count(old_required)} expected=1"
    )
new_required = (
    "    'IRIS_26452_V11_REAL_ESSL_REFERENCE_VALIDATOR',\n"
    "    'historical glslangValidator interface backed by real Khronos ESSL front end',\n"
    "    'REAL_GLSLANG_VALIDATOR',\n"
)
text = text.replace(old_required, new_required, 1)

old_print = (
    'print("PASS: historical Linux GLSL dependency replaced by Windows NDK glslc compatibility")'
)
if text.count(old_print) != 1:
    raise SystemExit(
        f"FAIL: V9 R4W old GLSL PASS message count={text.count(old_print)} expected=1"
    )
text = text.replace(
    old_print,
    'print("PASS: historical glslangValidator calls use real Khronos ESSL; explicit glslc remains separate")',
    1,
)

# Add real glslang execution proof next to the already-valid explicit glslc proof.
r4w_phrase = 'echo "PASS: real Windows NDK GLSL compiler executes"'
if text.count(r4w_phrase) != 1:
    raise SystemExit(
        f"FAIL: V9 R4W glslc execution phrase count={text.count(r4w_phrase)} expected=1"
    )
r4w_insert = r'''echo "PASS: real Windows NDK GLSL compiler executes"

[[ -n "${REAL_GLSLANG_VALIDATOR:-}" ]] \
    || fail "R4W REAL_GLSLANG_VALIDATOR environment variable missing"
[[ -f "$REAL_GLSLANG_VALIDATOR" ]] \
    || fail "R4W real Khronos glslangValidator.exe missing"
"$REAL_GLSLANG_VALIDATOR" --version >/dev/null 2>&1 \
    || fail "R4W real Khronos glslangValidator.exe cannot execute"
echo "PASS: real Khronos ESSL reference validator executes"'''
text = text.replace(r4w_phrase, r4w_insert, 1)

# Fail closed if the Vulkan-emulation implementation survived the semantic replacement.
for forbidden in (
    '.iris_glslc_validation.spv',
    'glslc produced no SPIR-V',
    '-fshader-stage="$glslc_stage"',
):
    if forbidden in text:
        raise SystemExit("FAIL: V9 Vulkan-emulation token survived V11: " + forbidden)

for required in (
    "IRIS_26452_V11_REAL_ESSL_REFERENCE_VALIDATOR",
    "real Khronos ESSL front end",
    "REAL_GLSLANG_VALIDATOR",
    "build_26439_windows_v2_temporal_channel_ownership.ps1",
    "IRIS_26452_GATE6B1_HARDENED_TRUNCATION_CONTRACT",
):
    if required not in text:
        raise SystemExit("FAIL: V11 generated contract missing: " + required)

dst.write_text(text, encoding="utf-8", newline="\n")
print("candidate/source validation PASS")
print("Temporary-copy validation: PASS")
print("PRE-BUILD SAFETY PROOF PASSED")
print("PASS: semantic V9 -> V11 transformation generated")
PY

# ---------------------------------------------------------------------------
# V11 GATE 6 — validate entire generated wrapper before execution
# ---------------------------------------------------------------------------
echo
echo "=== V11 GATE 6: COMPLETE GENERATED-WRAPPER VALIDATION ==="

[[ -s "$V11_GENERATED" ]] || fail "Generated V11 wrapper is empty"
bash -n "$V11_GENERATED" || fail "Generated V11 Bash syntax invalid"

python3 - "$V11_GENERATED" <<'PY'
from pathlib import Path
import ast
import re
import sys

text = Path(sys.argv[1]).read_text(encoding="utf-8")

for forbidden in (
    '.iris_glslc_validation.spv',
    'glslc produced no SPIR-V',
    '-fshader-stage="$glslc_stage"',
):
    if forbidden in text:
        raise SystemExit("FAIL: forbidden Vulkan-emulation token remains: " + forbidden)

for required in (
    "IRIS_26452_V11_REAL_ESSL_REFERENCE_VALIDATOR",
    "IRIS_26452_GATE6B1_HARDENED_TRUNCATION_CONTRACT",
    "IRIS_26452_WINDOWS_NESTED_CLONE_EXACT_BYTES",
    "build_26439_windows_v2_temporal_channel_ownership.ps1",
    "REAL_GLSLANG_VALIDATOR",
):
    if required not in text:
        raise SystemExit("FAIL: generated V11 required marker missing: " + required)

# Parse all simple quoted Python heredocs in the fully generated V11 source.
pattern = re.compile(r"<<'PY'\n(?P<body>.*?)\nPY(?:\n|$)", re.DOTALL)
bodies = [m.group("body") for m in pattern.finditer(text)]
if not bodies:
    raise SystemExit("FAIL: generated V11 contains no Python heredocs")
for i, body in enumerate(bodies, 1):
    try:
        ast.parse(body)
    except SyntaxError as exc:
        raise SystemExit(f"FAIL: generated V11 Python heredoc {i} syntax error: {exc}")

print(f"PASS: generated V11 Python heredocs parsed = {len(bodies)}")
print("PASS: no Vulkan-emulation implementation survives")
PY

set +e
diff -u "$V9_COPY" "$V11_GENERATED" > "$REVISION_PATCH"
DIFF_RC=$?
set -e
[[ "$DIFF_RC" -eq 1 && -s "$REVISION_PATCH" ]] \
    || fail "V11 revision patch proof failed"

APP_PATCH_AFTER="$SAFETY_DIR/pre_exec_app.patch"
git diff --binary HEAD -- app > "$APP_PATCH_AFTER" \
    || fail "Could not re-read app patch"
cmp -s "$PRE_PATCH" "$APP_PATCH_AFTER" \
    || fail "app/ changed during V11 audit preparation"

pass "candidate/source validation PASS"
pass "Temporary-copy validation: PASS"
echo "PRE-BUILD SAFETY PROOF PASSED"
pass "V11 revision patch saved: $REVISION_PATCH"
pass "app/ remained untouched"

# ---------------------------------------------------------------------------
# V11 GATE 7 — execute exact V9 recovery with only audited V11 semantic fix
# ---------------------------------------------------------------------------
echo
echo "======================================================================"
echo "V11 FULL-CHAIN PRE-EXECUTION AUDIT PASSED"
echo "EXECUTING IMMUTABLE V9 RECOVERY WITH ONLY ESSL SEMANTIC CORRECTION"
echo "======================================================================"

chmod +x "$V11_GENERATED"
exec bash "$V11_GENERATED"
