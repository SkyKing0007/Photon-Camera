#!/usr/bin/env python3
"""26906 original-source scope, tonal numeric, Night B/A Java, and capture-ownership regressions.
Actual ANGLE shader compilation is separately required by compile_gles.py. This is not Android assemble proof.
"""
from pathlib import Path
import os,hashlib,math,re,subprocess,sys,tempfile,shutil,statistics
base=Path(os.getenv('PHOTON_26906_BASE','/mnt/data/photon_26905_current_source'))
cand=Path(os.getenv('PHOTON_26906_CANDIDATE','/mnt/data/photon_26906_work/candidate'))
changed=[
 'app/version.properties',
 'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/IrisNightExposureSelector.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
 'app/src/main/assets/shaders/motionv2/render.glsl',
 'app/src/main/assets/shaders/motionv2/gainmap.glsl',
 'app/src/main/assets/shaders/iris26876/b_fused_final_p3_gain.frag'
]
def manifest(root):return {p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'app').rglob('*') if p.is_file()}
a=manifest(base);b=manifest(cand)
assert len(a)==len(b)==2027 and a.keys()==b.keys()
assert {p for p in a if a[p]!=b[p]}==set(changed)
assert not any('/vendor/' in s or '/spektra/' in s or '.spv' in s for s in changed)
assert b['app/version.properties']!=a['app/version.properties']
print('PASS original compiled 26905 source scope: 2027, 9 intentional changes, 2018 protected unchanged')
read=lambda x:(cand/x).read_text()
exp=read('app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/IrisNightExposureSelector.java')
cc=read('app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
selector=read('app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/IrisNightFrameSelector.java')
params=read('app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java')
hdr=read('app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java')
render=read('app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java')
assert 'freezeNormalOnlyB(CaptureController' in exp and 'experimentB ? 1.0 : Math.pow(2.0, 0.70)' in exp
assert 'IrisNightFrameSelector.freezeNormalOnlyB(iris26540RequestedFrames)' in cc
assert 'IrisNightFrameSelector.freezePlan(iris26540RequestedFrames)' in cc
assert 'IrisNightExposureSelector.freezeNormalOnlyB(' in cc
assert 'IrisNightExposureSelector.freezePlan(' in cc
assert 'return new Plan(total, total - longFrames, longFrames, false);' in selector
assert 'return new Plan(n, n, 0, true);' in selector
assert 'ticket.forceManualSensor = plan.iris26906BOffAllNormal;' in cc
assert 'final boolean useManualSensor = manual && (ticket.forceManualSensor || !halEquivalent);' in cc
assert 'if (!manual && !Boolean.TRUE.equals(aeLockAvailable))' in cc
assert 'normalTargetIso <= 0' in cc and 'motion26713ResultMatchesTarget(' in cc
assert 'public boolean iris26906ExperimentBSelected = false;' in params
assert 'iris26856BRequestedOnly || mIris26903NightB' in hdr
assert render.count('glProg.setVar("iris26906BVisualToneEnabled",')==2
print('PASS B-only frozen exposure and presentation identity; Night A and B all-NORMAL planning preserved')

shaders=[read('app/src/main/assets/shaders/'+s) for s in ('motionv2/render.glsl','motionv2/gainmap.glsl','iris26876/b_fused_final_p3_gain.frag')]
pattern=r'float iris26906BVisualTone\(float y\) \{.*?\n\}'
fns=[re.search(pattern,s,re.S).group(0) for s in shaders]
assert fns[0]==fns[1]==fns[2]
assert all(s.count('float iris26906BVisualTone(')==1 for s in shaders)
assert shaders[0].count('if(iris26906BVisualToneEnabled!=0) mappedGuide=iris26906BVisualTone(mappedGuide);')==2
assert shaders[1].count('iris26906BVisualToneEnabled!=0 ? iris26906BVisualTone(finalSdr) : finalSdr')==1
assert shaders[2].count('rgb*=iris26906BVisualTone(finishGuide)/finishGuide;')==1
assert shaders[2].index('rgb*=iris26906BVisualTone(finishGuide)')<shaders[2].index('rgb=iris26638ApplyShadowFloorGuard(rgb);')
for s in shaders[:2]: assert 'uniform int iris26906BVisualToneEnabled;' in s

def smooth(a,b,x):
 t=max(0.,min(1.,(x-a)/(b-a)))
 return t*t*(3.-2.*t)
def f(y):
 x=max(y,0.)
 if x>=0.70:return x
 toe=x*(1.-.330*(1.-smooth(.015,.145,x)))
 mid=.15*(x-.230)*smooth(.130,.190,x)*(1.-smooth(.5,.7,x))
 return max(toe+mid,0.)
def srgb(x):
 return 12.92*x if x<=.0031308 else 1.055*x**(1/2.4)-.055
mid=(f(.2300001)-f(.2299999))/.0000002
ratio=srgb(f(.025))/srgb(.025)
assert .77<=ratio<=.84,(ratio,'toe visual ratio expected about .80')
assert abs(mid-1.15)<1e-4,mid
assert all(abs(f(x)-x)<1e-8 for x in (.7,.78,.8,.92,1.0,1.7))
x=0;minSlope=20
for i in range(1,100001):
 y=i/100000;new=f(y);slope=(new-f(x))/(y-x);minSlope=min(minSlope,slope)
 assert new>=f(x)-1e-8,(i,new,f(x))
 x=y
assert minSlope>0.50,minSlope
print(f'PASS B SDR/Gainmap/50MP shader transfer identical, toe sRGB={ratio:.3f} (~20% darker), midtone slope={mid:.3f}, monotone minimum={minSlope:.3f}')

with tempfile.TemporaryDirectory(prefix='photon26906javac_') as td:
 out=Path(td);pkg=out/'com/particlesdevs/photoncamera/processing/parameters';pkg.mkdir(parents=True)
 for name in ('IrisNightFrameSelector','IrisNightExposureSelector'):
  shutil.copy2(cand/f'app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/{name}.java',pkg/(name+'.java'))
 def put(p,s):
  f=out/p;f.parent.mkdir(parents=True,exist_ok=True);f.write_text(s)
 put('android/util/Range.java','package android.util;public final class Range<T extends Comparable<T>>{T a,b;public Range(T a,T b){this.a=a;this.b=b;}public T getLower(){return a;}public T getUpper(){return b;}}')
 put('android/hardware/camera2/CameraCharacteristics.java','package android.hardware.camera2;import android.util.Range;public class CameraCharacteristics{public static class Key<T>{} public static final Key<Range<Long>> SENSOR_INFO_EXPOSURE_TIME_RANGE=new Key<>();public static final Key<Range<Integer>> SENSOR_INFO_SENSITIVITY_RANGE=new Key<>();public static final Key<Integer> SENSOR_MAX_ANALOG_SENSITIVITY=new Key<>();public <T>T get(Key<T> k){return null;}}')
 put('android/hardware/camera2/CaptureResult.java','package android.hardware.camera2;public class CaptureResult{public static final Object CONTROL_AE_ANTIBANDING_MODE=new Object();public static final int CONTROL_AE_ANTIBANDING_MODE_AUTO=0,CONTROL_AE_ANTIBANDING_MODE_50HZ=1;public <T>T get(Object o){return null;}}')
 put('android/hardware/camera2/CaptureRequest.java','package android.hardware.camera2;public class CaptureRequest{public static final Object CONTROL_AE_MODE=new Object(),SENSOR_EXPOSURE_TIME=new Object(),SENSOR_SENSITIVITY=new Object();public static final int CONTROL_AE_MODE_OFF=0;public static class Builder{public <T>void set(Object k,T v){}}}')
 put('com/particlesdevs/photoncamera/capture/CaptureController.java','package com.particlesdevs.photoncamera.capture;public class CaptureController{public long mPreviewExposureTime=100000000L;public int mPreviewIso=100;public static class Params{public double getCurrentExposureValue(){return 0;}public double getCurrentISOValue(){return 0;}}public Params getParamController(){return new Params();}}')
 put('com/particlesdevs/photoncamera/util/Log.java','package com.particlesdevs.photoncamera.util;public class Log{public static void i(String a,String b){}}')
 put('com/particlesdevs/photoncamera/processing/parameters/ExposureIndex.java','package com.particlesdevs.photoncamera.processing.parameters;public class ExposureIndex{public static final long sec=1000000000L;}')
 put('com/particlesdevs/photoncamera/processing/parameters/Check26906.java','''package com.particlesdevs.photoncamera.processing.parameters;
import com.particlesdevs.photoncamera.capture.CaptureController;
public class Check26906{public static void main(String[]a){
 for(int n:new int[]{2,8,14,30,50}){
 var pb=IrisNightFrameSelector.freezeNormalOnlyB(n);
 if(pb.totalFrames!=n||pb.shortFrames!=n||pb.longFrames!=0)throw new AssertionError("B frame allocation "+n);
 for(int i=0;i<n;i++)if(!pb.isShortFrame(i))throw new AssertionError("B normal index "+i);
 if(n>=3){var pa=IrisNightFrameSelector.freezePlan(n);if(pa.longFrames<1||pa.shortFrames+pa.longFrames!=n)throw new AssertionError("A changed "+n);}
 }
 var c=new CaptureController();
 var nightB=IrisNightExposureSelector.freezeNormalOnlyB(c,null,0f,false,30,null);
 var nightA=IrisNightExposureSelector.freezePlan(c,null,0f,false,30,null,false);
 long bEnergy=nightB.shortExposureNs*nightB.shortIso,aEnergy=nightA.shortExposureNs*nightA.shortIso;
 if(bEnergy<=aEnergy*1.5 || bEnergy>=aEnergy*1.75)throw new AssertionError("0.7 EV isolation "+bEnergy+"/"+aEnergy);
 if(nightB.longExposureNs!=nightB.shortExposureNs||nightB.longIso!=nightB.shortIso)throw new AssertionError("B no long");
 var nightAWithLong=IrisNightExposureSelector.freezePlan(c,null,0f,false,30,null,true);
 if(nightAWithLong.longExposureNs<=nightAWithLong.shortExposureNs)throw new AssertionError("Night A LONG changed");
 c.mPreviewExposureTime=500000000L;c.mPreviewIso=500;
 var capB=IrisNightExposureSelector.freezeNormalOnlyB(c,null,0f,false,30,null);
 if(capB.shortExposureNs<240000000L||capB.shortExposureNs>250000000L||capB.shortIso<995||capB.shortIso>1010)throw new AssertionError("B capped shutter/adaptive ISO");
 System.out.println("PASS real-source Night B exact all-NORMAL, A bracket unchanged; -0.70EV B-only removal; shutter-priority ISO preserved");
}}''')
 files=[str(p) for p in out.rglob('*.java')]
 proc=subprocess.run(['javac','-encoding','UTF-8','-d',str(out/'classes'),*files],capture_output=True,text=True)
 assert proc.returncode==0,(proc.stdout,proc.stderr)
 proc=subprocess.run(['java','-cp',str(out/'classes'),'com.particlesdevs.photoncamera.processing.parameters.Check26906'],capture_output=True,text=True)
 assert proc.returncode==0,(proc.stdout,proc.stderr)
 print(proc.stdout.strip())
print('PASS all 26906 locally-applicable scoped source / numeric tone / Java behavior checks')
