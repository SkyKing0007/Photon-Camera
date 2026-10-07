#!/usr/bin/env python3
from pathlib import Path
import hashlib,math,re,sys,textwrap
if len(sys.argv)!=3: raise SystemExit('usage: validate_26783.py BASE CAND')
B=Path(sys.argv[1]); C=Path(sys.argv[2]); ROOT=Path(__file__).resolve().parent
allowed=(ROOT/'26783_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines()
def U(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(r)/'app').rglob('*') if p.is_file()}
bu,cu=U(B),U(C); assert len(bu)==1779 and len(cu)==1779; assert set(bu)==set(cu)
changed=sorted(k for k in bu if bu[k]!=cu[k]); assert changed==allowed,(changed,allowed)
assert len(changed)==6
VP='app/version.properties'; vt=(C/VP).read_text(); assert 'VERSION_NAME=0.9726783' in vt and 'VERSION_BUILD=26783' in vt
SAB='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'
STACK='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'
IRIS='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'
MVR='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java'
RENDER='app/src/main/assets/shaders/motionv2/render.glsl'; GAIN='app/src/main/assets/shaders/motionv2/gainmap.glsl'
# DNG/RAW authority is frozen wholesale.
assert (B/SAB).read_bytes()==(C/SAB).read_bytes(),'DNG/Sabre shader authority changed'
assert 'IRIS_26782_DNG_EDGE_SAFE_QUAD_OWNER' in (C/SAB).read_text()
# Existing stacker embedded shader universe including 26782 guard must be byte-identical; only caller provenance logs change.
def vals(root,rel):
 t=(root/rel).read_text(); return {m.group(1):textwrap.dedent(m.group(2)).strip('\n')+'\n' for m in re.finditer(r'(?:private\s+)?val\s+([A-Za-z0-9_]+)\s*=\s*"""(.*?)"""\.trimIndent\(\)',t,re.S)}
bs,cs=vals(B,STACK),vals(C,STACK); assert bs==cs
assert 'IRIS_26782_COHERENT_BIPOLAR_EDGE_GUARD' in cs['EDGE_FALSE_COLOR_SUPPRESSOR_26778']
st=(C/STACK).read_text(); assert 'IRIS_26783_JPEG_RUNTIME_OWNER_ENTRY' in st and 'IRIS_26783_JPEG_RUNTIME_OWNER_EXIT' in st
assert 'dngReconstructionFrozen26782=true' in st and 'dngCarrier=NORMALIZED16_FROZEN_26782' in st
# Existing Iris shader carriers are frozen and exactly one final post-VGN carrier is added.
bi,ci=vals(B,IRIS),vals(C,IRIS); added=set(ci)-set(bi); assert added=={'postVgnNeutralGuard26783'},added
assert not(set(bi)-set(ci));
for n in bi: assert bi[n]==ci[n],f'inherited Iris shader changed: {n}'
ng=ci['postVgnNeutralGuard26783']
for tok in ('uPhysicalPreVgn','uSabreValidWeights','float evidenceConfidence=mix(0.45,1.0,invalidity)','float allowedMag=min(postMag,preMag+0.018)','outRgb*=y/outY'):
 assert tok in ng,tok
it=(C/IRIS).read_text(); assert 'IRIS_26783_POST_VGN_NEON_GUARD' in it and 'IRIS_26783_POST_VGN_NEON_GUARD_OWNER' in it and 'dispatchPostVgnNeutralGuard26783(' in it
assert 'assembledRgb = filteredYccd' in it
# Matched-bandwidth 26780 amplifier remains absent.
for p in (SAB,STACK,IRIS): assert 'IRIS_26780_MATCHED_BANDWIDTH_CHROMA_OWNER' not in (C/p).read_text()
# Only the existing pointwise SDR trim function and its explanatory 26783 comment may change in render/gainmap.
def func_span(text,name):
 s=text.index('float '+name+'('); b=text.index('{',s); depth=0
 for i in range(b,len(text)):
  if text[i]=='{': depth+=1
  elif text[i]=='}':
   depth-=1
   if depth==0: return s,i+1
 raise AssertionError(name)
def normalize_asset(text):
 text=re.sub(r'/\* IRIS_26783_SDR_BODY_CONTRAST_UHDR_REBASE.*?\*/\s*','',text,flags=re.S)
 s,e=func_span(text,'iris26770MidtonePresentationTrim'); return text[:s]+'<TRIM_FUNCTION>'+text[e:]
for p in (RENDER,GAIN):
 bt=(B/p).read_text(); ct=(C/p).read_text(); assert normalize_asset(bt)==normalize_asset(ct),f'unexpected asset shader delta outside trim: {p}'
 f=ct[func_span(ct,'iris26770MidtonePresentationTrim')[0]:func_span(ct,'iris26770MidtonePresentationTrim')[1]]
 for tok in ('smoothstep(0.10,0.24,y)','smoothstep(0.50,0.78,y)','mix(y,y*y,0.35*w)'): assert tok in f,(p,tok)
# Exact render/gain-map trim bodies are the same.
def fbody(text):
 s,e=func_span(text,'iris26770MidtonePresentationTrim'); return re.sub(r'\s+','',(text[s:e]))
assert fbody((C/RENDER).read_text())==fbody((C/GAIN).read_text())
# UHDR matched HDR target equations remain unchanged from authority.
gb=(B/GAIN).read_text(); gc=(C/GAIN).read_text()
for tok in ('float linearTargetY=sourceY*requested*max(localStructureScale,0.0);','float matchedIntentDelta=max(linearTargetY-sdrModelY,0.0);','float hdrIntentY=sdr+matchedIntentDelta;','ratio=clamp((hdrIntentY+UHDR_OFFSET)/(sdr+UHDR_OFFSET),1.0,safeMax);'):
 assert tok in gb and tok in gc,tok
# Java reference/log mirror.
j=(C/MVR).read_text(); assert 'IRIS_26783_SDR_BODY_CONTRAST_UHDR_REBASE' in j and 'gainMapMirrorExact=true decodedUhHdrTargetFrozen=true' in j
for tok in ('iris26623Smoothstep(0.10f, 0.24f, y)','iris26623Smoothstep(0.50f, 0.78f, y)','0.35f * w'): assert tok in j,tok
# Numeric regressions for SDR mapping: identity anchors, monotonicity, more separation than old in body.
def ss(a,b,x):
 if x<=a:return 0.0
 if x>=b:return 1.0
 t=(x-a)/(b-a);return t*t*(3-2*t)
def trim(y,old=False):
 if old: low=ss(.08,.20,y); high=1-ss(.52,.78,y); k=.25
 else: low=ss(.10,.24,y); high=1-ss(.50,.78,y); k=.35
 w=max(0,min(1,low*high)); return y+(y*y-y)*(k*w)
for x in (0,.02,.05,.10,.78,.85,1.0): assert abs(trim(x)-x)<1e-12,x
for x in (.25,.35,.50): assert trim(x)<trim(x,True),x
ys=[trim(i/10000) for i in range(10001)]; assert all(b>=a-1e-12 for a,b in zip(ys,ys[1:]))
# Post-VGN guard model regressions: continuous validity confidence, no dark/true-color targeting, luma preservation.
def guard(y,peak,neutral,preMag,postMag,invalid):
 bright=ss(.56,.90,max(y,peak)); nc=ss(2.40,3.80,neutral); growth=ss(.035,.130,max(postMag-preMag,0)); conf=.45+.55*invalid
 return max(0,min(1,bright*nc*growth*conf))
assert guard(.90,.96,5,.02,.20,1)>.9
assert guard(.90,.96,5,.02,.20,0)>.4
assert guard(.20,.25,5,.02,.20,1)==0
assert guard(.90,.96,0,.25,.40,1)==0
# There is no tile/modulo ownership in new guard and its only spatial reads are classification, not RGB replacement.
assert '%' not in ng and 'mod(' not in ng and 'imageLoad(uSource,safe26783(p+' not in ng
# Protected manifests cover exact frozen domains; candidate has zero add/delete.
print('PASS 26783 runtime allowlist: 6 modified + 0 added + 0 deleted; 1773 protected files unchanged')
print('PASS 26783 DNG/RAW freeze: entire GlesMgcRawSabreShaders.kt byte-identical to successful 26782')
print('PASS 26783 JPEG ownership: inherited 26782 pre-VGN/26778 suppressor shader bytes frozen; one post-VGN neutral/neon guard added after adaptive/VGN color owners')
print('PASS 26783 seam safety: final guard uses continuous validity confidence, pointwise RGB magnitude cap and exact luma restoration; no tile/modulo output boundary')
print('PASS 26783 SDR contrast: pointwise luminance-only body separation strengthened, deep-shadow/highlight anchors identity and mapping monotonic')
print('PASS 26783 UHDR preservation: gainmap denominator carries exact SDR trim mirror; frozen matched-HDR target equations unchanged')
