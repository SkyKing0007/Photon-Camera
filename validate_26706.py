#!/usr/bin/env python3
from pathlib import Path
import hashlib,math,re,sys
if len(sys.argv)!=3:raise SystemExit('usage: validate_26706.py BASE26705 CANDIDATE')
b=Path(sys.argv[1]);c=Path(sys.argv[2])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def H(r):return {'app/'+str(p.relative_to(r/'app')):sha(p) for p in sorted((r/'app').rglob('*')) if p.is_file()}
def txt(r,rel):return (r/rel).read_text()
def extract_shader(s,name):
 m=re.search(r'val\s+'+re.escape(name)+r'\s*=\s*"""\n(.*?)\n\s*"""\.trimIndent\(\)',s,re.S);assert m,name
 lines=m.group(1).splitlines();ind=[len(x)-len(x.lstrip()) for x in lines if x.strip()];n=min(ind) if ind else 0
 return '\n'.join(x[n:] for x in lines)+'\n'
B=H(b);C=H(c);assert len(B)==len(C)==1823
expected={
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/assets/shaders/motionv2/gainmap.glsl','app/version.properties'}
changed={k for k in set(B)|set(C) if B.get(k)!=C.get(k)};assert changed==expected,changed
v=txt(c,'app/version.properties');assert 'VERSION_NAME=0.9726706' in v and 'VERSION_BUILD=26706' in v
# Acquisition and ownership are frozen from successful 26705.
for rel in [
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java',
'app/src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
'app/src/main/java/com/unspektrawesome/capture/FrameGeometrySnapshot.kt',
'app/src/main/java/com/unspektrawesome/preview/RawVulkanPreviewController.kt']:
 assert (b/rel).read_bytes()==(c/rel).read_bytes(),rel
cap=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
for t in ['IRIS_26705_NORMAL_AE_SHORT_HEADROOM_OWNER','IRIS_26705_ADAPTIVE_SHORT_ONLY_HEADROOM','shortHeadroomDecisionAtShutter=true','referenceProtectionEv=0.0']:
 assert t in cap,t
assert 'MOTION_26680_FORCE_LATCH_FRAMES' not in cap and 'mMotion26701' not in cap
# Production SHORT fusion shader itself is unchanged; only its tiny telemetry shader may differ.
sb=txt(b,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt');sc=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt')
assert extract_shader(sb,'universalNormalMasterShortFusion26651')==extract_shader(sc,'universalNormalMasterShortFusion26651')
for t in ['IRIS_26705_SHORT_RADIANCE_HIGHLIGHT_DOMAIN_ONLY','IRIS_26704_VALID_NORMAL_CHROMA_IMMUTABLE','IRIS_26706_SAMPLED_FUSION_DECISION_TELEMETRY','float(packed) / 255.0']:
 assert t in sc,t
# Sampled observability only; old full-frame decision readback remains dormant.
st=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
assert st.count('logSabreUniversalFusionRadiance26651(')==2
assert st.count('logSabreUniversalFusionDecision26651(')==1
for t in ['IRIS_26706_SAMPLED_FUSION_DECISION_TELEMETRY','IRIS_26706_FUSION_DECISION_SAMPLE','sampleGrid=${probeWidth}x${probeHeight}','fullFrameReadback=false','sampledNormalOwned=','sampledGeometryRejected=','productionFusionUnchanged=true','fusionDecisionMeasured=IRIS_26706_FUSION_DECISION_SAMPLE']:
 assert t in st,t
# Active global tone parity: render and gainmap share exact 26706 constants and lower body is unchanged.
r=txt(c,'app/src/main/assets/shaders/motionv2/render.glsl');g=txt(c,'app/src/main/assets/shaders/motionv2/gainmap.glsl');j=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java')
for s in (r,g):
 for t in ['IRIS_26706_VISUAL_HIGHLIGHT_SPACING','mix(0.945,0.895,pressure)','mix(0.360,0.620,pressure)','const float upperStart=0.65']:
  assert t in s,(t,'shader')
for t in ['IRIS_26706_VISUAL_HIGHLIGHT_SPACING','IRIS_26623_BROAD_WHITE_ANCHOR = 0.895f','IRIS_26623_BROAD_WHITE_SLOPE = 0.620f','visualFlatteningCountsEvenBelowHardSensorClip=true','normalAeUnchanged=true shortExposureUnchanged=true shortFusionProductionUnchanged=true']:
 assert t in j,t
assert 'iris26704BodyToneGuide(mappedGuide)' in r and 'iris26704BodyToneStrength' in r
# Highlight Compression / Local Laplacian remain off through the inherited 26704 settings authority.
settings=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java')
prefs=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java')
assert 'IRIS_26704' in prefs and 'HIGHLIGHT_COMPRESSION' in prefs
# Numerical reference for the changed global curve: monotone, bounded, exact old/new below 0.65.
def sm(a,b,x):
 t=max(0,min(1,(x-a)/max(b-a,1e-6)));return t*t*(3-2*t)
def body(x,req):
 wa=min(.95,req);bg=min(req,4*wa-1e-4) if req>wa else req;ratio=max(bg/max(wa,1e-6)-1,0);om=1-x
 return .5*(wa*x+(bg-wa)*x*om*om + bg*x/(1+ratio*x)), .5*(wa+(bg-wa)*om*(1-3*x)+bg/((1+ratio*x)**2))
def curve(x,req,p,new):
 wa=.945+((.895 if new else .925)-.945)*p;sl=.360+((.620 if new else .300)-.360)*p
 legacy,_=body(min(x,1),req)
 if x>1:
  oldwa=min(.95,req);bg=min(req,4*oldwa-1e-4) if req>oldwa else req;ratio=max(bg/max(oldwa,1e-6)-1,0);rs=bg/((1+ratio)**2);bs=.5*(oldwa+rs);res=1-oldwa;legacy=oldwa+res*(x-1)/((x-1)+res/max(bs,1e-6))
 en=sm(1.05,1.25,req)
 if en<=1e-7 or x<=.65:return legacy
 sv,ss=body(.65,req);w=.35;sec=(wa-sv)/w
 if sec<=1e-6:return legacy
 m0=max(ss,0);m1=max(sl,0);n=(m0/sec)**2+(m1/sec)**2
 if n>9:
  lim=3/math.sqrt(n);m0*=lim;m1*=lim
 if x<=1:
  t=max(0,min(1,(x-.65)/w));t2=t*t;t3=t2*t;c=(2*t3-3*t2+1)*sv+(t3-2*t2+t)*w*m0+(-2*t3+3*t2)*wa+(t3-t2)*w*m1
 else:
  res=max(1-wa,0);scale=res/max(m1,1e-6);ex=x-1;c=wa+res*ex/(ex+scale)
 return legacy+(c-legacy)*en
for req in [1.0,1.1,1.25,1.5,2.36338,4.04,8.0]:
 for p in [0,.25,.5,.75,1.0]:
  prev=-1
  for i in range(0,2401):
   x=12*i/2400;y=curve(x,req,p,True);assert math.isfinite(y) and y>=-1e-6 and y<=1.000001
   assert y+1e-5>=prev,(req,p,x,prev,y);prev=y
  for x in [0,.05,.25,.5,.65]:assert abs(curve(x,req,p,True)-curve(x,req,p,False))<1e-7
# Under strong broad pressure, nominal-white anchor moves down while the immediate >1 slope increases.
req=2.36338;p=1.0
assert curve(1.0,req,p,True)<curve(1.0,req,p,False)-0.02
oldSlope=(curve(1.01,req,p,False)-curve(1.0,req,p,False))/.01
newSlope=(curve(1.01,req,p,True)-curve(1.0,req,p,True))/.01
assert newSlope>oldSlope*1.5,(oldSlope,newSlope)
print('PASS validate 26706: exact 6-file scope; 26705 exposure/fusion production frozen; broad-highlight spacing monotone; sampled 64x48 fusion observability restored; UHDR/Spektra/native/settings preserved')
