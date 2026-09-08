#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys
CHANGED=[
'app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl',
'app/src/main/assets/shaders/motionv2/gainmap.glsl',
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2AdaptiveColorAppearance.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
'app/version.properties']
PROTECTED_26611={
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt':'ddc9d5194fc0582b7de8a2173e6ec447ae3c71fff53009ed8f6f5d4e8c1b024d',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt':'3e218338533f0e5e60a5811850af974d37245df8f0659042350952c341cb41d7',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt':'9b3e8a35b7a20b3307e627b6759a0cc336436b4a8e520fadab3661310056ebb9'}
def fail(m):raise SystemExit('FAIL: '+m)
def H(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def allh(r):return {str(p.relative_to(r)):H(p) for p in sorted((Path(r)/'app').rglob('*')) if p.is_file()}
def need(s,t,l):
 if t not in s:fail(l+' missing '+t)
def main():
 if len(sys.argv)!=3:fail('usage base candidate')
 b,c=map(Path,sys.argv[1:]);bh,ch=allh(b),allh(c)
 if set(bh)!=set(ch) or len(bh)!=1708:fail('full app universe changed')
 diff=sorted(k for k in bh if bh[k]!=ch[k])
 if diff!=sorted(CHANGED):fail('runtime diff allowlist '+repr(diff))
 v=(c/'app/version.properties').read_text()
 for t in ['VERSION_NAME=0.9726612','VERSION_BUILD=26612']:need(v,t,'version')
 for p,h in PROTECTED_26611.items():
  if H(c/p)!=h or H(b/p)!=h:fail('successful-26611 SHORT/CFA/clean-HDR owner changed '+p)
 # Successful 26611 acquisition/preview/bridge/DNG remain byte-identical by direct owner checks too.
 frozen=[
 'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
 'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java',
 'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/GLPreview.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
 'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26545SabreProcessor.kt',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java']
 for p in frozen:
  if (b/p).read_bytes()!=(c/p).read_bytes():fail('successful-26611 frozen owner changed '+p)
 rj=(c/CHANGED[5]).read_text();rg=(c/CHANGED[2]).read_text();gg=(c/CHANGED[1]).read_text();aj=(c/CHANGED[4]).read_text();ag=(c/CHANGED[0]).read_text();enc=(c/CHANGED[6]).read_text();cpp=(c/CHANGED[3]).read_text()
 for t in ['IRIS_26612_UNIVERSAL_BODY_BROAD_COMPACT_PRESENTATION','motionV2ToneProjectedBroadTailStrength','motionV2ToneCompactTailStrength','motionV2ToneProjectedHardCeilingFraction','motionV2ToneAdaptiveStrength','motionV2DisplayGain','sourceP995Final','sdrP995Target','hdrP995Boost']:
  need(rj,t,'26612 tone-plan authority')
 # No semantic scene classifier inside the plan method.
 a=rj.index('public static Iris26612TonePlan iris26612TonePlan');z=rj.index('static float iris26612BaselineMotionSdr',a);code=re.sub(r'/\*.*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"',' ',rj[a:z],flags=re.S).lower()
 for word in ['night','day','window','cloud','chandelier','streetlight','headlight','candle','snow','sky','sun','curtain']:
  if re.search(r'\b'+word+r'\b',code):fail('scene-semantic 26612 tone-plan classifier '+word)
 # Exact uniform declared/assigned contract; catches 26611 1x UHDR silent-default bug.
 def uniforms(s):return set(re.findall(r'(?m)^\s*uniform\s+\w+\s+(iris26612\w+)\s*;',s))
 def setters(s):return set(re.findall(r'setVar\("(iris26612\w+)"',s))
 sdr={'iris26612SourceP99Final','iris26612SourceP995Final','iris26612SourceP998Final','iris26612SdrP99Target','iris26612SdrP995Target','iris26612SdrP998Target','iris26612ToneStrength'}
 hdr={'iris26612SourceP99Final','iris26612SourceP995Final','iris26612SourceP998Final','iris26612HdrP99Boost','iris26612HdrP995Boost','iris26612HdrP998Boost','iris26612ToneStrength'}
 if uniforms(rg)!=sdr:fail('render uniform declaration contract')
 if uniforms(gg)!=hdr:fail('gainmap uniform declaration contract')
 if uniforms(ag)!=sdr:fail('adaptive uniform declaration contract')
 ri=rj.find('useAssetProgram("motionv2/render")');gi=rj.find('useAssetProgram("motionv2/gainmap")')
 if ri<0:ri=rj.find('useAssetProgram("motionv2/render.glsl")')
 if gi<0:gi=rj.find('useAssetProgram("motionv2/gainmap.glsl")')
 if ri<0 or gi<0 or ri>=gi:fail('render/gainmap asset blocks')
 rb=rj[ri:gi]; gb=rj[gi:rj.find('glProg.closed',gi)+300]
 if not sdr.issubset(setters(rb)):fail('1x SDR setter contract '+repr(sdr-setters(rb)))
 if not hdr.issubset(setters(gb)):fail('1x UHDR setter contract '+repr(hdr-setters(gb)))
 if not sdr.issubset(setters(aj)):fail('adaptive setter contract '+repr(sdr-setters(aj)))
 for stale in ['iris26610HdrP99Boost','iris26610HdrP998Boost','iris26612SdrP99Target','iris26612SdrP998Target']:
  if f'setVar("{stale}"' in gb:fail('wrong 1x UHDR setter '+stale)
 # JNI transport exact field order.
 fields=['iris26612SourceP99Final','iris26612SourceP995Final','iris26612SourceP998Final','iris26612SdrP99Target','iris26612SdrP995Target','iris26612SdrP998Target','iris26612HdrP99Boost','iris26612HdrP995Boost','iris26612HdrP998Boost','iris26612ToneStrength']
 def ordered(s,names,label):
  p=[]
  for n in names:
   i=s.find(n)
   if i<0:fail(label+' missing '+n)
   p.append(i)
  if p!=sorted(p):fail(label+' field order')
 ordered(enc[enc.index('private static native boolean writeTrue2xNative('):],fields,'Java JNI declaration')
 ordered(cpp[cpp.index('Java_com_particlesdevs_photoncamera_processing_ultrahdr_MotionV2Jpeg444Encoder_writeTrue2xNative('):],fields,'C++ JNI signature')
 members=['sourceP99Final','sourceP995Final','sourceP998Final','sdrP99Target','sdrP995Target','sdrP998Target','hdrP99Boost','hdrP995Boost','hdrP998Boost','strength']
 call=enc[enc.index('final boolean baseOk = writeTrue2xNative('):enc.index('final long renderMs',enc.index('final boolean baseOk = writeTrue2xNative('))]
 ordered(call,['iris26612Tone.'+x for x in members],'Java JNI call')
 for f in fields:
  cap='uI'+f[1:]
  need(cpp,'uniform float '+cap+';','true2x GPU')
  need(cpp,'loc("'+cap+'"),params->'+f,'true2x GPU setter')
 # CPU/GPU/1x equations all have p99/p995/p998 knots and same body.
 for s,l in [(rg,'1x SDR'),(gg,'1x UHDR'),(cpp,'true2x CPU/GPU')]:
  for t in ['26612','P995','P998']:need(s,t,l)
 print('PASS exact 8-file 26612 runtime scope from successful 26611 Actions compiled candidate; version 0.9726612/26612')
 print('PASS successful-26611 SHORT/CFA/clean-HDR/acquisition/preview owners frozen byte-identical')
 print('PASS universal content-driven body/broad/compact/display-gain presentation plan has no scene-semantic branch')
 print('PASS 1x SDR / adaptive / 1x UHDR exact declared-assigned uniform contract; 26611 UHDR silent-default bug rejected')
 print('PASS true2x Java-JNI/native Params/GPU uniform transport uses the same p99/p995/p998 SDR/UHDR plan')
if __name__=='__main__':main()
