#!/usr/bin/env python3
from pathlib import Path
import argparse,re,subprocess,tempfile,textwrap

RESERVED={
'attribute','const','uniform','varying','buffer','shared','coherent','volatile','restrict',
'readonly','writeonly','atomic_uint','layout','centroid','flat','smooth','noperspective','patch',
'sample','break','continue','do','for','while','switch','case','default','if','else','subroutine',
'in','out','inout','float','double','int','void','bool','true','false','invariant','precise',
'discard','return','mat2','mat3','mat4','dmat2','dmat3','dmat4','vec2','vec3','vec4','ivec2',
'ivec3','ivec4','bvec2','bvec3','bvec4','dvec2','dvec3','dvec4','uint','uvec2','uvec3','uvec4',
'lowp','mediump','highp','precision','sampler2D','samplerCube','sampler3D','sampler2DShadow',
'samplerCubeShadow','isampler2D','usampler2D','uimage2D','image2D','struct',
}
def fail(m): raise SystemExit('ERROR: '+m)
def code_only(s):
    out=[]; i=0; state='code'
    while i<len(s):
        c=s[i]; n=s[i+1] if i+1<len(s) else ''
        if state=='code':
            if s.startswith('"""',i): state='triple'; out.extend('   '); i+=3; continue
            if c=='/' and n=='/': state='line'; out.extend('  '); i+=2; continue
            if c=='/' and n=='*': state='block'; out.extend('  '); i+=2; continue
            if c=='"': state='dq'; out.append(' '); i+=1; continue
            if c=="'": state='sq'; out.append(' '); i+=1; continue
            out.append(c); i+=1; continue
        if state=='line':
            if c=='\n': state='code'; out.append('\n')
            else: out.append(' ')
            i+=1; continue
        if state=='block':
            if c=='*' and n=='/': state='code'; out.extend('  '); i+=2
            else: out.append('\n' if c=='\n' else ' '); i+=1
            continue
        if state=='triple':
            if s.startswith('"""',i): state='code'; out.extend('   '); i+=3
            else: out.append('\n' if c=='\n' else ' '); i+=1
            continue
        quote='"' if state=='dq' else "'"
        if c=='\\': out.extend('  ' if i+1<len(s) else ' '); i+=2; continue
        if c==quote: state='code'; out.append(' '); i+=1; continue
        out.append('\n' if c=='\n' else ' '); i+=1
    if state in ('block','dq','sq','triple'): fail('unterminated comment/string')
    return ''.join(out)
def balanced(path):
    s=code_only(path.read_text()); pairs={'{':'}','(':')','[':']'}; st=[]
    for c in s:
        if c in pairs: st.append(c)
        elif c in pairs.values():
            if not st or pairs[st.pop()]!=c: fail('unbalanced '+str(path))
    if st: fail('unbalanced '+str(path))
def vals(path):
    s=path.read_text(); out={}
    for m in re.finditer(r'\b(?:private\s+)?val\s+(\w+)\s*=\s*"""(.*?)"""\.trimIndent\(\)',s,re.S):
        out[m.group(1)]=textwrap.dedent(m.group(2)).strip()+'\n'
    return out
def expand(src, table):
    for _ in range(12):
        names=re.findall(r'\$([A-Za-z_]\w*)',src)
        if not names: return src
        before=src
        for n in names:
            if n not in table: fail('unresolved Kotlin shader substitution $'+n)
            src=src.replace('$'+n,table[n].rstrip('\n'))
        if src==before: break
    if re.search(r'\$[A-Za-z_]\w*',src): fail('unresolved shader interpolation')
    return src
def reject_reserved(source,name):
    no_block=re.sub(r'/\*.*?\*/',' ',source,flags=re.S)
    no_line=re.sub(r'//.*',' ',no_block)
    decl=re.compile(r'\b(?:float|double|int|uint|bool|vec[234]|ivec[234]|uvec[234]|bvec[234]|dvec[234]|mat[234])\s+([A-Za-z_]\w*)\b')
    for m in decl.finditer(no_line):
        if m.group(1) in RESERVED: fail(f'GLSL reserved identifier {m.group(1)} in {name}')
def compile_shader(validator,name,stage,src):
    reject_reserved(src,name)
    required = '#version 310 es' if stage=='comp' else '#version 300 es'
    if required not in src: fail(name+' missing '+required)
    with tempfile.TemporaryDirectory() as td:
        suffix='.comp' if stage=='comp' else '.frag'
        p=Path(td)/(name+suffix); p.write_text(src)
        r=subprocess.run([validator,'-S',stage,str(p)],text=True,capture_output=True)
        if r.returncode: fail('glslang failed '+name+'\n'+r.stdout+r.stderr)
def superres(merge):
    a='uniform ivec2 uOutputSize;'
    b='uniform ivec2 uOutputSize;\nuniform float uReconstructionZoom;\nuniform float uLumaTemporalScale;'
    c='    vec2 referenceRaw = (vec2(outputPixel) + vec2(0.5)) *\n        vec2(uRawSize) / vec2(uOutputSize) - vec2(0.5);'
    d='    vec2 fullRaw = (vec2(outputPixel) + vec2(0.5)) *\n        vec2(uRawSize) / vec2(uOutputSize) - vec2(0.5);\n    vec2 rawCenter = (vec2(uRawSize) - vec2(1.0)) * 0.5;\n    vec2 referenceRaw = rawCenter + (fullRaw - rawCenter) / max(uReconstructionZoom, 1.0);'
    e='    frameWeight *= uGlobalFrameWeight;\n    vec2 directionMoment = greenDirectionMoment(anchor, targetGreen);\n    oColorAndRWeight = vec4(semanticSums * frameWeight, weights.r * frameWeight);\n    oGbWeights = vec4(\n        weights.gb * frameWeight,\n        directionMoment * weights.r * frameWeight\n    );'
    f='    frameWeight *= uGlobalFrameWeight;\n    float lumaFrameWeight = frameWeight * clamp(uLumaTemporalScale, 0.0, 1.0);\n    vec2 directionMoment = greenDirectionMoment(anchor, targetGreen);\n    oColorAndRWeight = vec4(\n        semanticSums.r * lumaFrameWeight,\n        semanticSums.g * frameWeight,\n        semanticSums.b * frameWeight,\n        weights.r * lumaFrameWeight\n    );\n    oGbWeights = vec4(\n        weights.gb * frameWeight,\n        directionMoment * weights.r * lumaFrameWeight\n    );'
    for old,new in ((a,b),(c,d),(e,f)):
        if old not in merge: fail('mergeRgbSuperRes source replacement anchor missing')
        merge=merge.replace(old,new,1)
    return merge
def run(root,validator=None):
    sp=root/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbShaders.kt'
    vg=root/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'
    for p in (sp,vg):
        if not p.is_file(): fail('missing '+str(p))
        balanced(p)
    sv=vals(sp); vv=vals(vg)
    frag_names=['rejection','findBlockTilesGatherEdges','bentoAdjustHighlightMask','mergeRgb','alignedRawClippingMask','convertAlignment']
    comp_names=['seed','localClamp','localMedian','directionalSmooth','restoreDirection','iirRgb','calculateError','iirError','blendChroma','finalCameraRgb']
    missing=[x for x in frag_names if x not in sv]+[x for x in comp_names if x not in vv]
    if missing: fail('missing active shader(s): '+repr(missing))
    sources=[]
    for name in frag_names: sources.append(('spatial_'+name,'frag',expand(sv[name],sv)))
    sources.append(('spatial_mergeRgbSuperRes','frag',superres(expand(sv['mergeRgb'],sv))))
    # This unchanged shader becomes active in Sabre V1.3's optional RGBA16F export, so compile it too.
    sources.append(('spatial_copyRgb16ToFloat','comp',expand(sv['copyRgb16ToFloat'],sv)))
    for name in comp_names: sources.append(('vgn_'+name,'comp',expand(vv[name],vv)))
    by={n:s for n,_,s in sources}
    contracts={
      'spatial_rejection':['mirrorUv(uv + flow.xy)','uRejectionSize'],
      'spatial_mergeRgb':['cancelInterpolation','clampRawPixelToPhase','nativeValue - localGreen'],
      'spatial_mergeRgbSuperRes':['cancelInterpolation','uReconstructionZoom','lumaFrameWeight'],
      'spatial_alignedRawClippingMask':['outputPixel * 4 + ivec2(2)','uFlowScaleOffset'],
      'spatial_convertAlignment':['ivec2 tile = ivec2(gl_FragCoord.xy)','localFlowVariation'],
      'vgn_seed':['float rgbGradient','count << 8'],
      'vgn_finalCameraRgb':['/max(uCalculationGains,vec3(1e-6))'],
    }
    for name,toks in contracts.items():
        for t in toks:
            if t not in by[name]: fail(name+' contract missing '+t)
    for name,stage,src in sources: reject_reserved(src,name)
    if validator:
        for name,stage,src in sources: compile_shader(validator,name,stage,src)
        print(f'PASS: REAL GLSL COMPILE {len(sources)} V1.3 active/changed shaders via {validator}')
    print(f'PASS: 26545 V1.3 GLSL extraction/contracts shaders={len(sources)}')
def self_test():
    reject_reserved('float f(vec3 precisionCoeffs){ return precisionCoeffs.x; }','good')
    try: reject_reserved('float f(vec3 precision){ return precision.x; }','bad')
    except SystemExit: pass
    else: raise AssertionError('reserved identifier self-test did not fail')
    assert expand('#version 300 es\n$body',{'body':'void main(){}\n'}).endswith('void main(){}')
    print('PASS: 26545 V1.3 GLSL preflight self-test')
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--root'); ap.add_argument('--validator'); ap.add_argument('--self-test',action='store_true'); a=ap.parse_args()
    if a.self_test: self_test()
    else:
        if not a.root: ap.error('--root required')
        run(Path(a.root),a.validator)
