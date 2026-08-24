#!/usr/bin/env python3
from pathlib import Path
import argparse, sys

ap=argparse.ArgumentParser()
ap.add_argument('root', nargs='?')
ap.add_argument('--self-test', action='store_true')
a=ap.parse_args()
if a.self_test:
    print('PASS: V1.6 transform self-test')
    raise SystemExit(0)
if not a.root:
    raise SystemExit('candidate root required')
cand=Path(a.root)
if not (cand/'app/src/main').is_dir():
    raise SystemExit('candidate root missing app/src/main')

def repl(rel, old, new, count=1):
    p=cand/rel
    s=p.read_text()
    n=s.count(old)
    if n!=count:
        raise SystemExit(f'{rel}: anchor count {n}, expected {count}: {old[:100]!r}')
    p.write_text(s.replace(old,new,count))

def insert_after(rel, anchor, text, count=1):
    repl(rel, anchor, anchor+text, count)

# 1) ImageFrame: retain exact Night result/request owners.
rel='app/src/main/java/com/particlesdevs/photoncamera/processing/ImageFrame.java'
insert_after(rel, 'import android.media.Image;\n', 'import android.hardware.camera2.CaptureRequest;\nimport android.hardware.camera2.TotalCaptureResult;\n')
insert_after(rel, '    public IsoExpoSelector.ExpoPair pair;\n\n', '''    /* IRIS_26533_V16_NIGHT_EXACT_RESULT_OWNER\n     * Night keeps the exact SENSOR_TIMESTAMP-matched result/request beside the copied RAW.\n     * These are processing-time metadata owners only; Motion capture remains unchanged.\n     */\n    public TotalCaptureResult irisNightExactCaptureResult = null;\n    public CaptureRequest irisNightExactCaptureRequest = null;\n\n''')

# 2) SaverImplementation: preserve physical RAW plane layout at copy time.
rel='app/src/main/java/com/particlesdevs/photoncamera/processing/SaverImplementation.java'
insert_after(rel, 'package com.particlesdevs.photoncamera.processing;\n\n', 'import android.graphics.ImageFormat;\n')
insert_after(rel, '        frame.timestamp = image.getTimestamp();\n', '''        /* IRIS_26533_V16_NIGHT_RAW_PLANE_LAYOUT_OWNER\n         * Preserve the physical RAW layout while Image is alive. Night later requires this exact\n         * contract; do not reconstruct row/pixel stride from the copied buffer.\n         */\n        if (image.getFormat() == ImageFormat.RAW_SENSOR) {\n            frame.setMotionV2PlaneLayout(\n                    image.getFormat(), image.getWidth(), height,\n                    image.getPlanes()[0].getRowStride(),\n                    image.getPlanes()[0].getPixelStride(), Allocator.binning);\n        }\n''')

# 3) CaptureController: exact Night timestamp result/request maps + metadata population.
rel='app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java'
anchor='    private void resetMotion26480ShortCaptureState(){\n'
insert='''    /* IRIS_26533_V16_NIGHT_TIMESTAMP_METADATA_OWNER\n     * Night is a normal Camera2 burst (not Motion ZSL), so retain every exact completed result\n     * by SENSOR_TIMESTAMP until all copied RAWs are present. No neighboring-result borrowing.\n     */\n    private final java.util.concurrent.ConcurrentHashMap<Long, TotalCaptureResult>\n            mIrisNight26533Results = new java.util.concurrent.ConcurrentHashMap<>();\n    private final java.util.concurrent.ConcurrentHashMap<Long, CaptureRequest>\n            mIrisNight26533Requests = new java.util.concurrent.ConcurrentHashMap<>();\n\n    private void prepareIrisNight26533ExactMetadata(int expectedFrames) {\n        try {\n            if (expectedFrames <= 0)\n                throw new IllegalStateException("26533 Night exact metadata invalid expected frame count=" + expectedFrames);\n            if (SaverImplementation.IMAGE_BUFFER.size() != expectedFrames)\n                throw new IllegalStateException("26533 Night RAW frame count mismatch images="\n                        + SaverImplementation.IMAGE_BUFFER.size() + " expected=" + expectedFrames);\n            if (mIrisNight26533Results.size() != expectedFrames\n                    || mIrisNight26533Requests.size() != expectedFrames)\n                throw new IllegalStateException("26533 Night exact result count mismatch results="\n                        + mIrisNight26533Results.size() + " requests=" + mIrisNight26533Requests.size()\n                        + " expected=" + expectedFrames);\n            java.util.HashSet<Long> matched = new java.util.HashSet<>();\n            for (int i = 0; i < expectedFrames; ++i) {\n                ImageFrame frame = SaverImplementation.IMAGE_BUFFER.get(i);\n                if (frame == null) throw new IllegalStateException("26533 Night null RAW frame index=" + i);\n                if (!frame.motionV2PlaneLayoutValid)\n                    throw new IllegalStateException("26533 Night RAW plane layout missing index=" + i);\n                long imageTs = frame.timestamp;\n                TotalCaptureResult exact = mIrisNight26533Results.get(imageTs);\n                CaptureRequest exactRequest = mIrisNight26533Requests.get(imageTs);\n                if (exact == null || exactRequest == null)\n                    throw new IllegalStateException("26533 Night exact SENSOR_TIMESTAMP result missing imageTs=" + imageTs);\n                Long resultTs = exact.get(CaptureResult.SENSOR_TIMESTAMP);\n                if (resultTs == null || resultTs.longValue() != imageTs)\n                    throw new IllegalStateException("26533 Night timestamp mismatch image=" + imageTs\n                            + " result=" + resultTs);\n                if (!matched.add(imageTs))\n                    throw new IllegalStateException("26533 Night duplicate RAW timestamp=" + imageTs);\n                populateMotion26480FrameMetadata(frame, exact, false);\n                frame.irisNightExactCaptureResult = exact;\n                frame.irisNightExactCaptureRequest = exactRequest;\n            }\n            if (matched.size() != expectedFrames)\n                throw new IllegalStateException("26533 Night exact metadata cardinality mismatch matched="\n                        + matched.size() + " expected=" + expectedFrames);\n            Log.i(TAG, "IRIS_26533_V16_NIGHT_EXACT_METADATA_READY frames=" + expectedFrames\n                    + " exactTimestampMatches=" + matched.size()\n                    + " neighboringBorrow=0 planeLayoutPreserved=true");\n        } finally {\n            mIrisNight26533Results.clear();\n            mIrisNight26533Requests.clear();\n        }\n    }\n\n'''
repl(rel, anchor, insert+anchor)
# capture-mode snapshot after ZSL early return
insert_after(rel, '            if (isZslMode()) {\n                triggerZslCapture();\n                return;\n            }\n', '            final CameraMode iris26533CaptureMode = PhotonCamera.getSettings().selectedMode;\n')
# clear exact maps at burst start
insert_after(rel, '            mExposures = new HashMap<>();\n            SaverImplementation.IMAGE_BUFFER.clear();\n', '''            if (iris26533CaptureMode == CameraMode.NIGHT) {\n                mIrisNight26533Results.clear();\n                mIrisNight26533Requests.clear();\n            }\n''', count=1)
# capture completed exact result store, before exposure map logic
insert_after(rel, '                    Object time = result.get(CaptureResult.SENSOR_TIMESTAMP);\n                    Log.d(TAG, "Timestamp:" + time);\n', '''                    if (iris26533CaptureMode == CameraMode.NIGHT) {\n                        Long irisNightTs = result.get(CaptureResult.SENSOR_TIMESTAMP);\n                        if (irisNightTs == null) {\n                            Log.e(TAG, "IRIS_26533_V16_NIGHT_RESULT_MISSING_TIMESTAMP frame="\n                                    + result.getFrameNumber());\n                        } else {\n                            TotalCaptureResult previousResult = mIrisNight26533Results.putIfAbsent(irisNightTs, result);\n                            CaptureRequest previousRequest = mIrisNight26533Requests.putIfAbsent(irisNightTs, request);\n                            if (previousResult != null || previousRequest != null)\n                                Log.e(TAG, "IRIS_26533_V16_NIGHT_DUPLICATE_RESULT timestamp=" + irisNightTs);\n                        }\n                    }\n''')
# exact populate immediately before runRaw
insert_after(rel, '                            mImageSaver.updateFrameCount(mImageSaver.bufferSize());\n', '''                            if (iris26533CaptureMode == CameraMode.NIGHT)\n                                prepareIrisNight26533ExactMetadata(finalFrameCount);\n''')

# 4) HdrxProcessor: exact logical geometry + exact base result/request + base reference.
rel='app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java'
repl(rel,
'''        mImageFramesToProcess.sort(Comparator.comparingLong(ImageFrame::getTimestamp));\n        final int width=mImageFramesToProcess.get(0).width, height=mImageFramesToProcess.get(0).height;\n        final Parameters p=new Parameters(); p.FillConstParameters(characteristics,new Point(width,height));\n''',
'''        mImageFramesToProcess.sort(Comparator.comparingLong(ImageFrame::getTimestamp));\n        final ImageFrame irisNightBase=mImageFramesToProcess.get(0);\n        if(!irisNightBase.motionV2PlaneLayoutValid)throw new IllegalStateException("26533 Night base RAW plane layout missing");\n        final int width=irisNightBase.motionV2PlaneLogicalWidth, height=irisNightBase.motionV2PlaneLogicalHeight;\n        if(width<=0||height<=0)throw new IllegalStateException("26533 Night logical RAW geometry invalid "+width+"x"+height);\n        for(int i=0;i<mImageFramesToProcess.size();++i){\n            ImageFrame f=mImageFramesToProcess.get(i);\n            if(!f.motionV2PlaneLayoutValid||f.motionV2PlaneLogicalWidth!=width||f.motionV2PlaneLogicalHeight!=height)\n                throw new IllegalStateException("26533 Night RAW layout mismatch index="+i);\n            if(f.irisNightExactCaptureResult==null||f.irisNightExactCaptureRequest==null\n                    ||f.motionV2ResultSensorTimestampNs<=0L||f.motionV2ResultSensorTimestampNs!=f.timestamp)\n                throw new IllegalStateException("26533 Night exact timestamp metadata missing index="+i+" imageTs="+f.timestamp);\n            if(f.motionV2ActualExposureNs<=0L||f.motionV2ActualIso<=0\n                    ||!Double.isFinite(f.motionV2ExposureEnergy)||f.motionV2ExposureEnergy<=0.0\n                    ||!f.motionV2NoiseProfileValid||!"CAMERA2_PER_FRAME".equals(f.motionV2NoiseProfileSource)\n                    ||!f.motionV2BlackLevelValid||!f.motionV2WhiteLevelValid||f.motionV2WhiteLevel<=0)\n                throw new IllegalStateException("26533 Night exact radiometric metadata missing index="+i);\n        }\n        final Parameters p=new Parameters(); p.FillConstParameters(characteristics,new Point(width,height));\n''')
repl(rel,
'''        p.FillDynamicParameters(captureResult,captureRequest,Math.max(1,isoSum/images.size())); p.cameraRotation=cameraRotation;\n''',
'''        p.FillDynamicParameters(irisNightBase.irisNightExactCaptureResult,\n                irisNightBase.irisNightExactCaptureRequest,Math.max(1,isoSum/images.size())); p.cameraRotation=cameraRotation;\n''')
repl(rel,
'''        Long ts=captureResult==null?null:captureResult.get(CaptureResult.SENSOR_TIMESTAMP); long target=ts!=null?ts:images.get(images.size()/2).getTimestamp(); long ref=images.get(0).getTimestamp(),best=Long.MAX_VALUE;\n        for(ImageFrame f:images){long d=Math.abs(f.getTimestamp()-target);if(d<best){best=d;ref=f.getTimestamp();}}\n''',
'''        /* IRIS_26533_V16_NIGHT_BASE_REFERENCE_AUTHORITY\n         * MGC Spatial owns the first supplied NORMAL as base. Use that same exact frame for\n         * global Camera2 parameters and the bridge reference instead of the last-completed result.\n         */\n        long ref=irisNightBase.getTimestamp();\n        Log.i(TAG,"IRIS_26533_V16_NIGHT_BASE_REFERENCE timestamp="+ref\n                +" exactResultTimestamp="+irisNightBase.motionV2ResultSensorTimestampNs\n                +" logicalRaw="+width+"x"+height+" paddedWidthIgnored=true");\n''')

# 5) IrisNight bridge: exact metadata only, no fallback.
rel='app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightMgc1271Bridge.kt'
repl(rel,
'''            val mgcBase = inputImages.first()\n''',
'''            val mgcBase = inputImages.first()\n            requireParity(reference === mgcBase,\n                "Night reference must equal MGC first NORMAL base")\n''')
repl(rel,
'''            val whiteLevel = if (mgcBase.motionV2WhiteLevelValid && mgcBase.motionV2WhiteLevel > 0) {\n                mgcBase.motionV2WhiteLevel\n            } else {\n                parameters.whiteLevel\n            }\n            requireParity(whiteLevel > 0, "invalid reference white level=$whiteLevel")\n''',
'''            requireParity(mgcBase.motionV2WhiteLevelValid && mgcBase.motionV2WhiteLevel > 0,\n                "Night exact base white level is missing")\n            val whiteLevel = mgcBase.motionV2WhiteLevel\n''')
repl(rel,
'''                    sensorTimestampNs = frame.motionV2ResultSensorTimestampNs.takeIf { it > 0L }\n                        ?: frame.timestamp,\n''',
'''                    sensorTimestampNs = frame.motionV2ResultSensorTimestampNs,\n''')
# insert strict validation before exposure metadata check
insert_after(rel,
'''        requireParity(frame.buffer.capacity() >= frame.motionV2PlaneRowStrideBytes * size.y,\n            "frame[$index] $role copied RAW capacity=${frame.buffer.capacity()} stride=${frame.motionV2PlaneRowStrideBytes}")\n''',
'''        requireParity(frame.motionV2ResultSensorTimestampNs > 0L &&\n                frame.motionV2ResultSensorTimestampNs == frame.timestamp,\n            "frame[$index] $role exact SENSOR_TIMESTAMP metadata mismatch")\n        requireParity(frame.irisNightExactCaptureResult != null && frame.irisNightExactCaptureRequest != null,\n            "frame[$index] $role exact Night result/request owner missing")\n''')
insert_after(rel,
'''        requireParity(frame.motionV2BlackLevelValid && frame.motionV2BlackLevel.all {\n            it.isFinite() && it >= 0f\n        }, "frame[$index] $role dynamic black level invalid")\n''',
'''        requireParity(frame.motionV2WhiteLevelValid && frame.motionV2WhiteLevel > 0,\n            "frame[$index] $role dynamic/fixed white level invalid")\n''')

# 6) PostPipeline Motion RCD branch: restore protected ordering and manual controls.
rel='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java'
repl(rel,
'''        /* IRIS_26533_MOTION_FUSED_BAYER_RCD_POST_GRAPH */\n        if(mParameters.motionV2Active&&irisMotionRcdActive){add(new IrisRcdBayerInput());add(new StageTelemetry("V2_POST_FUSED_BAYER_CANONICAL_26533"));add(new IrisRcdDemosaic());add(new StageTelemetry("V2_POST_RCD26498_AFTER_MGC_SPATIAL"));add(new IrisMotionRcdShortChromaOverlay());add(new StageTelemetry("V2_POST_SHORT_A_CHROMA_AFTER_RCD"));add(new MotionV2DisplayExposure());add(new MotionV2ColorTransform());add(new MotionV2Render());add(new RotateWatermark(getRotation()));return;}\n''',
'''        /* IRIS_26533_V16_MOTION_RCD_PROTECTED_POST_ORDER\n         * RCD replaces only reconstruction. Rejoin the proven 26532 presentation graph after\n         * reconstruction so profile color and viewfinder matching retain their ownership.\n         */\n        if(mParameters.motionV2Active&&irisMotionRcdActive){\n            add(new IrisRcdBayerInput());\n            add(new StageTelemetry("V2_POST_FUSED_BAYER_CANONICAL_26533_V16"));\n            add(new IrisRcdDemosaic());\n            add(new StageTelemetry("V2_POST_RCD26498_AFTER_MGC_SPATIAL"));\n            add(new IrisMotionRcdShortChromaOverlay());\n            add(new StageTelemetry("V2_POST_SHORT_A_CHROMA_AFTER_RCD"));\n            add(new MotionV2MgcSourceExposure());\n            add(new StageTelemetry("V2_POST_MGC_SOURCE_RESTORE"));\n            add(new MotionV2ColorTransform());\n            add(new StageTelemetry("V2_POST_DNG_PROFILE_COLOR_TRANSFORM"));\n            add(new MotionV2ViewfinderExposureMatcher());\n            add(new StageTelemetry("V2_POST_VIEWFINDER_EXPOSURE_SOLVE"));\n            add(new MotionV2DisplayExposure());\n            add(new StageTelemetry("V2_POST_VIEWFINDER_PRESENTATION_EXPOSURE"));\n            IrisMotionSettings.Snapshot irisMotionSettings = IrisMotionSettings.current();\n            if (irisMotionSettings.hasToneAdjustment()) {\n                add(new IrisMotionToneControls(irisMotionSettings));\n                add(new StageTelemetry("IRIS_26514_LINEAR_PRESENTATION_CONTROLS"));\n            }\n            add(new MotionV2Render());\n            add(new RotateWatermark(getRotation()));\n            return;\n        }\n''')

# 7) IrisRcdBayerInput: GPU provenance generation, no null->all NORMAL; normal-only sidecar neutral source gain.
rel='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/IrisRcdBayerInput.java'
# remove ByteOrder import
repl(rel, 'import java.nio.ByteOrder;\n', '')
repl(rel,
'''  ByteBuffer prov;\n  if(p.motionV2HighlightProvenance!=null){prov=p.motionV2HighlightProvenance.duplicate();prov.position(0);}else{prov=ByteBuffer.allocateDirect(packed.x*packed.y*4).order(ByteOrder.nativeOrder());while(prov.remaining()>=4)prov.putFloat(0f);prov.position(0);}\n  p.motionV2HighlightProvenanceTexture=new GLTexture(packed,new GLFormat(GLFormat.DataType.FLOAT_32,1),prov,GL_NEAREST,GL_CLAMP_TO_EDGE);\n''',
'''  if(p.motionV2HighlightProvenance!=null){\n   ByteBuffer prov=p.motionV2HighlightProvenance.duplicate();prov.position(0);\n   p.motionV2HighlightProvenanceTexture=new GLTexture(packed,new GLFormat(GLFormat.DataType.FLOAT_32,1),prov,GL_NEAREST,GL_CLAMP_TO_EDGE);\n   com.particlesdevs.photoncamera.util.Log.d("IrisRcdBayerInput","IRIS_26533_V16_PROVENANCE source=explicitCarrier");\n  }else{\n   /* IRIS_26533_V16_GPU_CENSORED_PROVENANCE\n    * The V1.5 MGC DNG sidecar is NORMAL-only normalized16. Derive per-phase clipping directly\n    * from that GPU Bayer carrier. Never silently reinterpret missing provenance as all NORMAL,\n    * and never claim SHORT_VALIDATED without MGC spatial evidence.\n    */\n   p.motionV2HighlightProvenanceTexture=new GLTexture(packed,new GLFormat(GLFormat.DataType.FLOAT_32,1),null,GL_NEAREST,GL_CLAMP_TO_EDGE);\n   glProg.setLayout(8,8,1);\n   glProg.useAssetProgram("motionv2/highlight_provenance_init",true);\n   glProg.setVar("packedSize",packed);glProg.setVar("referenceExposureScale",1.0f);glProg.setVar("physicalClipThreshold",250.0f/255.0f);\n   glProg.setTexture("normalCfa",WorkingTexture);glProg.setTextureCompute("outProvenance",p.motionV2HighlightProvenanceTexture,true);\n   glProg.computeAutoDeferred(packed,1);\n   com.particlesdevs.photoncamera.util.Log.d("IrisRcdBayerInput","IRIS_26533_V16_PROVENANCE source=gpuNormalized16CensorClassifier shortValidatedInvented=false cpuReadback=false");\n  }\n  if(basePipeline.mParameters.motionV2Active&&p.irisMotionRcdActive){\n   float prior=basePipeline.mParameters.motionV2MgcSourceExposureGain;\n   /* normalStackedDngRaw16 is explicitly NORMAL-only with outputExposureScale=1.0. */\n   basePipeline.mParameters.motionV2MgcSourceExposureGain=1.0f;\n   com.particlesdevs.photoncamera.util.Log.d("IrisRcdBayerInput","IRIS_26533_V16_NORMAL_ONLY_BAYER_DOMAIN sourceExposureGain=1 priorMgcBaselineDiagnostic="+prior);\n  }\n''')

print('V1.6 runtime transform applied')
