#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,re
B,C=map(Path,sys.argv[1:3])
A={'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt','app/version.properties'}
def need(v,m):
    if not v: raise AssertionError(m)
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def U(r): return {p.relative_to(r).as_posix():h(p) for p in (r/'app').rglob('*') if p.is_file()}
def template(text,name):
    pats=[r'^\s*(?:private\s+)?val\s+'+re.escape(name)+r'(?:\s*:\s*String)?\s*=\s*"""',r'^\s*(?:private\s+)?val\s+'+re.escape(name)+r'\s*:\s*String\s+by\s+lazy\s*\{\s*\n\s*"""']
    m=next((re.search(p,text,re.M) for p in pats if re.search(p,text,re.M)),None); need(m is not None,name+' declaration missing')
    e=text.find('""".trimIndent()',m.end()); need(e>=0,name+' terminator missing')
    return text[m.start():e+len('""".trimIndent()')]
def smoothstep(a,b,x):
    t=max(0.0,min(1.0,(x-a)/(b-a))); return t*t*(3.0-2.0*t)
def authority(valid,highlight=1.0,highlight_invalid=0.0,phase_invalid=0.0):
    r,g,b=valid; mn=min(valid)
    full=smoothstep(0.90,0.985,mn)
    bright=max(highlight_invalid,highlight)*(1.0-full)
    rg=smoothstep(0.90,0.985,min(r,g)); bg=smoothstep(0.90,0.985,min(b,g))
    return min(1.0-bright,(1.0-phase_invalid)+phase_invalid*rg),min(1.0-bright,(1.0-phase_invalid)+phase_invalid*bg)
b,c=U(B),U(C); changed={p for p in set(b)|set(c) if b.get(p)!=c.get(p)}
need(changed==A,f'changed allowlist mismatch actual={sorted(changed)} expected={sorted(A)}')
need(len(b)==1786 and len(c)==1786,f'universe count mismatch {len(b)}->{len(c)}')
v=(C/'app/version.properties').read_text(); bv=(B/'app/version.properties').read_text()
need('VERSION_NAME=0.9726832' in v and 'VERSION_BUILD=26832' in v,'version mismatch')
need(bv.replace('VERSION_NAME=0.9726831','VERSION_NAME=0.9726832',1).replace('VERSION_BUILD=26831','VERSION_BUILD=26832',1)==v,'version changed outside exact advance')
for rel in set(b)|set(c):
    if rel not in A: need(b.get(rel)==c.get(rel),f'protected path changed {rel}')
post='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'
bt=(B/post).read_text(); ct=(C/post).read_text(); bs=template(bt,'bipolarColorTrust26769'); cs=template(ct,'bipolarColorTrust26769')
need(bt.replace(bs,cs,1)==ct,'postprocessor changed outside bipolarColorTrust26769 shader')
for token in ['IRIS_26832_CFA_CHROMA_AUTHORITY_QUARANTINE','cfaValidity26832=validity26769(p)','fullColorAuthority26832=smoothstep(0.90,0.985,minCfaValidity26832)','brightColorInvalid26832=max(inheritedHighlightInvalid26832,sourceHighlight26832)*(1.0-fullColorAuthority26832)','rgAxisAuthority26832=smoothstep(0.90,0.985,min(cfaValidity26832.r,cfaValidity26832.g))','bgAxisAuthority26832=smoothstep(0.90,0.985,min(cfaValidity26832.b,cfaValidity26832.g))','green26832=finalY26832-0.25*(dRg26832+dBg26832)','finalFloor*=min(clamp(rgKeep26832,0.0,1.0),clamp(bgKeep26832,0.0,1.0))']:
    need(token in cs,'26832 quarantine token lost '+token)
for token in ['IRIS_26829_COLORED_PARENT_GREEN_CYAN_RESIDUAL_OWNER','IRIS_26818_SELECTIVE_GREEN_RESIDUAL_DENOISE','IRIS_26825_THIN_BRIGHT_MAGNITUDE_AMPLIFICATION_GUARD']:
    need(token in ct,'inherited VGN/color owner lost '+token)
need('IRIS_26776_NO_PHASE_INVALID_CHROMA_RESURRECTION' in cs,'inherited final-shader phase veto lost')
# 26831 spatial suppressor and 26830 Sabre/high-zoom mechanics are byte protected.
sp='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'; sb='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'
need((B/sp).read_bytes()==(C/sp).read_bytes(),'26831 SpatialStacker owner changed')
need('IRIS_26831_DIRECTIONAL_PHASE_VALID_THIN_NEUTRAL' in (C/sp).read_text(),'26831 inherited owner lost')
need((B/sb).read_bytes()==(C/sb).read_bytes(),'26830 Sabre/high-zoom/color owner changed')
st=(C/sb).read_text()
for token in ['IRIS_26829_GREEN_SUPPORT_HEADROOM_CLIPPED_RB_OWNER','IRIS_26829_WEIGHTED_GREEN_CLIP_CALC_DOMAIN','blockPhaseCount==2?0.0:0.0','blockPhaseCount==3?0.85','if(blockPhaseCount<3)reasonClass=6;']:
    need(token in st,'inherited 26829/26830 token lost '+token)
# Permanent semantic fixtures: scene/CFA-phase independence for invalid bright highlights; valid color survives.
for vld in [(1.0,1.0,1.0),(0.999,0.999,0.999)]:
    rg,bg=authority(vld); need(rg>0.99 and bg>0.99,f'fully-valid foliage/color not preserved {vld} -> {rg,bg}')
for vld in [(0.25,1.0,1.0),(1.0,0.25,1.0),(1.0,1.0,0.25)]:
    rg,bg=authority(vld); need(rg<0.01 and bg<0.01,f'bright clipped CFA phase did not fail closed {vld} -> {rg,bg}')
rg,bg=authority((0.25,1.0,1.0),highlight=0.0,phase_invalid=1.0); need(rg<0.01 and bg>0.99,'non-highlight partial R invalidity must remove only R-G axis')
rg,bg=authority((1.0,1.0,0.25),highlight=0.0,phase_invalid=1.0); need(rg>0.99 and bg<0.01,'non-highlight partial B invalidity must remove only B-G axis')
# Algebraic constant-luma reconstruction regression.
for y,dr,db in [(0.8,0.2,-0.1),(0.4,-0.25,0.35),(0.9,0.0,0.0)]:
    g=y-0.25*(dr+db); r=g+dr; b2=g+db; need(abs((0.25*r+0.5*g+0.25*b2)-y)<1e-12,'luma preservation algebra failed')
print('PASS 26832 exact 2-path runtime allowlist; 1786-file successful-26831 authority universe preserved')
print('PASS 26832 final VGN CFA chroma-authority quarantine localized to bipolarColorTrust26769; no neighbor hue donation; luma algebra preserved')
print('PASS 26832 CFA-phase regression: any severely invalid channel in a bright highlight fails closed to neutral; valid foliage/color remains unchanged')
print('PASS 26832 successful 26831 spatial owner and successful 26829/26830 Sabre/color/high-zoom owners byte-protected')
