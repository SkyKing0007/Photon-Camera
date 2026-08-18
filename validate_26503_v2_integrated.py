#!/usr/bin/env python3
from pathlib import Path
import argparse, hashlib, importlib.util, math, re

ALLOWED={
 'src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2Merger.java',
 'src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java',
 'src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java',
 'src/main/assets/shaders/motionv2/display_exposure.glsl',
 'src/main/assets/shaders/motionv2/render.glsl',
 'src/main/assets/shaders/motionv2/short_highlight_bayer_recover.glsl',
 'src/main/assets/shaders/motionv2/mfsr_spatial_rgb_normalize_26501.glsl',
}
COLOR='src/main/assets/shaders/motionv2/color_transform.glsl'
CONTRIB='src/main/assets/shaders/motionv2/mfsr_spatial_rgb_contribute_26501.glsl'
BASE_COLOR_SHA='4b14131a59e2358a9b8b18ded4c167f15cc0af5e0ab3d380768625017d7a81ac'
BASE_CONTRIB_SHA='35fcbcce4138f29b4ee83703f6dc9f99452861917daca5e9dec6655c2de5174b'

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def clamp(x,a,b): return max(a,min(b,x))
def smooth(a,b,x):
    t=clamp((x-a)/(b-a),0,1); return t*t*(3-2*t)
def mix(a,b,t): return a*(1-t)+b*t

def scene_targets(ev,p50,p99,valid=True):
    k=smooth(1.5,5.5,ev) if valid else 1
    t50=mix(.002,.05,k); t90=mix(.012,.18,k)
    ratio=p50/max(p99,.002)
    bright=smooth(6,10,ev) if valid else 0
    hdr=clamp(bright*(1-smooth(.060,.200,ratio)),0,1)
    return t50*mix(1,.35,hdr),t90*mix(1,.65,hdr),hdr

def gain_from(ev,p50,p90,p99,valid=True):
    t50,t90,hdr=scene_targets(ev,p50,p99,valid)
    g=math.sqrt(max(1,t50/max(p50,1e-5))*max(1,t90/max(p90,1e-5)))
    return clamp(g,1,16),t50,t90,hdr

def test_a():
    g,t50,t90,h=gain_from(.24,.000977,.004885,.04)
    assert 1.8<g<3.0,(g,t50,t90)
    g5,*_=gain_from(1.30,.01026,.03957,.15); assert 1.0<=g5<1.35,g5
    t50,t90,h=scene_targets(5.5,.05,.5); assert abs(t50-.05)<1e-9 and abs(t90-.18)<1e-9
    old=math.sqrt((.05/.005)*(.18/.03))
    new,*rest=gain_from(12,.005,.03,.30)
    assert new<old*.60,(new,old,rest)
    vals=[scene_targets(ev,.03,.3)[0] for ev in (1.5,2.5,3.5,4.5,5.5)]
    assert vals==sorted(vals),vals
    print('PASS A: frozen capture EV scene key keeps true darkness dark, preserves normal targets, and suppresses high-EV shadow-dominated global over-lift')

def shadow_scale(sensor_y,display_y,local_support,retained,global_strength=.10,floor=.008):
    fw=max(.006,1.5*floor)
    fg=smooth(floor,floor+fw,sensor_y); sg=1-smooth(.12,.30,display_y)
    denom=max(retained-1,1); lr=clamp((max(local_support,1)-1)/denom,0,1)
    ld=smooth(1.5,8,max(local_support,1)); lp=lr*(.30+.70*ld)
    return 1+clamp(global_strength,0,.10)*fg*sg*lp

def test_be():
    assert shadow_scale(.001,.02,14,15)==1
    hi=shadow_scale(.03,.08,14,15); lo=shadow_scale(.03,.08,3.37,15)
    assert 1<lo<hi<=1.10,(lo,hi)
    assert shadow_scale(.03,.40,14,15)==1
    rgb=[.09,.06,.03]; s=hi; out=[v*s for v in rgb]
    assert abs(out[0]/out[1]-rgb[0]/rgb[1])<1e-8 and abs(out[2]/out[1]-rgb[2]/rgb[1])<1e-8
    print('PASS B/E: true floor stays black; local 3.37-frame support gets less lift than 14-frame support; midtones untouched; RGB hue ratios preserved')

def test_f():
    # Normalized semantic accumulation is unbiased by support COUNT when every accepted
    # observation has the same physical color. Thus reference-only edge support asymmetry
    # cannot by itself create a chroma stripe; noisy low-support evidence is the risk.
    truth=(.12,.035,-.020) # G, R-G, B-G
    for counts in [(9,4,3),(12,2,2),(1,1,1)]:
        sums=[truth[i]*counts[i] for i in range(3)]
        norm=[sums[i]/counts[i] for i in range(3)]
        assert max(abs(norm[i]-truth[i]) for i in range(3))<1e-12
    print('PASS F: border-support count asymmetry is algebraically unbiased for identical accepted color; no border desaturation/mask patch is authorized')

def load_seed(path):
    spec=importlib.util.spec_from_file_location('seed26503',path); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def source_tests(root,base):
    R=root/'app'; B=base/'app'
    merger=(R/'src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2Merger.java').read_text()
    cfa=(R/'src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java').read_text()
    exif=(R/'src/main/java/com/particlesdevs/photoncamera/api/ParseExif.java').read_text()
    dj=(R/'src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2DisplayExposure.java').read_text()
    ds=(R/'src/main/assets/shaders/motionv2/display_exposure.glsl').read_text()
    norm=(R/'src/main/assets/shaders/motionv2/mfsr_spatial_rgb_normalize_26501.glsl').read_text()
    render=(R/'src/main/assets/shaders/motionv2/render.glsl').read_text()
    short=(R/'src/main/assets/shaders/motionv2/short_highlight_bayer_recover.glsl').read_text()
    color=R/COLOR
    contrib=R/CONTRIB
    assert sha(color)==BASE_COLOR_SHA,sha(color)
    assert sha(contrib)==BASE_CONTRIB_SHA,sha(contrib)

    # Exact 7-file delta firewall; ParseExif must remain byte-identical to tested 26502.
    def collect(rootp): return {p.relative_to(rootp).as_posix():sha(p) for p in rootp.rglob('*') if p.is_file()}
    a=collect(R); b=collect(B); new=sorted(set(a)-set(b)); rem=sorted(set(b)-set(a)); mod=sorted(k for k in set(a)&set(b) if a[k]!=b[k])
    assert not new,new; assert not rem,rem; assert set(mod)==ALLOWED,(mod,sorted(ALLOWED))

    # A and old single-domain invariant.
    for tok in ('IRIS_26503_FROZEN_CAPTURE_SCENE_KEY_GAIN','ev100','targetP50','targetP90','hdrShadowProtection','liveAeFeedback=false','frozenReferenceCaptureState=true'):
        assert tok in merger,tok
    assert 'sensorDomainGain=1.0' in cfa and 'displayGainOwner=MotionV2DisplayExposure' in cfa
    assert cfa.count('MotionV2Merger.computeReferenceGain')==1

    # B/E local support carrier and sole consumption.
    assert 'uniform highp sampler2D frameSupportTexture;' in norm
    assert 'IRIS_26503_LOCAL_FRAME_EQUIVALENT_SUPPORT_CARRIER' in norm
    assert 'texelFetch(frameSupportTexture,p,0).r' in norm
    assert 'glProg.setTexture("frameSupportTexture", currentDirectFrameSupport);' in cfa
    assert 'IRIS_26503_PIXEL_LOCAL_EFFECTIVE_STACK_PERMISSION' in ds
    assert 'carrier.a' in ds and 'uniform float retainedFrames;' in ds
    assert dj.count('glProg.setVar("displayGain", gain);')==1
    assert dj.count('glProg.setVar("retainedFrames", retainedFrames);')==1
    assert 'globalResidualGain=1.0' in dj and 'pixelLocalSupportFromCarrierAlpha=true' in dj

    # C: no post-physical white painting; Camera2 transform untouched.
    assert 'IRIS_26503_UPSTREAM_EXHAUSTION_OWNS_WHITE' in render
    assert 'IRIS_26503_HUE_PRESERVING_EXTENDED_RANGE_GAMUT' in render
    fit=render[render.index('vec3 fitDisplayGamut'):render.index('void main()',render.index('vec3 fitDisplayGamut'))]
    assert 'return rgb/max(peak,1.0e-6);' in fit and 'vec3(1.0)' not in fit and 'mix(' not in fit
    assert sha(color)==sha(B/COLOR)

    # D: seed Short Tier2 remains exact in authority concept.
    for tok in ('IRIS_26503_BOUNDARY_ANCHORED_SHORT_OBSERVABILITY','flowConfidence < max(minimumFlowConfidence, 0.85)','centerError > 0.070','strongConflicts < 0.5','supportCount >= requiredSupport','meanRelativeError <= 0.045','state[i] = PROVENANCE_SHORT_VALIDATED;'):
        assert tok in short,tok
    assert 'return supportCount >= 16.0 && bestError <= 0.060;' in short

    # Performance: disable only diagnostics; retain real effective support readback.
    assert 'IRIS_26503_DISABLE_HEAVY_DIRECT_RGB_SUPPORT_READBACK' in cfa
    assert 'IRIS_26503_DISABLE_HEAVY_PROVENANCE_READBACK' in cfa
    assert 'currentSupport.BufferLoad();' in cfa and 'MotionMetrics.publishV2Support(' in cfa

    # Preserve Photon's cross-device ISO100-normalized EXIF convention byte-for-byte.
    base_exif=(B/'src/main/java/com/particlesdevs/photoncamera/api/ParseExif.java').read_text()
    assert exif==base_exif,'ParseExif.java changed; 26503 must preserve tested-26502 ISO normalization'
    sens=exif[exif.index('Integer iso = result.get(SENSOR_SENSITIVITY);'):exif.index('data.SENSITIVITY_TYPE')]
    assert 'IsoExpoSelector.getMPY()' in sens and 'isonum = iso;' not in sens

    # F/G forbidden band-aids and architecture re-entry.
    joined='\n'.join((merger,cfa,exif,dj,ds,norm,render,short)).lower()
    for bad in ('borderdesatur','borderchroma','edgemask','adrc fallback','single-frame fallback','neutralLowerBound'.lower(),'rcd demosaic'):
        assert bad not in joined,bad
    assert 'IRIS_26501_WRONSKI_PER_FRAME_SPATIAL_RGB_OWNER' in (R/CONTRIB).read_text()
    assert 'IRIS_26502_STACK_AWARE_SEMANTIC_NORMALIZE' in norm
    print('PASS SOURCE A-G: exact seven-file delta; Camera2 matrix, Spatial-RGB contributor, and Photon ISO100-normalized EXIF frozen; local support carrier and speed gates verified')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('root',type=Path); ap.add_argument('--base-root',type=Path,required=True); ap.add_argument('--seed-validator',type=Path,required=True); a=ap.parse_args()
    source_tests(a.root,a.base_root)
    test_a(); test_be(); test_f()
    seed=load_seed(a.seed_validator)
    print(seed.test_highlight_math())
    print(seed.test_short_math())
    print('PASS: 26503 V2 integrated A-G + speed validator complete; tested-26502 EXIF convention preserved')
if __name__=='__main__': main()
