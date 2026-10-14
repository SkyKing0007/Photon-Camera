#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,re
B,C=map(Path,sys.argv[1:3])
A={
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/version.properties'}
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def U(r): return {p.relative_to(r).as_posix():h(p) for p in (r/'app').rglob('*') if p.is_file()}
def need(v,m):
    if not v: raise AssertionError(m)
def template(text,name):
    pats=[
      r'^\s*(?:private\s+)?val\s+'+re.escape(name)+r'(?:\s*:\s*String)?\s*=\s*"""',
      r'^\s*(?:private\s+)?val\s+'+re.escape(name)+r'\s*:\s*String\s+by\s+lazy\s*\{\s*\n\s*"""']
    m=None
    for pat in pats:
        m=re.search(pat,text,re.M)
        if m: break
    need(m is not None,name+' declaration missing')
    e=text.find('""".trimIndent()',m.end()); need(e>=0,name+' terminator missing')
    return text[m.start():e+len('""".trimIndent()')]
b,c=U(B),U(C); changed={p for p in set(b)|set(c) if b.get(p)!=c.get(p)}
need(changed==A,f'changed allowlist mismatch actual={sorted(changed)} expected={sorted(A)}')
need(len(b)==1786 and len(c)==1786,f'universe count mismatch {len(b)}->{len(c)}')
v=(C/'app/version.properties').read_text(); need('VERSION_NAME=0.9726830' in v and 'VERSION_BUILD=26830' in v,'version mismatch')
bv=(B/'app/version.properties').read_text(); ev=bv.replace('VERSION_NAME=0.9726829','VERSION_NAME=0.9726830',1).replace('VERSION_BUILD=26829','VERSION_BUILD=26830',1); need(ev==v,'version.properties changed outside exact version/build advance')
for rel in sorted(set(b)|set(c)):
    if rel not in A: need(b.get(rel)==c.get(rel),f'protected path changed {rel}')
rel='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'
bt=(B/rel).read_text(); ct=(C/rel).read_text(); bh=template(bt,'highZoomDetailResolve26718'); ch=template(ct,'highZoomDetailResolve26718')
need(bt.replace(bh,ch,1)==ct,'Sabre carrier changed outside highZoomDetailResolve26718')
old='float phaseGate=blockPhaseCount>=4?1.0:(blockPhaseCount==3?0.85:(blockPhaseCount==2?0.50:0.0));'
new='float phaseGate=blockPhaseCount>=4?1.0:(blockPhaseCount==3?0.85:(blockPhaseCount==2?0.0:0.0));'
need(old in bh,'26829 two-phase 0.50 authority anchor missing')
need(new in ch,'26830 exact two-phase zero confidence gate missing')
need(old not in ch,'old two-phase 0.50 confidence survived')
need('if(blockPhaseCount<2)reasonClass=6;' in bh,'26829 phase diagnostic anchor missing')
need('if(blockPhaseCount<3)reasonClass=6;' in ch,'26830 two-phase rejection diagnostic missing')
need('if(blockPhaseCount<2)reasonClass=6;' not in ch,'old <2 phase diagnostic survived')
expected_h=bh.replace(old,new,1).replace('if(blockPhaseCount<2)reasonClass=6;','if(blockPhaseCount<3)reasonClass=6;',1)
need(expected_h==ch,'highZoomDetailResolve26718 changed outside exact 2-phase confidence + diagnostic substitutions')
need('blockPhaseCount>=4?1.0' in ch and 'blockPhaseCount==3?0.85' in ch,'3/4-phase confidence changed')
need('IRIS_26718_HIGH_ZOOM_DETAIL_RESOLVE' in ct,'inherited high-zoom owner marker lost IRIS_26718_HIGH_ZOOM_DETAIL_RESOLVE')
for token in ['IRIS_26758_ADAPTIVE_FUSION_REJECTION','IRIS_26759_CONFIDENCE_GATED_ZOOM_DETAIL_REINFORCEMENT']:
    need(token in ch,'inherited high-zoom owner lost '+token)
# 26829 shared chroma/highlight owners must remain byte-identical in inherited shaders.
merge=template(ct,'merge')
for token in ['IRIS_26829_GREEN_SUPPORT_HEADROOM_CLIPPED_RB_OWNER','IRIS_26829_WEIGHTED_GREEN_CLIP_CALC_DOMAIN']:
    need(token in merge,'26829 clipped-R/B owner lost '+token)
post='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'
ptext=(C/post).read_text()
for token in ['IRIS_26829_COLORED_PARENT_GREEN_CYAN_RESIDUAL_OWNER','IRIS_26818_SELECTIVE_GREEN_RESIDUAL_DENOISE','IRIS_26825_THIN_BRIGHT_MAGNITUDE_AMPLIFICATION_GUARD']:
    need(token in ptext,'26829 shared VGN owner lost '+token)
print('PASS 26830 exact 2-path runtime allowlist; 1786-file authority-seeded universe preserved')
print('PASS 26830 highZoomDetailResolve26718 only: 2-phase confidence exact 0.0; 3-phase 0.85; 4-phase 1.0; diagnostics reject <3')
print('PASS 26830 successful 26829 clipped-R/B and shared VGN chroma owners preserved')
print('PASS 26830 all non-allowlisted successful-26829 runtime bytes protected')
