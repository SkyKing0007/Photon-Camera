#!/usr/bin/env python3
from __future__ import annotations
import argparse, difflib, hashlib, re
from pathlib import Path

CAPTURE='app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java'
SAVER='app/src/main/java/com/particlesdevs/photoncamera/processing/DefaultSaver.java'
HDRX='app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java'
CFA='app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java'
MERGER='app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2Merger.java'
SHADER='app/src/main/assets/shaders/motionv2/dng_cfa_to_raw16_26520.glsl'
CHANGED={CAPTURE,SAVER,HDRX,CFA,MERGER,SHADER}

DNG_SHADER=r'''#define LAYOUT //
LAYOUT
precision highp float;
precision highp sampler2D;
precision highp uimage2D;

uniform highp sampler2D fusedCfa;
layout(r16ui, binding = 0) uniform highp writeonly uimage2D outRaw;

uniform ivec2 rawSize;
uniform ivec2 packedSize;
uniform vec4 blackLevel;
uniform float whiteLevel;

/*
 * IRIS_26520_DNG_RAW16_CODE_DOMAIN
 *
 * Inverse of motionv2/raw_to_cfa for the NORMAL-ONLY fused Bayer accumulator.
 * The input is already aligned, robustness-weighted, temporally accumulated and
 * normalized exactly once. No WB, lens shading, RGB reconstruction, Short/Long,
 * tone, display exposure, denoise or sharpening is applied here.
 *
 * packed phase order:
 *   r = (0,0), g = (1,0), b = (0,1), a = (1,1)
 */
float phaseValue(vec4 v, int phase) {
    if (phase == 0) return v.r;
    if (phase == 1) return v.g;
    if (phase == 2) return v.b;
    return v.a;
}

void main() {
    ivec2 p = ivec2(gl_GlobalInvocationID.xy);
    if (any(greaterThanEqual(p, rawSize))) return;

    ivec2 q = p / 2;
    if (any(greaterThanEqual(q, packedSize))) return;
    int phase = (p.y & 1) * 2 + (p.x & 1);

    vec4 packed = texelFetch(fusedCfa, q, 0);
    float normalized = max(phaseValue(packed, phase), 0.0);
    float black = blackLevel[phase];
    float span = max(whiteLevel - black, 1.0);
    float rawCode = normalized * span + black;

    uint code = uint(clamp(floor(rawCode + 0.5), 0.0, 65535.0));
    imageStore(outRaw, p, uvec4(code, 0u, 0u, 0u));
}
'''

def norm(s:str)->str:
    return s.replace('\r\n','\n').replace('\r','\n')

def one(s:str, old:str, new:str, label:str)->str:
    n=s.count(old)
    if n != 1:
        raise AssertionError(f'{label} anchor count={n}')
    return s.replace(old,new,1)

def append_unique_call_argument(
        s:str, function_name:str, required_tokens:list[str],
        new_argument:str, label:str)->str:
    """IRIS_26520_V2_SEMANTIC_RECONSTRUCT_CALL_GATEFIX

    Locate exactly one Java invocation by function name, balance its parentheses,
    verify the expected semantic arguments are present, and append one final
    argument without depending on indentation/line wrapping from the recovered
    successful-build source artifact.
    """
    pattern = re.compile(
            r'(?m)^[ \t]*' + re.escape(function_name) + r'\s*\(')
    matches = list(pattern.finditer(s))
    if len(matches) != 1:
        raise AssertionError(
                f'{label} semantic call count={len(matches)} expected=1')

    match = matches[0]
    open_idx = s.find('(', match.start(), match.end() + 1)
    if open_idx < 0:
        raise AssertionError(f'{label} opening parenthesis missing')

    depth = 0
    quote = None
    escaped = False
    close_idx = -1
    i = open_idx
    while i < len(s):
        ch = s[i]
        if quote is not None:
            if escaped:
                escaped = False
            elif ch == '\\':
                escaped = True
            elif ch == quote:
                quote = None
        else:
            if ch == '"' or ch == "'":
                quote = ch
            elif ch == '(':
                depth += 1
            elif ch == ')':
                depth -= 1
                if depth == 0:
                    close_idx = i
                    break
                if depth < 0:
                    raise AssertionError(
                            f'{label} parenthesis underflow')
        i += 1

    if close_idx < 0:
        raise AssertionError(f'{label} closing parenthesis missing')

    body = s[open_idx + 1:close_idx]
    for token in required_tokens:
        if token not in body:
            raise AssertionError(
                    f'{label} required semantic token missing: {token}')
    if new_argument in body:
        raise AssertionError(
                f'{label} new argument already present')

    # Preserve the recovered artifact's formatting. Use the indentation of the
    # current final argument rather than assuming a fixed number of spaces.
    last_nonempty = ''
    for line in reversed(body.splitlines()):
        if line.strip():
            last_nonempty = line
            break
    if not last_nonempty:
        raise AssertionError(f'{label} empty argument list')
    indent = last_nonempty[:len(last_nonempty) - len(last_nonempty.lstrip())]

    core = body.rstrip()
    trailing = body[len(core):]
    new_body = core + ',\n' + indent + new_argument + trailing
    return s[:open_idx + 1] + new_body + s[close_idx:]

def capture_expected(text:str)->str:
    s=norm(text)
    for tok in (
        'IRIS_26486_FREEZE_BUFFER_AT_SHUTTER_NO_TOPUP_WAIT',
        'mMotionTopUpMinimumFrames = Math.min(mMotionTopUpTargetFrames, 2);',
        'if (iris26486ReadyNow < 2) {',
        'if (actualCount < 2) {',
        'neighborFallback=false',
    ):
        if tok not in s: raise AssertionError('CaptureController base anchor missing: '+tok)

    const='    private static final long MOTION_TOP_UP_POLL_MS = 25L;\n'
    s=one(s,const,const+
'''    /* IRIS_26520_FROZEN_METADATA_GRACE
     * A RAW Image may reach ImageReader a few callbacks before its exact SENSOR_TIMESTAMP
     * TotalCaptureResult is published. Freeze the already-present shutter-time ring and allow
     * only metadata to catch up; new normal RAWs remain inadmissible during this grace.
     */
    private static final long MOTION_26520_FROZEN_METADATA_GRACE_MS = 180L;
''','metadata grace constant')

    trigger='    private void triggerZslCapture() {\n'
    helper=r'''    /* IRIS_26520_FROZEN_METADATA_GRACE
     * This is NOT a RAW top-up. mMotionTopUpActive is false for the whole grace, so the
     * ImageReader closes newly arriving normal RAWs while exact Camera2 metadata may still
     * populate mZslResultMap for the shutter-frozen images already in mZslRingBuffer.
     */
    private void pollMotion26520FrozenMetadataGrace(
            long shotId,
            Motion26486ShortTicket shortTicket,
            boolean shortRequested,
            long graceStartMs) {
        if (!mZslCapturing || mMotionDiagnosticShotId != shotId) {
            return;
        }
        if (mMotionTopUpActive) {
            throw new IllegalStateException(
                    "26520 frozen metadata grace cannot run with normal top-up active");
        }

        int exactValid = countValidMotionFrames();
        long elapsed = android.os.SystemClock.elapsedRealtime() - graceStartMs;
        if (exactValid >= mMotionTopUpMinimumFrames) {
            com.particlesdevs.photoncamera.util.MotionTrace.state(
                    shotId,
                    "IRIS_26520_FROZEN_METADATA_GRACE_READY",
                    "valid=" + exactValid
                            + " minimum=" + mMotionTopUpMinimumFrames
                            + " elapsedMs=" + elapsed
                            + " requestedMaximum=" + mMotionTopUpTargetFrames
                            + " exactTimestampMetadata=true"
                            + " normalRingFrozen=true"
                            + " postShutterNormalAdmission=false"
                            + " shortNonBlocking=" + shortRequested);
            finalizeMotionZslCapture();
            return;
        }

        if (elapsed >= MOTION_26520_FROZEN_METADATA_GRACE_MS) {
            if (shortTicket != null) {
                shortTicket.slot.sealAndClose();
                clearMotion26490CaptureShortTicket(
                        shortTicket, "frozen_metadata_grace_timeout");
            }
            com.particlesdevs.photoncamera.util.MotionTrace.finish(
                    shotId,
                    "BUFFER_NOT_READY_FROZEN_METADATA_TIMEOUT",
                    "valid=" + exactValid
                            + " minimum=" + mMotionTopUpMinimumFrames
                            + " elapsedMs=" + elapsed
                            + " graceMs=" + MOTION_26520_FROZEN_METADATA_GRACE_MS
                            + " neighborFallback=false"
                            + " postShutterNormalAdmission=false");
            recoverMotionCaptureAfterEarlyExit(
                    "BUFFER_NOT_READY_FROZEN_METADATA_TIMEOUT",
                    "Motion metadata preparing");
            return;
        }

        if (mBackgroundHandler == null) {
            if (shortTicket != null) {
                shortTicket.slot.sealAndClose();
                clearMotion26490CaptureShortTicket(
                        shortTicket, "frozen_metadata_no_handler");
            }
            recoverMotionCaptureAfterEarlyExit(
                    "FROZEN_METADATA_NO_HANDLER", "Motion metadata unavailable");
            return;
        }
        mBackgroundHandler.postDelayed(
                () -> pollMotion26520FrozenMetadataGrace(
                        shotId, shortTicket, shortRequested, graceStartMs),
                MOTION_TOP_UP_POLL_MS);
    }

'''
    s=one(s,trigger,helper+trigger,'metadata grace helper')

    old=r'''        /* IRIS_26486_FREEZE_BUFFER_AT_SHUTTER_NO_TOPUP_WAIT
         * The slider is a maximum. Freeze the best qualifying exposure-energy
         * group already in the rolling ring; do not wait for replacement RAWs.
         */
        int iris26486ReadyNow = countValidMotionFrames();
        if (iris26486ReadyNow < 2) {
            mMotionTopUpActive = false;
            iris26486ShortTicket.slot.sealAndClose();
            clearMotion26490CaptureShortTicket(iris26486ShortTicket, "buffer_not_ready");
            com.particlesdevs.photoncamera.util.MotionTrace.finish(
                    mMotionDiagnosticShotId, "BUFFER_NOT_READY_NO_WAIT",
                    "valid=" + iris26486ReadyNow + " minimum=2 waitMs=0");
            recoverMotionCaptureAfterEarlyExit(
                    "BUFFER_NOT_READY_NO_WAIT", "Motion buffer preparing");
            return;
        }
        mMotionTopUpActive = false;
        com.particlesdevs.photoncamera.util.MotionTrace.state(
                mMotionDiagnosticShotId, "IRIS_26486_NO_TOP_UP_WAIT",
                "validAtPress=" + iris26486ReadyNow
                        + " requestedMaximum=" + mMotionTopUpTargetFrames
                        + " shortNonBlocking=" + iris26480ShortHighlightRequested
                        + " normalWaitMs=0");
        finalizeMotionZslCapture();
'''
    new=r'''        /* IRIS_26520_EXPLICIT_ONE_NORMAL_FRAME
         * The slider is a maximum. A requested value of one means one normal RAW is a valid
         * batch; it is not a fallback from a multi-frame request. Freeze the shutter-time ring
         * immediately. If RAW metadata is momentarily late, wait only for exact metadata on
         * those frozen images -- never for replacement/post-shutter normal RAWs.
         */
        int iris26486ReadyNow = countValidMotionFrames();
        mMotionTopUpActive = false;
        if (iris26486ReadyNow < mMotionTopUpMinimumFrames) {
            long iris26520GraceStartMs =
                    android.os.SystemClock.elapsedRealtime();
            com.particlesdevs.photoncamera.util.MotionTrace.state(
                    mMotionDiagnosticShotId,
                    "IRIS_26520_FROZEN_METADATA_GRACE_BEGIN",
                    "validAtPress=" + iris26486ReadyNow
                            + " minimum=" + mMotionTopUpMinimumFrames
                            + " requestedMaximum=" + mMotionTopUpTargetFrames
                            + " graceMs=" + MOTION_26520_FROZEN_METADATA_GRACE_MS
                            + " normalRingFrozen=true"
                            + " postShutterNormalAdmission=false"
                            + " exactTimestampMetadataRequired=true"
                            + " neighborFallback=false");
            if (mBackgroundHandler != null) {
                final long iris26520ShotId = mMotionDiagnosticShotId;
                mBackgroundHandler.postDelayed(
                        () -> pollMotion26520FrozenMetadataGrace(
                                iris26520ShotId,
                                iris26486ShortTicket,
                                iris26480ShortHighlightRequested,
                                iris26520GraceStartMs),
                        MOTION_TOP_UP_POLL_MS);
            } else {
                iris26486ShortTicket.slot.sealAndClose();
                clearMotion26490CaptureShortTicket(
                        iris26486ShortTicket, "frozen_metadata_no_handler");
                recoverMotionCaptureAfterEarlyExit(
                        "FROZEN_METADATA_NO_HANDLER",
                        "Motion metadata unavailable");
            }
            return;
        }
        com.particlesdevs.photoncamera.util.MotionTrace.state(
                mMotionDiagnosticShotId, "IRIS_26520_SHUTTER_FROZEN_BATCH_READY",
                "validAtPress=" + iris26486ReadyNow
                        + " minimum=" + mMotionTopUpMinimumFrames
                        + " requestedMaximum=" + mMotionTopUpTargetFrames
                        + " shortNonBlocking=" + iris26480ShortHighlightRequested
                        + " normalRingFrozen=true"
                        + " postShutterNormalAdmission=false"
                        + " normalWaitMs=0");
        finalizeMotionZslCapture();
'''
    s=one(s,old,new,'shutter frozen batch block')
    s=one(s,'        if (actualCount < 2) {\n',
          '        if (actualCount < mMotionTopUpMinimumFrames) {\n',
          'final equal-energy minimum')
    if 'if (iris26486ReadyNow < 2)' in s: raise AssertionError('hard-coded shutter two-frame minimum survived')
    if 'if (actualCount < 2)' in s: raise AssertionError('hard-coded final two-frame minimum survived')
    return s

def saver_expected(text:str)->str:
    s=norm(text)
    old=r'''        if (batch == null || batch.frames == null || batch.frames.size() < 2) {
            throw new IllegalStateException("26486 MotionBatch requires at least two normal RAW frames");
        }
'''
    new=r'''        /* IRIS_26520_EXPLICIT_ONE_NORMAL_FRAME
         * One normal RAW is valid only when capture explicitly admitted one. Multi-frame
         * requests still retain CaptureController's two-normal minimum and cannot silently
         * collapse to one here.
         */
        if (batch == null || batch.frames == null || batch.frames.isEmpty()) {
            throw new IllegalStateException("26520 MotionBatch requires at least one admitted normal RAW frame");
        }
'''
    return one(s,old,new,'DefaultSaver one-frame guard')

def merger_expected(text:str)->str:
    s=norm(text)
    field='        public final ByteBuffer highlightProvenance;\n'
    s=one(s,field,field+r'''        /* IRIS_26520_NORMAL_ONLY_FUSED_BAYER_DNG
         * RAW16 sensor-code mosaic derived from the normal-only Wronski Bayer accumulator
         * before Short/Long/Bento or any RGB/tone processing.
         */
        public final ByteBuffer stackedDngRaw16;
        public final int dngStackFrames;
''','Result DNG fields')
    old=r'''        Result(ByteBuffer raw, long referenceTimestamp, int inputFrames,
                float effectiveSupport, ByteBuffer highlightProvenance) {
            this.raw = raw;
            this.referenceTimestamp = referenceTimestamp;
            this.inputFrames = inputFrames;
            this.effectiveSupport = effectiveSupport;
            this.highlightProvenance = highlightProvenance;
        }
'''
    new=r'''        Result(ByteBuffer raw, long referenceTimestamp, int inputFrames,
                float effectiveSupport, ByteBuffer highlightProvenance,
                ByteBuffer stackedDngRaw16, int dngStackFrames) {
            this.raw = raw;
            this.referenceTimestamp = referenceTimestamp;
            this.inputFrames = inputFrames;
            this.effectiveSupport = effectiveSupport;
            this.highlightProvenance = highlightProvenance;
            this.stackedDngRaw16 = stackedDngRaw16;
            this.dngStackFrames = Math.max(0, dngStackFrames);
        }
'''
    s=one(s,old,new,'Result constructor')
    s=one(s,
          '        return new Result(output, referenceTimestamp, frames.size(), 1.0f, null);\n',
          '        return new Result(output, referenceTimestamp, frames.size(), 1.0f, null, null, 0);\n',
          'referenceFoundation result')
    return s

def cfa_expected(text:str)->str:
    s=norm(text)
    field='    private ByteBuffer highlightProvenanceOutput;\n'
    s=one(s,field,field+r'''    /* IRIS_26520_NORMAL_ONLY_FUSED_BAYER_DNG */
    private final boolean produceStackedDng;
    private ByteBuffer stackedDngRaw16Output;
''','CFA DNG fields')
    s=one(s,r'''            Parameters parameters,
            ImageFrame referenceFrame,
            MotionBatch.ShortHighlightSlot shortHighlightSlot) {
''',r'''            Parameters parameters,
            ImageFrame referenceFrame,
            MotionBatch.ShortHighlightSlot shortHighlightSlot,
            boolean produceStackedDng) {
''','CFA constructor signature')
    s=one(s,r'''        this.shortHighlightSlot = shortHighlightSlot;
        this.parameters = parameters;
''',r'''        this.shortHighlightSlot = shortHighlightSlot;
        this.produceStackedDng = produceStackedDng;
        this.parameters = parameters;
''','CFA constructor assignment')
    s=one(s,r'''            Parameters parameters,
            MotionBatch.ShortHighlightSlot shortHighlightSlot) {
''',r'''            Parameters parameters,
            MotionBatch.ShortHighlightSlot shortHighlightSlot,
            boolean produceStackedDng) {
''','reconstruct signature')
    s=one(s,r'''            script = new MotionV2CfaReconstruction(
                    size, ordered, referenceTimestamp, parameters, reference, shortHighlightSlot);
''',r'''            script = new MotionV2CfaReconstruction(
                    size, ordered, referenceTimestamp, parameters, reference,
                    shortHighlightSlot, produceStackedDng);
''','reconstruct constructor call')
    s=one(s,r'''            return new MotionV2Merger.Result(
                    script.output,
                    referenceTimestamp,
                    ordered.size(),
                    script.effectiveSupport,
                    script.highlightProvenanceOutput);
''',r'''            return new MotionV2Merger.Result(
                    script.output,
                    referenceTimestamp,
                    ordered.size(),
                    script.effectiveSupport,
                    script.highlightProvenanceOutput,
                    script.stackedDngRaw16Output,
                    script.stackedDngRaw16Output == null ? 0 : ordered.size());
''','reconstruct Result return')
    tex='        GLTexture result = null;\n'
    s=one(s,tex,tex+'        /* IRIS_26520_NORMAL_ONLY_FUSED_BAYER_DNG */\n        GLTexture iris26520DngRaw16Texture = null;\n',
          'DNG texture declaration')
    before='            /* IRIS_26494_PER_PHASE_HIGHLIGHT_PROVENANCE_OWNER\n'
    insert=r'''            /* IRIS_26520_NORMAL_ONLY_FUSED_BAYER_DNG
             * imageOutput here is the normalized normal-only Bayer accumulator. Queue an inverse
             * packed-CFA -> sensor RAW16 conversion now, before Short/Long/Bento can modify the
             * helper carrier. It shares the existing single GPU drain.
             */
            if (produceStackedDng) {
                if (!directBayer) {
                    throw new IllegalStateException(
                            "26520 stacked DNG requires standard Bayer Wronski path");
                }
                float[] iris26520DngBlack =
                        referenceFrame != null && referenceFrame.motionV2BlackLevelValid
                                ? referenceFrame.motionV2BlackLevel
                                : blackLevel;
                float iris26520DngWhite =
                        referenceFrame != null && referenceFrame.motionV2WhiteLevelValid
                                ? referenceFrame.motionV2WhiteLevel
                                : (float) parameters.whiteLevel;
                iris26520DngRaw16Texture = new GLTexture(
                        raw,
                        new GLFormat(GLFormat.DataType.UNSIGNED_16, 1),
                        null,
                        GL_NEAREST,
                        GL_CLAMP_TO_EDGE);
                glProg.setLayout(tile, tile, 1);
                glProg.useAssetProgram("motionv2/dng_cfa_to_raw16_26520", true);
                glProg.setVar("rawSize", raw);
                glProg.setVar("packedSize", rawHalf);
                glProg.setVar("blackLevel", iris26520DngBlack);
                glProg.setVar("whiteLevel", iris26520DngWhite);
                glProg.setTexture("fusedCfa", imageOutput);
                glProg.setTextureCompute("outRaw", iris26520DngRaw16Texture, true);
                glProg.computeAutoDeferred(raw, 1);
                Log.i(TAG, "IRIS_26520_DNG_FUSED_BAYER_QUEUED"
                        + " admittedNormalFrames=" + iris26489AdmittedFrames
                        + " contributedNormalFrames=" + iris26489ContributedFrames
                        + " normalOnly=true"
                        + " shortLongExcluded=true"
                        + " beforeHdrAux=true"
                        + " rgbReconstruction=false"
                        + " tone=false displayExposure=false denoise=false sharpening=false"
                        + " oneGpuDrain=true");
            }

'''
    s=one(s,before,insert+before,'DNG queue before HDR auxiliaries')
    drain='                iris26487GpuDrainMs = glProg.finishDeferredCompute("MotionV2 final image");\n'
    readback=drain+r'''                /* IRIS_26520_DNG_RAW16_READBACK
                 * The one normal-only DNG conversion was queued before HDR auxiliary recovery.
                 * Read it only after the existing single Motion GPU ownership drain.
                 */
                if (iris26520DngRaw16Texture != null) {
                    long iris26520DngReadbackStartNs = System.nanoTime();
                    try {
                        iris26520DngRaw16Texture.BufferLoad();
                        stackedDngRaw16Output =
                                iris26520DngRaw16Texture.textureBuffer(
                                        new GLFormat(GLFormat.DataType.UNSIGNED_16, 1),
                                        true);
                        stackedDngRaw16Output.position(0);
                    } finally {
                        iris26488ReleaseReadbackFramebuffer(iris26520DngRaw16Texture);
                    }
                    int iris26520ExpectedBytes = raw.x * raw.y * 2;
                    if (stackedDngRaw16Output == null
                            || stackedDngRaw16Output.capacity() < iris26520ExpectedBytes) {
                        throw new IllegalStateException(
                                "26520 stacked DNG RAW16 readback size mismatch");
                    }
                    Log.i(TAG, "IRIS_26520_DNG_RAW16_READY"
                            + " dngStackFrames=" + frameCount
                            + " bytes=" + stackedDngRaw16Output.capacity()
                            + " expectedBytes=" + iris26520ExpectedBytes
                            + " readbackMs="
                            + ((System.nanoTime() - iris26520DngReadbackStartNs) / 1000000L)
                            + " sensorCodeDomain=true"
                            + " sameNormalAccumulator=true"
                            + " shortLongExcluded=true");
                }
'''
    s=one(s,drain,readback,'DNG readback after one drain')
    cleanup='            iris26488ReleaseReadbackFramebuffer(iris26501ChromaGuideScratch);\n'
    s=one(s,cleanup,
          '            iris26488ReleaseReadbackFramebuffer(iris26520DngRaw16Texture);\n'
          '            if (iris26520DngRaw16Texture != null) iris26520DngRaw16Texture.close();\n'
          + cleanup,
          'DNG texture cleanup')
    return s

def hdrx_expected(text:str)->str:
    s=norm(text)
    old=r'''            /* IRIS_26480_DEFERRED_DNG_OUTPUT_V2 */
            iris26480DeferredDng = null;
            if (saveRAW >= 1) {
                if (images.get(0).buffer == null) throw new IllegalStateException("Motion V2 reference DNG buffer is null");
                if (saveRAW == 2) {
                    ByteBuffer immediate=images.get(0).buffer.duplicate(); immediate.position(0);
                    boolean saved=ImageSaver.Util.saveStackedRaw(dngFile,immediate,processingParameters);
                    processingEventsListener.notifyImageSavedStatus(saved,dngFile);
                    for(ImageFrame im:images)if(im!=null)im.close();
                    if(iris26480ShortHighlightFrame!=null){iris26480ShortHighlightFrame.close();iris26480ShortHighlightFrame=null;}
                    processingEventsListener.onProcessingFinished("Motion RAW Processing Finished");callback.onFinished();return;
                }
                ByteBuffer v=images.get(0).buffer.duplicate();v.position(0);
                iris26480DeferredDng=Allocator.allocateAndCopy(v.capacity(),v,0);iris26480DeferredDng.position(0);
                Log.d(TAG,"IRIS_26480_DEFERRED_DNG_CAPTURED bytes="+iris26480DeferredDng.capacity());
            }
'''
    s=one(s,old,r'''            /* IRIS_26520_REFERENCE_RAW_DNG_REMOVED
             * Motion DNG is no longer copied from images.get(0). The normal-only fused Bayer
             * accumulator later in MotionV2CfaReconstruction owns stacked DNG production.
             */
            iris26480DeferredDng = null;
''','remove reference-only Motion DNG')
    s=append_unique_call_argument(
            s,
            'MotionV2CfaReconstruction.reconstruct',
            [
                'new Point(width, height)',
                'images',
                'iris26363ReferenceTimestamp',
                'processingParameters',
                'mMotion26486ShortSlot',
            ],
            'saveRAW >= 1',
            'reconstruct DNG request')
    anchor=r'''            motionV2HighlightProvenance = iris26409V2.highlightProvenance;
            processingParameters.motionV2EffectiveSupport =
                    iris26409V2.effectiveSupport;
'''
    replacement=anchor+r'''            /* IRIS_26520_SHARED_NORMAL_BATCH_DNG
             * The DNG buffer came from the same normal-only accumulator fed by `images`.
             * Short/Long/Bento are separate auxiliary owners and never enter this RAW16 mosaic.
             */
            iris26480DeferredDng = iris26409V2.stackedDngRaw16;
            if (saveRAW >= 1 && iris26480DeferredDng == null) {
                throw new IllegalStateException(
                        "26520 stacked DNG requested but normal fused RAW16 is missing");
            }
            if (saveRAW >= 1
                    && iris26409V2.dngStackFrames != iris26409V2.inputFrames) {
                throw new IllegalStateException(
                        "26520 JPEG/DNG normal-frame population mismatch input="
                                + iris26409V2.inputFrames
                                + " dng=" + iris26409V2.dngStackFrames);
            }
            com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                    "IRIS_26520_SHARED_NORMAL_BATCH_DNG",
                    "requestedFrames=" + PhotonCamera.getSettings().frameCount
                            + " admittedNormalFrames=" + iris26409V2.inputFrames
                            + " jpegNormalCandidateFrames=" + iris26409V2.inputFrames
                            + " dngStackFrames=" + iris26409V2.dngStackFrames
                            + " effectiveSupport=" + iris26409V2.effectiveSupport
                            + " sameNormalBatch=true"
                            + " shortLongExcludedFromDng=true"
                            + " secondAlignmentPass=false"
                            + " pyramidMergeForDng=false");

            if (saveRAW == 2) {
                ByteBuffer iris26520RawOnly = iris26480DeferredDng;
                iris26480DeferredDng = null;
                iris26520RawOnly.position(0);
                boolean iris26520RawSaved = ImageSaver.Util.saveStackedRaw(
                        dngFile, iris26520RawOnly, processingParameters);
                processingEventsListener.notifyImageSavedStatus(
                        iris26520RawSaved, dngFile);
                try { Allocator.free(iris26520RawOnly); } catch (Throwable ignored) {}
                if (output != null) {
                    try { Allocator.free(output); } catch (Throwable ignored) {}
                    output = null;
                }
                if (motionV2HighlightProvenance != null) {
                    try { Allocator.free(motionV2HighlightProvenance); }
                    catch (Throwable ignored) {}
                    motionV2HighlightProvenance = null;
                }
                processingEventsListener.onProcessingFinished(
                        "Motion stacked RAW Processing Finished");
                callback.onFinished();
                return;
            }
'''
    s=one(s,anchor,replacement,'Hdrx shared normal DNG ownership')
    if 'Motion V2 reference DNG buffer is null' in s: raise AssertionError('reference-only Motion DNG path survived')
    if 'IRIS_26480_DEFERRED_DNG_CAPTURED bytes=' in s: raise AssertionError('reference DNG copy survived')
    return s

def expected_map(root:Path):
    out={}
    for rel,fn in ((CAPTURE,capture_expected),(SAVER,saver_expected),(HDRX,hdrx_expected),(CFA,cfa_expected),(MERGER,merger_expected)):
        p=root/rel
        if not p.is_file(): raise AssertionError('missing base runtime file '+rel)
        out[rel]=fn(p.read_text())
    if (root/SHADER).exists(): raise AssertionError('26520 DNG shader unexpectedly already exists')
    out[SHADER]=DNG_SHADER
    return out

def patch_text(root:Path, expected:dict[str,str])->str:
    chunks=[]
    for rel in sorted(expected):
        p=root/rel
        old=norm(p.read_text()) if p.exists() else ''
        new=expected[rel]
        if old==new: raise AssertionError('empty transform '+rel)
        chunks.append(''.join(difflib.unified_diff(
            old.splitlines(True),new.splitlines(True),
            fromfile=('a/'+rel if p.exists() else '/dev/null'),tofile='b/'+rel)))
    return ''.join(chunks)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('root',type=Path)
    ap.add_argument('--patch-out',required=True,type=Path)
    ap.add_argument('--patch-sha-out',required=True,type=Path)
    ns=ap.parse_args()
    base=ns.root.resolve()
    expected=expected_map(base)
    diff=patch_text(base,expected)
    if not diff: raise AssertionError('empty 26520 runtime patch')
    ns.patch_out.parent.mkdir(parents=True,exist_ok=True)
    ns.patch_out.write_text(diff)
    digest=hashlib.sha256(ns.patch_out.read_bytes()).hexdigest()
    ns.patch_sha_out.write_text(f'{digest}  {ns.patch_out.name}\n')
    # Patch exists before runtime writes.
    for rel,new in expected.items():
        p=base/rel
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(new)
    print('PASS: 26520 rollback patch existed before six-path runtime write')

if __name__=='__main__':
    main()
