#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,re,difflib
B,C=map(Path,sys.argv[1:3])
A={
'app/src/main/assets/shaders/motionv2/gainmap.glsl',
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2ProtectedChromaNative.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/version.properties'}
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def U(r): return {p.relative_to(r).as_posix():h(p) for p in (r/'app').rglob('*') if p.is_file()}
def need(v,m):
    if not v: raise AssertionError(m)
def template(text,name):
    m=re.search(r'^\s*(?:private\s+)?val\s+'+re.escape(name)+r'\s*=\s*"""',text,re.M); need(m is not None,name+' declaration missing')
    e=text.find('""".trimIndent()',m.end()); need(e>=0,name+' terminator missing')
    return text[m.start():e+len('""".trimIndent()')]
def between(text,start,end):
    i=text.index(start); j=text.index(end,i); return text[i:j]
b,c=U(B),U(C); changed={p for p in set(b)|set(c) if b.get(p)!=c.get(p)}
need(changed==A,f'changed allowlist mismatch actual={sorted(changed)} expected={sorted(A)}')
need(len(b)==1785 and len(c)==1786,f'universe count mismatch {len(b)}->{len(c)}')
helper='app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2ProtectedChromaNative.java'
need(helper not in b and helper in c,'native helper addition mismatch')
v=(C/'app/version.properties').read_text(); need('VERSION_NAME=0.9726828' in v and 'VERSION_BUILD=26828' in v,'version mismatch')

# Asset universe: only render/gainmap are allowed to differ, and only their direct-CFA detail sample function may change.
assetroot=B/'app/src/main/assets/shaders'
asset_changed=[]
for p in assetroot.rglob('*'):
    if p.is_file():
        rel=p.relative_to(B).as_posix()
        if h(p)!=h(C/rel): asset_changed.append(rel)
need(set(asset_changed)=={'app/src/main/assets/shaders/motionv2/gainmap.glsl','app/src/main/assets/shaders/motionv2/render.glsl'},f'asset delta {asset_changed}')
for rel in asset_changed:
    bt=(B/rel).read_text(); ct=(C/rel).read_text()
    start='float iris26718HighZoomLogDetail(vec2 sourcePixel){'
    end='\n}\n'
    bi=bt.index(start); bj=bt.index(end,bi)+len(end); ci=ct.index(start); cj=ct.index(end,ci)+len(end)
    need(bt[:bi]==ct[:ci] and bt[bj:]==ct[cj:],rel+' changed outside high-zoom detail sampler')
    body=ct[ci:cj]
    for token in ['IRIS_26828_HIGH_ZOOM_TRUSTED_INTERIOR_GATE','vec2 edgeDistance=min(local,vec2(sz)-vec2(1.0)-local);','float trustedInterior=smoothstep(2.0,4.0,minEdge);','*trustedInterior;']:
        need(token in body,rel+' missing '+token)
    need('GL_CLAMP_TO_EDGE' not in body,rel+' sampler function unexpectedly owns texture setup')

# High-zoom producer allocation changes only the two sidecar dimension lines plus its explanatory owner comment.
rel='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'
bt=(B/rel).read_text(); ct=(C/rel).read_text()
old='''        val detailWidth=roundUp4((kotlin.math.ceil(fullWidth/highZoomSourceZoom.toDouble()).toInt()+4).coerceAtMost(fullWidth)).coerceAtLeast(4).coerceAtMost(fullWidth)\n        val detailHeight=roundUp4((kotlin.math.ceil(fullHeight/highZoomSourceZoom.toDouble()).toInt()+4).coerceAtMost(fullHeight)).coerceAtLeast(4).coerceAtMost(fullHeight)'''
new='''        /* IRIS_26828_HIGH_ZOOM_TRUSTED_INTERIOR_HALO\n         * 26718/26752 used only +4 true-2x samples total. At extreme local zoom that put the\n         * visible crop within ~1-3 sidecar texels of the reconstruction boundary, so one 2x2\n         * residual cell could expand to tens of final pixels. Add six more texels per side; the\n         * render/gain-map owners independently taper any remaining untrusted edge detail to exact\n         * zero, exposing the native Sabre/VGN base. */\n        val detailWidth=roundUp4((kotlin.math.ceil(fullWidth/highZoomSourceZoom.toDouble()).toInt()+16).coerceAtMost(fullWidth)).coerceAtLeast(4).coerceAtMost(fullWidth)\n        val detailHeight=roundUp4((kotlin.math.ceil(fullHeight/highZoomSourceZoom.toDouble()).toInt()+16).coerceAtMost(fullHeight)).coerceAtLeast(4).coerceAtMost(fullHeight)'''
need(bt.count(old)==1,'26827 high-zoom dimension anchor mismatch')
need(ct==bt.replace(old,new,1),'stacker changed outside audited high-zoom halo')

# Sabre carrier: only NORMAL merge's sameLocationChroma26793 block changes; SHORT remains byte-identical.
rel='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'; bt=(B/rel).read_text(); ct=(C/rel).read_text()
bmerge=template(bt,'merge'); cmerge=template(ct,'merge')
need(bt.replace(bmerge,cmerge,1)==ct,'Sabre carrier changed outside merge template')
short='universalNormalMasterShortFusion26651'; need(template(bt,short)==template(ct,short),'SHORT/Night fusion template changed')
bs='        /* IRIS_26827_NORMAL_CLIPPED_RB_SIGNED_CHROMA_OWNER'; cs='        /* IRIS_26828_NORMAL_CLIPPED_RB_CONSENSUS_OWNER'; end='        void sampleNeighborhoodRbf('
bi=bmerge.index(bs); ci=cmerge.index(cs); be=bmerge.index(end,bi); ce=cmerge.index(end,ci)
need(bmerge[:bi]==cmerge[:ci] and bmerge[be:]==cmerge[ce:],'merge changed outside NORMAL same-location chroma owner')
owner=cmerge[ci:ce]
for token in ['float cleanWeight = evidenceWeight * siteValid;','float clippedWeight = evidenceWeight * (1.0 - siteValid);','redClippedConsensus','blueClippedConsensus','redCleanFraction >= 0.20','blueCleanFraction >= 0.20','clippedEnvelope','sameSign','greenConfidence']:
    need(token in owner,'NORMAL consensus missing '+token)
need('IRIS_26827_NORMAL_CLIPPED_RB_SIGNED_CHROMA_OWNER' not in owner,'26827 full-trust owner survived')

# Bridge: exact 26827 capture/apply math remains as fallback; JNI is primary. Everything else is unchanged.
rel='app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt'; bt=(B/rel).read_text(); ct=(C/rel).read_text()
base_capture=between(bt,'    private fun captureIris26728ProtectedChromaFloor(', '    /* IRIS_26795_SCENE_RELATIVE_BRIGHT_EDGE_CHROMA_VALIDITY')
cand_fallback=between(ct,'    private fun captureIris26728ProtectedChromaFloor26827Fallback(', '    /* IRIS_26795_SCENE_RELATIVE_BRIGHT_EDGE_CHROMA_VALIDITY')
need(cand_fallback.replace('captureIris26728ProtectedChromaFloor26827Fallback','captureIris26728ProtectedChromaFloor',1)==base_capture,'capture fallback math differs from exact 26827')
base_apply=between(bt,'    private fun applyIris26728ProtectedChromaFloor(', '    private fun forceOpaqueHalfAlpha(')
cand_apply=between(ct,'    private fun applyIris26728ProtectedChromaFloor26827Fallback(', '    private fun forceOpaqueHalfAlpha(')
need(cand_apply.replace('applyIris26728ProtectedChromaFloor26827Fallback','applyIris26728ProtectedChromaFloor',1)==base_apply,'apply fallback math differs from exact 26827')
# Strip the two replaced owner regions and prove the rest of the bridge is byte-identical.
bprefix=bt[:bt.index('    private fun captureIris26728ProtectedChromaFloor(')]
bmid=bt[bt.index('    /* IRIS_26795_SCENE_RELATIVE_BRIGHT_EDGE_CHROMA_VALIDITY'):bt.index('    private fun applyIris26728ProtectedChromaFloor(')]
bsuffix=bt[bt.index('    private fun forceOpaqueHalfAlpha('):]
cprefix=ct[:ct.index('    /* IRIS_26828_NATIVE_PROTECTED_CHROMA_PRIMARY',ct.index('private data class Iris26728ProtectedChromaFloor'))]
cmid=ct[ct.index('    /* IRIS_26795_SCENE_RELATIVE_BRIGHT_EDGE_CHROMA_VALIDITY'):ct.index('    /* IRIS_26828_NATIVE_PROTECTED_CHROMA_PRIMARY',ct.index('IRIS_26795_SCENE_RELATIVE_BRIGHT_EDGE_CHROMA_VALIDITY'))]
csuffix=ct[ct.index('    private fun forceOpaqueHalfAlpha('):]
need(bprefix==cprefix and bmid==cmid and bsuffix==csuffix,'bridge changed outside native wrapper/fallback owner regions')
for token in ['MotionV2ProtectedChromaNative.capture','MotionV2ProtectedChromaNative.apply','IRIS_26828_NATIVE_PROTECTED_CHROMA_CAPTURE','IRIS_26828_NATIVE_PROTECTED_CHROMA_APPLY','fallback=false','native failure can']:
    need(token in ct,'bridge native owner missing '+token)

# Native C++ owner is append-only relative to successful 26827; inherited TurboJPEG/shared carrier bytes cannot change.
rel='app/src/main/cpp/motionv2_jpeg444_jni.cpp'; bb=(B/rel).read_bytes(); cb=(C/rel).read_bytes(); need(cb.startswith(bb),'inherited native C++ prefix changed')
appended=cb[len(bb):].decode()
for token in ['IRIS_26828_NATIVE_PROTECTED_CHROMA_CLASSIFIER','MotionV2ProtectedChromaNative_countCaptureNative','MotionV2ProtectedChromaNative_fillCaptureNative','MotionV2ProtectedChromaNative_applyNative','GetDoubleArrayElements','round-to-nearest, ties-to-even','remainder==0x1000u&&(halfMant&1u)','return JNI_TRUE;']:
    need(token in appended,'native classifier missing '+token)
apply_native=appended[appended.index('MotionV2ProtectedChromaNative_applyNative'):]; need('NewDoubleArray' not in apply_native and 'SetDoubleArrayRegion' not in apply_native,'post-mutation JNI result allocation/write survived')
# Result carrier and all sparse indices are acquired/validated before mutation loop.
pos_metrics=appended.index('GetDoubleArrayElements'); pos_validate=appended.index('for(jsize i=0;i<n;i++)if(indices[i]<0'); pos_mutate=appended.index('for(jsize entry=0;entry<n;entry++){')
need(pos_metrics<pos_validate<pos_mutate,'native pre-write validation order changed')
jni=(C/rel).read_text(); need(jni.index('#include <GLES3/gl31.h>')<jni.index('#include <GLES2/gl2ext.h>'),'IRIS_26826_REGRESSION_NDK27_GLES_CORE_BEFORE_EXT')

helper_text=(C/helper).read_text()
for token in ['System.loadLibrary("motionv2jpeg")','final double[] metrics = new double[21];','if (!applyNative(buffer, width, height, indices, floorCodes, metrics))','private static native boolean applyNative']:
    need(token in helper_text,'native Java helper missing '+token)

# Frozen 26827 owners outside the audited domains.
for rel in [
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2CfaInput.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2Merger.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2SharedRgba16fCarrier.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java']:
    need(h(B/rel)==h(C/rel),'26827 performance owner changed '+rel)
# Capture/exposure policy files are not in changed allowlist by construction. Denoise invocation remains exact.
for token in ['MgcFullResolutionDenoise.denoise(','IRIS_26826_SHARED_RGBA16F_PRIMARY','parameters.cfaPattern in 0..3','targetMagnitude = minOf(targetMagnitude, currentMagnitude)']:
    need(token in ct,'critical bridge invariant missing '+token)
print('PASS 26828 semantic/ownership/domain validation: exact 8-path scope')
print('PASS 26828 NORMAL clipped-R/B consensus + high-zoom trusted interior + native exact protected-chroma classifier')
print('PASS 26828 inherited 26827 capture/JPEG/DNG/shared-carrier/SHORT-Night owners protected')
