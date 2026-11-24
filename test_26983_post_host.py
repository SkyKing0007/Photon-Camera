from pathlib import Path
import json,re,subprocess,tempfile,shutil,hashlib
r=Path(__file__).resolve().parent;a=r/'actual/app/src/main';b=r/'candidate/app/src/main';p='java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/'
# Copy transformation is reproduced rather than rerunning the non-idempotent implementation.
script=(r/'advance_post_26983.py').read_text(); head=script[:script.index('for n in classes:')]; scope={'__file__':str(r/'advance_post_26983.py')};exec(head,scope)
records=json.loads((r/'26983_post_copy_records.json').read_text())['copies']; nshader=0;njava=0
for row in records:
    x,y=a/row['source'],b/row['copy']
    if x.suffix=='.glsl':
        assert x.read_bytes()==y.read_bytes(),row;nshader+=1;continue
    s=scope['transformed'](x.read_text());n=x.stem
    if n=='MotionV2GainMapNative':s=s.replace('System.loadLibrary("motionv2jpeg")','System.loadLibrary("iris26983conjpeg")')
    if n=='MotionV2CfaInput':
        s=s.replace('import com.particlesdevs.photoncamera.processing.processor.MotionV2Merger;\n','').replace('MotionV2Merger.Result.LINEAR_RGB_CARRIER_', 'Iris26983COnPostPipeline.LINEAR_RGB_CARRIER_')
        s=s.replace('if (basePipeline.mParameters.motionV2Active\n                && basePipeline.mParameters.motionV2ReconstructionOwner\n                != com.particlesdevs.photoncamera.processing.render.Parameters.MOTION_V2_RECONSTRUCTION_SABRE\n                && basePipeline.mParameters.motionV2ReconstructionOwner', 'if (!basePipeline.mParameters.iris26983COnSelected || basePipeline.mParameters.iris26906ExperimentBSelected\n                || !basePipeline.mParameters.motionV2SuperResOutputEnabled\n                || basePipeline.mParameters.motionV2ReconstructionOwner')
    assert s==y.read_text(),row;njava+=1
print('PASS',njava,'post node source copies and',nshader,'byte-identical shader copies')
# Check original B reachable order, with C graph limited to standard Bayer all-NORMAL.
old=(a/(p+'PostPipeline.java')).read_text(); new=(b/(p+'Iris26983COnPostPipeline.java')).read_text(); seq=['MotionV2CfaInput','MotionV2PhotonHighlightCompression','MotionV2ColorTransform','MotionV2ViewfinderExposureMatcher','MotionV2PreviewHueMatch','MotionV2DisplayExposure','IrisMotionToneControls','MotionV2Render','RotateWatermark']; old=old[old.index('/* IRIS_26410_MOTION_V2_ISOLATED_POST_GRAPH */'):]; cursor=0
for n in seq: cursor=old.index('add(new '+n+'(',cursor)+len(n)+8
actual=re.findall(r'add\(new (Iris26983COn\w+)\(',new);assert actual==[scope['rename'][x] for x in seq],actual
print('PASS reachable B ON graph node sequence (source only)')
# Build and run the actual appended native gainmap functions with host JNI, using the actual C Java wrapper.
cpp=(b/'cpp/iris26983_con_jpeg_writer.cpp').read_text(); fragment=cpp[cpp.index('/* IRIS_26827_GAINMAP_NATIVE_EXACT_REMAP'):]; original=(a/'cpp/motionv2_jpeg444_jni.cpp').read_text(); i=original.index('/* IRIS_26827_GAINMAP_NATIVE_EXACT_REMAP'); j=original.index('extern "C" JNIEXPORT jboolean JNICALL Java_com_particlesdevs_photoncamera_processing_ultrahdr_MotionV2Jpeg444Encoder_writeNative',i);assert fragment==original[i:j].replace('MotionV2GainMapNative','Iris26983COnGainMapNative')
with tempfile.TemporaryDirectory() as t:
    t=Path(t); jdk=Path(shutil.which('javac')).resolve().parent.parent
    (t/'gain.cpp').write_text('#include <jni.h>\n#include <algorithm>\n#include <array>\n#include <cstdint>\n'+fragment)
    subprocess.run(['g++','-std=c++17','-shared','-fPIC','-O2','-I'+str(jdk/'include'),'-I'+str(jdk/'include/linux'),str(t/'gain.cpp'),'-o',str(t/'libiris26983conjpeg.so')],check=True)
    cls=t/'Test.java';cls.write_text('''package com.particlesdevs.photoncamera.processing.opengl.postpipeline;
import java.nio.*;import java.util.*;public class Test {static void check(boolean b){if(!b)throw new AssertionError();}public static void main(String[] args){Random r=new Random(26983);for(int n=0;n<1000;n++){int count=r.nextInt(4096)+1;ByteBuffer b=ByteBuffer.allocateDirect(count);int[] lut=new int[256];int nz=0,peak=0,expectedPeak=0;byte[] expected=new byte[count];for(int i=0;i<256;i++)lut[i]=r.nextInt(256);for(int i=0;i<count;i++){int v=r.nextInt(256);b.put(i,(byte)v);nz+=v==0?0:1;peak=Math.max(peak,v);expected[i]=(byte)lut[v];expectedPeak=Math.max(expectedPeak,lut[v]);}Iris26983COnGainMapNative.Scan s=Iris26983COnGainMapNative.scan(b,count);check(s.nonUnity==nz&&s.peakCode==peak);check(Iris26983COnGainMapNative.remap(b,count,lut)==expectedPeak);for(int i=0;i<count;i++)check(b.get(i)==expected[i]);int[] bad=lut.clone();bad[255]=256;try{Iris26983COnGainMapNative.remap(b,count,bad);throw new AssertionError();}catch(IllegalStateException ok){}for(int i=0;i<count;i++)check(b.get(i)==expected[i]);}System.out.println("PASS 1000 host JNI gain-map traversal/remap cases and atomic invalid LUT rejection");}}''')
    subprocess.run(['javac','-d',str(t),str(b/(p+'Iris26983COnGainMapNative.java')),str(cls)],check=True)
    subprocess.run(['java','-Djava.library.path='+str(t),'-cp',str(t),'com.particlesdevs.photoncamera.processing.opengl.postpipeline.Test'],check=True)
print('PASS exact appended native gain-map source and host-linked JNI entry points (not Android NDK)')
