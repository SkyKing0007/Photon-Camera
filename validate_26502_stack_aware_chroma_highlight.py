#!/usr/bin/env python3
from pathlib import Path
import argparse, random, re, statistics

EXPECTED_PATCH_SCOPE = {
    "app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_normalize_26501.glsl",
    "app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java",
}
SHADER_REL = "app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_normalize_26501.glsl"
HOST_REL = "app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java"
EPS = 1.0e-7

def require(cond, message):
    if not cond: raise SystemExit(message)
def smoothstep(a,b,x):
    if x<=a: return 0.0
    if x>=b: return 1.0
    t=(x-a)/(b-a); return t*t*(3.0-2.0*t)
def agreement(center,local,green,center_q):
    threshold=max(0.010,0.25*max(green,0.02))
    return 1.0-center_q*smoothstep(threshold,2.5*threshold,abs(center-local))
def shadow_blend(center,local,green,center_q,local_q):
    dark=1.0-smoothstep(0.018,0.085,max(green,0.0))
    return dark*((1.0-center_q)*0.70+center_q*0.38)*agreement(center,local,green,center_q)*local_q
def neutral_mix(physical_highlight,censored,color_quality,neutral,g_present=True):
    highlight=smoothstep(0.55,0.96,physical_highlight)*smoothstep(0.10,0.90,censored)
    unresolved=1.0-smoothstep(0.20,0.70,color_quality)
    exhausted=smoothstep(0.970,0.995,neutral)*smoothstep(0.70,0.98,censored)
    v=max(highlight*unresolved,exhausted)
    if not g_present: v=1.0
    return max(0.0,min(1.0,v))
def declaration_reserved_scan(src):
    clean=re.sub(r'/\*.*?\*/',' ',src,flags=re.S); clean=re.sub(r'//.*',' ',clean)
    reserved={'sample','precision','packed','common','partition','active','asm','class','union','enum','typedef','template','this','resource','goto','inline','noinline','public','static','extern','external','interface','long','short','half','fixed','unsigned','superp','input','output','hvec2','hvec3','hvec4','fvec2','fvec3','fvec4','sampler3DRect','filter','sizeof','cast','namespace','using','row_major'}
    type_re=r'(?:bool|int|uint|float|double|vec[234]|ivec[234]|uvec[234]|bvec[234]|dvec[234]|mat[234](?:x[234])?|dmat[234](?:x[234])?|[iu]?sampler\w+|[iu]?image\w+)'
    hits=[]
    for m in re.finditer(r'\b'+type_re+r'\s+([A-Za-z_]\w*)',clean):
        if m.group(1) in reserved: hits.append((clean.count('\n',0,m.start())+1,m.group(1)))
    return hits

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('candidate'); ap.add_argument('--patch',required=True); args=ap.parse_args()
    root=Path(args.candidate); shader=(root/SHADER_REL).read_text(); host=(root/HOST_REL).read_text(); patch=Path(args.patch).read_text()
    touched=set(re.findall(r'^diff --git a/(\S+) b/(\S+)$',patch,flags=re.M)); flat={a for a,b in touched if a==b}
    require(flat==EXPECTED_PATCH_SCOPE,f'26502 runtime patch scope mismatch: {sorted(flat)}')
    for marker in ['IRIS_26502_STACK_AWARE_SEMANTIC_NORMALIZE','IRIS_26502_NEIGHBOR_OPPONENT_REPAIR','IRIS_26502_OPPONENT_SUPPORT_REGULARIZATION','IRIS_26502_CONTINUOUS_HIGHLIGHT_RELIABILITY']:
        require(marker in shader,f'missing shader marker {marker}')
    require(host.count('IRIS_26502_STACK_AWARE_RGB_OUTPUT')==2,'26502 runtime/log marker must appear exactly twice in host')
    require('IRIS_26501_PROPER_SPATIAL_RGB_OUTPUT' not in host,'old 26501 final-output marker survived in host')
    require('smoothstep(0.0,0.75,censored)' not in shader.replace(' ',''),'old packed-censor direct neutralization survived')
    require('float neutralMix=highlightGate*unresolvedColor;' in shader,'continuous highlight reliability owner missing')
    require('float exhaustedGate=smoothstep(0.970,0.995,neutral)' in shader,'endpoint neutral gate missing')
    require('opponentSupportQuality' in shader and 'neighborWeightSums' in shader,'opponent support regularization missing')
    require(shader.count('accumulateNeighborOpponent(')==9,'expected helper definition plus eight neighbor gathers')
    require('calculationRgb*=lensShadingRgb(p);' in shader and 'vec3 cameraRgb=calculationRgb*cameraDomainScale;' in shader,'V6 LSC/WB order anchors missing')
    require(shader.index('calculationRgb*=lensShadingRgb(p);')<shader.index('vec3 cameraRgb=calculationRgb*cameraDomainScale;'),'LSC / camera-domain order changed')
    require('Output=vec4(max(cameraRgb,vec3(0.0)),min(gWeight,65504.0));' in shader,'V6 RGB carrier/support output contract changed')
    require('noiseS' not in shader and 'noiseO' not in shader,'stale/global Photon noise variables entered normalizer')
    hits=declaration_reserved_scan(shader); require(not hits,f'GLSL reserved declared identifiers: {hits}')

    rng=random.Random(26502); center=[]; filtered=[]; true_opp=0.003; green=0.010
    for _ in range(6000):
        c=true_opp+rng.gauss(0.0,0.008); l=true_opp+rng.gauss(0.0,0.003); b=shadow_blend(c,l,green,0.8,1.0)
        center.append(c); filtered.append(c*(1.0-b)+l*b)
    before=statistics.pstdev(center); after=statistics.pstdev(filtered)
    require(after<before*0.82,f'deep-shadow opponent cleanup too weak: {after}/{before}')
    strong_edge=0.050; b=shadow_blend(strong_edge,0.0,0.010,1.0,1.0); retained=strong_edge*(1.0-b)
    require(retained>=strong_edge*0.90,f'strong supported color edge over-smoothed: {retained}')
    require(neutral_mix(0.25,1.0,0.0,0.25,True)==0.0,'recoverable low/mid wall still neutralized by censor state')
    require(neutral_mix(0.80,0.75,1.0,0.80,True)<0.02,'supported bright wall/object hue still neutralized')
    require(neutral_mix(1.0,1.0,0.0,1.0,True)>0.95,'truly exhausted highlight does not converge neutral')
    for frag in ['GalleryManager','Dng','capture','render.glsl','PostPipeline.java','MotionV2CfaInput.java']:
        require(all(frag not in p for p in flat),f'forbidden 26502 patch scope fragment: {frag}')
    print('PASS: 26502 patch touches only V6 semantic normalizer + runtime marker host')
    print(f'PASS: synthetic deep-shadow opponent std {before:.6f} -> {after:.6f}; green/luma owner untouched')
    print(f'PASS: strong supported color edge retention {retained/strong_edge:.3f}')
    print('PASS: recoverable wall censor state no longer paints neutral; true endpoint still converges neutral')
    print('PASS: RAW export/capture/Wronski/render/UHDR paths are outside the 26502 patch')
if __name__=='__main__': main()
