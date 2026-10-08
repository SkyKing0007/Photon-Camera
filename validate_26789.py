#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys,textwrap
if len(sys.argv)!=3: raise SystemExit('usage: validate_26789.py BASE CANDIDATE')
BASE,CAND=map(Path,sys.argv[1:])
ALLOW=[
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/version.properties']
S=ALLOW[0]; T=ALLOW[1]
def U(root): return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'app').rglob('*') if p.is_file()}
def need(c,m):
 if not c: raise AssertionError(m)
def shader(root,rel,name):
 text=(root/rel).read_text(); m=re.search(r'^\s*(?:private\s+)?val\s+'+re.escape(name)+r'\s*=\s*"""',text,re.M)
 need(m is not None,f'{name}: declaration missing'); b=text.find('""".trimIndent()',m.end()); need(b>=0,f'{name}: terminator missing')
 return textwrap.dedent(text[m.end():b]).strip('\n')+'\n'
def funblock(text,signature):
 a=text.find(signature); need(a>=0,f'missing {signature}'); brace=text.find('{',a); need(brace>=0,'function brace missing')
 d=0
 for i in range(brace,len(text)):
  if text[i]=='{': d+=1
  elif text[i]=='}':
   d-=1
   if d==0:return text[a:i+1]
 raise AssertionError('function close missing')
b,c=U(BASE),U(CAND); need(len(b)==len(c)==1779,'file count'); need(set(b)==set(c),'file universe changed')
changed=sorted(k for k in b if b[k]!=c[k]); need(changed==ALLOW,f'changed allowlist mismatch {changed}')
print('PASS 26789 authority-seeded scope: 1779 files; exactly 3 modified / 0 added / 0 deleted')
ver=(CAND/'app/version.properties').read_text(); need('VERSION_NAME=0.9726789' in ver and 'VERSION_BUILD=26789' in ver,'version')
print('PASS 26789 version 0.9726789 / 26789')
# Protected critical shaders are byte-identical.
for rel,name in [
 (S,'normalDngMerge'),(S,'jpegNeutralHighlightClamp26787'),(S,'universalNormalMasterShortFusion26651'),
 (T,'EDGE_FALSE_COLOR_SUPPRESSOR_26778')]:
 need(shader(BASE,rel,name)==shader(CAND,rel,name),f'protected runtime shader changed: {name}')
 print(f'PASS 26789 protected runtime shader byte-identical: {name}')
cs=(CAND/S).read_text(); ct=(CAND/T).read_text(); merge=shader(CAND,S,'merge')
# NORMAL/LONG LCA is inside the RBF owner, with same-coordinate signal and headroom.
for tok in [
 'IRIS_26789_IN_RBF_DNG_GEOMETRY_LCA_OWNER','IRIS_26789_DNG_GEOMETRY_PER_CHANNEL_RBF',
 'dngGeometrySample26789','correctedQuadCenter','correctedTargetCenter','sharedTranslationPixels',
 'mat3 validityBayerValue26789 = bayerValue;','uJpegLcaEnabled26789','uJpegLcaKrKb26789']:
 need(tok in merge,f'merge missing {tok}')
need('uExtractedBayerValidity' not in merge,'stale split NORMAL/LONG validity sampler survived')
need('get3x3FromExtractedBayerValidity' not in merge,'stale split validity fetch survived')
need('if (channel == 0) return uJpegLcaKrKb26789.x;' in merge,'R LCA owner missing')
need('if (channel == 2) return uJpegLcaKrKb26789.y;' in merge,'B LCA owner missing')
need('return 0.0;' in merge,'G zero-LCA path missing')
print('PASS 26789 NORMAL/LONG LCA owner: integrated DNG radial geometry inside channel RBF; signal/headroom same CFA footprint')
# LONG guard is chroma-only, NORMAL anchored, temporal weights untouched.
for tok in ['IRIS_26789_LONG_CHROMA_NO_REINTRODUCTION','referenceNormalAnchor26789','uLongChromaGuard26789',
            'normalAtLongLuma26789','guardedLongMean26789','accumulatedColor = guardedLongMean26789 * accumulatedWeight;']:
 need(tok in merge,f'LONG guard missing {tok}')
need('accumulatedWeight =' not in merge[merge.find('IRIS_26789_LONG_CHROMA_NO_REINTRODUCTION'):merge.find('float frameWeight')],
     'LONG guard changes accumulated weights')
print('PASS 26789 LONG guard: NORMAL-reference chroma anchor; LONG luma preserved; temporal weights unchanged')
# Host route: reference NORMAL and ordinary NORMAL use same owner; guard only SHADOW_LONG.
rf=funblock(ct,'    private fun renderSabreMerge(')
need('renderSabreJpegPhaseSafeCfaLca26788(' not in rf,'26788 NORMAL/LONG prewarp still called inside merge host')
need('bindTexture(program, "uExtractedBayer", 0, extracted)' in rf,'merge signal not direct extracted CFA')
need('bindTexture(program, "uReferenceExtractedBayer26789", 4, referenceExtracted26789)' in rf,'NORMAL anchor binding missing')
need('uniform1i(program, "uJpegLcaEnabled26789"' in rf,'integrated LCA host uniform missing')
need('uniform1i(program, "uLongChromaGuard26789"' in rf,'LONG guard host uniform missing')
need('longChromaGuard26789 = frame.role == RawBurstFrameRole.SHADOW_LONG' in ct,'LONG-only route missing')
need(ct.count('jpegIntegratedLca26789 = dngOptions26786.lcaEnabled')==2,'reference/alternate NORMAL-LONG integrated LCA route count')
need('IRIS_26789_JPEG_CFA_OPTIONS' in ct and 'normalLongPrewarpRetired=true' in ct and 'sameCoordinateValidity=true' in ct,'owner telemetry missing')
print('PASS 26789 host ownership: NORMAL+LONG integrated LCA; LONG guard only SHADOW_LONG; NORMAL/LONG 26788 prewarp retired')
# SHORT remains inherited and separately scoped; office sample had no SHORT.
shortfun=funblock(ct,'    private fun renderSabreNormalMasterShortFusion26651(')
need('renderSabreJpegPhaseSafeCfaLca26788(' in shortfun,'inherited SHORT phase-safe prewarp unexpectedly removed')
need('uShortExtractedBayerValidity' in shader(CAND,S,'universalNormalMasterShortFusion26651'),'SHORT validity owner changed')
print('PASS 26789 SHORT path inherited unchanged: separate 26788 phase-safe CFA correction retained only for HIGHLIGHT_SHORT')
# Neutral clamp audit: preserve proven equivalent math exactly, do not invent a second owner.
neutral=shader(CAND,S,'jpegNeutralHighlightClamp26787')
need('source.r = min(source.r, 1.0);' in neutral and 'source.b = min(source.b, 1.0);' in neutral,'neutral cap changed')
need('measuredGreenValidity <= uZeroValidityThreshold26787' in neutral,'neutral validity gate changed')
need('neutralMath=DNG_AS_SHOT_NEUTRAL_WB_EQUIVALENT' in ct,'neutral-equivalence telemetry missing')
print('PASS 26789 neutral clamp preserved: audited calculation-WB equivalent of DNG AsShotNeutral censor cap')
# No downstream architectural expansion.
need('IRIS_26788_MATERIAL_BASELINE_PERIODIC_FALSE_COLOR' in shader(CAND,T,'EDGE_FALSE_COLOR_SUPPRESSOR_26778'),'26788 residual guard missing')
print('PASS 26789 downstream freeze: DNG/neutral/residual guard runtime shaders byte-identical; VGN/color/tone/UHDR/native/vendor protected by manifests')
