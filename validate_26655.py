#!/usr/bin/env python3
from pathlib import Path
import hashlib,math,re,sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26655.py BASE CANDIDATE')
base,cand=map(Path,sys.argv[1:3])
def H(root): return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((root/'app').rglob('*')) if p.is_file()}
def txt(root,r): return (root/r).read_text()
def req(c,m):
 if not c: raise SystemExit('FAIL '+m)
bh,ch=H(base),H(cand); req(len(bh)==len(ch)==1721,'app count')
allow={
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_downsample_26621.glsl',
'app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl',
'app/src/main/assets/shaders/motionv2/gainmap.glsl',
'app/version.properties'}
actual={r for r in set(bh)|set(ch) if bh.get(r)!=ch.get(r)}; req(actual==allow,f'allowlist mismatch {sorted(actual^allow)}')
# Critical upstream owners remain exact successful 26654 bytes.
for r in [
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2PhotonHighlightCompression.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java',
'app/src/main/assets/shaders/motionv2/local_laplacian_global_log_26621.glsl',
'app/src/main/assets/shaders/motionv2/color_transform.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/processing/DngCreator.java',
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java']:
 req(bh[r]==ch[r],'protected owner changed '+r)
matcher=txt(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java')
req('iris26623MapMotionSdrFinalGuide' in matcher and 'iris26654MapMotionSdrFinalGuide' not in matcher,'brightness matcher authority changed')
hc=txt(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2PhotonHighlightCompression.java')
req('private static final float KNEE_REF = 0.10f;' in hc,'KNEE_REF changed')
# New final owner and exact source-domain sequence.
r=txt(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java')
for t in ['IRIS_26655_SOURCE_DOMAIN_B_PLUS_R_FINAL_TONE','IRIS_26655_SOURCE_DOMAIN_SPATIAL_HIGHLIGHT_AUTHORITY',
          'absoluteOwner=SOURCE_DOMAIN_B','residualOwner=SOURCE_PROVEN_HIGH_FREQUENCY_R_ONLY',
          'sdrUhHdrExactSharedTexture=true','matcherUses26652OffMap=true',
          'iris26655BuildSourceDomainSpatialHighlightTone','IRIS_26655_BASE_TARGET_MAX_DIM = 32']:
 req(t in r,'missing render owner '+t)
req(r.count('glProg.setVar("iris26655EdgeAware", 1);')==1,'source-domain bilateral owner count')
req(r.count('glProg.setVar("iris26655EdgeAware", 0);')==4,'legacy downsample explicit-off count')
req('iris26621BuildLocalLaplacianTone(\n            GLTexture source, boolean publishTrue2xMap, boolean iris26655BodyReferenceOnly)' in r,'HC body-reference signature')
req('extendedLinearHdr, !iris26655SpatialHighlight, iris26655SpatialHighlight' in r,'HC body-reference call')
# Remap: B+R, generic fine evidence, and stale direct highlight owners absent from final mode8.
ll=txt(cand,'app/src/main/assets/shaders/motionv2/local_laplacian_remap_26621.glsl')
for t in ['IRIS_26655_UNIVERSAL_SOURCE_FINE_STRUCTURE_EVIDENCE','IRIS_26655_EDGE_AWARE_ILLUMINATION_BASE',
          'IRIS_26655_SOURCE_DOMAIN_ILLUMINATION_BASE_EXPAND','IRIS_26655_SOURCE_DOMAIN_B_PLUS_R_FINAL_COMPOSITE',
          'highlightGuide=max(sourceGuide,baseSource)','IRIS_26655_HC_ON_BODY_REFERENCE_NEUTRALIZES_OLD_HIGHLIGHT_OWNERS',
          'iris26655BodyReferenceOnly!=0?vec3(0.0):iris26646SourceRadianceSurvival(p)',
          'positiveOvershoot*(1.0-bodyReferenceFade)','upperGate*(1.0-bodyReferenceFade)']:
 req(t in ll,'missing remap contract '+t)
mm=re.search(r'if\(iris26626Mode==8\)\{(.*?)\n    \}\n    if\(iris26626Mode==5\)',ll,re.S); req(mm is not None,'mode8 extraction')
mode8=mm.group(1)
for bad in ['positiveOvershoot','protectedBase','reserveEv','iris26646Radiance','smoothShoulder','legacyBaseOut']:
 req(bad not in mode8,'stale direct tone in final B+R mode8 '+bad)
for good in ['baseMapped','pointMapped','iris26655SourceFineStructure','iris26645SourceTexture','iris26644SourceStructure']:
 req(good in mode8,'missing final B+R evidence '+good)
# Downsample must preserve exact legacy path and use bilateral only for 26655 source B.
down=txt(cand,'app/src/main/assets/shaders/motionv2/local_laplacian_downsample_26621.glsl')
for t in ['uniform int iris26655EdgeAware;','if(iris26655EdgeAware==0)','Output=legacySum*(1.0/256.0);',
          'IRIS_26655_SOURCE_DOMAIN_EDGE_AWARE_DOWNSAMPLE','float d=(sampleValue-centerValue)/0.65;']:
 req(t in down,'downsample contract '+t)
# Exact final spatial tone texture must be shared by SDR and UHDR; no 26654 zero-DC workaround survives.
rg=txt(cand,'app/src/main/assets/shaders/motionv2/render.glsl'); gm=txt(cand,'app/src/main/assets/shaders/motionv2/gainmap.glsl')
req('IRIS_26655_RENDER_CONSUMES_EXACT_FINAL_SPATIAL_TONE' in rg,'SDR shared final tone marker')
req('float mappedGuide=iris26654HighlightCompressionEnabled!=0?localMapped:legacyMapped;' in rg,'SDR HC-on not exact final texture')
req('IRIS_26655_UHDR_CONSUMES_EXACT_FINAL_SPATIAL_TONE' in gm,'UHDR shared final tone marker')
req('if(iris26654HighlightCompressionEnabled!=0)return localMapped;' in gm,'UHDR HC-on not exact final texture')
for bad in ['iris26654BoundedLocalDetail','iris26654GainLocalDeltaAt','iris26654GainStructureConfidence']:
 req(bad not in rg+gm+ll,'stale 26654 zero-DC path '+bad)
# No semantic/scene classifiers may be introduced by 26655. Inspect added code only so
# inherited generic identifiers such as ProjectedHardCeilingFraction do not false-fail.
import difflib
added=[]
for rel in allow:
 if not rel.endswith(('.java','.glsl')): continue
 before=txt(base,rel).splitlines(); after=txt(cand,rel).splitlines()
 for line in difflib.ndiff(before,after):
  if line.startswith('+ '): added.append(line[2:])
newsrc='\n'.join(added)
codeonly=re.sub(r'/\*.*?\*/',' ',newsrc,flags=re.S); codeonly=re.sub(r'//.*',' ',codeonly)
for bad in ['chandelier','laptop','screenClass','windowClass','sceneClass','objectClass']:
 req(bad.lower() not in codeonly.lower(),'scene-specific logic '+bad)
# Version/stage graph.
post=txt(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java')
req('IRIS_26655_PHOTON_HIGHLIGHT_ANALYSIS_KNEE_ONLY' in post,'analysis-only stage marker')
req('MotionV2Render[26655-source-domain-B-plus-R-final-spatial-tone]' in post,'graph owner marker')
ver=txt(cand,'app/version.properties'); req('VERSION_NAME=0.9726655' in ver and 'VERSION_BUILD=26655' in ver,'version')
# Shader brace structure.
for name,src in [('render',rg),('gainmap',gm),('remap',ll),('downsample',down)]:
 clean=re.sub(r'/\*.*?\*/',' ',src,flags=re.S); clean=re.sub(r'//.*',' ',clean)
 req(clean.count('{')==clean.count('}'),name+' brace mismatch')
# Scene-independent reference model for B. This verifies invariants, not sample-specific tuning.
K=[1.0,4.0,6.0,4.0,1.0]; N=4096
def down1(x,sigma=0.65):
 out=[]; n=len(x)
 for q in range((n+1)//2):
  ci=min(2*q,n-1); c=x[ci]; sm=ws=0.0
  for ko,off in zip(K,range(-2,3)):
   i=max(0,min(n-1,ci+off)); v=x[i]; rw=math.exp(-0.5*((v-c)/sigma)**2); w=ko*rw; sm+=v*w; ws+=w
  out.append(sm/ws)
 return out
def up1(coarse,source,sigma=0.75):
 n=len(source); m=len(coarse); out=[]
 for p in range(n):
  cp=(p+0.5)*m/n-0.5; c0=math.floor(cp); sm=ws=0.0
  for off in range(-1,3):
   q=max(0,min(m-1,c0+off)); d=cp-q; spatial=max(1.5-abs(d),0.0); v=coarse[q]; ev=(v-source[p])/sigma; w=spatial*math.exp(-0.5*ev*ev); sm+=v*w; ws+=w
  out.append(sm/ws if ws>1e-8 else source[p])
 return out
def bfield(vals):
 src=[math.log(max(v,2**-12),2) for v in vals]; c=src[:]
 while len(c)>32: c=down1(c)
 return [2**v for v in up1(c,src)]
flat=[0.8]*N; bf=bfield(flat); req(max(abs(a-b) for a,b in zip(flat,bf))<1e-9,'flat B identity')
m=N//2; step=[0.2]*m+[2.0]*(N-m); bs=bfield(step)
req(max(abs(v-0.2) for v in bs[m-100:m])<3e-4,'hard-step dark halo')
req(max(abs(v-2.0) for v in bs[m:m+100])<3e-3,'hard-step bright halo')
for sig in (60.0,120.0,240.0):
 vals=[0.25+1.5*math.exp(-0.5*((i-m)/sig)**2) for i in range(N)]; bb=bfield(vals)
 req(bb[m] < vals[m]-0.10,'smooth highlight center not redistributed')
 req(bb[m+200] > vals[m+200]+0.02,'smooth highlight shoulder not broadened')
fine=[0.8+0.10*math.sin(2*math.pi*i/8.0) for i in range(N)]; bb=bfield(fine)
mean=sum(bb)/N; bstd=(sum((v-mean)**2 for v in bb)/N)**0.5; sm=sum(fine)/N; sstd=(sum((v-sm)**2 for v in fine)/N)**0.5
req(bstd<sstd*0.10,'fine structure leaked into B')
print('PASS 26655 semantic/ownership + spatial model: 7-path/0-addition scope; successful 26654 fusion/matcher/color/DNG protected; source-domain bilateral B + source-proven R final owner; old direct highlight owners neutralized on HC-ON; exact SDR/UHDR final-tone texture; flat/edge/smooth/fine invariants PASS')
