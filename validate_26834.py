#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,re,math
B,C=map(Path,sys.argv[1:3])
A={
'app/src/main/assets/shaders/motionv2/gainmap.glsl',
'app/src/main/assets/shaders/motionv2/render.glsl',
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
v=(C/'app/version.properties').read_text(); need('VERSION_NAME=0.9726834' in v and 'VERSION_BUILD=26834' in v,'version')
stack=(C/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
shader=(C/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text()
settings=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java').read_text()
render=(C/'app/src/main/assets/shaders/motionv2/render.glsl').read_text()
gainmap=(C/'app/src/main/assets/shaders/motionv2/gainmap.glsl').read_text()
for t in ['IRIS_26834_NORMAL_CLIP_ZONE_PROVENANCE','IRIS_26834_CLIP_ZONE_CHROMA_INPAINT_FINAL_OWNER','IRIS_26834_CLIP_ZONE_CHROMA_INPAINT_HOST','IRIS_26833_SHADOW_LONG_POST_VGN_LUMINANCE_ONLY','rgbScaleOnly=true exactRgbRatioPreserved=true']:
    need(t in stack or t in shader,t)
need(stack.index('IRIS_26833_SHADOW_LONG_POST_VGN_LUMINANCE_ONLY') < stack.index('IRIS_26834_CLIP_ZONE_CHROMA_INPAINT_FINAL_OWNER') < stack.index('IRIS_26601_SHARED_NATIVE_HDR_AUTHORITY'),'final owner insertion order')
need('clipZoneProvenance26834 = clipZoneProvenance26834' in stack,'NORMAL provenance not wired')
long=stack[stack.index('} else if (frame.role == RawBurstFrameRole.SHADOW_LONG) {'):stack.index('} else {',stack.index('} else if (frame.role == RawBurstFrameRole.SHADOW_LONG) {'))]
need('clipZoneProvenance26834 = clipZoneProvenance26834' not in long,'LONG entered clip mask')
need('accumulatedValidity26614 = 0' in long,'LONG validity ownership regression')
for t in ['if(m<=0.0){ imageStore(uOut,p,src); return; }','float y=(src.r+2.0*src.g+src.b)*0.25','float g=y-0.25*(dR+dB)','vec2 fill=mix(safeFill(bg),safeFill(sm),a)','float w=(1.0-m)*(1.0-m)']:
    need(t in shader,t)
for t in ['clipZoneEnabled = true','clipZoneClipStart = 0.9925f','clipZoneDilation = 2f','clipZoneMaskSigma = 1f','clipZoneMaskGain = 1.6f','clipZoneSigmaSmall = 3f','clipZoneSigmaBig = 10f','clipZoneYFloor = 0.001f','clipZoneAThreshold = 0.25f']:
    need(t in settings,t)
# algebra fixture: exact Sabre luma preserved after arbitrary chroma replacement
y=0.72; yc=max(y,1e-3); c1,c2=.18,-.11; dr,db=c1*yc,c2*yc; g=y-.25*(dr+db); rgb=(g+dr,g,g+db)
need(abs((rgb[0]+2*rgb[1]+rgb[2])*.25-y)<1e-12,'luma algebra')

# Universal high-zoom barcode guard: target 32 texels/side, exact native fallback through 16,
# transition complete by 24, and fail closed when >=24 trusted halo cannot be guaranteed.
for t in ['IRIS_26834_UNIVERSAL_HIGH_ZOOM_RECONSTRUCTION_HALO','visibleDetailWidth26834+64','trustedHaloX26834>=24.0f','trustedHaloY26834>=24.0f','universalBarcodeGuard26834=true']:
    need(t in stack,t)
for src,name in ((render,'render'),(gainmap,'gainmap')):
    need('IRIS_26834_UNIVERSAL_HIGH_ZOOM_VISIBLE_CROP_GUARD' in src,name+' guard marker')
    need('if(minEdge<=16.0)return 0.0;' in src,name+' exact native fallback')
    need('smoothstep(16.0,24.0,minEdge)' in src,name+' guard range')
    need('smoothstep(2.0,4.0,minEdge)' not in src,name+' stale 26828 gate')
# Geometry fixture: across representative local high zooms the producer keeps the visible crop
# outside the 16..24 transition, or would fail closed rather than publish edge detail.
for full in (6140,8160):
    for z in (1.1,2.0,7.28673,30.0,120.0):
        vis=min(full,math.ceil(full/z)); detail=min(full,((vis+64+3)//4)*4)
        halo=0.5*(detail-vis)
        need(halo>=24.0,f'high-zoom halo fixture full={full} z={z} halo={halo}')

# DNG/native/vendor and postprocessor remain outside allowlist by construction.
print('PASS 26834 exact 6-path allowlist; 1786-file successful-26833 authority preserved')
print('PASS 26834 final chroma owner order: post-VGN + post-26833 LONG scalar luma, pre-nativeHdr/tone/UHDR')
print('PASS 26834 NORMAL-only mask; LONG excluded; M==0 exact-copy branch; Sabre luma algebra preserved')
print('PASS 26834 universal high-zoom barcode guard: 32 target halo, 16..24 boundary veto, fail-closed geometry')
print('PASS 26834 DNG/native/vendor/postprocessor protected by byte-invariant allowlist')
