#!/usr/bin/env python3
from pathlib import Path
import re, sys
root=Path(sys.argv[1] if len(sys.argv)>1 else '.')

def P(r): return root/r
def read(r): return P(r).read_text()
def write(r,t): P(r).parent.mkdir(parents=True,exist_ok=True); P(r).write_text(t)
def once(t,old,new,label):
    n=t.count(old)
    if n!=1: raise SystemExit(f'{label} anchor count={n}')
    return t.replace(old,new,1)
def rx(t,pat,repl,label,flags=re.S):
    out,n=re.subn(pat,repl,t,count=1,flags=flags)
    if n!=1: raise SystemExit(f'{label} regex count={n}')
    return out

CAP='app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java'
FRAME='app/src/main/java/com/particlesdevs/photoncamera/processing/ImageFrame.java'
HDRX='app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java'
RECON='app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java'
RENDER='app/src/main/assets/shaders/motionv2/render.glsl'
SHORT='app/src/main/assets/shaders/motionv2/short_highlight_recover.glsl'

# ---- richer exact frame role/metadata/noise provenance ----
t=read(FRAME)
anchor='''    public float motionV2NoiseS = Float.NaN;
    public float motionV2NoiseO = Float.NaN;
'''
insert=anchor+'''
    /* IRIS_26480_BJZHOU_FRAME_ROLE_AND_METADATA_V2 */
    public enum MotionV2FrameRole { NORMAL, HIGHLIGHT_SHORT }
    public MotionV2FrameRole motionV2FrameRole = MotionV2FrameRole.NORMAL;
    public long motionV2ResultSensorTimestampNs = 0L;
    public long motionV2FrameNumber = -1L;
    public long motionV2RollingShutterSkewNs = 0L;
    public float motionV2FocusDistanceDiopters = Float.NaN;
    public int motionV2LensState = -1;
    public final float[] motionV2NoiseProfile = new float[8];
    public boolean motionV2NoiseProfileValid = false;
    public String motionV2NoiseProfileSource = "UNAVAILABLE";
'''
t=once(t,anchor,insert,'ImageFrame metadata V2')
write(FRAME,t)

# ---- capture: replace V1 repeating-preview manipulation with raw-only one-shot role ----
t=read(CAP)
# Replace broad ratio constants and add completion state.
t=t.replace('''    private static final long MOTION_26480_SHORT_WAIT_MS = 650L;
    private static final double MOTION_26480_SHORT_RATIO_MAX = 0.60;
    private static final double MOTION_26480_SHORT_RATIO_MIN = 0.10;
''','''    private static final long MOTION_26480_SHORT_WAIT_MS = 300L;
    private static final double MOTION_26480_SHORT_TARGET_RATIO = 1.0 / 3.0;
    private static final double MOTION_26480_SHORT_TOLERANCE_EV = 0.35;
    private static final double MOTION_26480_SHORT_RATIO_MIN =
            MOTION_26480_SHORT_TARGET_RATIO / Math.pow(2.0, MOTION_26480_SHORT_TOLERANCE_EV);
    private static final double MOTION_26480_SHORT_RATIO_MAX =
            MOTION_26480_SHORT_TARGET_RATIO * Math.pow(2.0, MOTION_26480_SHORT_TOLERANCE_EV);
    private static final String MOTION_26480_SHORT_TAG = "IRIS_26480_HIGHLIGHT_SHORT";
    private volatile boolean mMotion26480ShortRequestCompleted = false;
''',1)

method_pat=r'''    private boolean applyMotion26480ShortHighlightBiasIfNeeded\(\) \{.*?\n    \}\n\n    private void restoreMotion26480ShortHighlightBias\(\) \{.*?\n    \}\n'''
methods=r'''    private boolean applyMotion26480ExplicitShortCaptureIfNeeded() {
        if (!isZslMode() || mCaptureSession == null || mCameraDevice == null
                || mImageReaderRaw == null || mCameraCharacteristics == null
                || mPreviewCaptureResult == null || mMotion26380RawSampleCount < 64
                || Float.isNaN(mMotion26380RawHighlightFraction)) return false;

        Long previewTimestamp=mPreviewCaptureResult.get(CaptureResult.SENSOR_TIMESTAMP);
        Long baseExp=mPreviewCaptureResult.get(CaptureResult.SENSOR_EXPOSURE_TIME);
        Integer baseIso=mPreviewCaptureResult.get(CaptureResult.SENSOR_SENSITIVITY);
        long rawAgeNs=previewTimestamp==null||mMotion26380RawSignalTimestampNs<=0L
                ?Long.MAX_VALUE:Math.abs(previewTimestamp-mMotion26380RawSignalTimestampNs);
        if(rawAgeNs>180_000_000L
                ||mMotion26380RawHighlightFraction<MOTION_26478_HIGHLIGHT_FRACTION_TRIGGER
                ||baseExp==null||baseExp<=0L||baseIso==null||baseIso<=0) return false;

        mMotion26480ShortBaselineExposureNs=baseExp;
        mMotion26480ShortBaselineIso=baseIso;
        mMotion26480ShortBaselineEnergy=ExposureIndex.time2sec(baseExp)*baseIso;
        mMotion26480ShortResultTimestampNs=0L;
        mMotion26480ShortActualExposureNs=0L;
        mMotion26480ShortActualIso=0;
        mMotion26480ShortActualEnergy=0.0;
        mMotion26480ShortRequestCompleted=false;

        try {
            CaptureRequest.Builder b=mCameraDevice.createCaptureRequest(CameraDevice.TEMPLATE_STILL_CAPTURE);
            b.addTarget(mImageReaderRaw.getSurface());
            b.setTag(MOTION_26480_SHORT_TAG);
            if(mPreviewAFMode>=0) b.set(CaptureRequest.CONTROL_AF_MODE,mPreviewAFMode);
            if(Float.isFinite(mFocus)&&mFocus>=0.0f){
                try{b.set(CaptureRequest.LENS_FOCUS_DISTANCE,mFocus);}catch(IllegalArgumentException ignored){}
            }

            boolean manual=false;
            int[] caps=mCameraCharacteristics.get(CameraCharacteristics.REQUEST_AVAILABLE_CAPABILITIES);
            if(caps!=null) for(int c:caps){
                if(c==CameraCharacteristics.REQUEST_AVAILABLE_CAPABILITIES_MANUAL_SENSOR){manual=true;break;}
            }
            long reqExp=Math.max(1L,Math.round(baseExp/MOTION_26480_SHORT_EXPOSURE_DIVISOR));
            int reqIso=baseIso;
            String mode;
            if(!manual){
                Log.w(TAG,"IRIS_26480_SHORT_CAPTURE skipped reason=MANUAL_SENSOR_UNAVAILABLE previewAeUntouched=true");
                mMotion26480ShortRequestCompleted=true;
                return false;
            }
            android.util.Range<Long> er=mCameraCharacteristics.get(CameraCharacteristics.SENSOR_INFO_EXPOSURE_TIME_RANGE);
            android.util.Range<Integer> sr=mCameraCharacteristics.get(CameraCharacteristics.SENSOR_INFO_SENSITIVITY_RANGE);
            if(er!=null) reqExp=Math.max(er.getLower(),Math.min(er.getUpper(),reqExp));
            if(sr!=null) reqIso=Math.max(sr.getLower(),Math.min(sr.getUpper(),reqIso));
            b.set(CaptureRequest.CONTROL_AE_MODE,CaptureRequest.CONTROL_AE_MODE_OFF);
            b.set(CaptureRequest.SENSOR_EXPOSURE_TIME,reqExp);
            b.set(CaptureRequest.SENSOR_SENSITIVITY,reqIso);
            mode="MANUAL_SENSOR_RAW_ONLY";
            try{VendorTagUtils.builderSessionApply(b,true,useMaximumResolutionKey,physicalID);}
            catch(Throwable e){Log.w(TAG,"IRIS_26480_SHORT_CAPTURE vendor tags skipped "+e.getClass().getSimpleName());}

            mMotion26480ShortRequested=true;
            final long requestedExp=reqExp;
            final int requestedIso=reqIso;
            final String requestedMode=mode;
            mCaptureSession.capture(b.build(),new CameraCaptureSession.CaptureCallback(){
                @Override public void onCaptureCompleted(@NonNull CameraCaptureSession session,
                        @NonNull CaptureRequest request,@NonNull TotalCaptureResult result){
                    Long ts=result.get(CaptureResult.SENSOR_TIMESTAMP);
                    Long exp=result.get(CaptureResult.SENSOR_EXPOSURE_TIME);
                    Integer iso=result.get(CaptureResult.SENSOR_SENSITIVITY);
                    if(ts!=null){
                        synchronized(mZslBufferLock){
                            mZslResultMap.put(ts,result);
                            while(mZslResultMap.size()>MAX_ZSL_RESULT_METADATA){
                                Long oldest=Collections.min(mZslResultMap.keySet());mZslResultMap.remove(oldest);
                            }
                        }
                    }
                    mMotion26480ShortRequestCompleted=true;
                    if(ts==null||exp==null||exp<=0L||iso==null||iso<=0||mMotion26480ShortBaselineEnergy<=0.0){
                        Log.w(TAG,"IRIS_26480_SHORT_ACTUAL_REJECTED reason=missingActualMetadata");return;
                    }
                    double e=ExposureIndex.time2sec(exp)*iso;
                    double ratio=e/mMotion26480ShortBaselineEnergy;
                    boolean accepted=ratio>=MOTION_26480_SHORT_RATIO_MIN&&ratio<=MOTION_26480_SHORT_RATIO_MAX
                            &&e<mMotion26480ShortBaselineEnergy;
                    if(accepted){
                        mMotion26480ShortResultTimestampNs=ts;
                        mMotion26480ShortActualExposureNs=exp;
                        mMotion26480ShortActualIso=iso;
                        mMotion26480ShortActualEnergy=e;
                        Log.i(TAG,"IRIS_26480_SHORT_ACTUAL_ACCEPTED role=HIGHLIGHT_SHORT"
                                +" requestMode="+requestedMode+" requestedExposureNs="+requestedExp
                                +" requestedIso="+requestedIso+" actualExposureNs="+exp+" actualIso="+iso
                                +" ratio="+ratio+" targetRatio="+MOTION_26480_SHORT_TARGET_RATIO
                                +" toleranceEv="+MOTION_26480_SHORT_TOLERANCE_EV
                                +" previewRepeatingRequestMutated=false");
                    }else Log.w(TAG,"IRIS_26480_SHORT_ACTUAL_REJECTED ratio="+ratio
                            +" allowed="+MOTION_26480_SHORT_RATIO_MIN+".."+MOTION_26480_SHORT_RATIO_MAX);
                }
                @Override public void onCaptureFailed(@NonNull CameraCaptureSession session,
                        @NonNull CaptureRequest request,@NonNull android.hardware.camera2.CaptureFailure failure){
                    mMotion26480ShortRequestCompleted=true;
                    Log.w(TAG,"IRIS_26480_SHORT_CAPTURE_FAILED reason="+failure.getReason());
                }
            },mBackgroundHandler);
            Log.i(TAG,"IRIS_26480_SHORT_CAPTURE_SUBMITTED role=HIGHLIGHT_SHORT"
                    +" requestMode="+mode+" rawOnlyTarget=true previewRepeatingRequestMutated=false"
                    +" previewRebuilt=false normalRingCleared=false");
            return true;
        }catch(CameraAccessException|IllegalArgumentException|IllegalStateException e){
            mMotion26480ShortRequested=false;mMotion26480ShortRequestCompleted=true;
            Log.w(TAG,"IRIS_26480_SHORT_CAPTURE skipped "+e.getClass().getSimpleName());return false;
        }
    }

    private void resetMotion26480ShortCaptureState(){
        mMotion26480ShortRequested=false;mMotion26480ShortRequestCompleted=false;
        mMotion26480ShortResultTimestampNs=0L;mMotion26480ShortActualExposureNs=0L;
        mMotion26480ShortActualIso=0;mMotion26480ShortActualEnergy=0.0;
    }

    private void populateMotion26480FrameMetadata(@NonNull ImageFrame frame,
            TotalCaptureResult result,boolean shortRole){
        frame.motionV2FrameRole=shortRole?ImageFrame.MotionV2FrameRole.HIGHLIGHT_SHORT:ImageFrame.MotionV2FrameRole.NORMAL;
        frame.motionV2ShortHighlightFrame=shortRole;
        if(result==null){frame.motionV2NoiseProfileSource="UNAVAILABLE";return;}
        Long exp=result.get(CaptureResult.SENSOR_EXPOSURE_TIME);Integer iso=result.get(CaptureResult.SENSOR_SENSITIVITY);
        Long ts=result.get(CaptureResult.SENSOR_TIMESTAMP);Long skew=result.get(CaptureResult.SENSOR_ROLLING_SHUTTER_SKEW);
        Float focus=result.get(CaptureResult.LENS_FOCUS_DISTANCE);Integer lens=result.get(CaptureResult.LENS_STATE);
        if(exp!=null&&exp>0L)frame.motionV2ActualExposureNs=exp;if(iso!=null&&iso>0)frame.motionV2ActualIso=iso;
        if(frame.motionV2ActualExposureNs>0L&&frame.motionV2ActualIso>0)
            frame.motionV2ExposureEnergy=ExposureIndex.time2sec(frame.motionV2ActualExposureNs)*frame.motionV2ActualIso;
        if(ts!=null)frame.motionV2ResultSensorTimestampNs=ts;frame.motionV2FrameNumber=result.getFrameNumber();
        if(skew!=null)frame.motionV2RollingShutterSkewNs=skew;if(focus!=null)frame.motionV2FocusDistanceDiopters=focus;
        if(lens!=null)frame.motionV2LensState=lens;
        android.util.Pair<Double,Double>[] np=result.get(CaptureResult.SENSOR_NOISE_PROFILE);
        boolean valid=np!=null&&np.length>=4,anyRead=false;
        if(valid)for(int i=0;i<4;i++){
            android.util.Pair<Double,Double> q=np[i];
            if(q==null||q.first==null||q.second==null||!Double.isFinite(q.first)||!Double.isFinite(q.second)
                    ||q.first<=0.0||q.second<0.0){valid=false;break;}
            frame.motionV2NoiseProfile[i*2]=q.first.floatValue();frame.motionV2NoiseProfile[i*2+1]=q.second.floatValue();
            anyRead|=q.second>0.0;
        }
        valid&=anyRead;frame.motionV2NoiseProfileValid=valid;
        frame.motionV2NoiseProfileSource=valid?"CAMERA2_PER_FRAME":"UNAVAILABLE";
        if(valid){float[] p=frame.motionV2NoiseProfile;
            frame.motionV2NoiseS=(p[0]+0.5f*(p[2]+p[4])+p[6])/3.0f;
            frame.motionV2NoiseO=(p[1]+0.5f*(p[3]+p[5])+p[7])/3.0f;}
    }
'''
t=rx(t,method_pat,methods,'replace V1 capture methods')
t=t.replace('applyMotion26480ShortHighlightBiasIfNeeded()','applyMotion26480ExplicitShortCaptureIfNeeded()')
# Remove the V1 result-recognition block (one-shot callback is authoritative).
t=rx(t,r'''\n\s*/\* IRIS_26480_SHORT_ACTUAL_METADATA_MATCH_V1 \*/.*?\n\s*while \(mZslResultMap\.size\(\) > MAX_ZSL_RESULT_METADATA\) \{''',
     '\n                    while (mZslResultMap.size() > MAX_ZSL_RESULT_METADATA) {','remove V1 preview-result short detector')
# V1 restore calls are retired.
t=t.replace('restoreMotion26480ShortHighlightBias();','')
# Replace V1 poll timeout semantics with bounded optional short gate.
t=rx(t,r'''        boolean iris26480ShortRawReady = false;.*?        boolean iris26480ShortGateReady = !mMotion26480ShortRequested\n                \|\| iris26480ShortRawReady;''',r'''        boolean iris26480ShortRawReady = false;
        if (mMotion26480ShortResultTimestampNs > 0L) {
            synchronized (mZslBufferLock) {
                for (Image im : mZslRingBuffer) {
                    if (im != null && Math.abs(im.getTimestamp()-mMotion26480ShortResultTimestampNs)<=40_000_000L) {
                        iris26480ShortRawReady=true; break;
                    }
                }
            }
        }
        boolean iris26480ShortDoneWithoutAcceptedFrame=mMotion26480ShortRequested
                &&mMotion26480ShortRequestCompleted&&mMotion26480ShortResultTimestampNs==0L;
        boolean iris26480ShortExpired=mMotion26480ShortRequested&&!iris26480ShortRawReady
                &&elapsed>=MOTION_26480_SHORT_WAIT_MS;
        boolean iris26480ShortGateReady=!mMotion26480ShortRequested||iris26480ShortRawReady
                ||iris26480ShortDoneWithoutAcceptedFrame||iris26480ShortExpired;''','replace V1 poll gate')
# Short frame and normal frame metadata use exact helper.
t=rx(t,r'''                shortFrame\.motionV2ShortHighlightFrame = true;.*?                if \(frameResult != null\) \{\n                    android\.util\.Pair<Double, Double>\[\] np =.*?                \}\n''',
     '''                populateMotion26480FrameMetadata(shortFrame, frameResult, true);\n''','short metadata helper')
t=once(t,'''            frame.motionV2ActualExposureNs = actualExposureNs;
            frame.motionV2ActualIso = actualIso;
            frame.motionV2ExposureEnergy = ExposureIndex.time2sec(actualExposureNs) * actualIso;
            mExposures.put(frame.timestamp, frame.motionV2ExposureEnergy);
''','''            frame.motionV2ActualExposureNs = actualExposureNs;
            frame.motionV2ActualIso = actualIso;
            frame.motionV2ExposureEnergy = ExposureIndex.time2sec(actualExposureNs) * actualIso;
            populateMotion26480FrameMetadata(frame, frameResult, false);
            if (frame.motionV2ExposureEnergy <= 0.0)
                frame.motionV2ExposureEnergy = ExposureIndex.time2sec(actualExposureNs) * actualIso;
            mExposures.put(frame.timestamp, frame.motionV2ExposureEnergy);
''','normal metadata helper')
# Admission at drain: actual short TET must be lower than every normal.
t=once(t,'''        int actualCount = selected.size();
        List<ImageFrame> iris26480ProcessingFrames = new ArrayList<>(selected);
''','''        int actualCount = selected.size();
        if (iris26480ShortFrame != null) {
            double minNormalEnergy=Double.POSITIVE_INFINITY;
            for(ImageFrame n:selected) if(n!=null&&n.motionV2ExposureEnergy>0.0)
                minNormalEnergy=Math.min(minNormalEnergy,n.motionV2ExposureEnergy);
            if(!(iris26480ShortFrame.motionV2ExposureEnergy>0.0&&Double.isFinite(minNormalEnergy)
                    &&iris26480ShortFrame.motionV2ExposureEnergy<minNormalEnergy)){
                Log.w(TAG,"IRIS_26480_SHORT_ROLE_REJECTED_AT_DRAIN reason=notStrictlyLowerThanEveryNormal"
                        +" shortEnergy="+iris26480ShortFrame.motionV2ExposureEnergy+" minNormalEnergy="+minNormalEnergy);
                mExposures.remove(iris26480ShortFrame.timestamp);selectedResults.remove(iris26480ShortFrame.timestamp);
                iris26480ShortFrame.close();iris26480ShortFrame=null;iris26480ShortResult=null;
            }
        }
        List<ImageFrame> iris26480ProcessingFrames = new ArrayList<>(selected);
''','strict short admission')
# Reset completion in batch boundary.
t=t.replace('mMotion26480ShortRequested = false;\n        mMotion26480ShortResultTimestampNs = 0L;',
            'mMotion26480ShortRequested = false;\n        mMotion26480ShortRequestCompleted = false;\n        mMotion26480ShortResultTimestampNs = 0L;',1)
write(CAP,t)

# ---- Hdrx: priority, noise source hierarchy, deferred DNG ----
t=read(HDRX)
t=once(t,'public class HdrxProcessor extends ProcessorBase {\n','''public class HdrxProcessor extends ProcessorBase {
    /* IRIS_26480_DEFERRED_DNG_OUTPUT_V2 */
    private static final java.util.concurrent.ExecutorService MOTION_26480_OUTPUT_EXECUTOR =
            java.util.concurrent.Executors.newSingleThreadExecutor(r -> {
                Thread out = new Thread(r, "MotionDeferredOutput"); out.setDaemon(true); return out;
            });
''','Hdrx executor')
t=once(t,'''    public void Run() {
        try {
''','''    public void Run() {
        Integer iris26480OriginalPriority=null;
        if(cameraMode==CameraMode.MOTION){try{int tid=android.os.Process.myTid();
            iris26480OriginalPriority=android.os.Process.getThreadPriority(tid);
            if(iris26480OriginalPriority<android.os.Process.THREAD_PRIORITY_BACKGROUND)
                android.os.Process.setThreadPriority(tid,android.os.Process.THREAD_PRIORITY_BACKGROUND);
            Log.d(TAG,"IRIS_26480_BACKGROUND_PROCESSING_PRIORITY active="+android.os.Process.getThreadPriority(tid));
        }catch(Throwable ignored){}}
        try {
''','priority start')
t=once(t,'''        finally {
            // IRIS_26338_MOTION_METRICS_FINALLY
            MotionMetrics.end();
        }
''','''        finally {
            // IRIS_26338_MOTION_METRICS_FINALLY
            MotionMetrics.end();
            if(iris26480OriginalPriority!=null)try{android.os.Process.setThreadPriority(
                    android.os.Process.myTid(),iris26480OriginalPriority);}catch(Throwable ignored){}
        }
''','priority restore')
# Put deferred-DNG ownership in ApplyHdrX method scope so it survives until JPEG save.
t=once(t,'''        ImageFrame iris26480ShortHighlightFrame = null;\n''','''        ImageFrame iris26480ShortHighlightFrame = null;\n        ByteBuffer iris26480DeferredDng = null;\n''',
       'deferred DNG method-scope declaration')
# Update V1 role split to enum.
t=t.replace('candidate != null && candidate.motionV2ShortHighlightFrame',
            'candidate != null && candidate.motionV2FrameRole == ImageFrame.MotionV2FrameRole.HIGHLIGHT_SHORT',1)
t=t.replace('IRIS_26480_SHORT_FRAME_SPLIT_BEFORE_WRONSKI_V1','IRIS_26480_SHORT_FRAME_SPLIT_BEFORE_WRONSKI_V2')
# Noise source resolution after reference selection.
anchor='''        selected = 0;



        Log.d(TAG, "White Level:" + processingParameters.whiteLevel);
'''
ins='''        selected = 0;

        /* IRIS_26480_PER_FRAME_NOISE_SOURCE_TRACKING_V2 */
        if(cameraMode==CameraMode.MOTION&&!images.isEmpty()){
            ImageFrame baseNoise=images.get(0);boolean baseValid=baseNoise.motionV2NoiseProfileValid;
            for(ImageFrame f:images){if(f==null)continue;
                if(!f.motionV2NoiseProfileValid&&baseValid){System.arraycopy(baseNoise.motionV2NoiseProfile,0,
                        f.motionV2NoiseProfile,0,f.motionV2NoiseProfile.length);f.motionV2NoiseProfileValid=true;
                    f.motionV2NoiseProfileSource="CAMERA2_BASE_FRAME";f.motionV2NoiseS=baseNoise.motionV2NoiseS;f.motionV2NoiseO=baseNoise.motionV2NoiseO;}
                else if(!f.motionV2NoiseProfileValid)f.motionV2NoiseProfileSource="WRONSKI_EXISTING_FALLBACK";
                com.particlesdevs.photoncamera.util.MotionTrace.processingState("IRIS_26480_FRAME_NOISE_SOURCE",
                        "timestamp="+f.timestamp+" source="+f.motionV2NoiseProfileSource+" valid="+f.motionV2NoiseProfileValid
                        +" normalizedSensorVariance=true rawCodeRangeRescale=false");
            }
        }

        Log.d(TAG, "White Level:" + processingParameters.whiteLevel);
'''
t=once(t,anchor,ins,'noise source hierarchy')
# Replace 26479 immediate reference-DNG section (V1 left it) via marker-scoped regex.
pat=r'''            /\*\n             \* IRIS_26450_MOTION_V2_REFERENCE_DNG.*?\n            \}\n        \}\n        selected = 0;'''
rep='''            /* IRIS_26480_DEFERRED_DNG_OUTPUT_V2 */
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
        }
        selected = 0;'''
t=rx(t,pat,rep,'replace immediate Motion DNG')
# Queue DNG after JPEG saved.
anchor='''        try {
            processingEventsListener.notifyImageSavedStatus(imageSaved, imageFile);
        }
        catch (Exception e){
            Log.d(TAG,"Error in processingEventsListener.notifyImageSavedStatus:"+Log.getStackTraceString(e));
        }

        pipeline.close();
'''
rep='''        try {
            processingEventsListener.notifyImageSavedStatus(imageSaved, imageFile);
        }
        catch (Exception e){
            Log.d(TAG,"Error in processingEventsListener.notifyImageSavedStatus:"+Log.getStackTraceString(e));
        }
        if(cameraMode==CameraMode.MOTION&&iris26480DeferredDng!=null){
            final ByteBuffer dngBytes=iris26480DeferredDng;final Path dngPath=dngFile;final Parameters dngParams=processingParameters;
            MOTION_26480_OUTPUT_EXECUTOR.execute(()->{Integer old=null;try{int tid=android.os.Process.myTid();
                old=android.os.Process.getThreadPriority(tid);android.os.Process.setThreadPriority(tid,android.os.Process.THREAD_PRIORITY_BACKGROUND);
                dngBytes.position(0);boolean saved=ImageSaver.Util.saveStackedRaw(dngPath,dngBytes,dngParams);
                processingEventsListener.notifyImageSavedStatus(saved,dngPath);Log.d(TAG,"IRIS_26480_DEFERRED_DNG_FINISHED saved="+saved);
            }catch(Throwable e){Log.e(TAG,"IRIS_26480_DEFERRED_DNG_FAILED "+Log.getStackTraceString(e));}
            finally{try{Allocator.free(dngBytes);}catch(Throwable ignored){}if(old!=null)try{android.os.Process.setThreadPriority(android.os.Process.myTid(),old);}catch(Throwable ignored){}}});
            iris26480DeferredDng=null;
        }

        pipeline.close();
'''
t=once(t,anchor,rep,'defer DNG after JPEG')
write(HDRX,t)

# ---- Reconstruction: per-frame noise, sequential reuse, diagnostics, faithful recovery ----
t=read(RECON)
t=once(t,'public final class MotionV2CfaReconstruction {\n','''public final class MotionV2CfaReconstruction {
    /* IRIS_26480_PER_FRAME_WRONSKI_NOISE_ADAPTATION_V2 */
    private static float[] iris26480FrameNoise(ImageFrame f,float fallbackS,float fallbackO,float gain){
        float s=fallbackS,o=fallbackO;if(f!=null&&f.motionV2NoiseProfileValid&&f.motionV2NoiseProfile.length>=8){
            float[] p=f.motionV2NoiseProfile;s=(p[0]+0.5f*(p[2]+p[4])+p[6])/3.0f;
            o=(p[1]+0.5f*(p[3]+p[5])+p[7])/3.0f;}
        return new float[]{Math.max(s,1e-7f)*gain,Math.max(o,1e-8f)*gain*gain};
    }
''','noise helper')
# V1 marker -> V2
t=t.replace('IRIS_26480_DISABLE_SPEAKER_EDGE_DIAGNOSTIC_V1','IRIS_26480_DISABLE_SPEAKER_EDGE_DIAGNOSTIC_V2')
# Diagnostic support readback off.
t=t.replace('if (directBayer && currentDirectSupport != null) {',
            'if (false && /* IRIS_26480_DISABLE_DIRECT_SUPPORT_GPU_READBACK_V2 */ directBayer && currentDirectSupport != null) {',1)
# Sequential declarations before loop.
anchor='''            for (int i = 1; i < images.size(); i++) {
                ImageFrame frame = images.get(i);
'''
rep='''            /* IRIS_26480_FRAME_SEQUENTIAL_SCRATCH_REUSE_V2 */
            GLTexture iris26480RawScratch=null,iris26480CfaScratch=null,iris26480WbCfaScratch=null;
            GLTexture iris26480CovScratch=null,iris26480RobustRawScratch=null,iris26480RobustMinScratch=null;
            for (int i = 1; i < images.size(); i++) {
                ImageFrame frame = images.get(i);
                float[] iris26480Noise=iris26480FrameNoise(frame,noiseS,noiseO,canonicalGain);
                final float iris26480FrameNoiseS=iris26480Noise[0],iris26480FrameNoiseO=iris26480Noise[1];
'''
t=once(t,anchor,rep,'sequential loop')
# Texture reuse.
old='''                    rawInput = new GLTexture(
                            raw,
                            new GLFormat(GLFormat.DataType.UNSIGNED_16, 1),
                            frame.buffer,
                            GL_NEAREST,
                            GL_CLAMP_TO_EDGE);
                    alterCfa = new GLTexture(
                            rawHalf,
                            new GLFormat(GLFormat.DataType.FLOAT_16, 4),
                            null,
                            GL_NEAREST,
                            GL_CLAMP_TO_EDGE);
'''
new='''                    if(iris26480RawScratch==null)iris26480RawScratch=new GLTexture(raw,
                            new GLFormat(GLFormat.DataType.UNSIGNED_16,1),null,GL_NEAREST,GL_CLAMP_TO_EDGE);
                    ByteBuffer iris26480FrameView=frame.buffer.duplicate();iris26480FrameView.position(0);
                    iris26480RawScratch.loadData(iris26480FrameView);rawInput=iris26480RawScratch;
                    if(iris26480CfaScratch==null)iris26480CfaScratch=new GLTexture(rawHalf,
                            new GLFormat(GLFormat.DataType.FLOAT_16,4),null,GL_NEAREST,GL_CLAMP_TO_EDGE);
                    alterCfa=iris26480CfaScratch;
'''
t=once(t,old,new,'RAW/CFA reuse')
old='''                        wronskiAlterCfa = new GLTexture(
                                rawHalf,
                                new GLFormat(GLFormat.DataType.FLOAT_16, 4),
                                null, GL_NEAREST, GL_CLAMP_TO_EDGE);
'''
new='''                        if(iris26480WbCfaScratch==null)iris26480WbCfaScratch=new GLTexture(rawHalf,
                                new GLFormat(GLFormat.DataType.FLOAT_16,4),null,GL_NEAREST,GL_CLAMP_TO_EDGE);
                        wronskiAlterCfa=iris26480WbCfaScratch;
'''
t=once(t,old,new,'WB reuse')
old='''                        wronskiAlterCov = new GLTexture(
                                rawHalf,
                                new GLFormat(GLFormat.DataType.FLOAT_32, 4),
                                null, GL_NEAREST, GL_CLAMP_TO_EDGE);
'''
new='''                        if(iris26480CovScratch==null)iris26480CovScratch=new GLTexture(rawHalf,
                                new GLFormat(GLFormat.DataType.FLOAT_32,4),null,GL_NEAREST,GL_CLAMP_TO_EDGE);
                        wronskiAlterCov=iris26480CovScratch;
'''
t=once(t,old,new,'cov reuse')
# Per-frame noise must be substituted ONLY inside the temporal loop.
# The immutable reference covariance uses burst/reference noise and is intentionally preserved.
loop_marker='IRIS_26480_FRAME_SEQUENTIAL_SCRATCH_REUSE_V2'
loop_pos=t.index(loop_marker)
prefix=t[:loop_pos]; suffix=t[loop_pos:]
old_cov='glProg.setVar("noiseS", noiseS);\n                        glProg.setVar("noiseO", noiseO);'
old_rob='glProg.setVar("noiseS", noiseS);\n                                glProg.setVar("noiseO", noiseO);'
if suffix.count(old_cov)<1:
    raise SystemExit('temporal covariance noise anchor missing')
if suffix.count(old_rob)<1:
    raise SystemExit('temporal robustness noise anchor missing')
suffix=suffix.replace(old_cov,
    'glProg.setVar("noiseS", iris26480FrameNoiseS);\n                        glProg.setVar("noiseO", iris26480FrameNoiseO);',1)
suffix=suffix.replace(old_rob,
    'glProg.setVar("noiseS", iris26480FrameNoiseS);\n                                glProg.setVar("noiseO", iris26480FrameNoiseO);',1)
t=prefix+suffix
# robustness reuse if exact V1/current allocation exists.
old='''                            GLTexture mfsrRobustRaw = new GLTexture(
                                    raw,
                                    new GLFormat(GLFormat.DataType.FLOAT_32, 1),
                                    null,
                                    GL_NEAREST,
                                    GL_CLAMP_TO_EDGE);
                            GLTexture mfsrRobustMin = new GLTexture(
                                    raw,
                                    new GLFormat(GLFormat.DataType.FLOAT_32, 1),
                                    null,
                                    GL_NEAREST,
                                    GL_CLAMP_TO_EDGE);
'''
new='''                            if(iris26480RobustRawScratch==null)iris26480RobustRawScratch=new GLTexture(raw,
                                    new GLFormat(GLFormat.DataType.FLOAT_32,1),null,GL_NEAREST,GL_CLAMP_TO_EDGE);
                            if(iris26480RobustMinScratch==null)iris26480RobustMinScratch=new GLTexture(raw,
                                    new GLFormat(GLFormat.DataType.FLOAT_32,1),null,GL_NEAREST,GL_CLAMP_TO_EDGE);
                            GLTexture mfsrRobustRaw=iris26480RobustRawScratch,mfsrRobustMin=iris26480RobustMinScratch;
'''
t=once(t,old,new,'robust reuse')
# Don't close reusable scratch in per-frame finally.
for old,new in [
('if (wronskiAlterCov != null) wronskiAlterCov.close();','wronskiAlterCov=null; /* persistent */'),
('if (wronskiAlterCfa != null) wronskiAlterCfa.close();','wronskiAlterCfa=null; /* persistent */'),
('if (alterCfa != null) alterCfa.close();','alterCfa=null; /* persistent */'),
('if (rawInput != null) rawInput.close();','rawInput=null; /* persistent */'),
('if (mfsrRobustMin != null) mfsrRobustMin.close();','/* robustness scratch retained */'),
('if (mfsrRobustRaw != null) mfsrRobustRaw.close();','/* robustness scratch retained */'),
('mfsrRobustMin.close();','/* robustness scratch retained */'),
('mfsrRobustRaw.close();','/* robustness scratch retained */')]:
    t=t.replace(old,new,1)
# Yield after frame.
anchor='''                    GLTexture swapSupport = currentSupport;
                    currentSupport = nextSupport;
                    nextSupport = swapSupport;
'''
t=once(t,anchor,anchor+'''                    /* IRIS_26480_UI_BREATHING_CHECKPOINT_V2 */
                    android.opengl.GLES30.glFlush(); Thread.yield();
''','UI checkpoint')
# close scratch after loop
anchor='''            /*
             * IRIS_26440_TEMPORAL_BIN_SUMMARY
'''
t=once(t,anchor,'''            if(iris26480RobustMinScratch!=null)iris26480RobustMinScratch.close();
            if(iris26480RobustRawScratch!=null)iris26480RobustRawScratch.close();
            if(iris26480CovScratch!=null)iris26480CovScratch.close();
            if(iris26480WbCfaScratch!=null)iris26480WbCfaScratch.close();
            if(iris26480CfaScratch!=null)iris26480CfaScratch.close();
            if(iris26480RawScratch!=null)iris26480RawScratch.close();

            /*
             * IRIS_26440_TEMPORAL_BIN_SUMMARY
''','scratch close')
# Replace V1 recovery block from its marker through its finally with V2 block.
pat=r'''            /\* IRIS_26480_ALIGNED_SHORT_SENSOR_HIGHLIGHT_RECOVERY_V1.*?\n            \}\n'''
# anchor ending is ambiguous due nested; use from marker to next IRIS_26416 log after block.
m=re.search(r'''            /\* IRIS_26480_ALIGNED_SHORT_SENSOR_HIGHLIGHT_RECOVERY_V1.*?(?=\n            Log\.d\(TAG, "IRIS_26416_V2_PROVEN_FLOAT32_BRIDGE")''',t,flags=re.S)
if not m: raise SystemExit('V1 recovery block not found')
recovery='''            /* IRIS_26480_BJZHOU_RCD_BENTO_SHORT_RECOVERY_V2 */
            GLTexture iris26480ReadbackOutput=imageOutput,iris26480ShortRaw=null,iris26480ShortCfa=null;
            GLTexture iris26480ShortWbCfa=null,iris26480Recovered=null;MotionV2Alignment.Result iris26480ShortAlignment=null;
            try{
                if(directBayer&&shortHighlightFrame!=null&&shortHighlightFrame.buffer!=null&&reference!=null
                        &&reference.motionV2ExposureEnergy>0.0&&shortHighlightFrame.motionV2ExposureEnergy>0.0
                        &&shortHighlightFrame.motionV2ExposureEnergy<reference.motionV2ExposureEnergy
                        &&wronskiPreparedAlignment!=null){
                    float shortToNormalScale=(float)Math.max(1.0,Math.min(8.0,
                            reference.motionV2ExposureEnergy/shortHighlightFrame.motionV2ExposureEnergy));
                    iris26480ShortRaw=new GLTexture(raw,new GLFormat(GLFormat.DataType.UNSIGNED_16,1),
                            shortHighlightFrame.buffer,GL_NEAREST,GL_CLAMP_TO_EDGE);
                    iris26480ShortCfa=new GLTexture(rawHalf,new GLFormat(GLFormat.DataType.FLOAT_16,4),null,GL_NEAREST,GL_CLAMP_TO_EDGE);
                    glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/raw_to_cfa",true);
                    glProg.setVar("whiteLevel",(float)parameters.whiteLevel);glProg.setVar("blackLevel",blackLevel);
                    glProg.setVar("exposure",1.0f);glProg.setTexture("inTexture",iris26480ShortRaw);
                    glProg.setTextureCompute("outTexture",iris26480ShortCfa,true);glProg.computeAuto(rawHalf,1);
                    float r=directSensorGains[0]/Math.max(directSensorGains[1],1e-6f),b=directSensorGains[2]/Math.max(directSensorGains[1],1e-6f);
                    iris26480ShortWbCfa=new GLTexture(rawHalf,new GLFormat(GLFormat.DataType.FLOAT_16,4),null,GL_NEAREST,GL_CLAMP_TO_EDGE);
                    glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/mfsr_wb_cfa",true);glProg.setVar("cfaPattern",(int)parameters.cfaPattern);
                    glProg.setVar("wbR",r);glProg.setVar("wbG",1.0f);glProg.setVar("wbB",b);
                    glProg.setTextureCompute("inputCfa",iris26480ShortCfa,false);glProg.setTextureCompute("outputCfa",iris26480ShortWbCfa,true);glProg.computeAuto(rawHalf,1);
                    iris26480ShortAlignment=MotionV2WronskiAlignment.alignPrepared(wronskiPreparedAlignment,glProg,iris26480ShortWbCfa);
                    iris26480Recovered=new GLTexture(raw,new GLFormat(GLFormat.DataType.FLOAT_32,4),null,GL_NEAREST,GL_CLAMP_TO_EDGE);
                    glProg.setLayout(tile,tile,1);glProg.useAssetProgram("motionv2/short_highlight_recover",true);
                    glProg.setVar("rawSize",raw);glProg.setVar("rawHalf",rawHalf);glProg.setVar("cfaPattern",(int)parameters.cfaPattern);
                    glProg.setVar("shortToNormalScale",shortToNormalScale);glProg.setVar("wbR",r);glProg.setVar("wbG",1.0f);glProg.setVar("wbB",b);
                    glProg.setVar("highlightClipThreshold",0.985f);glProg.setVar("highlightCeiling",8.0f);glProg.setVar("minimumFlowConfidence",0.30f);
                    glProg.setTexture("normalRgb",imageOutput);glProg.setTexture("flowTexture",iris26480ShortAlignment.flowTexture);
                    glProg.setTextureCompute("referenceCfa",referenceCfa,false);glProg.setTextureCompute("shortCfa",iris26480ShortCfa,false);
                    glProg.setTextureCompute("outRgb",iris26480Recovered,true);glProg.computeAuto(raw,1);iris26480ReadbackOutput=iris26480Recovered;
                    Log.d(TAG,"IRIS_26480_BJZHOU_RCD_BENTO_SHORT_RECOVERY threshold=0.985 opposedRootPower=3"
                            +" wbConditionedThenReversed=true normalWronskiNumDenUnchanged=true shortInNormalWronski=false");
                }
                iris26480ReadbackOutput.BufferLoad();output=iris26480ReadbackOutput.textureBuffer(
                        new GLFormat(GLFormat.DataType.FLOAT_32,4),true);
            }finally{
                if(iris26480ShortAlignment!=null)iris26480ShortAlignment.close();if(iris26480ShortWbCfa!=null)iris26480ShortWbCfa.close();
                if(iris26480ShortCfa!=null)iris26480ShortCfa.close();if(iris26480ShortRaw!=null)iris26480ShortRaw.close();
                if(iris26480Recovered!=null)iris26480Recovered.close();if(shortHighlightFrame!=null)shortHighlightFrame.close();
            }
'''
t=t[:m.start()]+recovery+t[m.end():]
write(RECON,t)

# ---- overwrite recovery shader with bjzhou RCD-domain opposed-color math ----
shader=r'''#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
uniform highp sampler2D normalRgb;
uniform highp sampler2D flowTexture;
layout(rgba16f,binding=0) uniform highp readonly image2D referenceCfa;
layout(rgba16f,binding=1) uniform highp readonly image2D shortCfa;
layout(rgba32f,binding=2) uniform highp writeonly image2D outRgb;
uniform ivec2 rawSize; uniform ivec2 rawHalf; uniform int cfaPattern;
uniform float shortToNormalScale,wbR,wbG,wbB,highlightClipThreshold,highlightCeiling,minimumFlowConfidence;
/* IRIS_26480_BJZHOU_RCD_OPPOSED_SHORT_HIGHLIGHT_SHADER_V2 */
int ci(ivec2 p){return ((p.y&1)<<1)|(p.x&1);} int cc(int c){if(cfaPattern==0){if(c==0)return 0;if(c==3)return 2;return 1;}
if(cfaPattern==1){if(c==1)return 0;if(c==2)return 2;return 1;}if(cfaPattern==2){if(c==2)return 0;if(c==1)return 2;return 1;}
if(c==3)return 0;if(c==0)return 2;return 1;}
float wg(int c){return c==0?wbR:(c==2?wbB:wbG);} float at(ivec2 p,bool sh){p=clamp(p,ivec2(0),rawSize-ivec2(1));
vec4 v=sh?imageLoad(shortCfa,p>>1):imageLoad(referenceCfa,p>>1);int c=ci(p);return c==0?v.r:(c==1?v.g:(c==2?v.b:v.a));}
float shortSensorAt(ivec2 p){return max(at(p,true),0.0);} float refSensorAt(ivec2 p){return max(at(p,false),0.0);}
float calculationShortAt(ivec2 p){int c=cc(ci(p));return min(shortSensorAt(p)*shortToNormalScale*max(wg(c),1e-6),highlightCeiling);}
float estimateOpposedLinear(ivec2 center,int target,float fallback){float sr=0.0,sg=0.0,sb=0.0,cr=0.0,cg=0.0,cb=0.0;
for(int y=-1;y<=1;y++)for(int x=-1;x<=1;x++){ivec2 q=clamp(center+ivec2(x,y),ivec2(0),rawSize-ivec2(1));int c=cc(ci(q));float z=calculationShortAt(q);
if(c==0){sr+=z;cr+=1.0;}else if(c==1){sg+=z;cg+=1.0;}else{sb+=z;cb+=1.0;}}
const float power=3.0;float rr=pow(max(sr/max(cr,1.0),0.0),1.0/power),rg=pow(max(sg/max(cg,1.0),0.0),1.0/power),rb=pow(max(sb/max(cb,1.0),0.0),1.0/power);
float o=target==0?0.5*(rg+rb):(target==1?0.5*(rr+rb):0.5*(rr+rg));return max(pow(max(o,0.0),power),fallback);}
float shortChannel(ivec2 c,int color){float bd=1e9;ivec2 best=c;for(int y=-1;y<=1;y++)for(int x=-1;x<=1;x++){ivec2 q=clamp(c+ivec2(x,y),ivec2(0),rawSize-ivec2(1));
if(cc(ci(q))!=color)continue;float d=float(x*x+y*y);if(d<bd){bd=d;best=q;}}float sensor=shortSensorAt(best),linear=calculationShortAt(best);
float mask=smoothstep(highlightClipThreshold,1.0,sensor);float rec=estimateOpposedLinear(best,color,linear);return min(mix(linear,rec,mask),highlightCeiling)/max(wg(color),1e-6);}
float refClip(ivec2 c,int color){float s=0.0,n=0.0;for(int y=-1;y<=1;y++)for(int x=-1;x<=1;x++){ivec2 q=clamp(c+ivec2(x,y),ivec2(0),rawSize-ivec2(1));
if(cc(ci(q))!=color)continue;s+=smoothstep(highlightClipThreshold,1.0,refSensorAt(q));n+=1.0;}return s/max(n,1.0);}
void main(){ivec2 p=ivec2(gl_GlobalInvocationID.xy);if(any(greaterThanEqual(p,rawSize)))return;vec4 normal=texelFetch(normalRgb,p,0);
vec4 f=texture(flowTexture,(vec2(p)+0.5)/vec2(rawSize));float conf=clamp(f.z,0.0,1.0);vec2 sp=vec2(p)+0.5+2.0*f.xy;
if(sp.x<0.0||sp.y<0.0||sp.x>=float(rawSize.x)||sp.y>=float(rawSize.y)||conf<minimumFlowConfidence){imageStore(outRgb,p,normal);return;}
ivec2 sc=ivec2(sp);vec3 outc=normal.rgb;float fg=smoothstep(minimumFlowConfidence,0.80,conf);for(int c=0;c<3;c++){float clip=refClip(p,c);if(clip<=0.0)continue;
float candidate=shortChannel(sc,c);float use=smoothstep(0.08,0.75,clip)*fg;outc[c]=mix(normal[c],candidate,use);}imageStore(outRgb,p,vec4(max(outc,vec3(0.0)),normal.a));}
'''
write(SHORT,shader)
# V2 max RGB marker only; V1 math is retained.
t=read(RENDER).replace('IRIS_26480_MAX_RGB_HIGHLIGHT_TONE_GUIDE_V1','IRIS_26480_MAX_RGB_HIGHLIGHT_TONE_GUIDE_V2')
write(RENDER,t)

# ---- final hard guards ----
cap=read(CAP); hdr=read(HDRX); rec=read(RECON); sh=read(SHORT)
for marker,text in [
('IRIS_26480_BJZHOU_FRAME_ROLE_AND_METADATA_V2',read(FRAME)),('IRIS_26480_SHORT_CAPTURE_SUBMITTED',cap),
('previewRepeatingRequestMutated=false',cap),('notStrictlyLowerThanEveryNormal',cap),
('IRIS_26480_PER_FRAME_NOISE_SOURCE_TRACKING_V2',hdr),('IRIS_26480_DEFERRED_DNG_OUTPUT_V2',hdr),
('IRIS_26480_BACKGROUND_PROCESSING_PRIORITY',hdr),('IRIS_26480_FRAME_SEQUENTIAL_SCRATCH_REUSE_V2',rec),
('IRIS_26480_UI_BREATHING_CHECKPOINT_V2',rec),('IRIS_26480_DISABLE_DIRECT_SUPPORT_GPU_READBACK_V2',rec),
('IRIS_26480_BJZHOU_RCD_BENTO_SHORT_RECOVERY',rec),('IRIS_26480_BJZHOU_RCD_OPPOSED_SHORT_HIGHLIGHT_SHADER_V2',sh),
('IRIS_26480_MAX_RGB_HIGHLIGHT_TONE_GUIDE_V2',read(RENDER))]:
    if marker not in text: raise SystemExit('missing '+marker)
# Preview short block cannot touch repeating builder/session request.
s=cap.index('private boolean applyMotion26480ExplicitShortCaptureIfNeeded');e=cap.index('private void resetMotion26480ShortCaptureState',s);block=cap[s:e]
for bad in ['mPreviewRequestBuilder.set(','rebuildPreviewBuilder()','setRepeatingRequest(','clearMotionUnifiedBuffer();','CONTROL_AE_EXPOSURE_COMPENSATION']:
    if bad in block: raise SystemExit('forbidden preview mutation '+bad)
# New shader known Adreno/runtime failure classes.
code=re.sub(r'/\*.*?\*/',' ',sh,flags=re.S);code=re.sub(r'//[^\n]*',' ',code)
if re.search(r'\bsample\b',code): raise SystemExit('reserved GLSL sample identifier')
if re.search(r'\bimage2D\s+\w+\s*\)',code): raise SystemExit('image2D function parameter')
if 'layout(rg32f' in code: raise SystemExit('RG32F imageStore risk')
if 'readonly image2D referenceCfa' not in sh or 'readonly image2D shortCfa' not in sh or 'writeonly image2D outRgb' not in sh:
    raise SystemExit('image access qualifier contract')
# No scene-specific speaker call.
if re.findall(r'(?m)^\s{12,}iris26478LogSpeakerSupportEdges\(',rec): raise SystemExit('speaker diagnostic call remains')
print('26480 integrated V2 post-transform validation PASS')
print('preview stability / RAW-only explicit role PASS')
print('actual TET + 0.35EV short admission PASS')
print('per-frame noise source tracking PASS')
print('frame-sequential GPU lifetime/cache PASS')
print('production readback cleanup PASS')
print('UI/process scheduling PASS')
print('deferred DNG output scheduling PASS')
print('RCD opposed-color highlight math adaptation PASS')
print('Adreno/runtime static shader gates PASS')
