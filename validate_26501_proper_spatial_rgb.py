#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import argparse, hashlib, math, re, sys

ALLOWLIST = {
    'app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_chroma_guide_26501.glsl',
    'app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_contribute_26501.glsl',
    'app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_normalize_26501.glsl',
    'app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_short_weight_26501.glsl',
    'app/src/main/assets/shaders/motionv2/render.glsl',
    'app/src/main/assets/shaders/motionv2/shadow_aux_bayer_fuse.glsl',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2CfaInput.java',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
    'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java',
}

def fail(msg: str) -> None:
    raise AssertionError(msg)

def need(cond: bool, msg: str) -> None:
    if not cond: fail(msg)

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def text(root: Path, rel: str) -> str:
    return (root/rel).read_text()

def changed_runtime_files(base: Path, cand: Path) -> set[str]:
    roots = [base/'app/src/main', cand/'app/src/main']
    rels=set()
    for root, origin in [(roots[0],base),(roots[1],cand)]:
        for p in root.rglob('*'):
            if p.is_file(): rels.add(str(p.relative_to(origin)).replace('\\','/'))
    changed=set()
    for rel in rels:
        a,b=base/rel,cand/rel
        if not a.exists() or not b.exists() or sha(a)!=sha(b): changed.add(rel)
    return changed

# ---------- CPU reference model for the new semantic architecture ----------
BLACK=[64.0,66.0,68.0,70.0]
WHITE=1023.0
WB_R=2.25
WB_B=1.65
CLIP=0.985
W=32; H=32

def phase(x,y): return ((y&1)<<1)|(x&1)
def color_for(pattern,x,y):
    q=phase(x,y)
    if pattern==0: return 0 if q==0 else (2 if q==3 else 1)
    if pattern==1: return 0 if q==1 else (2 if q==2 else 1)
    if pattern==2: return 0 if q==2 else (2 if q==1 else 1)
    return 0 if q==3 else (2 if q==0 else 1)

def phase_clamp_coord(v, extent):
    ph=v&1
    if ph>=extent: return extent-1
    last=ph+2*((extent-1-ph)//2)
    return max(ph,min(v,last))
def phase_clamp(x,y): return phase_clamp_coord(x,W), phase_clamp_coord(y,H)

def make_raw(pattern, scene):
    raw=[[0.0]*W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            c=color_for(pattern,x,y); q=phase(x,y)
            rgb=scene(x,y)
            s=max(0.0,min(0.96,rgb[c]))
            raw[y][x]=round(BLACK[q]+s*(WHITE-BLACK[q]))
    return raw

def sensor(raw,x,y):
    x,y=phase_clamp(x,y); q=phase(x,y)
    return max(raw[y][x]-BLACK[q],0.0)/max(WHITE-BLACK[q],1.0)
def wb_for(c): return WB_R if c==0 else (WB_B if c==2 else 1.0)
def gained(raw,pattern,x,y):
    x,y=phase_clamp(x,y)
    return sensor(raw,x,y)*wb_for(color_for(pattern,x,y))

def guide(raw,pattern):
    g=[[0.0]*W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            c=color_for(pattern,x,y); center=gained(raw,pattern,x,y)
            if c==1:
                g[y][x]=center; continue
            gL=gained(raw,pattern,x-1,y); gR=gained(raw,pattern,x+1,y)
            gU=gained(raw,pattern,x,y-1); gD=gained(raw,pattern,x,y+1)
            cL=gained(raw,pattern,x-2,y); cR=gained(raw,pattern,x+2,y)
            cU=gained(raw,pattern,x,y-2); cD=gained(raw,pattern,x,y+2)
            hl=.5*(gL+gR); vl=.5*(gU+gD)
            hc=max(-.5*abs(gL-gR),min(.25*(2*center-cL-cR),.5*abs(gL-gR)))
            vc=max(-.5*abs(gU-gD),min(.25*(2*center-cU-cD),.5*abs(gU-gD)))
            hh=hl+hc; vv=vl+vc
            gh=abs(gL-gR)+abs(2*center-cL-cR)
            gv=abs(gU-gD)+abs(2*center-cU-cD)
            blend=gv/max(gh+gv,1e-7)
            val=vv*(1-blend)+hh*blend
            lo=min(gL,gR,gU,gD); hi=max(gL,gR,gU,gD)
            g[y][x]=max(lo,min(val,hi))
    return g

def kernel(dx,dy):
    # Positive symmetric stand-in for a flat-field/identity Wronski precision matrix.
    return 2**(-0.5*(dx*dx+dy*dy))+0.00005

def reconstruct(raw,pattern):
    gg=guide(raw,pattern)
    out=[[(0.0,0.0,0.0) for _ in range(W)] for __ in range(H)]
    for y in range(H):
        for x in range(W):
            gs=gw=0.0
            for dy in (-1,0,1):
                for dx in (-1,0,1):
                    qx,qy=phase_clamp(x+dx,y+dy)
                    if color_for(pattern,qx,qy)!=1 or sensor(raw,qx,qy)>=CLIP: continue
                    wt=kernel(dx,dy); gs+=gained(raw,pattern,qx,qy)*wt; gw+=wt
            if gw<=1e-8: continue
            target=gs/gw
            opp=[0.0,0.0]; den=[0.0,0.0]
            for dy in (-1,0,1):
                for dx in (-1,0,1):
                    qx,qy=phase_clamp(x+dx,y+dy)
                    c=color_for(pattern,qx,qy)
                    if c==1 or sensor(raw,qx,qy)>=CLIP: continue
                    spatial=kernel(dx,dy)
                    local=gg[qy][qx]
                    signal=max(local,target,0.0)
                    # Nonzero reasonable noise only changes edge borrowing, never chroma survival.
                    variance=1e-4*signal+1e-6
                    sigma=max(1/160,2.5*math.sqrt(variance))
                    edge=math.exp(-.5*((local-target)/max(sigma,1e-7))**2)
                    wt=spatial*edge
                    idx=0 if c==0 else 1
                    opp[idx]+=(gained(raw,pattern,qx,qy)-local)*wt; den[idx]+=wt
            rg=opp[0]/den[0] if den[0]>1e-8 else 0.0
            bg=opp[1]/den[1] if den[1]>1e-8 else 0.0
            calc=(target+rg,target,target+bg)
            out[y][x]=(max(calc[0]/WB_R,0.0),max(calc[1],0.0),max(calc[2]/WB_B,0.0))
    return out

def mean(values): return sum(values)/len(values)
def parity_means(out, channel, margin=4):
    bins=[[] for _ in range(4)]
    for y in range(margin,H-margin):
        for x in range(margin,W-margin): bins[phase(x,y)].append(out[y][x][channel])
    return [mean(v) for v in bins]

def flat_scene(rgb): return lambda x,y: rgb

def assert_flat(pattern, name, rgb):
    raw=make_raw(pattern,flat_scene(rgb)); out=reconstruct(raw,pattern)
    for c in range(3):
        vals=[]
        for y in range(5,H-5):
            for x in range(5,W-5): vals.append(out[y][x][c])
        actual=mean(vals)
        need(abs(actual-rgb[c])<0.0045,
             f'{name} pattern={pattern} channel={c} expected={rgb[c]:.5f} got={actual:.5f}')
        pm=parity_means(out,c,margin=5)
        need(max(pm)-min(pm)<0.0015,
             f'{name} pattern={pattern} parity leak channel={c} means={pm}')

def assert_vertical_edge(pattern, left, right, name):
    raw=make_raw(pattern,lambda x,y: left if x<W//2 else right); out=reconstruct(raw,pattern)
    # Scene is vertically invariant: a Bayer-row sawtooth is illegal. Check columns away from edge.
    for x in list(range(5,W//2-4))+list(range(W//2+4,W-5)):
        for c in range(3):
            even=[out[y][x][c] for y in range(6,H-6) if (y&1)==0]
            odd=[out[y][x][c] for y in range(6,H-6) if (y&1)==1]
            need(abs(mean(even)-mean(odd))<0.0015,
                 f'{name} pattern={pattern} vertical CFA-row razor x={x} c={c}')

def assert_horizontal_edge(pattern, top, bottom, name):
    raw=make_raw(pattern,lambda x,y: top if y<H//2 else bottom); out=reconstruct(raw,pattern)
    for y in list(range(5,H//2-4))+list(range(H//2+4,H-5)):
        for c in range(3):
            even=[out[y][x][c] for x in range(6,W-6) if (x&1)==0]
            odd=[out[y][x][c] for x in range(6,W-6) if (x&1)==1]
            need(abs(mean(even)-mean(odd))<0.0015,
                 f'{name} pattern={pattern} horizontal CFA-column razor y={y} c={c}')

def assert_normalizer_domain_and_highlight():
    # Neutral fallback lives in the temporary WB-balanced calculation domain.
    n=.73
    camera=(n/WB_R,n,n/WB_B)
    downstream=(camera[0]*WB_R,camera[1],camera[2]*WB_B)
    need(max(downstream)-min(downstream)<1e-12,
         f'neutral fallback does not survive WB round-trip: {downstream}')

    out_scale=.80; start=.50; log_shape=6.0
    def mapped(y,scene_white):
        if y<=start: return y*out_scale
        wp=max(scene_white,start+.05)
        x=max(0.0,min(1.0,(y-start)/max(wp-start,1e-6)))
        shaped=math.log(1+log_shape*x)/math.log(1+log_shape)
        pre_white=1.0/out_scale
        return (start+(pre_white-start)*shaped)*out_scale
    for sw in (1.0,1.5,3.0,6.0):
        prev=-1.0
        for k in range(201):
            y=sw*k/200.0; val=mapped(y,sw)
            need(val+1e-10>=prev, f'highlight shoulder non-monotonic sceneWhite={sw} at y={y}')
            prev=val
        need(abs(mapped(sw,sw)-1.0)<1e-9, f'final white unreachable for sceneWhite={sw}')

def assert_packed_highlight_rolloff():
    # Model the normalizer's manual bilinear expansion of packed 2x2 provenance.
    # A packed step must not remain a hard two-pixel block edge in full-res RGB.
    packed=[0.0]*6+[1.0]*6
    def at(i): return packed[max(0,min(i,len(packed)-1))]
    vals=[]
    for raw_x in range(2*len(packed)):
        pc=0.5*raw_x-0.5
        lo=math.floor(pc); f=pc-lo; hi=lo+1
        c=at(lo)*(1-f)+at(hi)*f
        vals.append(c)
    # Monotonic transition, with at least one intermediate full-res sample.
    for a,b in zip(vals,vals[1:]):
        need(b+1e-12>=a, f'packed highlight mask becomes non-monotonic: {vals}')
    need(any(1e-6<v<1.0-1e-6 for v in vals),
         f'packed highlight mask was not spatially expanded: {vals}')
    # No pair of raw parities may alternate once the transition is away from its center.
    # The only differences are the intended monotonic ramp, never a repeating 2x2 checker.
    diffs=[vals[i+2]-vals[i] for i in range(len(vals)-2)]
    need(all(d>=-1e-12 for d in diffs), f'highlight rolloff contains CFA parity reversal: {vals}')

def assert_phase_authority_mapping():
    for pat in range(4):
        qs={0:[],1:[],2:[]}
        for q in range(4): qs[color_for(pat,q&1,q>>1)].append(q)
        need(len(qs[0])==1 and len(qs[1])==2 and len(qs[2])==1,
             f'invalid Bayer axis mapping pattern={pat}: {qs}')
        for color in (0,2):
            weights=[0.0]*4; weights[qs[color][0]]=1.0
            axes=(.5*(weights[qs[1][0]]+weights[qs[1][1]]),
                  weights[qs[0][0]],weights[qs[2][0]])
            expected=(0.0,1.0,0.0) if color==0 else (0.0,0.0,1.0)
            need(axes==expected, f'phase authority leaks pattern={pat} color={color}: {axes}')

def run_synthetic():
    colors={
        'gray':(.30,.30,.30), 'red':(.62,.09,.07), 'green':(.08,.55,.10),
        'blue':(.07,.10,.60), 'cyan':(.08,.50,.52), 'yellow':(.58,.52,.08),
        'white':(.72,.72,.72),
    }
    for p in range(4):
        for name,rgb in colors.items(): assert_flat(p,name,rgb)
        assert_vertical_edge(p,(.06,.06,.06),(.72,.72,.72),'neutral vertical')
        assert_horizontal_edge(p,(.08,.08,.08),(.68,.68,.68),'neutral horizontal')
        assert_vertical_edge(p,(.55,.10,.08),(.08,.12,.56),'color vertical')
    assert_phase_authority_mapping()
    assert_packed_highlight_rolloff()
    assert_normalizer_domain_and_highlight()

def uniform_names(shader: str) -> set[str]:
    # Includes samplers/images and ordinary uniforms; SSBO buffer declarations are validated separately.
    return set(re.findall(
        r'\buniform\s+(?:highp\s+|mediump\s+|lowp\s+)?(?:readonly\s+|writeonly\s+)?[A-Za-z0-9_]+\s+([A-Za-z_][A-Za-z0-9_]*)\s*;',
        shader))

def host_bound_names(segment: str) -> set[str]:
    return set(re.findall(r'glProg\.set(?:Var|Texture|TextureCompute)\(\s*"([A-Za-z_][A-Za-z0-9_]*)"', segment))

def method_segment(host: str, method_name: str, next_method_name: str) -> str:
    a=host.index(method_name)
    b=host.index(next_method_name,a)
    return host[a:b]

def static_source_checks(base: Path, cand: Path):
    changed=changed_runtime_files(base,cand)
    need(changed==ALLOWLIST, f'runtime scope mismatch\nexpected={sorted(ALLOWLIST)}\nactual={sorted(changed)}')

    guide=text(cand,'app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_chroma_guide_26501.glsl')
    contrib=text(cand,'app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_contribute_26501.glsl')
    norm=text(cand,'app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_normalize_26501.glsl')
    shortw=text(cand,'app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_short_weight_26501.glsl')
    shadow=text(cand,'app/src/main/assets/shaders/motionv2/shadow_aux_bayer_fuse.glsl')
    host=text(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java')
    post=text(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java')
    inp=text(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2CfaInput.java')
    render=text(cand,'app/src/main/assets/shaders/motionv2/render.glsl')

    for marker in ['IRIS_26501_PER_FRAME_NATIVE_GREEN_GUIDE','greenAtNonGreen','nativeMin','nativeMax']:
        need(marker in guide, f'green guide invariant missing {marker}')
    need('neutralLowerBound' not in guide, '26500 red/blue-to-green lower-bound bug survived')
    need('LensShading' not in guide and 'lensShading' not in guide, 'lens shading leaked into green guide')

    for marker in ['IRIS_26501_WRONSKI_PER_FRAME_SPATIAL_RGB_OWNER','semanticPhaseWeightTexture',
                   'useSemanticPhaseWeight','useFrameWeight','chromaGuideWeight','semanticAxisPhaseWeight']:
        need(marker in contrib, f'contribution invariant missing {marker}')
    need('smoothstep(1.25' not in contrib and 'statistical' not in contrib,
         'post-SNR chroma eraser survived')
    need('chromaEdgeNoiseSigmas*sqrt' in contrib and 'chromaEdgeSigmaFloor' in contrib,
         'noise is not limited to edge agreement')
    need('LensShading' not in contrib and 'lensShading' not in contrib,
         'lens shading leaked into per-frame opponent reconstruction')
    need('layout(location=0)' in contrib and 'layout(location=1)' in contrib,
         'MRT semantic output missing')

    need('layout(rgba32f,binding=0)' in shortw, 'Short-A phase weight is not RGBA per phase')
    need('weight[q]' in shortw and 'state-2.0' in shortw, 'Short-A phase admission is not phase-specific')
    need('layout(rgba32f, binding = 1)' in shadow, 'shadow semantic weight is not RGBA per phase')
    need('semanticPhaseWeight[phase]=blend' in shadow, 'shadow exact per-phase blend not carried to RGB')

    for marker in ['IRIS_26501_SPATIAL_RGB_NORMALIZE_EXACTLY_ONCE','cameraDomainScale','lensShadingRgb',
                   'Censored highlight fallback is brightness-only']:
        need(marker.lower() in norm.lower(), f'normalizer invariant missing {marker}')
    need(norm.count('cameraDomainScale')>=2, 'camera-domain WB inverse missing')
    need('calculationRgb*=lensShadingRgb' in norm, 'lens shading is not after completed RGB')
    need('vec3(max(neutral,green))' in norm, 'neutral censored fallback missing')
    need('IRIS_26501_PHASE_INVARIANT_CENSORED_ROLLOFF' in norm,
         'packed provenance is not smoothed before highlight neutralization')
    need('smoothCensoredFraction' in norm and 'neutralMix=smoothstep(0.0,0.75,censored)' in norm,
         'censored highlight neutralization is not continuous')
    need('if(censored>0.0' not in norm, 'hard 2x2 censored highlight switch survived')

    for marker in ['GL_ONE, android.opengl.GLES30.GL_ONE','iris26501SemanticAccumulator',
                   'iris26501OpponentWeightAccumulator','IRIS_26501_SPATIAL_RGB_CONTRIBUTION_INVARIANT_PASS',
                   'motionV2BlackLevelValid','motionV2WhiteLevelValid','IRIS_26501_PROPER_SPATIAL_RGB_OUTPUT']:
        need(marker in host, f'host invariant missing {marker}')
    need('chromaEdgeNoiseSigmas", 2.5f' in host, '1.27.1 chroma edge sigma count not exact')
    need('chromaEdgeSigmaFloor", 1.0f / 160.0f' in host, '1.27.1 chroma edge floor not exact')
    need('FLOAT_16, 4' in host, 'RGBA16F semantic accumulator storage missing')
    need('directMultiframeRgb=false' not in host, 'stale false RGB telemetry survived')
    need('joint_green_26500' not in host and 'joint_rgb_26500' not in host,
         'failed hybrid 26500 shader is active')
    need('direct_rgb_' not in host, 'historical failed direct_rgb path reactivated')

    # Java <-> GLSL contract: every declared runtime uniform must be bound by the owning host pass.
    guide_seg=method_segment(host,'private static void iris26501RenderChromaGuide(',
                                  'private static void iris26501RenderRgbCovariance(')
    contrib_seg=method_segment(host,'private static void iris26501ContributeRgbFrame(',
                                    'private final ArrayList<ImageFrame> images;')
    for label,shader,seg in [('greenGuide',guide,guide_seg),('contribute',contrib,contrib_seg)]:
        missing=uniform_names(shader)-host_bound_names(seg)
        need(not missing, f'{label} Java/GLSL uniforms unbound: {sorted(missing)}')
    # Final normalization is in the single finalization block rather than a helper method.
    na=host.index('IRIS_26501_PROPER_SPATIAL_RGB_FINAL_NORMALIZATION')
    nb=host.index('IRIS_26488_TINY_DIAGNOSTICS_BEFORE_SINGLE_GPU_DRAIN',na)
    missing=uniform_names(norm)-host_bound_names(host[na:nb])
    need(not missing, f'normalize Java/GLSL uniforms unbound: {sorted(missing)}')
    sa=host.index('mfsr_spatial_rgb_short_weight_26501')-300
    sb=host.index('iris26501ContributeRgbFrame(',sa)
    missing=uniform_names(shortw)-host_bound_names(host[sa:sb])
    need(not missing, f'Short-A phase-weight uniforms unbound: {sorted(missing)}')
    need('setTextureCompute("outSemanticWeight",iris26501ShadowWeight,true)' in host,
         'shadow semantic phase-weight output is not bound')

    # Normal auxiliary must contribute semantic RGB before helper Bayer accumulator.
    marker=host.index('IRIS_26501_PER_FRAME_SEMANTIC_ACCUMULATION')
    helper=host.index('glProg.useAssetProgram("motionv2/mfsr_bayer_accumulate",true);', marker)
    call=host.index('iris26501ContributeRgbFrame(', marker)
    need(call < helper, 'auxiliary Bayer collapse occurs before semantic RGB contribution')
    # Exact role modes: reference no temporal/phase weight; normal temporal only; HDR phase only.
    need('true, false, false);' in host, 'reference semantic role mode missing')
    need('false, true, false);' in host, 'normal auxiliary semantic role mode missing')
    need(host.count('false,false,true);') >= 2, 'Short-A/shadow phase-specific semantic role modes missing')

    for marker in ['motionV2DirectRgbCarrier','V2_POST_PROPER_PER_FRAME_RGB']:
        need(marker in post, f'post RGB carrier invariant missing {marker}')
    need('without direct RGB carrier' in post, 'post graph does not hard-fail ambiguous standard Bayer carrier')
    need('properPerFrameCameraRgbFullRes' in inp, 'input node is not full-resolution RGB')
    need('directBayer && !directRgbCarrier' in inp, 'input node does not reject ambiguous standard Bayer')

    for marker in ['IRIS_26501_WHITE_TARGET_AFTER_EXISTING_OUTPUT_EXPOSURE',
                   'IRIS_26501_GENTLE_NEUTRAL_WHITE_ROLLOFF','preScaleDisplayWhite','neutralMix']:
        need(marker in render, f'render highlight invariant missing {marker}')
    need('return rgb/max(peak' not in render, 'old unconditional hue-preserving overflow rule survived')

    # Changed compute shaders must keep every layout declaration on its own physical line for Photon GLInterface.
    for rel in [
        'app/src/main/assets/shaders/motionv2/mfsr_spatial_rgb_short_weight_26501.glsl',
        'app/src/main/assets/shaders/motionv2/shadow_aux_bayer_fuse.glsl']:
        for i,line in enumerate(text(cand,rel).splitlines(),1):
            if line.count('layout(')>1: fail(f'{rel}:{i} multiple layout declarations on one physical line')

    # Old direct-RGB assets may exist historically, but no changed runtime owner may invoke them.
    for rel in ALLOWLIST:
        if rel.endswith(('.java','.glsl')):
            t=text(cand,rel)
            need('motionv2/direct_rgb_' not in t, f'historical direct RGB invocation in {rel}')


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('candidate', nargs='?', default='/mnt/data/26501_work')
    ap.add_argument('--base', default='/mnt/data/26501_base')
    args=ap.parse_args()
    base=Path(args.base); cand=Path(args.candidate)
    need(base.is_dir() and cand.is_dir(), 'base/candidate directory missing')
    static_source_checks(base,cand)
    print('PASS: exact 5 modified + 4 new runtime scope')
    print('PASS: proper per-frame Spatial RGB static ownership contracts')
    run_synthetic()
    print('PASS: synthetic flat RGB/WB round-trip for all 4 CFA patterns')
    print('PASS: synthetic CFA parity invariance and razor-edge regression gates')
    print('PASS: packed highlight provenance expands smoothly without a 2x2 block exit')
    print('PASS: 26500 green-floor and post-SNR chroma regressions absent')
    print('PASS: Short-A/shadow phase-specific semantic authority')
    print('VALIDATION 26501 PROPER SPATIAL RGB: PASS')

if __name__=='__main__':
    try: main()
    except Exception as e:
        print(f'VALIDATION 26501 PROPER SPATIAL RGB: FAIL: {e}', file=sys.stderr)
        raise
