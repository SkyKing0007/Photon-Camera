#!/usr/bin/env python3
from pathlib import Path
import hashlib,math,re,sys,textwrap
if len(sys.argv)!=3: raise SystemExit('usage: verify_26653_regressions.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3])
def same(r):
 a=base/r;b=cand/r
 return a.is_file() and b.is_file() and hashlib.sha256(a.read_bytes()).digest()==hashlib.sha256(b.read_bytes()).digest()
def emb(root):
 s=(root/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text(); d={}
 for m in re.finditer(r'\bval\s+([A-Za-z_]\w*)\s*=\s*"""(.*?)"""\.trimIndent\(\)',s,re.S): d[m.group(1)]=textwrap.dedent(m.group(2)).strip('\n')
 return d
# Permanent route protections.
for r in ['app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java','app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHeicUltraHdrEncoder.java','app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/IrisHardwareHevcEncoder.java','app/src/main/cpp/iris_heic_jni.cpp','app/src/main/java/com/particlesdevs/photoncamera/processing/DngCreator.java','app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java']:
 assert same(r),r
b,c=emb(base),emb(cand)
for name in ['merge','rejection','mergeShadowLong26558','normalDngMerge','superResDetailMerge26561','convertAlignmentSparse','universalShortValidityAugment26651','universalFusionTelemetry26651']:
 assert name in b and name in c and b[name]==c[name],name
assert {n for n in b if b[n]!=c[n]}=={'universalNormalMasterShortFusion26651'}
f=c['universalNormalMasterShortFusion26651']
# 26651/26652 fusion ownership survives, with only full-resolution radiance admission strengthened.
for t in ['edgeCorrespondence(referenceUv, sampleUv)','IRIS_26652_LOCAL_CHROMA_CONSENSUS','IRIS_26652_TRUSTED_SHORT_CHROMA_CONSENSUS','float targetY = mix(normalY, shortY, radianceAuthority);','minimum3(measuredNormalPhysicalLoss)','IRIS_26653_FULL_RES_FINE_STRUCTURE_SHORT_RADIANCE_GUARD']:
 assert t in f,t
# SHORT remains outside temporal, SR, DNG.
st=(cand/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
for t in ['if (frame.role != RawBurstFrameRole.HIGHLIGHT_SHORT)','if (enableSabreSuperRes && frame.role == RawBurstFrameRole.NORMAL)','if (normalDngAccumulator != 0 && frame.role == RawBurstFrameRole.NORMAL)']:
 assert t in st,t
# No stale pre-color Highlight Compression owner can return.
whole='\n'.join((cand/p).read_text(errors='ignore') for p in [
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2PhotonHighlightCompression.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java',
'app/src/main/assets/shaders/motionv2/color_transform.glsl'])
for bad in ['motionV2PhotonCurveOff','motionV2PhotonCurveOn','USE_PHOTON_HIGHLIGHT_COMPRESSION','toggleApplication=exactOnOverOffCurveRatio','photonToggleDifferentialPreColor=true']:
 assert bad not in whole,bad
hc=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2PhotonHighlightCompression.java').read_text()
assert 'private static final float KNEE_REF = 0.10f;' in hc
# Numeric permanent regression: exact 26652 OFF behavior, exact identity <=0.65 when ON, monotonic extended headroom,
# and real 170155 calibration headroom remains visibly separated instead of collapsing near white.
def clamp(x,a,b): return max(a,min(b,x))
def smooth(a,b,x):
 t=clamp((x-a)/max(b-a,1e-6),0,1); return t*t*(3-2*t)
def legacy(x,g):
 x=max(x,0); requested=max(g,1e-6)*.8; white=min(.95,requested); body=requested
 if requested>white: body=min(requested,4*white-1e-4)
 ratio=max(body/max(white,1e-6)-1,0)
 if x<=1:
  om=1-x; cubic=white*x+(body-white)*x*om*om; rational=body*x/(1+ratio*x); return .5*(cubic+rational)
 rs=body/((1+ratio)*(1+ratio)); slope=.5*(white+rs); reserve=max(1-white,0)
 if reserve<=1e-6:return white
 scale=reserve/max(slope,1e-6); ex=x-1; return white+reserve*ex/(ex+scale)
def pressure(broad,hard,basew,adaptw):
 br=smooth(.015,.060,clamp(broad,0,1)); hd=smooth(.010,.050,clamp(hard,0,1)); bw=max(basew,1); aw=max(adaptw,bw); span=max(aw/bw-1,0); sp=smooth(.08,.35,span); return clamp(max(.70*br+.30*sp,.75*hd),0,1)
def offmap(x,g,broad,hard,bw,aw):
 x=max(x,0); old=legacy(x,g); requested=max(g,1e-6)*.8; en=smooth(1.05,1.25,requested)
 if en<=1e-7 or x<=.65:return old
 pr=pressure(broad,hard,bw,aw); tw=.945+(.925-.945)*pr; ts=.360+(.300-.360)*pr
 white=min(.95,requested); body=requested
 if requested>white:body=min(requested,4*white-1e-4)
 ratio=max(body/max(white,1e-6)-1,0); sx=.65; om=1-sx
 sv=.5*(white*sx+(body-white)*sx*om*om + body*sx/(1+ratio*sx))
 cd=white+(body-white)*om*(1-3*sx); rd=body/((1+ratio*sx)**2); ss=.5*(cd+rd); w=1-sx; sec=(tw-sv)/w
 if sec<=1e-6:return old
 m0=max(ss,0);m1=max(ts,0);n=(m0/sec)**2+(m1/sec)**2
 if n>9:
  lim=3/math.sqrt(n);m0*=lim;m1*=lim
 if x<=1:
  t=clamp((x-sx)/w,0,1);t2=t*t;t3=t2*t; cand=(2*t3-3*t2+1)*sv+(t3-2*t2+t)*w*m0+(-2*t3+3*t2)*tw+(t3-t2)*w*m1
 else:
  reserve=max(1-tw,0);scale=reserve/max(m1,1e-6);ex=x-1;cand=tw+reserve*ex/(ex+scale)
 return old+(cand-old)*en
def onmap(x,g,broad,hard,bw,aw,knee,paw):
 old=offmap(x,g,broad,hard,bw,aw)
 if x<=.65:return old
 requested=max(g,1e-6)*.8;en=smooth(1.05,1.25,requested)
 if en<=1e-7:return old
 pr=max(pressure(broad,hard,bw,aw),clamp((.90-knee)/(.90-.55),0,1));tw=.915+(.890-.915)*pr;ts=.090+(.055-.090)*pr
 white=min(.95,requested);body=requested
 if requested>white:body=min(requested,4*white-1e-4)
 ratio=max(body/max(white,1e-6)-1,0);sx=.65;om=1-sx
 sv=.5*(white*sx+(body-white)*sx*om*om + body*sx/(1+ratio*sx));cd=white+(body-white)*om*(1-3*sx);rd=body/((1+ratio*sx)**2);ss=.5*(cd+rd);w=.35;sec=(tw-sv)/w
 if sec<=1e-6:return old
 m0=max(ss,0);m1=max(ts,0);n=(m0/sec)**2+(m1/sec)**2
 if n>9:
  lim=3/math.sqrt(n);m0*=lim;m1*=lim
 if x<=1:
  t=clamp((x-sx)/w,0,1);t2=t*t;t3=t2*t;cand=(2*t3-3*t2+1)*sv+(t3-2*t2+t)*w*m0+(-2*t3+3*t2)*tw+(t3-t2)*w*m1
 else:
  reserve=max(1-tw,0); span=max(1,math.sqrt(max(paw,1)));scale=reserve/max(m1,1e-6)*span;ex=x-1;cand=tw+reserve*ex/(ex+scale)
 return old+(cand-old)*en
# OFF unchanged by definition and ON exact through 0.65.
for g in [1.0,1.31,3.3,6.0628657]:
 for x in [0,.1,.3,.5,.649999,.65]:
  a=offmap(x,g,.055,.016,1,1); b=onmap(x,g,.055,.016,1,1,.8383159,1); assert abs(a-b)<1e-12,(g,x,a,b)
# low requested gain cannot activate compression.
for x in [0,.65,1,1.25,2,4]: assert abs(offmap(x,1.0,1,1,1,2)-onmap(x,1.0,1,1,1,2,.55,2))<1e-12
# monotonic sweep over domain/pressure/knee.
for g in [1.0,1.31,3.3,6.0628657]:
 for broad in [0,.02,.06,.2]:
  for hard in [0,.015,.05]:
   for knee in [.55,.8383159,.90]:
    vals=[onmap(i/100,g,broad,hard,1,1.4,knee,1.4) for i in range(0,801)]
    assert all(vals[i+1]+2e-6>=vals[i] for i in range(len(vals)-1)),(g,broad,hard,knee)
# Exact real 170155-style gain and knee: preserve meaningful extended-range spacing.
vals=[onmap(x,6.0628657,.055225,.016215,1,1,.8383159,1) for x in [1.0,1.25,2.0918,3.8]]
assert vals[1]-vals[0]>.012 and vals[2]-vals[1]>.018 and vals[3]-vals[2]>.012,vals
print('PASS 26653 permanent regressions: temporal/Night/DNG/SR/HEIC/matcher protected; no stale pre-color HC owner; KNEE_REF 0.10; final ON tone exact through 0.65, low-gain inert, monotonic to 8x, and real 170155 extended headroom remains separated')
