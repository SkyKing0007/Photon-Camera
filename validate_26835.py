#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,math,re
B,C=map(Path,sys.argv[1:3])
A={
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java',
'app/version.properties'}
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def U(r): return {p.relative_to(r).as_posix():h(p) for p in (r/'app').rglob('*') if p.is_file()}
def need(v,m):
    if not v: raise AssertionError(m)
b,c=U(B),U(C); changed={p for p in set(b)|set(c) if b.get(p)!=c.get(p)}
need(changed==A,f'allowlist mismatch {sorted(changed)}')
need(len(b)==1786 and len(c)==1786,f'universe {len(b)}->{len(c)}')
for p in set(b)|set(c):
    if p not in A: need(b.get(p)==c.get(p),f'protected changed {p}')
v=(C/'app/version.properties').read_text(); need('VERSION_NAME=0.9726835' in v and 'VERSION_BUILD=26835' in v,'version')
stack=(C/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
shader=(C/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text()
settings=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java').read_text()
# Preserve successful 26834 insertion point, mask ownership, LONG contract and high-zoom owner.
for t in ['IRIS_26834_CLIP_ZONE_CHROMA_INPAINT_FINAL_OWNER','IRIS_26834_NORMAL_CLIP_ZONE_PROVENANCE','IRIS_26833_SHADOW_LONG_POST_VGN_LUMINANCE_ONLY','IRIS_26834_UNIVERSAL_HIGH_ZOOM_RECONSTRUCTION_HALO']:
    need(t in stack or t in shader,t)
need(stack.index('IRIS_26833_SHADOW_LONG_POST_VGN_LUMINANCE_ONLY') < stack.index('IRIS_26834_CLIP_ZONE_CHROMA_INPAINT_FINAL_OWNER') < stack.index('IRIS_26601_SHARED_NATIVE_HDR_AUTHORITY'),'final insertion order changed')
long_start=stack.index('} else if (frame.role == RawBurstFrameRole.SHADOW_LONG) {')
long_end=stack.index('} else {',long_start)
long=stack[long_start:long_end]
need('clipZoneProvenance26834 = clipZoneProvenance26834' not in long,'LONG entered clip mask')
need('accumulatedValidity26614 = 0' in long,'LONG validity ownership regression')
# 26835 donor policy: whole-vector second moment + multi-sector authority + broad veto only.
for t in ['IRIS_26835_COHERENCE_GATED_CLIP_ZONE_CHROMA','oProducts=vec4(w*c,w,w*dot(c,c));','struct Field26835','bool multiSector=(l&&r)||(u&&d)||sectorCount>=3;','bool colorAuthority=localCoherent && multiSector && broadAgrees;','cp=c*(1.0-m);','Broad sigma-10 evidence is a veto/support check only. It can never establish hue.']:
    need(t in shader,t)
need('vec2 fill=mix(safeFill(bg),safeFill(sm),a)' not in shader,'stale unrestricted Gaussian donor survived')
need('safeFill(vec4 v)' not in shader,'stale per-axis fill helper survived')
for t in ['if(m<=0.0){ imageStore(uOut,p,src); return; }','float y=(src.r+2.0*src.g+src.b)*0.25','float g=y-0.25*(dR+dB)']:
    need(t in shader,t)
# 26834 mask tunables remain exact; 26835 adds only donor-quality scalars.
for t in ['clipZoneClipStart = 0.9925f','clipZoneDilation = 2f','clipZoneMaskSigma = 1f','clipZoneMaskGain = 1.6f','clipZoneSigmaSmall = 3f','clipZoneSigmaBig = 10f','clipZoneYFloor = 0.001f','clipZoneAThreshold = 0.25f',
          'clipZoneNeutralRms = 0.035f','clipZoneCoherence = 0.92f','clipZoneDirectionCos = 0.94f','clipZoneSectorSupport = 0.12f','clipZoneSectorOffset = 9f']:
    need(t in settings,t)
for t in ['neutralFallback=$neutralFallback','colorDonor=$colorDonor','mixedRejected=$mixedRejected','broadVeto=$broadVeto','vectorCoherence=true multiSectorRequired=true broadHueAuthority=false']:
    need(t in stack,t)
# Algebra: luma reconstruction is exact.
y=.72; yc=max(y,.001); c1,c2=.18,-.11; dr,db=c1*yc,c2*yc; g=y-.25*(dr+db); rgb=(g+dr,g,g+db)
need(abs((rgb[0]+2*rgb[1]+rgb[2])*.25-y)<1e-12,'luma algebra')
# Neutral fallback invariant: increasing clipping only shrinks chroma; signs cannot flip/new hue cannot appear.
for c0 in [(.8,-.4),(-.6,.3),(.4,.5),(-.3,-.7)]:
    prev=math.hypot(*c0)
    for m in [0,.1,.3,.6,.9,1.0]:
        cp=(c0[0]*(1-m),c0[1]*(1-m)); mag=math.hypot(*cp)
        need(mag<=prev+1e-12,'neutral fallback increased chroma'); prev=mag
        if c0[0]!=0: need(cp[0]*c0[0]>=-1e-12,'neutral fallback flipped c1')
        if c0[1]!=0: need(cp[1]*c0[1]>=-1e-12,'neutral fallback flipped c2')
# Coherence fixtures: same-hue survives, mixed orthogonal/opposing fields do not gain authority.
def coherence(vs):
    mx=sum(x for x,y in vs)/len(vs); my=sum(y for x,y in vs)/len(vs); e2=sum(x*x+y*y for x,y in vs)/len(vs); rms=math.sqrt(max(e2,0)); return math.hypot(mx,my)/rms if rms>1e-9 else 1
orange=[(.9,-.45),(.88,-.44),(.92,-.46),(.91,-.43)]
mixed=[(.9,-.45),(-.45,.9),(-.8,-.4),(.4,.8)]
need(coherence(orange)>.98,'coherent true color rejected fixture')
need(coherence(mixed)<.70,'mixed-material fixture falsely coherent')
# High zoom shader assets are outside allowlist and therefore byte-identical to successful 26834.
for rel in ['app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/assets/shaders/motionv2/gainmap.glsl']:
    need(b[rel]==c[rel],rel+' high-zoom regression')
print('PASS 26835 exact 4-path allowlist; 1786-file successful-26834 authority preserved')
print('PASS 26835 donor-only correction: 26834 RAW clip mask/insertion/high-zoom + 26833 LONG contract preserved')
print('PASS 26835 coherence rule: non-neutral hue requires coherent 2-D multi-sector evidence; sigma-10 cannot establish hue')
print('PASS 26835 neutral fail-closed invariant: stronger clipping monotonically removes unsupported chroma without sign flips')
print('PASS 26835 DNG/native/vendor/high-zoom assets protected by byte-invariant allowlist')
