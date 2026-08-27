#!/usr/bin/env python3
from pathlib import Path
import argparse,re,subprocess,tempfile,textwrap

RESERVED={
'attribute','const','uniform','varying','buffer','shared','coherent','volatile','restrict','readonly','writeonly',
'atomic_uint','layout','centroid','flat','smooth','noperspective','patch','sample','break','continue','do','for',
'while','switch','case','default','if','else','subroutine','in','out','inout','float','double','int','void','bool',
'true','false','invariant','precise','discard','return','mat2','mat3','mat4','dmat2','dmat3','dmat4','vec2','vec3',
'vec4','ivec2','ivec3','ivec4','bvec2','bvec3','bvec4','dvec2','dvec3','dvec4','uint','uvec2','uvec3','uvec4',
'lowp','mediump','highp','precision','sampler2D','samplerCube','sampler3D','sampler2DShadow','samplerCubeShadow',
'isampler2D','usampler2D','uimage2D','image2D','struct'
}
def fail(m): raise SystemExit('ERROR: '+m)
def vals(path):
    s=path.read_text(); out={}
    for m in re.finditer(r'\b(?:private\s+)?val\s+(\w+)\s*=\s*"""(.*?)"""\.trimIndent\(\)',s,re.S):
        out[m.group(1)]=textwrap.dedent(m.group(2)).strip()+'\n'
    return out
def expand(src, table):
    for _ in range(16):
        names=re.findall(r'\$([A-Za-z_]\w*)',src)
        if not names: return src
        before=src
        for n in names:
            if n not in table: fail('unresolved Kotlin shader substitution $'+n)
            src=src.replace('$'+n,table[n].rstrip('\n'))
        if src==before: break
    if re.search(r'\$[A-Za-z_]\w*',src): fail('unresolved shader interpolation')
    return src
def reject_reserved(src,name):
    x=re.sub(r'/\*.*?\*/',' ',src,flags=re.S); x=re.sub(r'//.*',' ',x)
    decl=re.compile(r'\b(?:float|double|int|uint|bool|vec[234]|ivec[234]|uvec[234]|bvec[234]|dvec[234]|mat[234])\s+([A-Za-z_]\w*)\b')
    for m in decl.finditer(x):
        if m.group(1) in RESERVED: fail(f'GLSL reserved identifier {m.group(1)} in {name}')
def compile_shader(validator,name,stage,src):
    reject_reserved(src,name)
    required='#version 310 es' if stage=='comp' else '#version 300 es'
    if required not in src: fail(name+' missing '+required)
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/(name+('.comp' if stage=='comp' else '.frag')); p.write_text(src)
        r=subprocess.run([validator,'-S',stage,str(p)],text=True,capture_output=True)
        if r.returncode: fail('glslang failed '+name+'\n'+r.stdout+r.stderr)
def superres(merge):
    pairs=[
      ('uniform ivec2 uOutputSize;', 'uniform ivec2 uOutputSize;\nuniform float uReconstructionZoom;\nuniform float uLumaTemporalScale;'),
      ('    vec2 referenceRaw = (vec2(outputPixel) + vec2(0.5)) *\n        vec2(uRawSize) / vec2(uOutputSize) - vec2(0.5);',
       '    vec2 fullRaw = (vec2(outputPixel) + vec2(0.5)) *\n        vec2(uRawSize) / vec2(uOutputSize) - vec2(0.5);\n    vec2 rawCenter = (vec2(uRawSize) - vec2(1.0)) * 0.5;\n    vec2 referenceRaw = rawCenter + (fullRaw - rawCenter) / max(uReconstructionZoom, 1.0);'),
      ('    frameWeight *= uGlobalFrameWeight;\n    vec2 directionMoment = greenDirectionMoment(anchor, targetGreen);\n    oColorAndRWeight = vec4(semanticSums * frameWeight, weights.r * frameWeight);\n    oGbWeights = vec4(\n        weights.gb * frameWeight,\n        directionMoment * weights.r * frameWeight\n    );',
       '    frameWeight *= uGlobalFrameWeight;\n    float lumaFrameWeight = frameWeight * clamp(uLumaTemporalScale, 0.0, 1.0);\n    vec2 directionMoment = greenDirectionMoment(anchor, targetGreen);\n    oColorAndRWeight = vec4(\n        semanticSums.r * lumaFrameWeight,\n        semanticSums.g * frameWeight,\n        semanticSums.b * frameWeight,\n        weights.r * lumaFrameWeight\n    );\n    oGbWeights = vec4(\n        weights.gb * frameWeight,\n        directionMoment * weights.r * lumaFrameWeight\n    );')]
    for old,new in pairs:
        if old not in merge: fail('mergeRgbSuperRes source replacement anchor missing')
        merge=merge.replace(old,new,1)
    return merge

def run(root,validator=None):
    sp=root/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbShaders.kt'
    vg=root/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'
    sa=root/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'
    for p in (sp,vg,sa):
        if not p.is_file(): fail('missing '+str(p))
    sv,vv,av=vals(sp),vals(vg),vals(sa)
    spatial_frag=['rejection','findBlockTilesGatherEdges','bentoAdjustHighlightMask','mergeRgb','alignedRawClippingMask','convertAlignment']
    vgn_comp=['seed','localClamp','localMedian','directionalSmooth','restoreDirection','iirRgb','calculateError','iirError','blendChroma','finalCameraRgb']
    sabre_frag=['extractBayer','guideAndCovariance','rejection','merge','convertAlignmentSparse','normalDngMerge','copyMask','copyAlpha','reciprocalGreenWeight4x4','dehomogenize','outputTransformUint16','outputTransformFloat']
    missing=[x for x in spatial_frag if x not in sv]+[x for x in vgn_comp if x not in vv]+[x for x in sabre_frag if x not in av]
    if missing: fail('missing active shader(s): '+repr(missing))
    sources=[]
    for n in spatial_frag: sources.append(('spatial_'+n,'frag',expand(sv[n],sv)))
    sources.append(('spatial_mergeRgbSuperRes','frag',superres(expand(sv['mergeRgb'],sv))))
    sources.append(('spatial_copyRgb16ToFloat','comp',expand(sv['copyRgb16ToFloat'],sv)))
    for n in vgn_comp: sources.append(('vgn_'+n,'comp',expand(vv[n],vv)))
    for n in sabre_frag: sources.append(('sabre_'+n,'frag',expand(av[n],av)))
    by={n:s for n,_,s in sources}
    contracts={
      'sabre_guideAndCovariance':['rggb = sqrt(max(vec4(0.0), rggb))','centerGreen >= uGreenClippingPoint'],
      'sabre_rejection':['uColorDifferenceMultiplier','combinedNoise = referenceNoise + currentNoise','frameWeight = exp2(min(-distance, 0.0))'],
      'sabre_merge':['uUseFrameWeight','uRejection'],
      'sabre_normalDngMerge':['uUseFrameWeight'],
      'spatial_mergeRgb':['cancelInterpolation','clampRawPixelToPhase','nativeValue - localGreen'],
      'spatial_mergeRgbSuperRes':['uReconstructionZoom','lumaFrameWeight'],
      'vgn_localMedian':['strength>=0.9999?sum','strength<=0.0001?centerChroma'],
      'vgn_directionalSmooth':['strength>=0.9999?fc','strength<=0.0001?originalChroma'],
      'vgn_blendChroma':['if(strength<0.9999)f*=strength;'],
    }
    for n,toks in contracts.items():
        for tok in toks:
            if tok not in by[n]: fail(n+' contract missing '+tok)
    for n,stage,src in sources: reject_reserved(src,n)
    if validator:
        for n,stage,src in sources: compile_shader(validator,n,stage,src)
        print(f'PASS: REAL GLSL COMPILE {len(sources)} active Spatial/VGN/Sabre shaders via {validator}')
    print(f'PASS: 26547 V1.1 GLSL extraction/contracts shaders={len(sources)}')

def self_test():
    reject_reserved('float f(vec3 precisionCoeffs){ return precisionCoeffs.x; }','good')
    try: reject_reserved('float f(vec3 precision){ return precision.x; }','bad')
    except SystemExit: pass
    else: raise AssertionError('reserved identifier self-test did not fail')
    assert expand('#version 300 es\n$body',{'body':'void main(){}\n'}).endswith('void main(){}')
    print('PASS: 26547 V1.1 GLSL preflight self-test')

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--root'); ap.add_argument('--validator'); ap.add_argument('--self-test',action='store_true'); a=ap.parse_args()
    if a.self_test: self_test()
    else:
        if not a.root: ap.error('--root required')
        run(Path(a.root),a.validator)
