#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: transform_26485_runtime_shutter_full_fix_v1.py <candidate-root>")

root = Path(sys.argv[1])
cap = root / "app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java"
cov = root / "app/src/main/assets/shaders/motionv2/mfsr_mgc_covariance.glsl"

def replace_once(path: Path, old: str, new: str, label: str):
    text = path.read_text()
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one anchor, found {count}")
    path.write_text(text.replace(old, new, 1))

# -------------------------------------------------------------------------
# 1) Runtime crash fix
# -------------------------------------------------------------------------
# Photon GLInterface.getLayouts() is line-oriented. A physical line containing
# two layout(...) declarations is parsed from the FIRST '(' to the LAST ')',
# which turns "binding=0)...layout(...binding=1" into a non-integer token.
# glslangValidator accepts that GLSL, but Photon's runtime parser does not.
replace_once(
    cov,
    "layout(rgba16f,binding=0) uniform highp readonly image2D inputCfa;layout(rgba32f,binding=1) uniform highp writeonly image2D outputCov;",
    "layout(rgba16f,binding=0) uniform highp readonly image2D inputCfa;\n"
    "layout(rgba32f,binding=1) uniform highp writeonly image2D outputCov;",
    "26485 covariance one-layout-per-line runtime fix",
)

# -------------------------------------------------------------------------
# 2) Fully authoritative full-ZSL-prebuffer shutter behavior
# -------------------------------------------------------------------------
# Store whether the rolling RAW ring was already at the requested maximum
# AT SHUTTER PRESS. pollMotionTopUp() runs later/repeatedly, so this must persist.
replace_once(
    cap,
    "\n    private void triggerZslCapture() {",
    "\n    /* IRIS_26485_FULL_PREBUFFER_AUTHORITATIVE_ZSL\n"
    "     * True only when the rolling RAW ring already contained the requested\n"
    "     * maximum at the instant of shutter press. Such a shot must not spend\n"
    "     * 1.4 s trying to manufacture another normal frame group after press.\n"
    "     */\n"
    "    private boolean mMotion26485PrebufferFullAtPress = false;\n"
    "\n    private void triggerZslCapture() {",
    "26485 persistent full-prebuffer press state",
)

# Capture full-ring ownership only after target/minimum are established.
replace_once(
    cap,
    "        int buffered;\n"
    "        synchronized (mZslBufferLock) {\n"
    "            buffered = mZslRingBuffer.size();\n"
    "        }\n\n"
    "        mMotionDiagnosticShotId =",
    "        int buffered;\n"
    "        synchronized (mZslBufferLock) {\n"
    "            buffered = mZslRingBuffer.size();\n"
    "        }\n"
    "        mMotion26485PrebufferFullAtPress =\n"
    "                buffered >= mMotionTopUpTargetFrames;\n\n"
    "        mMotionDiagnosticShotId =",
    "26485 full-prebuffer capture at shutter press",
)

# Make the press-state visible in the trace.
replace_once(
    cap,
    '                        + " iris26480ShortAeTargetSteps="\n'
    '                        + mMotion26478HighlightSafeTargetSteps);',
    '                        + " iris26480ShortAeTargetSteps="\n'
    '                        + mMotion26478HighlightSafeTargetSteps\n'
    '                        + " iris26485PrebufferFullAtPress="\n'
    '                        + mMotion26485PrebufferFullAtPress);',
    "26485 TOP_UP_BEGIN trace",
)

# Full implementation:
# - normal requested count remains a MAXIMUM, never reduced globally;
# - if the rolling ring was already full at press, use the best safe equal-
#   exposure group already present as soon as the existing minimum and exposure
#   safety gates are satisfied;
# - do not wait 1.4 s merely because one or more already-buffered candidates
#   are rejected by exact metadata/exposure grouping;
# - if a deliberate short-highlight RAW was requested, its existing short gate
#   remains authoritative, so highlight recovery is not silently dropped.
replace_once(
    cap,
    "        if ((iris26379TargetReady\n"
    "                || iris26383TimeoutMinimumReady)\n"
    "                && iris26480ShortGateReady) {",
    "        /* IRIS_26485_FULL_PREBUFFER_IMMEDIATE_PROCESS\n"
    "         * Full rolling ZSL buffer at press is authoritative. The valid\n"
    "         * equal-exposure group may be smaller than the requested maximum\n"
    "         * after exact metadata filtering; that is not a reason to wait\n"
    "         * 1.4 s after the shutter. Keep the existing safe minimum,\n"
    "         * exposure-readiness, RAW-adequacy, and short-highlight gates.\n"
    "         */\n"
    "        boolean iris26485FullPrebufferReady =\n"
    "                mMotion26485PrebufferFullAtPress\n"
    "                        && validBuffered >= mMotionTopUpMinimumFrames\n"
    "                        && iris26379TargetExposureReady\n"
    "                        && iris26382RawAdequacyReady;\n\n"
    "        if ((iris26379TargetReady\n"
    "                || iris26485FullPrebufferReady\n"
    "                || iris26383TimeoutMinimumReady)\n"
    "                && iris26480ShortGateReady) {",
    "26485 authoritative full-prebuffer completion gate",
)

# Extend TOP_UP_END diagnostics.
replace_once(
    cap,
    '                            + " iris26383TimeoutMinimumReady="\n'
    '                            + iris26383TimeoutMinimumReady\n'
    '                            + " iris26380RawFloorFraction="',
    '                            + " iris26383TimeoutMinimumReady="\n'
    '                            + iris26383TimeoutMinimumReady\n'
    '                            + " iris26485PrebufferFullAtPress="\n'
    '                            + mMotion26485PrebufferFullAtPress\n'
    '                            + " iris26485FullPrebufferReady="\n'
    '                            + iris26485FullPrebufferReady\n'
    '                            + " iris26380RawFloorFraction="',
    "26485 TOP_UP_END trace",
)

# Hard transform assertions.
cap_text = cap.read_text()
cov_text = cov.read_text()

for marker in (
    "IRIS_26485_FULL_PREBUFFER_AUTHORITATIVE_ZSL",
    "IRIS_26485_FULL_PREBUFFER_IMMEDIATE_PROCESS",
    "mMotion26485PrebufferFullAtPress",
    "iris26485FullPrebufferReady",
):
    if marker not in cap_text:
        raise SystemExit("missing 26485 shutter marker " + marker)

if "layout(rgba16f,binding=0) uniform highp readonly image2D inputCfa;layout(" in cov_text:
    raise SystemExit("26485 covariance runtime layout hazard survived")

for line_no, line in enumerate(cov_text.splitlines(), 1):
    if line.count("layout(") > 1:
        raise SystemExit(f"multiple layout declarations remain on covariance line {line_no}")

print("26485 transform PASS")
