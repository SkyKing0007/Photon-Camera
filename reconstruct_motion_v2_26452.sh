#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# Photon Camera Motion V2 26452 reconstruction — V10 ESSL validator wrapper
#
# V10 preserves the exact audited V9 reconstruction launcher from commit
# c156d3748f460e4499ade9c488828a47e96662f9 and changes ONLY the historical
# GLSL validation compatibility layer:
#
#   V9: historical glslangValidator calls -> Android NDK glslc -> SPIR-V/Vulkan
#   V10: historical glslangValidator calls -> real Khronos glslangValidator
#        in GLSL/ESSL front-end validation mode (NO -V, NO -G, NO SPIR-V)
# ============================================================================

V9_COMMIT="c156d3748f460e4499ade9c488828a47e96662f9"
V9_PATH="reconstruct_motion_v2_26452.sh"
V9_BLOB="f1062dc4f3aa8418af2f08c10ffc1463332c3149"

fail() {
    echo "FAIL: $*" >&2
    exit 1
}

echo "======================================================================"
echo "MOTION V2 26452 RECONSTRUCTION — V10 REAL ESSL VALIDATION"
echo "======================================================================"

echo
echo "=== REVISION GATE R0: REPOSITORY + V9 SOURCE PROOF ==="

git rev-parse --is-inside-work-tree >/dev/null 2>&1 \
    || fail "Not inside the Photon Camera Git repository"

CURRENT_BRANCH="$(git branch --show-current)"
[[ -n "$CURRENT_BRANCH" ]] || fail "Detached HEAD is not allowed"
[[ "$CURRENT_BRANCH" != "dev" ]] || fail "Refusing to execute on dev"

ACTUAL_V9_BLOB="$(git rev-parse "${V9_COMMIT}:${V9_PATH}" 2>/dev/null || true)"
[[ "$ACTUAL_V9_BLOB" == "$V9_BLOB" ]] || {
    echo "Expected V9 blob: $V9_BLOB"
    echo "Actual V9 blob:   ${ACTUAL_V9_BLOB:-MISSING}"
    fail "Exact audited V9 launcher could not be proven"
}

STAMP="$(date +%Y%m%d_%H%M%S)_$$"
SAFETY_DIR="reconstruct_26452_v10_safety_${STAMP}"
mkdir -p "$SAFETY_DIR"

V9_COPY="$SAFETY_DIR/reconstruct_motion_v2_26452.v9.original.sh"
V10_GENERATED="$SAFETY_DIR/reconstruct_motion_v2_26452.v10.generated.sh"
PRE_PATCH="$SAFETY_DIR/pre_run_app.patch"
STATE="$SAFETY_DIR/pre_run_state.txt"

git show "${V9_COMMIT}:${V9_PATH}" > "$V9_COPY"
[[ -s "$V9_COPY" ]] || fail "Could not materialize V9 launcher"
[[ "$(git hash-object --no-filters "$V9_COPY")" == "$V9_BLOB" ]] \
    || fail "Materialized V9 launcher blob mismatch"

echo "PASS: exact V9 launcher materialized byte-for-byte"

echo
echo "=== REVISION GATE R1: BACKUP BRANCH + BINARY PRE-RUN PATCH ==="

BACKUP_BRANCH="backup/runner-before-26452-v10-${STAMP}"
git branch "$BACKUP_BRANCH" HEAD \
    || fail "Could not create backup branch $BACKUP_BRANCH"

git diff --binary HEAD -- app > "$PRE_PATCH" \
    || fail "Could not create binary pre-run app patch"

{
    echo "Photon Camera 26452 V10 pre-run state"
    echo "branch=$CURRENT_BRANCH"
    echo "head=$(git rev-parse HEAD)"
    echo "v9_commit=$V9_COMMIT"
    echo "v9_blob=$V9_BLOB"
    echo "backup_branch=$BACKUP_BRANCH"
    echo
    git status --short
} > "$STATE"

echo "PASS: backup branch created: $BACKUP_BRANCH"
echo "PASS: binary pre-run app patch saved: $PRE_PATCH"

echo
echo "=== REVISION GATE R2: SURGICAL V9 -> V10 ESSL TRANSFORMATION ==="

python3 - "$V9_COPY" "$V10_GENERATED" <<'__PY_V10__'
from pathlib import Path
import sys

src = Path(sys.argv[1])
dst = Path(sys.argv[2])
text = src.read_text(encoding="utf-8")

start_anchor = "hist_glsl_block = r'''\\nHIST_GLSL_BIN="
end_anchor = "'''\\n\\ntext = text.replace(hist_glsl_anchor, hist_glsl_anchor + hist_glsl_block, 1)"

if text.count(start_anchor) != 1:
    raise SystemExit(f"FAIL: V9 GLSL block start count={text.count(start_anchor)}")
if text.count(end_anchor) != 1:
    raise SystemExit(f"FAIL: V9 GLSL block end count={text.count(end_anchor)}")

start = text.index(start_anchor)
end = text.index(end_anchor, start)
old_block = text[start:end]

for required in (
    'WINDOWS_NDK_GLSLC',
    '-fshader-stage="$glslc_stage"',
    '.iris_glslc_validation.spv',
    'glslc produced no SPIR-V',
    'historical glslangValidator interface backed by real Windows NDK glslc.exe',
):
    if required not in old_block:
        raise SystemExit("FAIL: audited V9 validator token missing: " + required)

new_block = r'''hist_glsl_block = r"""
# IRIS_26452_V10_REAL_ESSL_REFERENCE_VALIDATOR
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
            [[ "$#" -ge 2 ]] || exit 2
            stage="$2"
            shift 2
            ;;
        -*)
            echo "glslangValidator compatibility: unsupported option $1" >&2
            exit 2
            ;;
        *)
            [[ -z "$source_file" ]] || exit 2
            source_file="$1"
            shift
            ;;
    esac
done
[[ "$stage" == "comp" || "$stage" == "frag" ]] || exit 2
[[ -n "$source_file" && -f "$source_file" ]] || exit 2
# Front-end GLSL/ESSL validation only: NO -V, NO -G, NO SPIR-V output.
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
uniform float exposure;
uniform vec2 irisImageSize;
void main() {
    vec2 uv=(vec2(gl_GlobalInvocationID.xy)+vec2(0.5))/irisImageSize;
    float v=texture(inputTexture,uv).r*exposure;
    if(v < -1.0){ return; }
}
EOF_COMP
cat > "$HIST_GLSL_SMOKE/fragment.frag" <<'EOF_FRAG'
#version 310 es
precision highp float;
uniform sampler2D inputTexture;
uniform float exposure;
layout(location=0) out vec4 outColor;
void main(){ outColor=texture(inputTexture,vec2(0.5))*exposure; }
EOF_FRAG

glslangValidator -S comp "$HIST_GLSL_SMOKE/compute.comp" \
    || fail "Historical OpenGL ES compute validation smoke test failed"
glslangValidator -S frag "$HIST_GLSL_SMOKE/fragment.frag" \
    || fail "Historical OpenGL ES fragment validation smoke test failed"

echo "PASS: real Khronos OpenGL ES / ESSL reference validation active"
"""
'''

text = text[:start] + new_block + text[end:]

proof_anchor = (
    "for required_hist_contract in (\\n"
    '    \'HIST_GLSL_BIN="$REPLAY_AUX/windows_glsl_compat"\',\\n'
)
if text.count(proof_anchor) != 1:
    raise SystemExit("FAIL: V9 historical contract-list anchor mismatch")
text = text.replace(
    proof_anchor,
    (
        "for required_hist_contract in (\\n"
        '    \'IRIS_26452_V10_REAL_ESSL_REFERENCE_VALIDATOR\',\\n'
        '    \'REAL_GLSLANG_VALIDATOR\',\\n'
        '    \'HIST_GLSL_BIN="$REPLAY_AUX/windows_glsl_compat"\',\\n'
    ),
    1,
)

r4w_anchor = 'echo "PASS: real Windows NDK GLSL compiler executes"\\n'
if text.count(r4w_anchor) != 1:
    raise SystemExit("FAIL: V9 R4W GLSL anchor mismatch")
r4w_new = r'''echo "PASS: real Windows NDK GLSL compiler executes"
[[ -n "${REAL_GLSLANG_VALIDATOR:-}" ]] \
    || fail "R4W REAL_GLSLANG_VALIDATOR environment variable missing"
[[ -f "$REAL_GLSLANG_VALIDATOR" ]] \
    || fail "R4W real Khronos glslangValidator.exe missing"
"$REAL_GLSLANG_VALIDATOR" --version >/dev/null 2>&1 \
    || fail "R4W real Khronos glslangValidator.exe cannot execute"
echo "PASS: real Khronos GLSL/ESSL reference validator executes"
'''
text = text.replace(r4w_anchor, r4w_new, 1)

for forbidden in (
    '.iris_glslc_validation.spv',
    'glslc produced no SPIR-V',
    '-fshader-stage="$glslc_stage"',
    'interface backed by real Windows NDK glslc.exe',
):
    if forbidden in text:
        raise SystemExit("FAIL: V9 Vulkan validation survived: " + forbidden)

for required in (
    'IRIS_26452_V10_REAL_ESSL_REFERENCE_VALIDATOR',
    'REAL_GLSLANG_VALIDATOR',
    'NO -V, NO -G, NO SPIR-V output',
    'real Khronos OpenGL ES / ESSL reference validation active',
):
    if required not in text:
        raise SystemExit("FAIL: V10 ESSL contract missing: " + required)

dst.write_text(text, encoding="utf-8", newline="\n")
print("candidate/source validation PASS")
print("Temporary-copy validation: PASS")
print("PRE-BUILD SAFETY PROOF PASSED")
print("PASS: V10 ESSL transformation generated")
__PY_V10__

echo
echo "=== REVISION GATE R3: TEMPORARY-COPY VALIDATION ==="
[[ -s "$V10_GENERATED" ]] || fail "V10 generated launcher is empty"
bash -n "$V10_GENERATED" || fail "Generated V10 launcher has Bash syntax error"
echo "candidate/source validation PASS"
echo "Temporary-copy validation: PASS"
echo "PRE-BUILD SAFETY PROOF PASSED"

echo
echo "=== REVISION GATE R4: REAL ESSL VALIDATOR PROOF ==="
[[ -n "${REAL_GLSLANG_VALIDATOR:-}" ]] \
    || fail "REAL_GLSLANG_VALIDATOR missing; workflow did not install Khronos validator"
[[ -f "$REAL_GLSLANG_VALIDATOR" ]] \
    || fail "REAL_GLSLANG_VALIDATOR path does not exist"
"$REAL_GLSLANG_VALIDATOR" --version \
    || fail "Real Khronos validator cannot execute"

SMOKE="$SAFETY_DIR/v10_essl_smoke"
mkdir -p "$SMOKE"
cat > "$SMOKE/legal_photon_style.comp" <<'EOF'
#version 310 es
precision highp float;
layout(local_size_x=1, local_size_y=1, local_size_z=1) in;
uniform sampler2D tex;
uniform float gain;
uniform vec2 size;
void main(){
    vec2 uv=(vec2(gl_GlobalInvocationID.xy)+vec2(0.5))/size;
    float x=texture(tex,uv).r*gain;
    if(x < -1.0){ return; }
}
EOF
"$REAL_GLSLANG_VALIDATOR" -S comp "$SMOKE/legal_photon_style.comp" \
    || fail "Real ESSL validator rejected legal Photon-style compute GLSL"

cat > "$SMOKE/invalid.comp" <<'EOF'
#version 310 es
layout(local_size_x=1) in;
void main( {
EOF
if "$REAL_GLSLANG_VALIDATOR" -S comp "$SMOKE/invalid.comp" >/dev/null 2>&1; then
    fail "Real ESSL validator accepted intentionally invalid GLSL"
fi

echo "PASS: legal Photon-style ESSL accepted"
echo "PASS: intentionally invalid ESSL rejected"

echo
echo "=== REVISION GATE R5: EXECUTE FULL V10 RECONSTRUCTION ==="
chmod +x "$V10_GENERATED"
exec "$V10_GENERATED"
