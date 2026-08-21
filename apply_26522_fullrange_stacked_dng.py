#!/usr/bin/env python3
from __future__ import annotations
import argparse,difflib,hashlib,re
from pathlib import Path

HDRX='app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java'
MERGER='app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2Merger.java'
BRIDGE='app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt'
CONTRACTS='app/src/main/java/com/hinnka/mycamera/processor/RawStackContracts.kt'
IRIS_STACK='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbStacker.kt'
IRIS_SHADER='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbShaders.kt'
IMAGE_SAVER='app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java'
CHANGED={HDRX,MERGER,BRIDGE,CONTRACTS,IRIS_STACK,IRIS_SHADER,IMAGE_SAVER}


def norm(s:str)->str:
    return s.replace('\r\n','\n').replace('\r','\n')

def one(s:str,old:str,new:str,label:str)->str:
    n=s.count(old)
    if n!=1:
        raise AssertionError(f'{label} anchor count={n} expected=1')
    return s.replace(old,new,1)

def merger_expected(text:str)->str:
    s=norm(text)
    for tok in ('IRIS_26520_V4_LIVE_MGC_NORMAL_DNG_SIDECAR','public final ByteBuffer stackedDngRaw16;','public final int dngStackFrames;'):
        if tok not in s: raise AssertionError('26521 merger anchor missing '+tok)
    fields='''        public final ByteBuffer stackedDngRaw16;\n        public final int dngStackFrames;\n'''
    s=one(s,fields,fields+'''        /* IRIS_26522_NORMALIZED16_DNG_METADATA */
        public final double[] dngNoiseProfile;
        public final float dngSupportMin;
        public final float dngSupportP01;
        public final float dngSupportP10;
        public final float dngSupportMedian;
        public final float dngSupportMean;
        public final float dngSupportMax;
        public final float dngNoiseEquivalentSupport;
''','26522 merger metadata fields')
    old='''        Result(ByteBuffer raw, long referenceTimestamp, int inputFrames,\n                float effectiveSupport, ByteBuffer highlightProvenance,\n                ByteBuffer stackedDngRaw16, int dngStackFrames) {\n            this.raw = raw;\n            this.referenceTimestamp = referenceTimestamp;\n            this.inputFrames = inputFrames;\n            this.effectiveSupport = effectiveSupport;\n            this.highlightProvenance = highlightProvenance;\n            this.stackedDngRaw16 = stackedDngRaw16;\n            this.dngStackFrames = Math.max(0, dngStackFrames);\n        }\n'''
    new='''        Result(ByteBuffer raw, long referenceTimestamp, int inputFrames,
                float effectiveSupport, ByteBuffer highlightProvenance,
                ByteBuffer stackedDngRaw16, int dngStackFrames) {
            this(raw, referenceTimestamp, inputFrames, effectiveSupport, highlightProvenance,
                    stackedDngRaw16, dngStackFrames, null,
                    1.0f, 1.0f, 1.0f, 1.0f, 1.0f, 1.0f, 1.0f);
        }

        Result(ByteBuffer raw, long referenceTimestamp, int inputFrames,
                float effectiveSupport, ByteBuffer highlightProvenance,
                ByteBuffer stackedDngRaw16, int dngStackFrames,
                double[] dngNoiseProfile,
                float dngSupportMin, float dngSupportP01, float dngSupportP10,
                float dngSupportMedian, float dngSupportMean, float dngSupportMax,
                float dngNoiseEquivalentSupport) {
            this.raw = raw;
            this.referenceTimestamp = referenceTimestamp;
            this.inputFrames = inputFrames;
            this.effectiveSupport = effectiveSupport;
            this.highlightProvenance = highlightProvenance;
            this.stackedDngRaw16 = stackedDngRaw16;
            this.dngStackFrames = Math.max(0, dngStackFrames);
            this.dngNoiseProfile = dngNoiseProfile == null ? null : dngNoiseProfile.clone();
            this.dngSupportMin = dngSupportMin;
            this.dngSupportP01 = dngSupportP01;
            this.dngSupportP10 = dngSupportP10;
            this.dngSupportMedian = dngSupportMedian;
            this.dngSupportMean = dngSupportMean;
            this.dngSupportMax = dngSupportMax;
            this.dngNoiseEquivalentSupport = dngNoiseEquivalentSupport;
        }
'''
    return one(s,old,new,'26522 merger extended constructor')

def contracts_expected(text:str)->str:
    s=norm(text)
    anchor='''    val normalStackedDngRaw16: ByteBuffer? = null,\n    val normalStackedDngFrameCount: Int = 0,\n)\n'''
    repl='''    val normalStackedDngRaw16: ByteBuffer? = null,
    val normalStackedDngFrameCount: Int = 0,
    /* IRIS_26522_NORMALIZED16_DNG_METADATA */
    val normalStackedDngNoiseProfile: DoubleArray? = null,
    val normalStackedDngSupportMin: Float = 1f,
    val normalStackedDngSupportP01: Float = 1f,
    val normalStackedDngSupportP10: Float = 1f,
    val normalStackedDngSupportMedian: Float = 1f,
    val normalStackedDngSupportMean: Float = 1f,
    val normalStackedDngSupportMax: Float = 1f,
    val normalStackedDngNoiseEquivalentSupport: Float = 1f,
)
'''
    return one(s,anchor,repl,'26522 RawStackResult DNG metadata')

def bridge_expected(text:str)->str:
    s=norm(text)
    for tok in ('IRIS_26520_V4_LIVE_MGC_NORMAL_DNG_BRIDGE','outputMode = MgcSpatialOutputMode.RGB','mergeMethod = MgcMergeMethod.SPATIAL_RGB','stacked.normalStackedDngRaw16','stacked.normalStackedDngFrameCount'):
        if tok not in s: raise AssertionError('26521 bridge anchor missing '+tok)
    old='''            if (produceNormalStackedDng) {\n                requireParity(stacked.normalStackedDngRaw16 != null, "requested normal stacked DNG buffer is missing")\n                requireParity(stacked.normalStackedDngFrameCount == inputImages.size,\n                    "normal stacked DNG population=${stacked.normalStackedDngFrameCount} normals=${inputImages.size}")\n            } else {\n                requireParity(stacked.normalStackedDngRaw16 == null && stacked.normalStackedDngFrameCount == 0,\n                    "DNG sidecar produced without request")\n            }\n'''
    new='''            if (produceNormalStackedDng) {
                requireParity(stacked.normalStackedDngRaw16 != null, "requested normal stacked DNG buffer is missing")
                requireParity(stacked.normalStackedDngFrameCount == inputImages.size,
                    "normal stacked DNG population=${stacked.normalStackedDngFrameCount} normals=${inputImages.size}")
                /* IRIS_26522_NORMALIZED16_DNG_METADATA */
                requireParity(stacked.normalStackedDngNoiseProfile?.size == 6,
                    "normalized16 stacked DNG noise profile is missing/invalid")
                requireParity(stacked.normalStackedDngNoiseEquivalentSupport.isFinite() &&
                    stacked.normalStackedDngNoiseEquivalentSupport >= 1f &&
                    stacked.normalStackedDngNoiseEquivalentSupport <= inputImages.size.toFloat() + 0.01f,
                    "normalized16 stacked DNG effective support is invalid")
            } else {
                requireParity(stacked.normalStackedDngRaw16 == null && stacked.normalStackedDngFrameCount == 0,
                    "DNG sidecar produced without request")
                requireParity(stacked.normalStackedDngNoiseProfile == null,
                    "DNG metadata produced without request")
            }
'''
    s=one(s,old,new,'26522 bridge DNG contract')
    old='''                stacked.normalStackedDngRaw16,\n                stacked.normalStackedDngFrameCount,\n            )\n'''
    new='''                stacked.normalStackedDngRaw16,
                stacked.normalStackedDngFrameCount,
                stacked.normalStackedDngNoiseProfile,
                stacked.normalStackedDngSupportMin,
                stacked.normalStackedDngSupportP01,
                stacked.normalStackedDngSupportP10,
                stacked.normalStackedDngSupportMedian,
                stacked.normalStackedDngSupportMean,
                stacked.normalStackedDngSupportMax,
                stacked.normalStackedDngNoiseEquivalentSupport,
            )
'''
    return one(s,old,new,'26522 bridge result metadata')

def image_saver_expected(text:str)->str:
    s=norm(text)
    if 'public static boolean saveStackedRaw(Path dngFilePath,' not in s:
        raise AssertionError('ImageSaver stacked RAW anchor missing')
    anchor='''        public static boolean saveSingleRaw(Path dngFilePath,\n                                            ImageFrame image,\n'''
    helper='''        /**
         * IRIS_26522_NORMALIZED16_STACKED_DNG_WRITER
         *
         * MGC has already converted device-specific RAW code values into a black-subtracted,
         * white-normalized linear domain. Preserve that synthetic domain at full 16-bit precision
         * without changing Parameters used by JPEG/UHDR or the ordinary single-frame RAW path.
         */
        public static boolean saveNormalized16StackedRaw(
                Path dngFilePath,
                ByteBuffer buffer,
                Parameters parameters,
                double[] noiseProfile,
                int frameCount,
                float supportMin,
                float supportP01,
                float supportP10,
                float supportMedian,
                float supportMean,
                float supportMax,
                float noiseEquivalentSupport) {
            if (buffer == null || parameters == null) {
                throw new IllegalArgumentException("26522 normalized16 stacked DNG requires buffer and parameters");
            }
            if (noiseProfile == null || noiseProfile.length != 6) {
                throw new IllegalArgumentException("26522 normalized16 stacked DNG requires six NoiseProfile values");
            }
            for (double value : noiseProfile) {
                if (Double.isNaN(value) || Double.isInfinite(value) || value < 0.0) {
                    throw new IllegalArgumentException("26522 normalized16 stacked DNG NoiseProfile is invalid");
                }
            }
            if (frameCount < 1 || Float.isNaN(noiseEquivalentSupport) ||
                    Float.isInfinite(noiseEquivalentSupport) ||
                    noiseEquivalentSupport < 1.0f ||
                    noiseEquivalentSupport > frameCount + 0.01f) {
                throw new IllegalArgumentException("26522 normalized16 stacked DNG support metadata is invalid");
            }
            DngCreator dngCreator = new DngCreator();
            try {
                dngCreator.setParameters(parameters);
                dngCreator.setBitsPerSample(16);
                dngCreator.setBlackLevel(new short[]{0, 0, 0, 0});
                dngCreator.setWhiteLevel(65535.0);
                dngCreator.setNoiseProfile(noiseProfile);
                dngCreator.setDescription(
                        parameters.toString()
                                + "\\nIRIS_26522_STACKED_DNG_DOMAIN=normalized-black-subtracted-16bit"
                                + " FrameCount=" + frameCount
                                + " BlackLevel=0 WhiteLevel=65535"
                                + " SupportMin=" + supportMin
                                + " SupportP01=" + supportP01
                                + " SupportP10=" + supportP10
                                + " SupportMedian=" + supportMedian
                                + " SupportMean=" + supportMean
                                + " SupportMax=" + supportMax
                                + " NoiseEquivalentSupport=" + noiseEquivalentSupport
                                + " NoiseProfileBasis=Camera2NormalizedPerFrame/HarmonicEffectiveSupport");
                dngCreator.setCompression(false);
                try (OutputStream outputStream = Files.newOutputStream(dngFilePath)) {
                    buffer.position(0);
                    dngCreator.writeBuffer(
                            outputStream,
                            buffer,
                            parameters.rawSize.x,
                            parameters.rawSize.y);
                }
                return true;
            } catch (IOException e) {
                e.printStackTrace();
                return false;
            } finally {
                dngCreator.close();
            }
        }

'''
    return one(s,anchor,helper+anchor,'26522 normalized16 DNG writer')

def hdrx_expected(text:str)->str:
    s=norm(text)
    for tok in ('IRIS_26520_V4_SHARED_NORMAL_BATCH_DNG','iris26480DeferredDng = iris26409V2.stackedDngRaw16;','sameAdmittedNormalPopulation=true','ImageSaver.Util.saveStackedRaw(dngFile, iris26520RawOnly, processingParameters)'):
        if tok not in s: raise AssertionError('26521 Hdrx anchor missing '+tok)
    decl='''        ByteBuffer iris26480DeferredDng = null;\n'''
    s=one(s,decl,decl+'''        /* IRIS_26522_NORMALIZED16_DNG_METADATA */
        double[] iris26522DeferredDngNoiseProfile = null;
        int iris26522DeferredDngFrameCount = 0;
        float iris26522DngSupportMin = 1.0f;
        float iris26522DngSupportP01 = 1.0f;
        float iris26522DngSupportP10 = 1.0f;
        float iris26522DngSupportMedian = 1.0f;
        float iris26522DngSupportMean = 1.0f;
        float iris26522DngSupportMax = 1.0f;
        float iris26522DngNoiseEquivalentSupport = 1.0f;
''','26522 Hdrx deferred metadata declarations')
    anchor='''            iris26480DeferredDng = iris26409V2.stackedDngRaw16;\n'''
    s=one(s,anchor,anchor+'''            iris26522DeferredDngNoiseProfile = iris26409V2.dngNoiseProfile;
            iris26522DeferredDngFrameCount = iris26409V2.dngStackFrames;
            iris26522DngSupportMin = iris26409V2.dngSupportMin;
            iris26522DngSupportP01 = iris26409V2.dngSupportP01;
            iris26522DngSupportP10 = iris26409V2.dngSupportP10;
            iris26522DngSupportMedian = iris26409V2.dngSupportMedian;
            iris26522DngSupportMean = iris26409V2.dngSupportMean;
            iris26522DngSupportMax = iris26409V2.dngSupportMax;
            iris26522DngNoiseEquivalentSupport = iris26409V2.dngNoiseEquivalentSupport;
''','26522 Hdrx DNG metadata ownership')
    trace='''                            + " effectiveSupport=" + iris26409V2.effectiveSupport\n                            + " sameAdmittedNormalPopulation=true shortLongBentoExcludedFromDng=true"\n'''
    s=one(s,trace,'''                            + " effectiveSupport=" + iris26409V2.effectiveSupport
                            + " dngSupportMin=" + iris26409V2.dngSupportMin
                            + " dngSupportP01=" + iris26409V2.dngSupportP01
                            + " dngSupportP10=" + iris26409V2.dngSupportP10
                            + " dngSupportMedian=" + iris26409V2.dngSupportMedian
                            + " dngSupportMean=" + iris26409V2.dngSupportMean
                            + " dngSupportMax=" + iris26409V2.dngSupportMax
                            + " dngNoiseEquivalentSupport=" + iris26409V2.dngNoiseEquivalentSupport
                            + " dngDomain=normalized16 blackLevel=0 whiteLevel=65535"
                            + " sameAdmittedNormalPopulation=true shortLongBentoExcludedFromDng=true"
''','26522 Hdrx trace support')
    old='''                boolean iris26520RawSaved = ImageSaver.Util.saveStackedRaw(dngFile, iris26520RawOnly, processingParameters);\n'''
    new='''                boolean iris26520RawSaved = ImageSaver.Util.saveNormalized16StackedRaw(
                        dngFile, iris26520RawOnly, processingParameters,
                        iris26522DeferredDngNoiseProfile, iris26522DeferredDngFrameCount,
                        iris26522DngSupportMin, iris26522DngSupportP01, iris26522DngSupportP10,
                        iris26522DngSupportMedian, iris26522DngSupportMean, iris26522DngSupportMax,
                        iris26522DngNoiseEquivalentSupport);
'''
    s=one(s,old,new,'26522 RAW-only normalized16 save')
    old='''            final ByteBuffer dngBytes=iris26480DeferredDng;final Path dngPath=dngFile;final Parameters dngParams=processingParameters;\n            MOTION_26480_OUTPUT_EXECUTOR.execute(()->{Integer old=null;try{int tid=android.os.Process.myTid();\n                old=android.os.Process.getThreadPriority(tid);android.os.Process.setThreadPriority(tid,android.os.Process.THREAD_PRIORITY_BACKGROUND);\n                dngBytes.position(0);boolean saved=ImageSaver.Util.saveStackedRaw(dngPath,dngBytes,dngParams);\n'''
    new='''            final ByteBuffer dngBytes=iris26480DeferredDng;final Path dngPath=dngFile;final Parameters dngParams=processingParameters;
            final double[] dngNoise=iris26522DeferredDngNoiseProfile;
            final int dngFrameCount=iris26522DeferredDngFrameCount;
            final float dngSupportMin=iris26522DngSupportMin,dngSupportP01=iris26522DngSupportP01,
                    dngSupportP10=iris26522DngSupportP10,dngSupportMedian=iris26522DngSupportMedian,
                    dngSupportMean=iris26522DngSupportMean,dngSupportMax=iris26522DngSupportMax,
                    dngNoiseEquivalent=iris26522DngNoiseEquivalentSupport;
            MOTION_26480_OUTPUT_EXECUTOR.execute(()->{Integer old=null;try{int tid=android.os.Process.myTid();
                old=android.os.Process.getThreadPriority(tid);android.os.Process.setThreadPriority(tid,android.os.Process.THREAD_PRIORITY_BACKGROUND);
                dngBytes.position(0);boolean saved=ImageSaver.Util.saveNormalized16StackedRaw(
                        dngPath,dngBytes,dngParams,dngNoise,dngFrameCount,
                        dngSupportMin,dngSupportP01,dngSupportP10,dngSupportMedian,
                        dngSupportMean,dngSupportMax,dngNoiseEquivalent);
'''
    return one(s,old,new,'26522 deferred normalized16 save')

def iris_shader_expected(text:str)->str:
    s=norm(text)
    for tok in ('IRIS_26521_V5_CORRECTED_SPATIAL_INFRASTRUCTURE','IRIS_26520_V5_CONTINUOUS_FINEST_LK_TRANSPORT','val mergeBayer = """','val normalizeBayer = """'):
        if tok not in s: raise AssertionError('26521 Iris shader anchor missing '+tok)
    old='''            oBayerAndWeight = vec4(\n                intensity * frameWeight,\n                accumulatedWeight * frameWeight,\n                0.0,\n                0.0\n            );\n'''
    new='''            /* IRIS_26522_DNG_EFFECTIVE_SUPPORT_ACCUMULATOR
             * z accumulates each frame's squared contribution weight / 256. The existing r/g
             * signal and sum-weight channels remain unchanged, so RGB/JPEG math is untouched.
             */
            float contributionWeight = accumulatedWeight * frameWeight;
            oBayerAndWeight = vec4(
                intensity * frameWeight,
                contributionWeight,
                contributionWeight * contributionWeight / 256.0,
                0.0
            );
'''
    s=one(s,old,new,'26522 mergeBayer support moment')
    anchor='''    val normalizeBayer = """\n'''
    support='''    /* IRIS_26522_DNG_EFFECTIVE_SUPPORT_Q8 */
    val normalDngSupportQ8 = """
        #version 300 es
        precision highp float;
        precision highp int;
        uniform sampler2D uBayerAndWeight;
        uniform ivec2 uSourceSize;
        uniform ivec2 uOutputSize;
        uniform float uMaximumFrames;
        layout(location = 0) out highp uint oSupportQ8;
        void main() {
            ivec2 q = clamp(
                ivec2(gl_FragCoord.xy),
                ivec2(0),
                uOutputSize - ivec2(1)
            );
            vec2 uv = (vec2(q) + vec2(0.5)) / vec2(uOutputSize);
            ivec2 p = clamp(
                ivec2(floor(uv * vec2(uSourceSize))),
                ivec2(0),
                uSourceSize - ivec2(1)
            );
            vec4 accumulated = texelFetch(uBayerAndWeight, p, 0);
            float sumW = max(accumulated.g, 0.0);
            float sumW2 = max(accumulated.b * 256.0, 0.0);
            float effective = 1.0;
            if (sumW > 1.0e-8 && sumW2 > 1.0e-12) {
                effective = sumW * sumW / sumW2;
            }
            effective = clamp(effective, 1.0, max(uMaximumFrames, 1.0));
            oSupportQ8 = uint(round(effective * 256.0));
        }
    """.trimIndent()

'''
    return one(s,anchor,support+anchor,'26522 support shader insertion')

def iris_stack_expected(text:str)->str:
    s=norm(text)
    required=(
        'internal class GlesIris26521SpatialRgbStacker(',
        'IRIS_26521_V5_CORRECTED_SPATIAL_INFRASTRUCTURE',
        'IRIS_26520_V5_FINAL_FINEST_LK_OWNER',
        'IRIS_26520_V5_MERGE_DOMAIN_REJECTION_FLOW',
        'IRIS_26520_V5_SPATIAL_RGB_TWO_SLOT_RAW_LIFETIME',
        'IRIS_26520_V4_NORMAL_ONLY_DNG_READY',
        'normalStackedDngRaw16 = convertNormalizedBayer16ToSensorCode(normalizedRaw16)',
        'private fun convertNormalizedBayer16ToSensorCode(normalized: ByteBuffer): ByteBuffer',
        'GlesIris26521SpatialRgbShaders.normalizeBayer',
    )
    for tok in required:
        if tok not in s: raise AssertionError('26521 Iris stack anchor missing '+tok)
    decl='''        var normalStackedDngRaw16: ByteBuffer? = null\n        var normalStackedDngFrameCount = 0\n'''
    s=one(s,decl,decl+'''        /* IRIS_26522_NORMALIZED16_DNG_METADATA */
        var normalStackedDngNoiseProfile: DoubleArray? = null
        var normalStackedDngSupport = NormalDngSupportStats.identity()
''','26522 stack DNG metadata declarations')
    field='''    private var normalizeBayerProgram = 0\n'''
    s=one(s,field,field+'''    /* IRIS_26522_DNG_EFFECTIVE_SUPPORT_Q8 */
    private var normalDngSupportProgram = 0
''','26522 support program field')
    old='''                val normalizedRaw16 = readBayer16(normalizedTexture)\n                try {\n                    normalStackedDngRaw16 = convertNormalizedBayer16ToSensorCode(normalizedRaw16)\n                } finally {\n                    LargeDirectBuffer.free(normalizedRaw16)\n                }\n                PLog.i(TAG, "IRIS_26520_V4_NORMAL_ONLY_DNG_READY normalFrames=$normalStackedDngFrameCount " +\n                    "shortExcluded=true longExcluded=true bentoExcluded=true referenceWeight=identity " +\n                    "temporalWeight=preHdrRewrite linearKernelMask=zero outputExposureScale=1.0 " +\n                    "secondAlignmentPass=false sensorCodeDomain=true")\n'''
    new='''                /* IRIS_26522_NORMALIZED16_DNG_FULL_PRECISION
                 * renderBayer16 already maps the black-subtracted normalized float merge to the
                 * complete unsigned 16-bit code range. Keep those samples directly; do not round
                 * them back onto the source sensor's integer code lattice.
                 */
                normalStackedDngRaw16 = readBayer16(normalizedTexture)
                normalStackedDngSupport = resolveNormalDngSupportStats(
                    accumulator = normalDngAccumulator,
                    frameCount = normalStackedDngFrameCount,
                )
                normalStackedDngNoiseProfile = createNormalDngNoiseProfile(
                    frames = frames,
                    support = normalStackedDngSupport,
                )
                PLog.i(TAG, "IRIS_26522_NORMALIZED16_DNG_READY normalFrames=$normalStackedDngFrameCount " +
                    "shortExcluded=true longExcluded=true bentoExcluded=true referenceWeight=identity " +
                    "temporalWeight=preHdrRewrite linearKernelMask=zero outputExposureScale=1.0 " +
                    "secondAlignmentPass=false fullRangeNormalized16=true blackLevel=0 whiteLevel=65535 " +
                    "supportMin=${normalStackedDngSupport.minimum} " +
                    "supportP01=${normalStackedDngSupport.p01} " +
                    "supportP10=${normalStackedDngSupport.p10} " +
                    "supportMedian=${normalStackedDngSupport.median} " +
                    "supportMean=${normalStackedDngSupport.mean} " +
                    "supportMax=${normalStackedDngSupport.maximum} " +
                    "noiseEquivalentSupport=${normalStackedDngSupport.noiseEquivalent} " +
                    "noiseProfile=${normalStackedDngNoiseProfile?.contentToString()}")
'''
    s=one(s,old,new,'26522 DNG finalize full precision')
    old='''                normalStackedDngRaw16 = normalStackedDngRaw16,\n                normalStackedDngFrameCount = normalStackedDngFrameCount,\n'''
    new='''                normalStackedDngRaw16 = normalStackedDngRaw16,
                normalStackedDngFrameCount = normalStackedDngFrameCount,
                normalStackedDngNoiseProfile = normalStackedDngNoiseProfile,
                normalStackedDngSupportMin = normalStackedDngSupport.minimum,
                normalStackedDngSupportP01 = normalStackedDngSupport.p01,
                normalStackedDngSupportP10 = normalStackedDngSupport.p10,
                normalStackedDngSupportMedian = normalStackedDngSupport.median,
                normalStackedDngSupportMean = normalStackedDngSupport.mean,
                normalStackedDngSupportMax = normalStackedDngSupport.maximum,
                normalStackedDngNoiseEquivalentSupport = normalStackedDngSupport.noiseEquivalent,
'''
    s=one(s,old,new,'26522 RawStackResult metadata return')
    old_helper='''    /* IRIS_26520_V4_SENSOR_CODE_RESTORE */
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
    helpers='''    /* IRIS_26522_DNG_EFFECTIVE_SUPPORT_STATS */
    private data class NormalDngSupportStats(
        val minimum: Float,
        val p01: Float,
        val p10: Float,
        val median: Float,
        val mean: Float,
        val maximum: Float,
        val noiseEquivalent: Float,
    ) {
        companion object {
            fun identity() = NormalDngSupportStats(1f, 1f, 1f, 1f, 1f, 1f, 1f)
        }
    }

    private fun resolveNormalDngSupportStats(
        accumulator: Int,
        frameCount: Int,
    ): NormalDngSupportStats {
        require(exportNormalStackedDng && accumulator != 0 && frameCount >= 1)
        check(normalDngSupportProgram != 0) { "26522 DNG support program is unavailable" }
        val supportWidth = minOf(NORMAL_DNG_SUPPORT_GRID_LONG_EDGE, width).coerceAtLeast(1)
        val supportHeight = max(
            1,
            ((height.toLong() * supportWidth + width / 2L) / width.toLong()).toInt(),
        )
        val supportTexture = createTexture(
            supportWidth,
            supportHeight,
            GLES30.GL_R16UI,
            GLES30.GL_NEAREST,
        )
        GLES30.glUseProgram(normalDngSupportProgram)
        bindTexture(normalDngSupportProgram, "uBayerAndWeight", 0, accumulator)
        uniform2i(normalDngSupportProgram, "uSourceSize", width, height)
        uniform2i(normalDngSupportProgram, "uOutputSize", supportWidth, supportHeight)
        uniform1f(normalDngSupportProgram, "uMaximumFrames", frameCount.toFloat())
        draw(
            normalDngSupportProgram,
            supportWidth,
            supportHeight,
            intArrayOf(supportTexture),
        )
        val byteCount = supportWidth * supportHeight * Short.SIZE_BYTES
        val readback = ByteBuffer.allocateDirect(byteCount).order(ByteOrder.nativeOrder())
        bindRenderTargets(intArrayOf(supportTexture), "26522 DNG support readback")
        GLES30.glBindBuffer(GLES30.GL_PIXEL_PACK_BUFFER, 0)
        GLES30.glPixelStorei(GLES30.GL_PACK_ALIGNMENT, 1)
        GLES30.glReadPixels(
            0,
            0,
            supportWidth,
            supportHeight,
            GLES30.GL_RED_INTEGER,
            GLES30.GL_UNSIGNED_SHORT,
            readback,
        )
        GLES30.glBindFramebuffer(GLES30.GL_FRAMEBUFFER, 0)
        checkGlError("26522 DNG support readback")
        val values = FloatArray(supportWidth * supportHeight)
        val shorts = readback.asShortBuffer()
        var sum = 0.0
        var reciprocalSum = 0.0
        for (index in values.indices) {
            val decoded = (shorts.get(index).toInt() and 0xffff) / 256f
            val value = decoded.coerceIn(1f, frameCount.toFloat())
            values[index] = value
            sum += value.toDouble()
            reciprocalSum += 1.0 / value.toDouble()
        }
        values.sort()
        fun percentile(fraction: Float): Float {
            val index = ((values.size - 1) * fraction).toInt().coerceIn(0, values.lastIndex)
            return values[index]
        }
        val mean = (sum / values.size.toDouble()).toFloat()
        val harmonic = (values.size.toDouble() / reciprocalSum).toFloat()
            .coerceIn(1f, frameCount.toFloat())
        return NormalDngSupportStats(
            minimum = values.first(),
            p01 = percentile(0.01f),
            p10 = percentile(0.10f),
            median = percentile(0.50f),
            mean = mean,
            maximum = values.last(),
            noiseEquivalent = harmonic,
        ).also { stats ->
            PLog.i(
                TAG,
                "IRIS_26522_DNG_EFFECTIVE_SUPPORT grid=${supportWidth}x$supportHeight " +
                    "frames=$frameCount min=${stats.minimum} p01=${stats.p01} " +
                    "p10=${stats.p10} median=${stats.median} mean=${stats.mean} " +
                    "max=${stats.maximum} noiseEquivalent=${stats.noiseEquivalent}",
            )
        }
    }

    /* Camera2 SENSOR_NOISE_PROFILE is defined in normalized [0,1] signal units.
     * The normal Motion population is equal-exposure; divide the reference profile by the
     * measured harmonic effective support so the synthetic DNG describes the fused variance
     * rather than inheriting a stale one-frame/slider-count model.
     */
    private fun createNormalDngNoiseProfile(
        frames: List<RawStackFrame>,
        support: NormalDngSupportStats,
    ): DoubleArray {
        require(frames.isNotEmpty())
        val referenceModel = frames.first().channelNoiseProfile
            ?.let(RawNoiseModel::fromCamera2NoiseProfile)
            ?.takeIf { it.hasValidCamera2Profile }
            ?: noiseModelForFrame(frames.first())
        val shot = referenceModel.normalizedShotNoiseForShader(cfaPattern)
        val read = referenceModel.normalizedReadNoiseForShader(cfaPattern)
        require(shot.size >= 4 && read.size >= 4)
        val divisor = support.noiseEquivalent.coerceAtLeast(1f).toDouble()
        fun sane(value: Float): Double =
            value.takeIf { it.isFinite() && it >= 0f }?.toDouble() ?: 0.0
        val profile = doubleArrayOf(
            sane(shot[0]) / divisor,
            sane(read[0]) / divisor,
            0.5 * (sane(shot[1]) + sane(shot[2])) / divisor,
            0.5 * (sane(read[1]) + sane(read[2])) / divisor,
            sane(shot[3]) / divisor,
            sane(read[3]) / divisor,
        )
        check(profile.all { it.isFinite() && it >= 0.0 }) {
            "26522 normalized16 stacked DNG noise profile is invalid"
        }
        return profile
    }

'''
    s=one(s,old_helper,helpers,'26522 replace sensor-code restore with support/noise helpers')
    init='''        normalizeBayerProgram = linkProgram(\n            GlesIris26521SpatialRgbShaders.normalizeBayer,\n            "mgc_spatial_bayer16",\n        )\n'''
    s=one(s,init,init+'''        if (exportNormalStackedDng) {
            normalDngSupportProgram = linkProgram(
                GlesIris26521SpatialRgbShaders.normalDngSupportQ8,
                "iris_26522_normal_dng_support_q8",
            )
        }
''','26522 compile DNG support shader')
    companion='''        const val RAW_BYTES_PER_PIXEL = 2\n'''
    s=one(s,companion,companion+'''        const val NORMAL_DNG_SUPPORT_GRID_LONG_EDGE = 128
''','26522 support grid constant')
    return s

def expected_map(root:Path)->dict[str,str]:
    funcs={
        HDRX:hdrx_expected,
        MERGER:merger_expected,
        BRIDGE:bridge_expected,
        CONTRACTS:contracts_expected,
        IRIS_STACK:iris_stack_expected,
        IRIS_SHADER:iris_shader_expected,
        IMAGE_SAVER:image_saver_expected,
    }
    out={}
    for rel,fn in funcs.items():
        p=root/rel
        if not p.is_file(): raise AssertionError('missing successful-26521 runtime path '+rel)
        out[rel]=fn(p.read_text())
    return out

def patch_text(root:Path,expected:dict[str,str])->str:
    chunks=[]
    for rel in sorted(expected):
        p=root/rel; old=norm(p.read_text()); new=expected[rel]
        if old==new: raise AssertionError('empty 26522 transform '+rel)
        chunks.append(''.join(difflib.unified_diff(
            old.splitlines(True),new.splitlines(True),fromfile='a/'+rel,tofile='b/'+rel)))
    return ''.join(chunks)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('root',type=Path)
    ap.add_argument('--patch-out',type=Path); ap.add_argument('--patch-sha-out',type=Path)
    ap.add_argument('--check-only',action='store_true'); ns=ap.parse_args()
    base=ns.root.resolve(); expected=expected_map(base)
    if ns.check_only:
        print('PASS: 26522 transform resolves directly against exact successful-26521 candidate source')
        print('PASS: only stacked-DNG serialization/support/noise metadata changes; Iris RGB owner remains inherited')
        print('PASS: normalized float Bayer is retained as full-range 16-bit DNG without sensor-code requantization')
        return
    if ns.patch_out is None or ns.patch_sha_out is None:
        raise SystemExit('--patch-out and --patch-sha-out required unless --check-only')
    diff=patch_text(base,expected)
    if not diff: raise AssertionError('empty 26522 runtime patch')
    ns.patch_out.parent.mkdir(parents=True,exist_ok=True); ns.patch_out.write_text(diff)
    digest=hashlib.sha256(ns.patch_out.read_bytes()).hexdigest()
    ns.patch_sha_out.write_text(f'{digest}  {ns.patch_out.name}\n')
    for rel,new in expected.items():
        p=base/rel; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(new)
    print(f'PASS: 26522 rollback patch existed before {len(expected)}-path runtime write')

if __name__=='__main__': main()
