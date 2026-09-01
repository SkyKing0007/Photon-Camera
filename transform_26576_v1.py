#!/usr/bin/env python3
from pathlib import Path
import shutil, sys

def once(s, old, new, label):
    n=s.count(old)
    if n!=1: raise SystemExit(f'FAIL {label}: anchor count={n}')
    return s.replace(old,new,1)

def main():
    if len(sys.argv)!=3: raise SystemExit('usage: transform base candidate')
    base=Path(sys.argv[1]); out=Path(sys.argv[2])
    if out.exists(): shutil.rmtree(out)
    shutil.copytree(base,out)

    # CaptureController: persist the already-frozen 26575 shutter state with an actual shot id.
    p=out/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java'
    s=p.read_text()
    s=once(s,
'''        mMotionDiagnosticShotId =
                com.particlesdevs.photoncamera.util.MotionTrace.beginShot(
                        physicalID,
                        mMotionTopUpTargetFrames,
                        buffered,
                        mMotionManualLadderActive,
                        mMotionUnifiedGeneration);

        com.particlesdevs.photoncamera.util.MotionTrace.state(''',
'''        mMotionDiagnosticShotId =
                com.particlesdevs.photoncamera.util.MotionTrace.beginShot(
                        physicalID,
                        mMotionTopUpTargetFrames,
                        buffered,
                        mMotionManualLadderActive,
                        mMotionUnifiedGeneration);

        /* IRIS_26576_SR_SHOT_SCOPED_SHUTTER_PROOF
         * Mirror the already-proven 26575 immutable shutter decision into the persistent trace
         * after beginShot() assigns the diagnostic shot id. No capture state is changed here.
         */
        com.particlesdevs.photoncamera.util.MotionTrace.state(
                mMotionDiagnosticShotId,
                "IRIS_26576_SR_SHUTTER_STATE",
                "frozen=" + mMotion26575SuperResAtShutter
                        + " preferenceReadbackDiagnosticOnly=" + PreferenceKeys.isIrisSuperResOn()
                        + " immutableBatch=true");

        com.particlesdevs.photoncamera.util.MotionTrace.state(''',
        'capture persistent SR shutter proof')
    p.write_text(s)

    # Camera UI: persist requested/stored commit in the same trace file (shot=0 before shutter).
    p=out/'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIController.java'
    s=p.read_text()
    s=once(s,
'''                        Log.i(TAG, "IRIS_26575_SUPER_RES_UI_COMMIT requested="
                                + iris26575RequestedSuperRes
                                + " stored=" + iris26575StoredSuperRes
                                + " match=" + (iris26575RequestedSuperRes == iris26575StoredSuperRes));
                        break;''',
'''                        Log.i(TAG, "IRIS_26575_SUPER_RES_UI_COMMIT requested="
                                + iris26575RequestedSuperRes
                                + " stored=" + iris26575StoredSuperRes
                                + " match=" + (iris26575RequestedSuperRes == iris26575StoredSuperRes));
                        /* IRIS_26576_SR_UI_PERSISTENT_PROOF */
                        com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                                "IRIS_26576_SR_UI_COMMIT",
                                "requested=" + iris26575RequestedSuperRes
                                        + " stored=" + iris26575StoredSuperRes
                                        + " match="
                                        + (iris26575RequestedSuperRes == iris26575StoredSuperRes));
                        break;''',
        'UI persistent SR commit proof')
    p.write_text(s)

    # Hdrx: persist processing-state agreement, actual JPEG dimensions, and one end-of-shot SR summary.
    p=out/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java'
    s=p.read_text()
    s=once(s,
'''            Log.i(TAG, "IRIS_26575_SUPER_RES_PROCESSING_SNAPSHOT frozen="
                    + mMotion26575SuperResEnabled
                    + " livePreferenceDiagnosticOnly="
                    + com.particlesdevs.photoncamera.settings.PreferenceKeys.isIrisSuperResOn()
                    + " outputScale=" + processingParameters.motionV2SuperResOutputScale);
            processingParameters.motionV2GlobalZoom = mMotion26524GlobalZoom;''',
'''            Log.i(TAG, "IRIS_26575_SUPER_RES_PROCESSING_SNAPSHOT frozen="
                    + mMotion26575SuperResEnabled
                    + " livePreferenceDiagnosticOnly="
                    + com.particlesdevs.photoncamera.settings.PreferenceKeys.isIrisSuperResOn()
                    + " outputScale=" + processingParameters.motionV2SuperResOutputScale);
            /* IRIS_26576_SR_PROCESSING_PERSISTENT_PROOF */
            com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                    "IRIS_26576_SR_PROCESSING_STATE",
                    "frozen=" + mMotion26575SuperResEnabled
                            + " livePreferenceDiagnosticOnly="
                            + com.particlesdevs.photoncamera.settings.PreferenceKeys.isIrisSuperResOn()
                            + " outputScale=" + processingParameters.motionV2SuperResOutputScale);
            processingParameters.motionV2GlobalZoom = mMotion26524GlobalZoom;''',
        'Hdrx processing persistent proof')
    s=once(s,
'''            Log.i(TAG, "IRIS_26575_FINAL_JPEG_DIMENSION_PROOF imageSaved=" + imageSaved
                    + " frozenSuperRes=" + mMotion26575SuperResEnabled
                    + " processingSuperRes=" + processingParameters.motionV2SuperResOutputEnabled
                    + " true2xWidth=" + iris26564True2xWidth
                    + " true2xHeight=" + iris26564True2xHeight
                    + " jpegWidth=" + iris26575JpegWidth
                    + " jpegHeight=" + iris26575JpegHeight
                    + " path=" + imageFile);
        }''',
'''            Log.i(TAG, "IRIS_26575_FINAL_JPEG_DIMENSION_PROOF imageSaved=" + imageSaved
                    + " frozenSuperRes=" + mMotion26575SuperResEnabled
                    + " processingSuperRes=" + processingParameters.motionV2SuperResOutputEnabled
                    + " true2xWidth=" + iris26564True2xWidth
                    + " true2xHeight=" + iris26564True2xHeight
                    + " jpegWidth=" + iris26575JpegWidth
                    + " jpegHeight=" + iris26575JpegHeight
                    + " path=" + imageFile);
            /* IRIS_26576_SR_FINAL_DIMENSION_PERSISTENT_PROOF */
            com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                    "IRIS_26576_SR_FINAL_DIMENSIONS",
                    "imageSaved=" + imageSaved
                            + " frozenSuperRes=" + mMotion26575SuperResEnabled
                            + " processingSuperRes=" + processingParameters.motionV2SuperResOutputEnabled
                            + " true2xWidth=" + iris26564True2xWidth
                            + " true2xHeight=" + iris26564True2xHeight
                            + " jpegWidth=" + iris26575JpegWidth
                            + " jpegHeight=" + iris26575JpegHeight);
        }''',
        'Hdrx final persistent dimensions')
    s=once(s,
'''            Log.d(TAG,"IRIS_26513_JPEG_COMPLETION_AFTER_SAVE"
                    + " imageSaved=" + imageSaved
                    + " jpegSaveAndPublishMs=" + iris26513JpegSaveMs
                    + " nonMotionCompletionUnchanged=true"
                    + " deferredDngExcluded=true");''',
'''            Log.d(TAG,"IRIS_26513_JPEG_COMPLETION_AFTER_SAVE"
                    + " imageSaved=" + imageSaved
                    + " jpegSaveAndPublishMs=" + iris26513JpegSaveMs
                    + " nonMotionCompletionUnchanged=true"
                    + " deferredDngExcluded=true");
            /* IRIS_26576_SR_CAPTURE_SUMMARY
             * One compact end-of-JPEG line. Reconstruction and final dimensions are existing
             * authorities; native publication backend/timing is emitted separately by the encoder.
             */
            com.particlesdevs.photoncamera.util.MotionTrace.processingState(
                    "IRIS_26576_SR_CAPTURE_SUMMARY",
                    "requested=" + mMotion26575SuperResEnabled
                            + " reconstructionBackend=" + iris26564True2xBackend
                            + " reconstructionMs=" + iris26564True2xReconstructionMs
                            + " phaseMean=" + iris26564True2xPhaseMean
                            + " phaseP10=" + iris26564True2xPhaseP10
                            + " true2xWidth=" + iris26564True2xWidth
                            + " true2xHeight=" + iris26564True2xHeight
                            + " jpegSaveAndPublishMs=" + iris26513JpegSaveMs
                            + " imageSaved=" + imageSaved);''',
        'Hdrx compact final summary')
    p.write_text(s)

    # Stacker: route decisive reconstruction/refinement markers through the real persistent helper.
    p=out/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'
    s=p.read_text()
    s=once(s,
'''import com.particlesdevs.photoncamera.processing.IrisTrue2xSrNative
import java.io.BufferedOutputStream''',
'''import com.particlesdevs.photoncamera.processing.IrisTrue2xSrNative
import com.particlesdevs.photoncamera.util.MotionTrace
import java.io.BufferedOutputStream''',
        'stacker MotionTrace import')
    s=once(s,
'''                PLog.i(SABRE_TAG,"IRIS_26568_TRUE2X_EVIDENCE_POLICY dngRequested=$exportNormalStackedDng " +
                    "normalFrames=$normalFrameCount retained=${reconstructionEvidence.size} jpegTop2PerPhase=${true2xFastPhaseSlots!=null}")
                val rawResult=reconstructTrue2x(frames,images,reconstructionEvidence,exportedTexture,exportNormalStackedDng)''',
'''                val evidencePolicy = "dngRequested=$exportNormalStackedDng normalFrames=$normalFrameCount " +
                    "retained=${reconstructionEvidence.size} jpegTop2PerPhase=${true2xFastPhaseSlots!=null} " +
                    "maxEvidence=${if (true2xFastPhaseSlots!=null) TRUE2X_JPEG_MAX_EVIDENCE else reconstructionEvidence.size}"
                PLog.i(SABRE_TAG,"IRIS_26568_TRUE2X_EVIDENCE_POLICY $evidencePolicy")
                MotionTrace.processingState("IRIS_26576_SR_EVIDENCE", evidencePolicy)
                val rawResult=reconstructTrue2x(frames,images,reconstructionEvidence,exportedTexture,exportNormalStackedDng)''',
        'stacker evidence proof')
    s=once(s,
'''                PLog.i(SABRE_TAG,"IRIS_26568_TRUE2X_READY normalFrames=$normalFrameCount shadowLongExcluded=$shadowLongFrameCount " +
                    "size=${result.width}x${result.height} backend=${result.backend} phaseMean=${result.phaseSupportMean} phaseP10=${result.phaseSupportP10} " +
                    "reconstruction=${result.reconstructionMs}ms dngBoundary=PRE_VGN sabreRgbChromaOwner=true highResLumaOwner=DIRECT_CFA directChromaOwner=false trueDetail26573=temporal-cross-frame directDng=${result.linearRgbPath!=null} fusedRender=${result.renderRgbPath!=null}")''',
'''                val readyDetails = "normalFrames=$normalFrameCount shadowLongExcluded=$shadowLongFrameCount " +
                    "size=${result.width}x${result.height} backend=${result.backend} phaseMean=${result.phaseSupportMean} phaseP10=${result.phaseSupportP10} " +
                    "reconstruction=${result.reconstructionMs}ms dngBoundary=PRE_VGN sabreRgbChromaOwner=true " +
                    "highResLumaOwner=DIRECT_CFA directChromaOwner=false trueDetail26573=temporal-cross-frame " +
                    "directDng=${result.linearRgbPath!=null} fusedRender=${result.renderRgbPath!=null}"
                PLog.i(SABRE_TAG,"IRIS_26568_TRUE2X_READY $readyDetails")
                MotionTrace.processingState("IRIS_26576_SR_RECONSTRUCTION_SUMMARY", readyDetails)''',
        'stacker ready persistent summary')
    s=once(s,
'''                    PLog.i(SABRE_TAG, "IRIS_26574_TRUE2X_FLOW_REFINE $details")
                    PLog.i("MotionTrace", "PIPELINE_STATE stage=IRIS_26574_TRUE2X_FLOW_REFINE details=$details")''',
'''                    PLog.i(SABRE_TAG, "IRIS_26574_TRUE2X_FLOW_REFINE $details")
                    MotionTrace.processingState("IRIS_26574_TRUE2X_FLOW_REFINE", details)''',
        'stacker flow refine persistent route')
    s=once(s,
'''        PLog.i(SABRE_TAG, "IRIS_26573_SR_PROOF $proof")
        PLog.i("MotionTrace", "PIPELINE_STATE stage=IRIS_26573_SR_PROOF details=$proof")''',
'''        PLog.i(SABRE_TAG, "IRIS_26573_SR_PROOF $proof")
        MotionTrace.processingState("IRIS_26573_SR_PROOF", proof)''',
        'stacker GPU SR proof persistent route')
    s=once(s,
'''        val gpuFailure=gpuAttempt.exceptionOrNull()?:IllegalStateException("IRIS_26568_TRUE2X_GPU_FALLBACK_CPU unknown GPU failure")
        PLog.e(SABRE_TAG,"IRIS_26568_TRUE2X_GPU_FALLBACK_CPU reason=${gpuFailure.message}",gpuFailure)
        runCatching { directGpuFile?.delete() }; runCatching { renderGpuFile.delete() }''',
'''        val gpuFailure=gpuAttempt.exceptionOrNull()?:IllegalStateException("IRIS_26568_TRUE2X_GPU_FALLBACK_CPU unknown GPU failure")
        PLog.e(SABRE_TAG,"IRIS_26568_TRUE2X_GPU_FALLBACK_CPU reason=${gpuFailure.message}",gpuFailure)
        MotionTrace.processingState(
            "IRIS_26576_SR_RECONSTRUCTION_GPU_FALLBACK",
            "reason=${gpuFailure.javaClass.simpleName}:${gpuFailure.message} gpuAttemptMs=${elapsedMs(start)} cpuFallback=true",
        )
        runCatching { directGpuFile?.delete() }; runCatching { renderGpuFile.delete() }''',
        'stacker GPU reconstruction fallback persistent')
    s=once(s,
'''        return try {
            val phase=runTrue2xCpu(frames,images,evidence,cpuFile,cpuPhaseFile,outputWidth,outputHeight)
            True2xResult(cpuFile.absolutePath,null,nativeGuide.absolutePath,cpuPhaseFile.absolutePath,outputWidth,outputHeight,"CPU",phase.mean,phase.p10,elapsedMs(cpuStart))
        } catch(error:Throwable) { runCatching{nativeGuide.delete()};runCatching{cpuFile.delete()};runCatching{cpuPhaseFile.delete()};throw error }''',
'''        return try {
            val phase=runTrue2xCpu(frames,images,evidence,cpuFile,cpuPhaseFile,outputWidth,outputHeight)
            val cpuMs = elapsedMs(cpuStart)
            /* IRIS_26576_CPU_SR_PROOF_NO_EXTRA_READBACK
             * CPU reconstruction already packs phase count + temporal agreement into the existing
             * 26573 phase-support carrier. Report that authority without rereading the carrier.
             */
            MotionTrace.processingState(
                "IRIS_26576_SR_CPU_PROOF",
                "backend=CPU evidence=${evidence.size} crossFrame=${evidence.size > 1} " +
                    "phaseMean=${phase.mean} phaseP10=${phase.p10} temporalProofPacked=true " +
                    "highResLumaOwner=DIRECT_CFA_TEMPORAL directChromaOwner=false cpuMs=$cpuMs",
            )
            True2xResult(cpuFile.absolutePath,null,nativeGuide.absolutePath,cpuPhaseFile.absolutePath,outputWidth,outputHeight,"CPU",phase.mean,phase.p10,cpuMs)
        } catch(error:Throwable) { runCatching{nativeGuide.delete()};runCatching{cpuFile.delete()};runCatching{cpuPhaseFile.delete()};throw error }''',
        'stacker CPU SR proof')
    p.write_text(s)

    # Java encoder: read the native backend/timing result after the true2x publication call and
    # mirror it through the persistent MotionTrace helper.
    p=out/'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java'
    s=p.read_text()
    s=once(s,
'''import com.particlesdevs.photoncamera.util.Log;
import com.particlesdevs.photoncamera.app.PhotonCamera;''',
'''import com.particlesdevs.photoncamera.util.Log;
import com.particlesdevs.photoncamera.util.MotionTrace;
import com.particlesdevs.photoncamera.app.PhotonCamera;''',
        'encoder MotionTrace import')
    s=once(s,
'''            final long renderMs = (System.nanoTime() - renderStartNs) / 1_000_000L;
            Log.i(TAG, "IRIS_26564_TRUE2X_TIMING colorRenderJpegMs=" + renderMs
                    + " size=" + trueWidth + "x" + trueHeight
                    + " jin=" + useJin + " watermark=" + watermarkEnabled
                    + " gainmap=" + hasGain);
            if (!baseOk) return false;''',
'''            final long renderMs = (System.nanoTime() - renderStartNs) / 1_000_000L;
            Log.i(TAG, "IRIS_26564_TRUE2X_TIMING colorRenderJpegMs=" + renderMs
                    + " size=" + trueWidth + "x" + trueHeight
                    + " jin=" + useJin + " watermark=" + watermarkEnabled
                    + " gainmap=" + hasGain);
            /* IRIS_26576_NATIVE_PUBLICATION_BACKEND_PERSISTENT_PROOF
             * Native 26571 remains GPU-first with the exact 26570 CPU fallback. Retrieve only the
             * timing/backend record produced by that call; no publication math or routing changes.
             */
            String iris26576Publication = getLastTrue2xPublicationTelemetryNative();
            if (iris26576Publication == null || iris26576Publication.isEmpty()) {
                iris26576Publication = "backend=UNKNOWN nativeTelemetryMissing=true";
            }
            MotionTrace.processingState(
                    "IRIS_26576_SR_PUBLICATION_BACKEND",
                    iris26576Publication
                            + " colorRenderJpegMs=" + renderMs
                            + " baseOk=" + baseOk
                            + " gainmap=" + hasGain
                            + " jin=" + useJin
                            + " watermark=" + watermarkEnabled);
            if (!baseOk) return false;''',
        'encoder persistent native publication proof')
    s=once(s,
'''    private static native boolean writeNative(Bitmap bitmap,String path,int quality,boolean sourceDisplayP3);''',
'''    private static native String getLastTrue2xPublicationTelemetryNative();
    private static native boolean writeNative(Bitmap bitmap,String path,int quality,boolean sourceDisplayP3);''',
        'encoder native telemetry getter declaration')
    p.write_text(s)

    # Native publication: keep exact GPU-first/CPU-fallback pixel path; expose its backend/timing
    # through a thread-local string read immediately by the Java caller on the same processing thread.
    p=out/'app/src/main/cpp/motionv2_jpeg444_jni.cpp'
    s=p.read_text()
    s=once(s,
'''#include <condition_variable>
#include <deque>''',
'''#include <condition_variable>
#include <cstdarg>
#include <deque>''',
        'native cstdarg include')
    s=once(s,
'''namespace { struct U{JNIEnv*e;jstring s;const char*c;U(JNIEnv*e,jstring s):e(e),s(s),c(s?e->GetStringUTFChars(s,nullptr):nullptr){}~U(){if(c)e->ReleaseStringUTFChars(s,c);}};
bool write(const char*p,const unsigned char*d,size_t n){FILE*f=fopen(p,"wb");if(!f)return false;size_t w=fwrite(d,1,n,f);int a=fflush(f),b=fclose(f);return w==n&&a==0&&b==0;}
bool f3(JNIEnv*e,jfloatArray a,std::array<float,3>*o){if(!a||e->GetArrayLength(a)!=3)return false;e->GetFloatArrayRegion(a,0,3,o->data());return !e->ExceptionCheck();}}''',
'''namespace { struct U{JNIEnv*e;jstring s;const char*c;U(JNIEnv*e,jstring s):e(e),s(s),c(s?e->GetStringUTFChars(s,nullptr):nullptr){}~U(){if(c)e->ReleaseStringUTFChars(s,c);}};
/* IRIS_26576_NATIVE_PUBLICATION_TELEMETRY_ONLY
 * Single active Motion processing is already enforced. Keep one per-native-thread summary of the
 * just-completed 26571 GPU-first / 26570 CPU-fallback publication call for Java to persist.
 */
thread_local std::string gIris26576PublicationTelemetry;
void iris26576SetPublicationTelemetry(const char*fmt,...){
    char buffer[2048];va_list args;va_start(args,fmt);vsnprintf(buffer,sizeof(buffer),fmt,args);va_end(args);
    gIris26576PublicationTelemetry=buffer;
}
bool write(const char*p,const unsigned char*d,size_t n){FILE*f=fopen(p,"wb");if(!f)return false;size_t w=fwrite(d,1,n,f);int a=fflush(f),b=fclose(f);return w==n&&a==0&&b==0;}
bool f3(JNIEnv*e,jfloatArray a,std::array<float,3>*o){if(!a||e->GetArrayLength(a)!=3)return false;e->GetFloatArrayRegion(a,0,3,o->data());return !e->ExceptionCheck();}}''',
        'native telemetry helper')
    s=once(s,
'''extern "C" JNIEXPORT jboolean JNICALL Java_com_particlesdevs_photoncamera_processing_ultrahdr_MotionV2Jpeg444Encoder_writeTrue2xNative(
        JNIEnv*e,jclass,jobject bitmap,jstring renderPath,jint trueW,jint trueH,jint rawW,jint rawH,jint cropW,jint cropH,jint rotation,jboolean mirror,jfloat residualZoom,''',
'''extern "C" JNIEXPORT jstring JNICALL Java_com_particlesdevs_photoncamera_processing_ultrahdr_MotionV2Jpeg444Encoder_getLastTrue2xPublicationTelemetryNative(JNIEnv*e,jclass){
    return e->NewStringUTF(gIris26576PublicationTelemetry.c_str());
}

extern "C" JNIEXPORT jboolean JNICALL Java_com_particlesdevs_photoncamera_processing_ultrahdr_MotionV2Jpeg444Encoder_writeTrue2xNative(
        JNIEnv*e,jclass,jobject bitmap,jstring renderPath,jint trueW,jint trueH,jint rawW,jint rawH,jint cropW,jint cropH,jint rotation,jboolean mirror,jfloat residualZoom,''',
        'native telemetry getter implementation')
    s=once(s,
'''    using namespace iris26564render;AndroidBitmapInfo info{};if(!bitmap||!renderPath||!path||trueW<=0||trueH<=0||rawW<=0||rawH<=0||cropW<=0||cropH<=0||trueW!=rawW*2||trueH!=rawH*2||cropW>rawW||cropH>rawH||AndroidBitmap_getInfo(e,bitmap,&info)!=ANDROID_BITMAP_RESULT_SUCCESS||info.format!=ANDROID_BITMAP_FORMAT_RGBA_8888)return JNI_FALSE;''',
'''    using namespace iris26564render;gIris26576PublicationTelemetry="backend=UNSET callStarted=true";AndroidBitmapInfo info{};if(!bitmap||!renderPath||!path||trueW<=0||trueH<=0||rawW<=0||rawH<=0||cropW<=0||cropH<=0||trueW!=rawW*2||trueH!=rawH*2||cropW>rawW||cropH>rawH||AndroidBitmap_getInfo(e,bitmap,&info)!=ANDROID_BITMAP_RESULT_SUCCESS||info.format!=ANDROID_BITMAP_FORMAT_RGBA_8888){iris26576SetPublicationTelemetry("backend=NONE validationFailed=true");return JNI_FALSE;}''',
        'native telemetry init')
    s=once(s,
'''    if(gpuEncoded){
        close(sourceFd);
        __android_log_print(ANDROID_LOG_INFO,TAG,"IRIS_26571_TRUE2X_GPU_PUBLICATION gpuEligible=1 gpuUsed=1 sourceReadMs=%.3f uploadDispatchMs=%.3f readbackWaitMs=%.3f deinterleaveMs=%.3f producerMs=%.3f baseJpegMs=%.3f gainJpegMs=%.3f totalMs=%.3f bandRows=%d pboSlots=2 gain1to1=%d",(double)gpuTiming.sourceReadNs/1000000.0,(double)gpuTiming.uploadDispatchNs/1000000.0,(double)gpuTiming.readbackWaitNs/1000000.0,(double)gpuTiming.deinterleaveNs/1000000.0,(double)gpuTiming.producerNs/1000000.0,(double)gpuBaseJpegNs/1000000.0,(double)gpuGainJpegNs/1000000.0,(double)gpuTotalNs/1000000.0,bandRows,generateGain?1:0);''',
'''    if(gpuEncoded){
        close(sourceFd);
        iris26576SetPublicationTelemetry("backend=GPU gpuEligible=1 gpuUsed=1 sourceReadMs=%.3f uploadDispatchMs=%.3f readbackWaitMs=%.3f deinterleaveMs=%.3f producerMs=%.3f baseJpegMs=%.3f gainJpegMs=%.3f totalMs=%.3f bandRows=%d pboSlots=2 gain1to1=%d",(double)gpuTiming.sourceReadNs/1000000.0,(double)gpuTiming.uploadDispatchNs/1000000.0,(double)gpuTiming.readbackWaitNs/1000000.0,(double)gpuTiming.deinterleaveNs/1000000.0,(double)gpuTiming.producerNs/1000000.0,(double)gpuBaseJpegNs/1000000.0,(double)gpuGainJpegNs/1000000.0,(double)gpuTotalNs/1000000.0,bandRows,generateGain?1:0);
        __android_log_print(ANDROID_LOG_INFO,TAG,"IRIS_26571_TRUE2X_GPU_PUBLICATION gpuEligible=1 gpuUsed=1 sourceReadMs=%.3f uploadDispatchMs=%.3f readbackWaitMs=%.3f deinterleaveMs=%.3f producerMs=%.3f baseJpegMs=%.3f gainJpegMs=%.3f totalMs=%.3f bandRows=%d pboSlots=2 gain1to1=%d",(double)gpuTiming.sourceReadNs/1000000.0,(double)gpuTiming.uploadDispatchNs/1000000.0,(double)gpuTiming.readbackWaitNs/1000000.0,(double)gpuTiming.deinterleaveNs/1000000.0,(double)gpuTiming.producerNs/1000000.0,(double)gpuBaseJpegNs/1000000.0,(double)gpuGainJpegNs/1000000.0,(double)gpuTotalNs/1000000.0,bandRows,generateGain?1:0);''',
        'native GPU publication telemetry')
    s=once(s,
'''    bool baseEncoded=streamed&&baseFlush==0&&baseClose==0;bool gainEncoded=!generateGain||(streamed&&gainFlush==0&&gainClose==0);if(!baseEncoded)unlink(op.c);if(generateGain&&!gainEncoded)unlink(gp.c);__android_log_print(ANDROID_LOG_INFO,TAG,"IRIS_26570_TRUE2X_ENCODER_TIMING profileMs=%.3f renderMs=%.3f jinMs=%.3f baseJpegMs=%.3f gainJpegMs=%.3f overlapPipelineMs=%.3f streamMs=%.3f workers=%d bandRows=%d profileCache=%d jpegBatchRows=%d doubleBuffered=%d concurrentGain=%d",timing.profileNs/1000000.0,timing.renderNs/1000000.0,timing.jinNs/1000000.0,baseJpegNs/1000000.0,gainJpegNs/1000000.0,overlapNs/1000000.0,iris26569Ns(streamStart,streamEnd)/1000000.0,workers,bandRows,motionFast?1:0,32,1,generateGain?1:0);''',
'''    bool baseEncoded=streamed&&baseFlush==0&&baseClose==0;bool gainEncoded=!generateGain||(streamed&&gainFlush==0&&gainClose==0);if(!baseEncoded)unlink(op.c);if(generateGain&&!gainEncoded)unlink(gp.c);iris26576SetPublicationTelemetry("backend=CPU gpuEligible=%d gpuUsed=0 gpuAttemptMs=%.3f gpuFallbackReason=%s profileMs=%.3f renderMs=%.3f jinMs=%.3f baseJpegMs=%.3f gainJpegMs=%.3f streamMs=%.3f workers=%d bandRows=%d baseEncoded=%d gainEncoded=%d",(int)gpuEligible,(double)gpuTotalNs/1000000.0,gpuReason.empty()?(gpuEligible?"gpu_failed":"jin_or_watermark"):gpuReason.c_str(),(double)timing.profileNs/1000000.0,(double)timing.renderNs/1000000.0,(double)timing.jinNs/1000000.0,(double)baseJpegNs/1000000.0,(double)gainJpegNs/1000000.0,(double)iris26569Ns(streamStart,streamEnd)/1000000.0,workers,bandRows,baseEncoded?1:0,gainEncoded?1:0);__android_log_print(ANDROID_LOG_INFO,TAG,"IRIS_26570_TRUE2X_ENCODER_TIMING profileMs=%.3f renderMs=%.3f jinMs=%.3f baseJpegMs=%.3f gainJpegMs=%.3f overlapPipelineMs=%.3f streamMs=%.3f workers=%d bandRows=%d profileCache=%d jpegBatchRows=%d doubleBuffered=%d concurrentGain=%d",timing.profileNs/1000000.0,timing.renderNs/1000000.0,timing.jinNs/1000000.0,baseJpegNs/1000000.0,gainJpegNs/1000000.0,overlapNs/1000000.0,iris26569Ns(streamStart,streamEnd)/1000000.0,workers,bandRows,motionFast?1:0,32,1,generateGain?1:0);''',
        'native CPU publication telemetry')
    p.write_text(s)

    # Version/build only. VERSION_MINOR remains the existing project family marker by design.
    p=out/'app/version.properties'
    s=p.read_text()
    s=once(s,'VERSION_NAME=0.9726575\nVERSION_BUILD=26575\n','VERSION_NAME=0.9726576\nVERSION_BUILD=26576\n','version')
    p.write_text(s)

if __name__=='__main__': main()
