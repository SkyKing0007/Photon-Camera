#!/usr/bin/env python3
from __future__ import annotations
import argparse, difflib, hashlib, re
from pathlib import Path

CAPTURE='app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java'
SAVER='app/src/main/java/com/particlesdevs/photoncamera/processing/DefaultSaver.java'
HDRX='app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java'
MERGER='app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2Merger.java'
BRIDGE='app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt'
FUSION='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt'
STACK='app/src/main/java/com/hinnka/mycamera/processor/GlesMgc1271ReleasedSpatialStacker.kt'
CONTRACTS='app/src/main/java/com/hinnka/mycamera/processor/RawStackContracts.kt'
CHANGED={CAPTURE,SAVER,HDRX,MERGER,BRIDGE,FUSION,STACK,CONTRACTS}

def norm(s:str)->str:
    return s.replace('\r\n','\n').replace('\r','\n')

def one(s:str, old:str, new:str, label:str)->str:
    n=s.count(old)
    if n != 1:
        raise AssertionError(f'{label} anchor count={n} expected=1')
    return s.replace(old,new,1)

def append_unique_call_argument(s:str, function_name:str, required_tokens:list[str], new_argument:str, label:str)->str:
    pat=re.compile(re.escape(function_name)+r'\s*\(')
    ms=list(pat.finditer(s))
    if len(ms)!=1:
        raise AssertionError(f'{label} call count={len(ms)} expected=1')
    m=ms[0]; open_idx=s.find('(',m.start(),m.end()+1)
    depth=0; quote=None; esc=False; close=-1
    for i in range(open_idx,len(s)):
        ch=s[i]
        if quote is not None:
            if esc: esc=False
            elif ch=='\\': esc=True
            elif ch==quote: quote=None
            continue
        if ch in ('"',"'"): quote=ch
        elif ch=='(': depth+=1
        elif ch==')':
            depth-=1
            if depth==0: close=i; break
    if close<0: raise AssertionError(label+' unterminated call')
    body=s[open_idx+1:close]
    for tok in required_tokens:
        if tok not in body: raise AssertionError(f'{label} missing semantic token {tok}')
    if new_argument in body: raise AssertionError(f'{label} new arg already present')
    lines=[x for x in body.splitlines() if x.strip()]
    if not lines: raise AssertionError(label+' empty call')
    last=lines[-1]; indent=last[:len(last)-len(last.lstrip())]
    core=body.rstrip(); trailing=body[len(core):]
    return s[:open_idx+1]+core+',\n'+indent+new_argument+trailing+s[close:]

def capture_expected(text:str)->str:
    s=norm(text)
    for tok in ('IRIS_26486_FREEZE_BUFFER_AT_SHUTTER_NO_TOPUP_WAIT','mMotionTopUpMinimumFrames = Math.min(mMotionTopUpTargetFrames, 2);','if (iris26486ReadyNow < 2) {','if (actualCount < 2) {','neighborFallback=false'):
        if tok not in s: raise AssertionError('CaptureController base anchor missing: '+tok)
    const='    private static final long MOTION_TOP_UP_POLL_MS = 25L;\n'
    s=one(s,const,const+'''    /* IRIS_26520_V4_FROZEN_METADATA_GRACE
     * RAW can arrive before its exact SENSOR_TIMESTAMP TotalCaptureResult. Freeze the already
     * present shutter-time RAW population and allow metadata only to catch up. New normal RAWs
     * remain inadmissible for the entire grace window.
     */
    private static final long MOTION_26520_FROZEN_METADATA_GRACE_MS = 180L;
''','metadata grace constant')
    trigger='    private void triggerZslCapture() {\n'
    helper='''    /* IRIS_26520_V4_FROZEN_METADATA_GRACE
     * This is metadata-only grace, never a post-shutter RAW top-up.
     */
    private void pollMotion26520FrozenMetadataGrace(
            long shotId,
            Motion26486ShortTicket shortTicket,
            boolean shortRequested,
            long graceStartMs) {
        if (!mZslCapturing || mMotionDiagnosticShotId != shotId) return;
        if (mMotionTopUpActive) {
            throw new IllegalStateException("26520 frozen metadata grace cannot run with normal top-up active");
        }
        int exactValid = countValidMotionFrames();
        long elapsed = android.os.SystemClock.elapsedRealtime() - graceStartMs;
        if (exactValid >= mMotionTopUpMinimumFrames) {
            com.particlesdevs.photoncamera.util.MotionTrace.state(
                    shotId, "IRIS_26520_V4_FROZEN_METADATA_GRACE_READY",
                    "valid=" + exactValid + " minimum=" + mMotionTopUpMinimumFrames
                            + " elapsedMs=" + elapsed + " requestedMaximum=" + mMotionTopUpTargetFrames
                            + " exactTimestampMetadata=true normalRingFrozen=true"
                            + " postShutterNormalAdmission=false shortNonBlocking=" + shortRequested);
            finalizeMotionZslCapture();
            return;
        }
        if (elapsed >= MOTION_26520_FROZEN_METADATA_GRACE_MS) {
            if (shortTicket != null) {
                shortTicket.slot.sealAndClose();
                clearMotion26490CaptureShortTicket(shortTicket, "frozen_metadata_grace_timeout");
            }
            com.particlesdevs.photoncamera.util.MotionTrace.finish(
                    shotId, "BUFFER_NOT_READY_FROZEN_METADATA_TIMEOUT",
                    "valid=" + exactValid + " minimum=" + mMotionTopUpMinimumFrames
                            + " elapsedMs=" + elapsed + " graceMs=" + MOTION_26520_FROZEN_METADATA_GRACE_MS
                            + " neighborFallback=false postShutterNormalAdmission=false");
            recoverMotionCaptureAfterEarlyExit("BUFFER_NOT_READY_FROZEN_METADATA_TIMEOUT", "Motion metadata preparing");
            return;
        }
        if (mBackgroundHandler == null) {
            if (shortTicket != null) {
                shortTicket.slot.sealAndClose();
                clearMotion26490CaptureShortTicket(shortTicket, "frozen_metadata_no_handler");
            }
            recoverMotionCaptureAfterEarlyExit("FROZEN_METADATA_NO_HANDLER", "Motion metadata unavailable");
            return;
        }
        mBackgroundHandler.postDelayed(
                () -> pollMotion26520FrozenMetadataGrace(shotId, shortTicket, shortRequested, graceStartMs),
                MOTION_TOP_UP_POLL_MS);
    }

'''
    s=one(s,trigger,helper+trigger,'metadata grace helper')
    old='''        /* IRIS_26486_FREEZE_BUFFER_AT_SHUTTER_NO_TOPUP_WAIT
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
    new='''        /* IRIS_26520_V4_EXPLICIT_ONE_NORMAL_FRAME
         * Slider value 1 is an explicit one-normal capture. Values >=2 retain a two-normal
         * admission floor, while the slider remains a maximum and the shutter-time ring stays
         * frozen. Metadata may catch up; replacement normal RAWs may not.
         */
        int iris26486ReadyNow = countValidMotionFrames();
        mMotionTopUpActive = false;
        if (iris26486ReadyNow < mMotionTopUpMinimumFrames) {
            long iris26520GraceStartMs = android.os.SystemClock.elapsedRealtime();
            com.particlesdevs.photoncamera.util.MotionTrace.state(
                    mMotionDiagnosticShotId, "IRIS_26520_V4_FROZEN_METADATA_GRACE_BEGIN",
                    "validAtPress=" + iris26486ReadyNow + " minimum=" + mMotionTopUpMinimumFrames
                            + " requestedMaximum=" + mMotionTopUpTargetFrames
                            + " graceMs=" + MOTION_26520_FROZEN_METADATA_GRACE_MS
                            + " normalRingFrozen=true postShutterNormalAdmission=false"
                            + " exactTimestampMetadataRequired=true neighborFallback=false");
            if (mBackgroundHandler != null) {
                final long iris26520ShotId = mMotionDiagnosticShotId;
                mBackgroundHandler.postDelayed(
                        () -> pollMotion26520FrozenMetadataGrace(
                                iris26520ShotId, iris26486ShortTicket,
                                iris26480ShortHighlightRequested, iris26520GraceStartMs),
                        MOTION_TOP_UP_POLL_MS);
            } else {
                iris26486ShortTicket.slot.sealAndClose();
                clearMotion26490CaptureShortTicket(iris26486ShortTicket, "frozen_metadata_no_handler");
                recoverMotionCaptureAfterEarlyExit("FROZEN_METADATA_NO_HANDLER", "Motion metadata unavailable");
            }
            return;
        }
        com.particlesdevs.photoncamera.util.MotionTrace.state(
                mMotionDiagnosticShotId, "IRIS_26520_V4_SHUTTER_FROZEN_BATCH_READY",
                "validAtPress=" + iris26486ReadyNow + " minimum=" + mMotionTopUpMinimumFrames
                        + " requestedMaximum=" + mMotionTopUpTargetFrames
                        + " shortNonBlocking=" + iris26480ShortHighlightRequested
                        + " normalRingFrozen=true postShutterNormalAdmission=false normalWaitMs=0");
        finalizeMotionZslCapture();
'''
    s=one(s,old,new,'shutter frozen batch block')
    s=one(s,'        if (actualCount < 2) {\n','        if (actualCount < mMotionTopUpMinimumFrames) {\n','final equal-energy minimum')
    if 'if (iris26486ReadyNow < 2)' in s or 'if (actualCount < 2)' in s:
        raise AssertionError('hard-coded two-frame gate survived')
    return s

def saver_expected(text:str)->str:
    s=norm(text)
    old='''        if (batch == null || batch.frames == null || batch.frames.size() < 2) {
            throw new IllegalStateException("26486 MotionBatch requires at least two normal RAW frames");
        }
'''
    new='''        /* IRIS_26520_V4_EXPLICIT_ONE_NORMAL_FRAME */
        if (batch == null || batch.frames == null || batch.frames.isEmpty()) {
            throw new IllegalStateException("26520 MotionBatch requires at least one admitted normal RAW frame");
        }
'''
    return one(s,old,new,'DefaultSaver one-frame guard')

def merger_expected(text:str)->str:
    s=norm(text)
    field='        public final ByteBuffer highlightProvenance;\n'
    s=one(s,field,field+'''        /* IRIS_26520_V4_LIVE_MGC_NORMAL_DNG_SIDECAR */
        public final ByteBuffer stackedDngRaw16;
        public final int dngStackFrames;
''','Result DNG fields')
    old='''        Result(ByteBuffer raw, long referenceTimestamp, int inputFrames,
                float effectiveSupport, ByteBuffer highlightProvenance) {
            this.raw = raw;
            this.referenceTimestamp = referenceTimestamp;
            this.inputFrames = inputFrames;
            this.effectiveSupport = effectiveSupport;
            this.highlightProvenance = highlightProvenance;
        }
'''
    new='''        Result(ByteBuffer raw, long referenceTimestamp, int inputFrames,
                float effectiveSupport, ByteBuffer highlightProvenance) {
            this(raw, referenceTimestamp, inputFrames, effectiveSupport,
                    highlightProvenance, null, 0);
        }

        Result(ByteBuffer raw, long referenceTimestamp, int inputFrames,
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
    return one(s,old,new,'Result constructor overload')

def contracts_expected(text:str)->str:
    s=norm(text)
    anchor='    val mgcSpatialReferenceOnlyDiagnostic: Boolean = false,\n)\n'
    repl='''    val mgcSpatialReferenceOnlyDiagnostic: Boolean = false,
    /* IRIS_26520_V4_LIVE_MGC_NORMAL_DNG_SIDECAR */
    val normalStackedDngRaw16: ByteBuffer? = null,
    val normalStackedDngFrameCount: Int = 0,
)
'''
    return one(s,anchor,repl,'RawStackResult DNG ABI')

def fusion_expected(text:str)->str:
    s=norm(text)
    marker='IRIS_26517_RELEASED_1271_SPATIAL_RGB_OWNER'
    if s.count(marker)<1: raise AssertionError('released c4ff route marker missing')
    ctor='''    private val exportGpuLinearRgbSource: Boolean,
    private val gpuLinearRgbStorage: GpuLinearRgbStorage,
) {
'''
    s=one(s,ctor,'''    private val exportGpuLinearRgbSource: Boolean,
    private val gpuLinearRgbStorage: GpuLinearRgbStorage,
    /* IRIS_26520_V4_LIVE_MGC_NORMAL_DNG_REQUEST */
    private val exportNormalStackedDng: Boolean = false,
) {
''','Fusion constructor DNG request')
    a=s.find(marker); b=s.find('        return GlesMgcRawSpatialStacker(',a)
    if b<0: raise AssertionError('Fusion fallback boundary missing')
    active=s[a:b]
    call='''                gpuLinearRgbStorage = gpuLinearRgbStorage,
            ).processFrames(scheduledFrames)
'''
    active=one(active,call,'''                gpuLinearRgbStorage = gpuLinearRgbStorage,
                exportNormalStackedDng = exportNormalStackedDng,
            ).processFrames(scheduledFrames)
''','released route DNG forward')
    return s[:a]+active+s[b:]

def stack_expected(text:str)->str:
    s=norm(text)
    for tok in ('internal class GlesMgc1271ReleasedSpatialStacker(','IRIS_26518_RELEASED_1271_RESULT_ABI_SNR_BRIDGE','private val guideWidth = max(1, width / 4)','val accumulatorColor = if (outputMode == MgcSpatialOutputMode.BAYER)','val mergeWeight = if (identityTemporalWeights)','val bayer16 = renderBayer16(','private fun renderBayer16(','private fun readBayer16('):
        if tok not in s: raise AssertionError('released stacker anchor missing: '+tok)
    ctor='''    private val exportGpuLinearRgbSource: Boolean,
    private val gpuLinearRgbStorage: GpuLinearRgbStorage = GpuLinearRgbStorage.RGBA16UI,
) {
'''
    s=one(s,ctor,'''    private val exportGpuLinearRgbSource: Boolean,
    private val gpuLinearRgbStorage: GpuLinearRgbStorage = GpuLinearRgbStorage.RGBA16UI,
    /* IRIS_26520_V4_LIVE_MGC_NORMAL_DNG_REQUEST */
    private val exportNormalStackedDng: Boolean = false,
) {
''','released stacker constructor request')
    decl='''        var cpuOutput: ByteBuffer? = null
        var returned = false
'''
    s=one(s,decl,'''        var cpuOutput: ByteBuffer? = null
        /* IRIS_26520_V4_LIVE_MGC_NORMAL_DNG_SIDECAR */
        var normalStackedDngRaw16: ByteBuffer? = null
        var normalStackedDngFrameCount = 0
        var returned = false
''','DNG output ownership declarations')
    accumulator='''            val accumulatorColor = if (outputMode == MgcSpatialOutputMode.BAYER) {
                createTexture(
                    width,
                    height,
                    GLES30.GL_RGBA16F,
                    GLES30.GL_NEAREST,
                )
            } else {
                0
            }
'''
    s=one(s,accumulator,accumulator+'''            /* IRIS_26520_V4_LIVE_MGC_NORMAL_DNG_SIDECAR */
            val normalDngAccumulator = if (exportNormalStackedDng) {
                createTexture(width, height, GLES30.GL_RGBA16F, GLES30.GL_NEAREST)
            } else {
                0
            }
''','normal DNG accumulator allocation')
    ref='''            if (outputMode == MgcSpatialOutputMode.BAYER) {
                clearAccumulator(accumulatorColor)
            }
            if (bentoAccepted) {
'''
    s=one(s,ref,'''            if (outputMode == MgcSpatialOutputMode.BAYER) {
                clearAccumulator(accumulatorColor)
            }
            /* IRIS_26520_V4_NORMAL_ONLY_REFERENCE_CONTRIBUTION */
            if (exportNormalStackedDng) {
                check(normalDngAccumulator != 0)
                clearAccumulator(normalDngAccumulator)
                renderMerge(
                    rawTexture = referenceRaw,
                    bayerAlignmentTexture = zeroFlow,
                    weightTexture = identityWeight,
                    linearKernelMaskTexture = zeroLinearKernelMask,
                    calibration = referenceCalibration,
                    accumulatorColor = normalDngAccumulator,
                    useFrameWeight = false,
                )
                normalStackedDngFrameCount = 1
            }
            if (bentoAccepted) {
''','normal DNG reference contribution')
    temp='''                    val postPrepareStartNs = System.nanoTime()
                    val mergeWeight = if (identityTemporalWeights) {
'''
    s=one(s,temp,'''                    val postPrepareStartNs = System.nanoTime()
                    /* IRIS_26520_V4_NORMAL_ONLY_TEMPORAL_CONTRIBUTION */
                    if (exportNormalStackedDng && frame.role == RawBurstFrameRole.NORMAL) {
                        renderMerge(
                            rawTexture = temporalRaw,
                            bayerAlignmentTexture = prepared.bayerAlignmentTexture,
                            weightTexture = prepared.weightTexture,
                            linearKernelMaskTexture = zeroLinearKernelMask,
                            calibration = prepared.calibration,
                            accumulatorColor = normalDngAccumulator,
                            useFrameWeight = true,
                        )
                        normalStackedDngFrameCount += 1
                    }
                    val mergeWeight = if (identityTemporalWeights) {
''','normal DNG temporal contribution')
    fin='            val readyStrengthCapture = strengthCapture?.also { capture ->\n'
    block='''            /* IRIS_26520_V4_NORMAL_ONLY_DNG_FINALIZE */
            if (exportNormalStackedDng) {
                val expectedNormalFrames = frames.count { it.role == RawBurstFrameRole.NORMAL }
                check(normalStackedDngFrameCount == expectedNormalFrames) {
                    "26520 normal DNG contribution mismatch contributed=$normalStackedDngFrameCount expected=$expectedNormalFrames"
                }
                val normalizedTexture = renderBayer16(
                    accumulator = normalDngAccumulator,
                    outputExposureScale = 1f,
                )
                val normalizedRaw16 = readBayer16(normalizedTexture)
                try {
                    normalStackedDngRaw16 = convertNormalizedBayer16ToSensorCode(normalizedRaw16)
                } finally {
                    LargeDirectBuffer.free(normalizedRaw16)
                }
                PLog.i(TAG, "IRIS_26520_V4_NORMAL_ONLY_DNG_READY normalFrames=$normalStackedDngFrameCount " +
                    "shortExcluded=true longExcluded=true bentoExcluded=true referenceWeight=identity " +
                    "temporalWeight=preHdrRewrite linearKernelMask=zero outputExposureScale=1.0 " +
                    "secondAlignmentPass=false sensorCodeDomain=true")
            }

'''
    s=one(s,fin,block+fin,'normal DNG finalization')
    result='''                mgcSpatialReferenceOnlyDiagnostic = referenceOnly,
            )
'''
    s=one(s,result,'''                mgcSpatialReferenceOnlyDiagnostic = referenceOnly,
                normalStackedDngRaw16 = normalStackedDngRaw16,
                normalStackedDngFrameCount = normalStackedDngFrameCount,
            )
''','RawStackResult DNG output')
    fail='''                LargeDirectBuffer.free(cpuOutput)
                if (exportedBayerTexture != 0) {
'''
    s=one(s,fail,'''                LargeDirectBuffer.free(cpuOutput)
                LargeDirectBuffer.free(normalStackedDngRaw16)
                if (exportedBayerTexture != 0) {
''','failed output DNG cleanup')
    method='    private fun initPrograms(\n'
    helper='''    /* IRIS_26520_V4_SENSOR_CODE_RESTORE */
    private fun convertNormalizedBayer16ToSensorCode(normalized: ByteBuffer): ByteBuffer {
        val byteCount = width.toLong() * height.toLong() * Short.SIZE_BYTES
        require(byteCount in 1..Int.MAX_VALUE.toLong())
        val output = LargeDirectBuffer.allocate(byteCount, "26520 normal-only stacked DNG sensor code")
            ?.order(ByteOrder.nativeOrder()) ?: error("Unable to allocate 26520 stacked DNG output")
        val src = normalized.duplicate().order(ByteOrder.nativeOrder()).asShortBuffer()
        val dst = output.asShortBuffer()
        require(src.remaining() >= width * height)
        for (y in 0 until height) {
            for (x in 0 until width) {
                val phase = ((y and 1) shl 1) + (x and 1)
                val channel = canonicalChannelAtPhase(phase)
                val black = canonicalBlackLevel[channel]
                val span = (sensorWhiteLevel.toFloat() - black).coerceAtLeast(1f)
                val normalizedValue = (src.get().toInt() and 0xffff) / 65535f
                val sensorCode = (normalizedValue * span + black + 0.5f).toInt().coerceIn(0, 65535)
                dst.put(sensorCode.toShort())
            }
        }
        output.position(0)
        output.limit(width * height * Short.SIZE_BYTES)
        return output
    }

'''
    s=one(s,method,helper+method,'sensor code restore helper')
    return s

def bridge_expected(text:str)->str:
    s=norm(text)
    for tok in ('IRIS_26512_MGC1271_SPATIAL_RGB_PARITY_OWNER','outputMode = MgcSpatialOutputMode.RGB','mergeMethod = MgcMergeMethod.SPATIAL_RGB','GlesMgcRawFusion(','return MotionV2Merger.Result('):
        if tok not in s: raise AssertionError('bridge anchor missing: '+tok)
    sig='''        parameters: Parameters,
        shortSlot: MotionBatch.ShortHighlightSlot?,
    ): MotionV2Merger.Result {
'''
    s=one(s,sig,'''        parameters: Parameters,
        shortSlot: MotionBatch.ShortHighlightSlot?,
        /* IRIS_26520_V4_LIVE_MGC_NORMAL_DNG_REQUEST */
        produceNormalStackedDng: Boolean,
    ): MotionV2Merger.Result {
''','bridge signature DNG request')
    fc='''                gpuLinearRgbStorage = GpuLinearRgbStorage.RGBA16F,
            )
'''
    s=one(s,fc,'''                gpuLinearRgbStorage = GpuLinearRgbStorage.RGBA16F,
                exportNormalStackedDng = produceNormalStackedDng,
            )
''','bridge Fusion DNG request')
    pre='            PLog.i(TAG, "IRIS_26512_MGC1271_PARITY_VALID " +\n'
    own='''            /* IRIS_26520_V4_LIVE_MGC_NORMAL_DNG_BRIDGE */
            if (produceNormalStackedDng) {
                requireParity(stacked.normalStackedDngRaw16 != null, "requested normal stacked DNG buffer is missing")
                requireParity(stacked.normalStackedDngFrameCount == inputImages.size,
                    "normal stacked DNG population=${stacked.normalStackedDngFrameCount} normals=${inputImages.size}")
            } else {
                requireParity(stacked.normalStackedDngRaw16 == null && stacked.normalStackedDngFrameCount == 0,
                    "DNG sidecar produced without request")
            }

'''
    s=one(s,pre,own+pre,'bridge sidecar contract')
    ret='''            return MotionV2Merger.Result(
                output,
                mgcBase.timestamp,
                frames.size,
                stacked.mergedFrameCount.toFloat(),
                null,
            )
'''
    s=one(s,ret,'''            return MotionV2Merger.Result(
                output,
                mgcBase.timestamp,
                frames.size,
                stacked.mergedFrameCount.toFloat(),
                null,
                stacked.normalStackedDngRaw16,
                stacked.normalStackedDngFrameCount,
            )
''','bridge Result sidecar return')
    return s

def hdrx_expected(text:str)->str:
    s=norm(text)
    if 'PhotonMotionMgc1271Bridge.reconstruct' not in s: raise AssertionError('active Photon MGC bridge call missing')
    old='''            /* IRIS_26480_DEFERRED_DNG_OUTPUT_V2 */
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
    s=one(s,old,'''            /* IRIS_26520_V4_REFERENCE_ONLY_DNG_REMOVED */
            iris26480DeferredDng = null;
''','remove reference-only DNG')
    decl='            MotionV2Merger.Result iris26409V2 =\n'
    s=one(s,decl,'            final int iris26520ExpectedNormalFrames = images.size();\n'+decl,'normal population snapshot')
    s=append_unique_call_argument(s,'PhotonMotionMgc1271Bridge.reconstruct',['new Point(width, height)','images','iris26363ReferenceTimestamp','processingParameters','mMotion26486ShortSlot'],'saveRAW >= 1','active bridge DNG request')
    anchor='''            motionV2HighlightProvenance = iris26409V2.highlightProvenance;
            processingParameters.motionV2EffectiveSupport =
                    iris26409V2.effectiveSupport;
'''
    replacement=anchor+'''            /* IRIS_26520_V4_SHARED_NORMAL_BATCH_DNG */
            iris26480DeferredDng = iris26409V2.stackedDngRaw16;
            if (saveRAW >= 1 && iris26480DeferredDng == null) {
                throw new IllegalStateException("26520 stacked DNG requested but live MGC sidecar is missing");
            }
            if (saveRAW >= 1 && iris26409V2.dngStackFrames != iris26520ExpectedNormalFrames) {
                throw new IllegalStateException("26520 JPEG-normal/DNG-normal population mismatch admittedNormal="
                        + iris26520ExpectedNormalFrames + " dng=" + iris26409V2.dngStackFrames);
            }
            com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                    "IRIS_26520_V4_SHARED_NORMAL_BATCH_DNG",
                    "requestedFrames=" + PhotonCamera.getSettings().frameCount
                            + " admittedNormalFrames=" + iris26520ExpectedNormalFrames
                            + " dngStackFrames=" + iris26409V2.dngStackFrames
                            + " bridgeTotalScheduledFrames=" + iris26409V2.inputFrames
                            + " effectiveSupport=" + iris26409V2.effectiveSupport
                            + " sameAdmittedNormalPopulation=true shortLongBentoExcludedFromDng=true"
                            + " secondAlignmentPass=false c4ffRgbOwnerUnchanged=true");
            if (saveRAW == 2) {
                ByteBuffer iris26520RawOnly = iris26480DeferredDng;
                iris26480DeferredDng = null;
                iris26520RawOnly.position(0);
                boolean iris26520RawSaved = ImageSaver.Util.saveStackedRaw(dngFile, iris26520RawOnly, processingParameters);
                processingEventsListener.notifyImageSavedStatus(iris26520RawSaved, dngFile);
                try { Allocator.free(iris26520RawOnly); } catch (Throwable ignored) {}
                if (output != null) { try { Allocator.free(output); } catch (Throwable ignored) {} output = null; }
                if (motionV2HighlightProvenance != null) {
                    try { Allocator.free(motionV2HighlightProvenance); } catch (Throwable ignored) {}
                    motionV2HighlightProvenance = null;
                }
                processingEventsListener.onProcessingFinished("Motion stacked RAW Processing Finished");
                callback.onFinished();
                return;
            }
'''
    s=one(s,anchor,replacement,'Hdrx live sidecar ownership')
    if re.search(r'\bMotionV2CfaReconstruction\.reconstruct\s*\(',s):
        raise AssertionError('legacy MotionV2CfaReconstruction active call survived in Hdrx')
    return s

def expected_map(root:Path)->dict[str,str]:
    funcs={CAPTURE:capture_expected,SAVER:saver_expected,HDRX:hdrx_expected,MERGER:merger_expected,BRIDGE:bridge_expected,FUSION:fusion_expected,STACK:stack_expected,CONTRACTS:contracts_expected}
    out={}
    for rel,fn in funcs.items():
        path=root/rel
        if not path.is_file(): raise AssertionError('missing successful-26519 runtime path '+rel)
        out[rel]=fn(path.read_text())
    return out

def patch_text(root:Path, expected:dict[str,str])->str:
    chunks=[]
    for rel in sorted(expected):
        path=root/rel; old=norm(path.read_text()); new=expected[rel]
        if old==new: raise AssertionError('empty transform '+rel)
        chunks.append(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/'+rel,tofile='b/'+rel)))
    return ''.join(chunks)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('root',type=Path); ap.add_argument('--patch-out',type=Path); ap.add_argument('--patch-sha-out',type=Path); ap.add_argument('--check-only',action='store_true'); ns=ap.parse_args()
    base=ns.root.resolve(); expected=expected_map(base)
    if ns.check_only:
        print('PASS: 26520 V4 complete live-MGC transform resolves in memory')
        print('PASS: active owner is PhotonMotionMgc1271Bridge -> released c4ff Spatial RGB')
        print('PASS: DNG is optional NORMAL-only sidecar; no legacy CFA owner/shader')
        return
    if ns.patch_out is None or ns.patch_sha_out is None: raise SystemExit('--patch-out and --patch-sha-out required unless --check-only')
    diff=patch_text(base,expected)
    if not diff: raise AssertionError('empty 26520 V4 runtime patch')
    ns.patch_out.parent.mkdir(parents=True,exist_ok=True); ns.patch_out.write_text(diff)
    digest=hashlib.sha256(ns.patch_out.read_bytes()).hexdigest(); ns.patch_sha_out.write_text(f'{digest}  {ns.patch_out.name}\n')
    for rel,new in expected.items():
        path=base/rel; path.parent.mkdir(parents=True,exist_ok=True); path.write_text(new)
    print('PASS: 26520 V4 rollback patch existed before eight-path runtime write')

if __name__=='__main__': main()
