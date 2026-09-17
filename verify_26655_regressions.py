#!/usr/bin/env python3
from pathlib import Path
import hashlib,math,re,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26655_regressions.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3])
def same(r):
 a=base/r;b=cand/r
 return a.is_file() and b.is_file() and hashlib.sha256(a.read_bytes()).digest()==hashlib.sha256(b.read_bytes()).digest()
def req(c,m):
 if not c: raise SystemExit('FAIL '+m)
# Proven upstream/runtime owners from successful 26654 must remain byte-identical.
protected=[
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2PhotonHighlightCompression.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java',
'app/src/main/assets/shaders/motionv2/local_laplacian_global_log_26621.glsl',
'app/src/main/assets/shaders/motionv2/color_transform.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/DngCreator.java',
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java']
for r in protected: req(same(r),'protected successful-26654 owner changed '+r)
hc=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2PhotonHighlightCompression.java').read_text()
req('private static final float KNEE_REF = 0.10f;' in hc,'KNEE_REF changed')
matcher=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java').read_text()
req('iris26623MapMotionSdrFinalGuide' in matcher and 'iris26654MapMotionSdrFinalGuide' not in matcher,'brightness matcher no longer frozen on inherited OFF/base map')
render=(cand/'app/src/main/assets/shaders/motionv2/render.glsl').read_text()
gain=(cand/'app/src/main/assets/shaders/motionv2/gainmap.glsl').read_text()
ll=(cand/'app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl').read_text()
down=(cand/'app/src/main/assets/shaders/motionv2/local_laplacian_downsample_26621.glsl').read_text()
java=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text()
# Exact 26654 failure must never return: pointwise-global + bounded-zero-DC post-tone correction.
for bad in ['iris26654BoundedLocalDetail','iris26654GainLocalDeltaAt','iris26654GainStructureConfidence']:
 req(bad not in render+gain+ll,'26654 pointwise/zero-DC failure returned '+bad)
# Earlier Local-Laplacian toggle authority remains removed.
req('iris26650HighlightCompressionEnabled' not in ll,'old Local-Laplacian HC toggle returned')
# 26655 must derive B from the extended-linear master before display tone and publish one final texture.
for t in ['IRIS_26655_SOURCE_DOMAIN_B_PLUS_R_FINAL_TONE','baseDomain=EXTENDED_LINEAR_LOG_RADIANCE',
          'absoluteOwner=SOURCE_DOMAIN_B','residualOwner=SOURCE_PROVEN_HIGH_FREQUENCY_R_ONLY',
          'sdrUhHdrExactSharedTexture=true']:
 req(t in java,'missing 26655 source-domain final owner '+t)
req('glProg.setTexture("SourceLinear", source);' in java,'source-domain master not bound')
req('glProg.useAssetProgram("motionv2/local_laplacian_global_log_26621");' in java,'frozen final tone not applied to B/S')
req('IRIS_26655_RENDER_CONSUMES_EXACT_FINAL_SPATIAL_TONE' in render,'SDR does not consume final texture')
req('IRIS_26655_UHDR_CONSUMES_EXACT_FINAL_SPATIAL_TONE' in gain,'UHDR does not consume final texture')
req('float mappedGuide=iris26654HighlightCompressionEnabled!=0?localMapped:legacyMapped;' in render,'SDR final-texture switch changed')
req('if(iris26654HighlightCompressionEnabled!=0)return localMapped;' in gain,'UHDR final-texture switch changed')
# Final HC-ON composite must not contain old direct highlight brightness owners.
mm=re.search(r'if\(iris26626Mode==8\)\{(.*?)\n    \}\n    if\(iris26626Mode==5\)',ll,re.S)
req(mm is not None,'mode8 source-domain final composite missing')
mode8=mm.group(1)
for bad in ['positiveOvershoot','protectedBase','reserveEv','iris26646Radiance','smoothShoulder','legacyBaseOut']:
 req(bad not in mode8,'old direct highlight owner returned to final composite '+bad)
for good in ['baseMapped','pointMapped','iris26655SourceFineStructure','iris26645SourceTexture','iris26644SourceStructure']:
 req(good in mode8,'source structure evidence missing '+good)
# Old 26635/45/46 local brightness math may exist only in legacy mode6 and is explicitly faded/disabled for HC-ON body reference.
req('IRIS_26655_HC_ON_BODY_REFERENCE_NEUTRALIZES_OLD_HIGHLIGHT_OWNERS' in ll,'HC-ON legacy-owner neutralization missing')
req('iris26655BodyReferenceOnly!=0?vec3(0.0):iris26646SourceRadianceSurvival(p)' in ll,'26646 radiance not disabled on HC-ON body reference')
req('positiveOvershoot*(1.0-bodyReferenceFade)' in ll and 'upperGate*(1.0-bodyReferenceFade)' in ll,'legacy highlight operations not faded out on HC-ON')
# Edge-aware source-domain pyramid must coexist with byte-semantic legacy downsample branch.
for t in ['uniform int iris26655EdgeAware;','if(iris26655EdgeAware==0)','Output=legacySum*(1.0/256.0);',
          'IRIS_26655_SOURCE_DOMAIN_EDGE_AWARE_DOWNSAMPLE','float d=(sampleValue-centerValue)/0.65;']:
 req(t in down,'source/legacy downsample regression '+t)
# Generic spatial reference model: flat identity, strong-edge isolation, smooth redistribution, fine detail separated into R.
K=[1.0,4.0,6.0,4.0,1.0];N=4096
def down1(x,sigma=.65):
 out=[];n=len(x)
 for q in range((n+1)//2):
  ci=min(2*q,n-1);c=x[ci];sm=ws=0.0
  for ko,off in zip(K,range(-2,3)):
   i=max(0,min(n-1,ci+off));v=x[i];rw=math.exp(-.5*((v-c)/sigma)**2);w=ko*rw;sm+=v*w;ws+=w
  out.append(sm/ws)
 return out
def up1(coarse,source,sigma=.75):
 n=len(source);m=len(coarse);out=[]
 for p in range(n):
  cp=(p+.5)*m/n-.5;c0=math.floor(cp);sm=ws=0.0
  for off in range(-1,3):
   q=max(0,min(m-1,c0+off));d=cp-q;sp=max(1.5-abs(d),0.0);v=coarse[q];ev=(v-source[p])/sigma;w=sp*math.exp(-.5*ev*ev);sm+=v*w;ws+=w
  out.append(sm/ws if ws>1e-8 else source[p])
 return out
def bfield(vals):
 src=[math.log(max(v,2**-12),2) for v in vals];c=src[:]
 while len(c)>32:c=down1(c)
 return [2**v for v in up1(c,src)]
flat=[.8]*N;bf=bfield(flat);req(max(abs(a-b) for a,b in zip(flat,bf))<1e-9,'flat-field identity failed')
m=N//2;step=[.2]*m+[2.0]*(N-m);bs=bfield(step)
req(max(abs(v-.2) for v in bs[m-100:m])<3e-4,'strong edge dark-side halo')
req(max(abs(v-2.0) for v in bs[m:m+100])<3e-3,'strong edge bright-side halo')
for sig in (60.,120.,240.):
 src=[.25+1.5*math.exp(-.5*((i-m)/sig)**2) for i in range(N)];b=bfield(src)
 req(b[m]<src[m]-.10,'smooth compact highlight center not redistributed')
 req(b[m+200]>src[m+200]+.02,'smooth compact highlight shoulder not broadened')
fine=[.8+.10*math.sin(2*math.pi*i/8.) for i in range(N)];b=bfield(fine)
mb=sum(b)/N;sb=(sum((v-mb)**2 for v in b)/N)**.5;ms=sum(fine)/N;ss=(sum((v-ms)**2 for v in fine)/N)**.5
req(sb<ss*.10,'high-frequency structure leaked into illumination base')
print('PASS 26655 permanent regressions: successful-26654 fusion/matcher/HC/color/DNG protected; 26654 pointwise-zeroDC failure absent; source-domain B+R precedes display tone; old direct highlight owners excluded from final HC path; SDR/UHDR exact shared final texture; generic flat/edge/smooth/fine spatial invariants PASS')
