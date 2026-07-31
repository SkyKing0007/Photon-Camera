#!/usr/bin/env bash
set -Eeuo pipefail

cd /workspaces/Photon-Camera

REPORT="/workspaces/Photon-Camera/motion_26172_hdrx_failure_exact_context.txt"

PYRAMID="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/scripts/PyramidMerging.java"
HDRX="app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java"
PARAMS="app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java"
NOISE="app/src/main/java/com/particlesdevs/photoncamera/processing/render/NoiseModeler.java"
POST="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java"
MOTION_SHADER="app/src/main/assets/shaders/merge/motionmerge11.glsl"
INIT_SHADER="app/src/main/assets/shaders/merge/contributioninit.glsl"
CAPTURE="app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java"
GYRO="app/src/main/java/com/particlesdevs/photoncamera/control/Gyro.java"
IMAGE_SAVER="app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java"
DEFAULT_SAVER="app/src/main/java/com/particlesdevs/photoncamera/processing/DefaultSaver.java"
PROCESSOR_BASE="app/src/main/java/com/particlesdevs/photoncamera/processing/processor/ProcessorBase.java"
GLPROG="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLProg.java"
GLFORMAT="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLFormat.java"
GLTEXTURE="app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLTexture.java"
LOG_FILE="app/src/main/java/com/particlesdevs/photoncamera/util/Log.java"
VERSION="app/version.properties"

EXPECTED_HEAD="cedc3ab3e39ad49d42523cff7e3711f8baa69a13"

method_dump_py='
from pathlib import Path
import re
import sys

path = Path(sys.argv[1])
pattern = sys.argv[2]
label = sys.argv[3]

print(f"\n----- {label}: {path} / {pattern} -----")

if not path.exists():
    print("FILE MISSING")
    raise SystemExit(0)

text = path.read_text(errors="replace")
lines = text.splitlines()

matches = []
regex = re.compile(pattern)

for index, line in enumerate(lines):
    if regex.search(line):
        matches.append(index)

if not matches:
    print("NO MATCH")
    raise SystemExit(0)

for occurrence, start in enumerate(matches, 1):
    declaration = start
    while declaration > 0 and "{" not in lines[declaration]:
        declaration -= 1
        if start - declaration > 12:
            declaration = start
            break

    brace_start = None
    for pos in range(declaration, min(len(lines), start + 15)):
        if "{" in lines[pos]:
            brace_start = pos
            break

    if brace_start is None:
        lo = max(0, start - 15)
        hi = min(len(lines), start + 45)
    else:
        depth = 0
        seen = False
        hi = min(len(lines), brace_start + 240)

        for pos in range(brace_start, len(lines)):
            line = lines[pos]
            depth += line.count("{")
            depth -= line.count("}")

            if line.count("{"):
                seen = True

            if seen and depth <= 0:
                hi = pos + 1
                break

        lo = declaration

    print(f"\n### occurrence {occurrence}, lines {lo + 1}-{hi}")
    for pos in range(lo, hi):
        print(f"{pos + 1:05d}: {lines[pos]}")
'

{
    echo "============================================================"
    echo " PhotonCamera 26172 HDRX failure source audit"
    echo "============================================================"
    echo

    echo "=== REPOSITORY STATE ==="
    echo "Branch: $(git branch --show-current)"
    echo "HEAD:   $(git rev-parse HEAD)"
    grep '^VERSION_BUILD=' "$VERSION" || true
    echo
    git status --short
    echo

    echo "=== CHECKPOINT ASSERTIONS ==="
    [ "$(git branch --show-current)" = "experimental-effective-stack" ] \
        && echo "PASS branch" \
        || echo "FAIL branch"

    [ "$(git rev-parse HEAD)" = "$EXPECTED_HEAD" ] \
        && echo "PASS base HEAD" \
        || echo "FAIL base HEAD"

    grep -q '^VERSION_BUILD=26172$' "$VERSION" \
        && echo "PASS build 26172" \
        || echo "FAIL build 26172"
    echo

    echo "=== GENERATED 26172 FILE HASHES ==="
    for item in \
        "c9d04e25111921936faddbfa65a6c48ed6b4b295c6941eaad7d25441597ce75e|$PYRAMID" \
        "201a7e3938d36c4a42101374c46051b1d0ad7794e65009a653d9219ba3a1ef39|$HDRX" \
        "1c3f43bcf4733c3fac6fd0dcd88f8e645c9fd122589cdd170cd85ccf8ae1ff1c|$PARAMS" \
        "7a6c9beba00891bdc19f581e194b3cd1271cfa89b4c73ba3c0d8869d0100519e|$NOISE" \
        "99ef221fef9dbf1e1781a2fb0701e4fa8a78dba03c103f39e84bbf5ab5e0f8cc|$POST" \
        "c1bb9bd42df33624a139ac664c71fef9e640fff6064bbb37d2d24f8eb0fc69d8|$MOTION_SHADER" \
        "4cf84898efa241ffb1fe60daea554ce23b0f91f1f0ae5a00b785525098cb6123|$INIT_SHADER"; do

        expected="${item%%|*}"
        file="${item#*|}"

        if [ ! -f "$file" ]; then
            echo "MISSING $file"
            continue
        fi

        actual="$(sha256sum "$file" | awk "{print \$1}")"

        if [ "$actual" = "$expected" ]; then
            echo "PASS $file"
        else
            echo "MISMATCH $file"
            echo "  expected=$expected"
            echo "  actual=$actual"
        fi
    done
    echo

    echo "=== CAPTURE FINALIZATION METHOD ==="
    python3 -c "$method_dump_py" \
        "$CAPTURE" \
        'finalizeDedicatedMotionBurst[[:space:]]*\(' \
        "finalizeDedicatedMotionBurst"
    echo

    echo "=== CAPTURE HANDOFF MARKERS WITH CONTEXT ==="
    grep -n -B45 -A100 -E \
        'MOTION_26166_BLACK_LEVEL_SELECTED|CompleteSequence|COMBINED_GYRO_PADDED|COMBINED_EXPOSURE_MAP_READY|buffer handed to saver|Dedicated Motion HDRX format|Starting dedicated Motion HDRX|mImageSaver\.runRaw|Dedicated Motion runRaw|onProcessingError' \
        "$CAPTURE" || true
    echo

    echo "=== GYRO COMPLETESEQUENCE ==="
    python3 -c "$method_dump_py" \
        "$GYRO" \
        'CompleteSequence[[:space:]]*\(' \
        "Gyro.CompleteSequence"
    echo

    echo "=== GYRO BURST COLLECTION AND LIST OWNERSHIP ==="
    grep -n -B35 -A110 -E \
        'BurstShakiness|CompleteGyroBurst|PrepareGyroBurst|CompleteSequence|buildZslBurstShakiness' \
        "$GYRO" || true
    echo

    echo "=== IMAGE SAVER RUNRAW ==="
    python3 -c "$method_dump_py" \
        "$IMAGE_SAVER" \
        'runRaw[[:space:]]*\(' \
        "ImageSaver.runRaw"
    echo

    echo "=== DEFAULT SAVER RUNRAW ==="
    python3 -c "$method_dump_py" \
        "$DEFAULT_SAVER" \
        'runRaw[[:space:]]*\(' \
        "DefaultSaver.runRaw"
    echo

    echo "=== HDRX CONSTRUCTOR, START, RUN AND APPLYHDRX ENTRY ==="
    python3 -c "$method_dump_py" \
        "$HDRX" \
        'HdrxProcessor[[:space:]]*\(' \
        "HdrxProcessor constructor"

    python3 -c "$method_dump_py" \
        "$HDRX" \
        'void[[:space:]]+start[[:space:]]*\(' \
        "HdrxProcessor.start"

    python3 -c "$method_dump_py" \
        "$HDRX" \
        'void[[:space:]]+Run[[:space:]]*\(' \
        "HdrxProcessor.Run"

    python3 -c "$method_dump_py" \
        "$HDRX" \
        'ApplyHdrX[[:space:]]*\(' \
        "HdrxProcessor.ApplyHdrX"
    echo

    echo "=== PROCESSOR THREAD / CALLBACK ROUTING ==="
    sed -n '1,520p' "$PROCESSOR_BASE" 2>/dev/null || true
    echo

    grep -RIn -B35 -A100 -E \
        'new HdrxProcessor|HdrxProcessor\(|configure\(.*CameraMode|processor\.start|callback\.onFailed|HdrX Processing Failed|Hdrx processing failed|FAILED_MSG' \
        app/src/main/java/com/particlesdevs/photoncamera/processing \
        app/src/main/java/com/particlesdevs/photoncamera/ui \
        app/src/main/java/com/particlesdevs/photoncamera/capture \
        2>/dev/null || true
    echo

    echo "=== 26172 PYRAMID ENTRY AND CONTRIBUTION PATH ==="
    grep -n -B35 -A120 -E \
        'MOTION_26172_CONTRIBUTION_TRACKING|contributioninit|motionmerge11|contributionTexture|measureMotionContribution|MOTION_26172_LOCAL_CONTRIBUTION|GLHistogram|readBuffer|BufferLoad' \
        "$PYRAMID" || true
    echo

    echo "=== MOTION MERGE SHADER ==="
    nl -ba "$MOTION_SHADER" 2>/dev/null || true
    echo

    echo "=== CONTRIBUTION INITIALIZER ==="
    nl -ba "$INIT_SHADER" 2>/dev/null || true
    echo

    echo "=== GL SHADER LAYOUT PARSER ==="
    grep -n -B40 -A160 -E \
        'mComputeLayouts|GLComputeLayout|layout\(|binding|image2D|r16f|rgba16f|useProgram|useAssetProgram|compileShader|createProgram' \
        "$GLPROG" || true
    echo

    echo "=== GL COMPUTE LAYOUT CLASS ==="
    grep -RIn -B20 -A160 -E \
        'class GLComputeLayout|enum.*DataType|FLOAT_16|R16F|GL_R16F|SIMPLE_16|mFormat' \
        app/src/main/java/com/particlesdevs/photoncamera/processing/opengl \
        | head -12000 || true
    echo

    echo "=== GL FORMAT AND TEXTURE SUPPORT ==="
    nl -ba "$GLFORMAT" 2>/dev/null || true
    echo
    sed -n '1,900p' "$GLTEXTURE" 2>/dev/null || true
    echo

    echo "=== APPLICATION LOGGING / FLUSH BEHAVIOR ==="
    sed -n '1,900p' "$LOG_FILE" 2>/dev/null || true
    echo

    grep -RIn -B35 -A100 -E \
        'UncaughtExceptionHandler|setDefaultUncaughtExceptionHandler|Thread\.setDefault|RuntimeException|OutOfMemoryError|onProcessingError|FAILED_MSG|Log\.getStackTraceString' \
        app/src/main/java/com/particlesdevs/photoncamera \
        | head -14000 || true
    echo

    echo "=== LATEST 26172 BUILD ARTIFACTS ==="
    find /workspaces/Photon-Camera \
        -maxdepth 2 \
        -type f \
        \( -name 'build-26172.log' -o -name 'relevant-errors.txt' -o -name '*26172*.apk' \) \
        -printf '%TY-%Tm-%Td %TH:%TM:%TS %p\n' \
        | sort || true
    echo

    LATEST_BUILD_LOG="$(
        find /workspaces/Photon-Camera \
            -maxdepth 3 \
            -type f \
            -name 'build-26172.log' \
            -printf '%T@ %p\n' \
            | sort -nr \
            | head -n 1 \
            | cut -d' ' -f2-
    )"

    if [ -n "$LATEST_BUILD_LOG" ] && [ -f "$LATEST_BUILD_LOG" ]; then
        echo "Latest build log: $LATEST_BUILD_LOG"
        grep -nE \
            'warning:|error:|FAILURE:|shader|asset|BUILD SUCCESSFUL|BUILD FAILED' \
            "$LATEST_BUILD_LOG" \
            | tail -1000 || true
    else
        echo "No 26172 build log located."
    fi
    echo

    echo "=== CURRENT DIFF SUMMARY ==="
    git diff --stat
    echo
    git diff --check || true
    echo

    echo "REPORT COMPLETE"
} > "$REPORT" 2>&1

echo "============================================================"
echo " 26172 HDRX FAILURE AUDIT COMPLETE"
echo "============================================================"
echo "Report: $REPORT"
echo "No source files were modified."
