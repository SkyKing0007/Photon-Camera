from pathlib import Path
import tempfile, subprocess, re
r=Path(__file__).resolve().parent
base=r/'actual/app/src/main/java'; cand=r/'candidate/app/src/main/java'
with tempfile.TemporaryDirectory() as tmp:
 t=Path(tmp); j=t/'java'; classes=t/'classes'; classes.mkdir()
 def write(name,txt):
  p=j/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(txt);return p
 def fields(path,names):
  s=(base/path).read_text();out=[]
  for name in names.split():
   x=re.search(r'public\s+(?:final\s+)?([\w.<>\[\]]+)\s+'+name+r'\s*(?:=\s*([^;]+))?;',s)
   assert x,name
   out.append('public '+x[1]+' '+name+('='+x[2] if x[2] else '')+';')
  return '\n'.join(out)
 write('android/content/Context.java','package android.content; public class Context {}')
 write('android/graphics/ImageFormat.java','package android.graphics; public class ImageFormat { public static final int RAW_SENSOR=32; }')
 write('android/graphics/Point.java','package android.graphics; public class Point {public int x,y;public Point(int x,int y){this.x=x;this.y=y;}}')
 write('com/hinnka/mycamera/utils/PLog.java','package com.hinnka.mycamera.utils;public class PLog {}')
 write('com/hinnka/mycamera/utils/LargeDirectBuffer.java','package com.hinnka.mycamera.utils; import java.nio.ByteBuffer;public class LargeDirectBuffer {public static int frees;public static ByteBuffer allocate(long n,String s){return ByteBuffer.allocateDirect((int)n);}public static void free(ByteBuffer b){frees++;}}')
 write('android/util/Pair.java','package android.util; public class Pair<A,B>{public final A first;public final B second;public Pair(A a,B b){first=a;second=b;}}')
 write('android/hardware/camera2/params/BlackLevelPattern.java','package android.hardware.camera2.params; public class BlackLevelPattern {public final int[] values;public BlackLevelPattern(int...v){values=v;}public void copyTo(int[] out,int offset){System.arraycopy(values,0,out,offset,4);}}')
 write('android/hardware/camera2/CaptureRequest.java','package android.hardware.camera2; public class CaptureRequest {}')
 write('android/hardware/camera2/CaptureResult.java','''package android.hardware.camera2; import java.util.*; import android.util.Pair;public class CaptureResult {public static class Key<T>{} public static final Key<Long> SENSOR_TIMESTAMP=new Key<>();public static final Key<float[]> SENSOR_DYNAMIC_BLACK_LEVEL=new Key<>();public static final Key<Integer> SENSOR_DYNAMIC_WHITE_LEVEL=new Key<>();public static final Key<Pair<Double,Double>[]> SENSOR_NOISE_PROFILE=new Key<>();private final Map<Key<?>,Object> m=new HashMap<>();public <T> void put(Key<T> k,T v){m.put(k,v);} @SuppressWarnings("unchecked") public <T>T get(Key<T> k){return (T)m.get(k);}}''')
 write('android/hardware/camera2/CameraCharacteristics.java','''package android.hardware.camera2; import java.util.*;import android.hardware.camera2.params.BlackLevelPattern;public class CameraCharacteristics{public static class Key<T>{} public static final Key<Integer> SENSOR_INFO_COLOR_FILTER_ARRANGEMENT=new Key<>(),SENSOR_INFO_WHITE_LEVEL=new Key<>();public static final Key<BlackLevelPattern> SENSOR_BLACK_LEVEL_PATTERN=new Key<>();private final Map<Key<?>,Object> m=new HashMap<>();public <T>void put(Key<T> k,T v){m.put(k,v);} @SuppressWarnings("unchecked") public <T>T get(Key<T> k){return (T)m.get(k);}}''')
 write('com/particlesdevs/photoncamera/control/GyroBurst.java','package com.particlesdevs.photoncamera.control; public class GyroBurst{public float shakiness;public int samples;public GyroBurst(float s,int n){shakiness=s;samples=n;}}')
 write('com/particlesdevs/photoncamera/processing/parameters/IsoExpoSelector.java','package com.particlesdevs.photoncamera.processing.parameters;public class IsoExpoSelector{public static class ExpoPair{public int iso;public ExpoPair(int n){iso=n;}}}')
 write('com/particlesdevs/photoncamera/util/Log.java','package com.particlesdevs.photoncamera.util; public class Log{public static void d(String t,String s){}}')
 write('com/particlesdevs/photoncamera/util/MotionTrace.java','package com.particlesdevs.photoncamera.util; public class MotionTrace{public static void processingState(String t,String s){}}')
 write('com/particlesdevs/photoncamera/api/ParseExif.java','package com.particlesdevs.photoncamera.api;public class ParseExif{public static class ExifData{}}')
 write('com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java','package com.particlesdevs.photoncamera.processing.processor;public class IrisMotionSettings{ public static class DngOptions{public static class Snapshot{} public static Snapshot defaults(){return new Snapshot();}} public static class Snapshot{public boolean customNoiseModelEnabled;}}')
 names='timestamp buffer motionV2ReconstructionExperiment26856 motionV2PhysicalCameraId motionV2FrameRole motionV2ShortHighlightFrame motionV2ResultSensorTimestampNs motionV2FrameNumber motionV2PlaneLayoutValid motionV2PlaneTransformedByBinning motionV2PlaneFormat motionV2PlaneLogicalWidth motionV2PlaneLogicalHeight motionV2PlanePixelStrideBytes motionV2PlaneRowStrideBytes motionV2ActualExposureNs motionV2ActualIso motionV2ExposureEnergy motionV2BlackLevelValid motionV2BlackLevel motionV2WhiteLevelValid motionV2WhiteLevel motionV2FocusDistanceDiopters motionV2LensState motionV2RollingShutterSkewNs motionV2VerifiedHotPixels26855 motionV2NoiseProfile motionV2NoiseProfileValid motionV2RowFlickerValid motionV2RowFlickerHarmonic motionV2RowFlickerA motionV2RowFlickerB motionV2RowFlickerStrength motionV2ReferenceProtectionEv motionV2AlternativeHighlight26912 motionV2PreviewHighlightP99526912 frameGyro'
 write('com/particlesdevs/photoncamera/processing/ImageFrame.java','package com.particlesdevs.photoncamera.processing;import java.nio.ByteBuffer;import com.particlesdevs.photoncamera.control.GyroBurst;public class ImageFrame {public enum MotionV2FrameRole {NORMAL,HIGHLIGHT_SHORT,SHADOW_LONG} public int width,height; public long getTimestamp(){return timestamp;}'+fields('com/particlesdevs/photoncamera/processing/ImageFrame.java',names)+'}')
 names='frames gyro referenceResult referenceRequest exposurePairs rotation iris26524GlobalZoom iris26524OpticalZoomAnchor iris26524OutputLocalZoom iris26524HardwareLocalZoom iris26524ResidualSoftwareZoom localLaplacianToneEnabled imageFormat candidateCount retainedCount processingFrameCount totalFrameCount shortHighlightSlot iris26524OwnerCameraId superResEnabled heicOutputEnabled dngOptions26786'
 write('com/particlesdevs/photoncamera/processing/MotionBatch.java','package com.particlesdevs.photoncamera.processing;import java.util.*;import android.hardware.camera2.*;import com.particlesdevs.photoncamera.control.GyroBurst;import com.particlesdevs.photoncamera.processing.parameters.IsoExpoSelector;public class MotionBatch { public Map<Long,Double> exposures;public static class ShadowAuxSlot{public boolean has;public boolean hasFrame(){return has;}}public static class ShortHighlightSlot { public boolean complete=true,shortExpected,longExpected,has;public ShadowAuxSlot shadowAuxSlot=new ShadowAuxSlot();public boolean requiredFreezeComplete(){return complete;}public boolean shortWasExpected(){return shortExpected;}public boolean shadowWasExpected(){return longExpected;}public boolean hasFrame(){return has;}}'+fields('com/particlesdevs/photoncamera/processing/MotionBatch.java',names)+'}')
 write('com/particlesdevs/photoncamera/processing/render/Parameters.java','package com.particlesdevs.photoncamera.processing.render;import android.graphics.Point;import android.hardware.camera2.*;import com.particlesdevs.photoncamera.processing.processor.IrisMotionSettings; public class Parameters{public boolean iris26983COnSelected,iris26906ExperimentBSelected,motionV2Active,motionV2SuperResOutputEnabled,irisNightActive,iris26983COnNight;public Point rawSize;public byte cfaPattern;public float[] blackLevel;public int whiteLevel;public float motionV2ReferenceProtectionEv,motionCanonicalExposureGain,motionV2SpatialReconstructionZoom,motionV2ReconstructionZoom,motionV2RenderResidualZoom,motionV2OutputZoom;public float motionV2SuperResOutputScale,motionV2GlobalZoom,motionV2OpticalZoomAnchor,motionV2HardwareZoom,motionV2ResidualSoftwareZoom,motionV2WronskiNoiseS,motionV2WronskiNoiseO;public boolean motionV2LocalLaplacianToneEnabled,motionV2StrictWronskiSensorValid;public IrisMotionSettings.DngOptions.Snapshot motionV2DngOptions26786;public int cameraRotation,avgIso;public void FillConstParameters(CameraCharacteristics c,Point s){rawSize=s;}public void FillDynamicParameters(CaptureResult r,CaptureRequest q,int i){avgIso=i;} }')
 subprocess.run(['javac','-d',str(classes),*[str(p) for p in j.rglob('*.java')],str(cand/'com/particlesdevs/photoncamera/processing/processor/Iris26983COnCapturePreparation.java')],check=True)
 stub=write('Pipeline.kt','''package com.hinnka.mycamera.processor
import android.content.Context
import com.particlesdevs.photoncamera.processing.render.Parameters
import com.particlesdevs.photoncamera.processing.processor.IrisMotionSettings
import com.particlesdevs.photoncamera.api.ParseExif
import java.nio.file.Path
object GlesIris26983COnPipeline {
 var calls=0;var frames:List<RawStackFrame> = emptyList();var fail=false;var black=FloatArray(0)
 fun execute(app:Context,fs:List<RawStackFrame>,physical:String,n:Int,number:Long,ts:Long,b:FloatArray,white:Int,p:Parameters,t:IrisMotionSettings.Snapshot,clip:Float,alt:Boolean,p995:Float,h:Boolean,w:Boolean,a:Boolean,e:Boolean,o:Path,heic:Boolean,exif:ParseExif.ExifData):Boolean {
 calls++;frames=fs;black=b.copyOf();check(fs.size==n && fs.first().sensorTimestampNs==ts && fs.first().frameNumber==number && physical=="2" && white==4095 && !heic && alt && p995==0.8f);if(fail)error("simulated downstream failure");return true
 }
}''')
 test=write('Test.kt','''package com.hinnka.mycamera.processor
import android.content.Context
import android.graphics.Point
import android.graphics.ImageFormat
import com.particlesdevs.photoncamera.processing.*
import com.particlesdevs.photoncamera.control.GyroBurst
import com.particlesdevs.photoncamera.processing.processor.Iris26983COnCapturePreparation
import com.particlesdevs.photoncamera.processing.parameters.IsoExpoSelector
import android.hardware.camera2.*
import android.hardware.camera2.params.BlackLevelPattern
import android.util.Pair
import com.particlesdevs.photoncamera.processing.render.Parameters
import com.particlesdevs.photoncamera.processing.processor.IrisMotionSettings
import com.particlesdevs.photoncamera.api.ParseExif
import com.hinnka.mycamera.utils.LargeDirectBuffer
import java.nio.ByteBuffer
import java.nio.file.Paths
fun main(){
 fun frame(i:Int)=ImageFrame().apply{timestamp=100L+i;motionV2FrameNumber=i.toLong();motionV2ResultSensorTimestampNs=timestamp;motionV2ReconstructionExperiment26856="C";motionV2PhysicalCameraId="2";motionV2PlaneLayoutValid=true;motionV2PlaneFormat=ImageFormat.RAW_SENSOR;motionV2PlaneLogicalWidth=64;motionV2PlaneLogicalHeight=64;motionV2PlanePixelStrideBytes=2;motionV2PlaneRowStrideBytes=128;buffer=ByteBuffer.allocateDirect(8192);buffer.putShort(0,(100+i).toShort());motionV2ActualExposureNs=1000;motionV2ActualIso=100;motionV2ExposureEnergy=100000.0;motionV2BlackLevelValid=true;motionV2BlackLevel.fill(64f);motionV2WhiteLevelValid=true;motionV2WhiteLevel=4095;motionV2AlternativeHighlight26912=true;motionV2PreviewHighlightP99526912=0.8f;motionV2ReferenceProtectionEv=0.75f}
 val f=List(3){frame(it)}; val batch=MotionBatch().apply{frames=f;gyro=listOf(GyroBurst(1f,2),GyroBurst(3f,4),GyroBurst(2f,6));imageFormat=ImageFormat.RAW_SENSOR;candidateCount=3;retainedCount=3;processingFrameCount=3;totalFrameCount=3;superResEnabled=true;iris26524OwnerCameraId="2";shortHighlightSlot=MotionBatch.ShortHighlightSlot();dngOptions26786=IrisMotionSettings.DngOptions.defaults()}
 val p=Parameters().apply{iris26983COnSelected=true;motionV2Active=true;motionV2SuperResOutputEnabled=true;rawSize=Point(64,64);cfaPattern=1;blackLevel=floatArrayOf(1f,2f,3f,4f);whiteLevel=4095;motionV2OutputZoom=2f};val tone=IrisMotionSettings.Snapshot()
 fun execute()=GlesIris26983COnMotionIngress.executeFrozenMotion(Context(),batch,3,101L,p,tone,0.01f,false,false,false,false,Paths.get("/unused"),ParseExif.ExifData())
 check(execute()); val owner=GlesIris26983COnPipeline;check(owner.frames.map{it.sensorTimestampNs}==listOf(101L,102L,100L));check(owner.frames.map{it.gyroShakiness}==listOf(3f,2f,1f));check(owner.frames.map{it.gyroSampleCount}==listOf(4,6,2));check(owner.black.contentEquals(floatArrayOf(1f,2f,3f,4f)));check(p.motionV2RenderResidualZoom==2f && p.motionV2ReferenceProtectionEv==0.75f && p.motionCanonicalExposureGain==1f);check(owner.frames.first().image.planes[0].buffer.getShort(0)==101.toShort());f[1].motionV2BlackLevel[0]=99f;check(owner.frames.first().dynamicBlackLevelByCfaPosition!![0]==64f)
 fun reject(change:()->Unit,restore:()->Unit){val n=owner.calls;change();check(runCatching{execute()}.isFailure);check(owner.calls==n);restore()}
 reject({f[0].motionV2ReconstructionExperiment26856="B"},{f[0].motionV2ReconstructionExperiment26856="C"});reject({f[0].motionV2PhysicalCameraId="1"},{f[0].motionV2PhysicalCameraId="2"});reject({f[0].motionV2ResultSensorTimestampNs=5L},{f[0].motionV2ResultSensorTimestampNs=100L});reject({batch.candidateCount=4},{batch.candidateCount=3});reject({batch.shortHighlightSlot.longExpected=true},{batch.shortHighlightSlot.longExpected=false});reject({batch.heicOutputEnabled=true},{batch.heicOutputEnabled=false});reject({f[0].motionV2FrameRole=ImageFrame.MotionV2FrameRole.SHADOW_LONG},{f[0].motionV2FrameRole=ImageFrame.MotionV2FrameRole.NORMAL});reject({f[0].motionV2PlanePixelStrideBytes=1},{f[0].motionV2PlanePixelStrideBytes=2});reject({p.iris26906ExperimentBSelected=true},{p.iris26906ExperimentBSelected=false});reject({f[0].motionV2ExposureEnergy=Double.NaN},{f[0].motionV2ExposureEnergy=100000.0});reject({batch.frames=listOf(f[1],f[1],f[2])},{batch.frames=f})
 // Exact source B's metadata prep with typed host Camera2 stubs.
 val characteristics=CameraCharacteristics().apply{put(CameraCharacteristics.SENSOR_INFO_COLOR_FILTER_ARRANGEMENT,2);put(CameraCharacteristics.SENSOR_INFO_WHITE_LEVEL,4095);put(CameraCharacteristics.SENSOR_BLACK_LEVEL_PATTERN,BlackLevelPattern(64,65,66,67))}
 val result=CaptureResult().apply{put(CaptureResult.SENSOR_TIMESTAMP,101L);put(CaptureResult.SENSOR_DYNAMIC_BLACK_LEVEL,floatArrayOf(10f,20f,30f,40f));put(CaptureResult.SENSOR_DYNAMIC_WHITE_LEVEL,4000);put(CaptureResult.SENSOR_NOISE_PROFILE,arrayOf(Pair(0.1,0.01),Pair(0.2,0.02),Pair(0.4,0.04),Pair(0.5,0.05)))}
 batch.referenceResult=result;batch.referenceRequest=CaptureRequest();batch.exposurePairs=listOf(IsoExpoSelector.ExpoPair(100),IsoExpoSelector.ExpoPair(200),IsoExpoSelector.ExpoPair(300));batch.exposures=f.associate{it.timestamp to it.motionV2ExposureEnergy};batch.rotation=90;batch.iris26524GlobalZoom=4f;batch.iris26524OutputLocalZoom=2f;batch.iris26524OpticalZoomAnchor=2f;batch.iris26524HardwareLocalZoom=1f;batch.iris26524ResidualSoftwareZoom=2f;batch.localLaplacianToneEnabled=true
 val prep=Iris26983COnCapturePreparation.prepare(characteristics,batch);val pp=prep.parameters
 check(prep.referenceTimestamp==101L && prep.frames.map{it.frame.timestamp}==listOf(101L,102L,100L));check(pp.avgIso==200 && pp.cfaPattern.toInt()==2 && pp.whiteLevel==4000 && pp.blackLevel.contentEquals(floatArrayOf(10f,20f,30f,40f)));check(pp.motionV2WronskiNoiseS.toRawBits()==((0.1+0.5*(0.2+0.4)+0.5)/3.0).toFloat().toRawBits());check(pp.motionV2WronskiNoiseO.toRawBits()==((0.01+0.5*(0.02+0.04)+0.05)/3.0).toFloat().toRawBits());check(pp.iris26983COnSelected && !pp.iris26906ExperimentBSelected && pp.motionV2SuperResOutputScale==2f && pp.cameraRotation==90 && pp.motionV2OutputZoom==2f)
 f[1].motionV2NoiseProfileValid=true; f[1].motionV2NoiseProfile.fill(0.125f);val n=Iris26983COnCapturePreparation.order(batch,101L);check(n.all{it.noise.all{v->v==0.125f}});check(!f[0].motionV2NoiseProfileValid && f[0].motionV2NoiseProfile.all{it==0f});f[1].motionV2NoiseProfile.fill(0.25f);check(n[1].noise.all{it==0.125f});
 // The prepared entry must actually connect its private metadata owner to the ingress.
 val before=owner.calls
 check(GlesIris26983COnMotionIngress.executePreparedMotion(Context(),characteristics,batch,3,101L,tone,0.01f,false,false,false,false,Paths.get("/unused"),ParseExif.ExifData()))
 check(owner.calls==before+1 && owner.black.contentEquals(floatArrayOf(10f,20f,30f,40f)))
 check(runCatching{GlesIris26983COnMotionIngress.executePreparedMotion(Context(),characteristics,batch,3,102L,tone,0.01f,false,false,false,false,Paths.get("/unused"),ParseExif.ExifData())}.isFailure && owner.calls==before+1)
 // Randomized exact B chronological + stable gyro sort and swap, including tied values and cyclic reuse.
 val rng=java.util.Random(26983);repeat(1000){val k=2+rng.nextInt(23);val fs=(0 until k).map{frame(it)}.shuffled(kotlin.random.Random(it));val gs=(0 until (1+rng.nextInt(k))).map{GyroBurst(rng.nextInt(5).toFloat(),it)};val ref=fs[rng.nextInt(k)].timestamp;batch.frames=fs;batch.gyro=gs;val sorted=fs.sortedBy{it.timestamp}.mapIndexed{i,fr->fr to gs[i%gs.size]}.toMutableList();if(k>=3)sorted.sortWith{a,b->java.lang.Float.compare(a.second.shakiness,b.second.shakiness)};val index=sorted.indexOfFirst{it.first.timestamp==ref};java.util.Collections.swap(sorted,0,index);val actual=Iris26983COnCapturePreparation.order(batch,ref);check(actual.map{it.frame.timestamp}==sorted.map{it.first.timestamp} && actual.map{it.gyro.samples}==sorted.map{it.second.samples});check(batch.frames==fs)}
 batch.frames=f;batch.gyro=listOf(GyroBurst(1f,2),GyroBurst(3f,4),GyroBurst(2f,6));println("PASS 1000 B/C RAW ordering parity cases, strict sensor calculation, independent capture-local parameters, noise fallback and no input mutation")
 owner.fail=true;check(runCatching{execute()}.isFailure);check(LargeDirectBuffer.frees==0);check(f.map{it.buffer.getShort(0).toInt()}==listOf(100,101,102));println("PASS C-only Motion ingress, B-equivalent reference order, metadata copies, physical CFA positional black, 11 rejection cases and borrowed RAW survival on failure")
}''')
 src=[cand/'com/hinnka/mycamera/processor/GlesIris26983COnMotionIngress.kt',base/'com/hinnka/mycamera/processor/RawStackFrameCompat.kt',base/'com/hinnka/mycamera/model/SafeImage.kt',stub,test]
 subprocess.run(['kotlinc','-nowarn','-cp',str(classes),*[str(x) for x in src],'-d',str(t/'test.jar')],check=True)
 subprocess.run(['kotlin','-cp',f'{classes}:{t}/test.jar','com.hinnka.mycamera.processor.TestKt'],check=True)
