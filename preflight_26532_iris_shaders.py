#!/usr/bin/env python3
from pathlib import Path
import argparse,re,subprocess,tempfile,sys,textwrap

SH='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbShaders.kt'
PP='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'

def need(x,msg):
    if not x: raise RuntimeError(msg)
def triple(text,name,require_version=True):
    m=re.search(r'\b(?:private\s+)?val\s+'+re.escape(name)+r'\s*=\s*"""(.*?)"""(?:\.trimIndent\(\))?',text,re.S)
    need(m is not None,'missing shader '+name)
    s=textwrap.dedent(m.group(1)).strip()+"\n"
    if require_version: need(s.startswith('#version '),name+' #version is not first byte')
    return s
def rep(s,a,b,label):
    need(s.count(a)==1,f'{label} anchor count={s.count(a)}')
    return s.replace(a,b,1)
def merge_sr(base):
    base=rep(base,'uniform ivec2 uOutputSize;','uniform ivec2 uOutputSize;\nuniform float uReconstructionZoom;\nuniform float uLumaTemporalScale;','merge uniforms')
    base=rep(base,
      '    vec2 referenceRaw = (vec2(outputPixel) + vec2(0.5)) *\n        vec2(uRawSize) / vec2(uOutputSize) - vec2(0.5);',
      '    vec2 fullRaw = (vec2(outputPixel) + vec2(0.5)) *\n        vec2(uRawSize) / vec2(uOutputSize) - vec2(0.5);\n    vec2 rawCenter = (vec2(uRawSize) - vec2(1.0)) * 0.5;\n    vec2 referenceRaw = rawCenter + (fullRaw - rawCenter) / max(uReconstructionZoom, 1.0);','merge crop geometry')
    base=rep(base,
      '    frameWeight *= uGlobalFrameWeight;\n    frameWeight *= clamp(flowAndConfidence.z, 0.0, 1.0);\n    vec2 directionMoment = greenDirectionMoment(anchor, targetGreen);\n    oColorAndRWeight = vec4(semanticSums * frameWeight, weights.r * frameWeight);\n    oGbWeights = vec4(\n        weights.gb * frameWeight,\n        directionMoment * weights.r * frameWeight\n    );',
      '    frameWeight *= uGlobalFrameWeight;\n    frameWeight *= clamp(flowAndConfidence.z, 0.0, 1.0);\n    float lumaFrameWeight = frameWeight * clamp(uLumaTemporalScale, 0.0, 1.0);\n    vec2 directionMoment = greenDirectionMoment(anchor, targetGreen);\n    oColorAndRWeight = vec4(\n        semanticSums.r * lumaFrameWeight,\n        semanticSums.g * frameWeight,\n        semanticSums.b * frameWeight,\n        weights.r * lumaFrameWeight\n    );\n    oGbWeights = vec4(\n        weights.gb * frameWeight,\n        directionMoment * weights.r * lumaFrameWeight\n    );','merge luma/chroma weights')
    return base
def norm_sr(base):
    base=rep(base,'uniform ivec2 uOutputSize;','uniform ivec2 uOutputSize;\nuniform ivec2 uRawSize;\nuniform float uReconstructionZoom;','norm uniforms')
    base=rep(base,'vec2 uv = (vec2(outputPixel) + vec2(0.5)) / vec2(uOutputSize);',
      'vec2 fullRaw = (vec2(outputPixel) + vec2(0.5)) * vec2(uRawSize) / vec2(uOutputSize) - vec2(0.5);\n                vec2 rawCenter = (vec2(uRawSize) - vec2(1.0)) * 0.5;\n                vec2 referenceRaw = rawCenter + (fullRaw - rawCenter) / max(uReconstructionZoom, 1.0);\n                vec2 uv = (referenceRaw + vec2(0.5)) / vec2(uRawSize);','norm sensor LSC')
    return base
def compile_one(v,name,s,stage):
    with tempfile.TemporaryDirectory(prefix='iris26532_glsl_') as td:
        ext='comp' if stage=='comp' else 'frag'; p=Path(td)/(name+'.'+ext); p.write_text(s)
        r=subprocess.run([v,'-S',stage,str(p)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        if r.returncode: raise RuntimeError(name+' GLSL failed:\n'+r.stdout)
        print('PASS: GLSL',name)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',required=True); ap.add_argument('--validator',default='glslangValidator'); a=ap.parse_args()
    root=Path(a.root); sh=(root/SH).read_text(); pp=(root/PP).read_text()
    base_merge=triple(sh,'mergeRgb'); base_norm=triple(sh,'normalizeRgb16')
    shaders={
      'rejection_real_support':(triple(sh,'rejection'),'frag'),
      'merge_rgb':(base_merge,'frag'),
      'merge_rgb_superres20':(merge_sr(base_merge),'frag'),
      'normalize_rgb16':(base_norm,'frag'),
      'normalize_rgb16_superres20':(norm_sr(base_norm),'frag'),
      'downsample_2x_to_native':(triple(sh,'downsampleRgb16SuperRes2x'),'frag'),
      'strength_alignment':(triple(sh,'strengthAlignment'),'frag'),
    }
    common=triple(pp,'common',False).rstrip()
    for n in ('seed','localClamp','localMedian','directionalSmooth','restoreDirection','iirRgb','calculateError','iirError','blendChroma','finalCameraRgb'):
        shaders['chroma_'+n]=(triple(pp,n).replace('$common',common),'comp')
    # New architecture must be present in the actual compiled strings.
    ms=shaders['merge_rgb_superres20'][0]
    for tok in ('uReconstructionZoom','uLumaTemporalScale','flowAndConfidence.z','rawInside(p)','referenceRaw = rawCenter'):
        need(tok in ms,'SR merge missing '+tok)
    rej=shaders['rejection_real_support'][0]
    need('IRIS_26532_REJECTION_REAL_SENSOR_SUPPORT' in rej,'rejection physical support missing')
    seed=shaders['chroma_seed'][0]
    need('directionMomentAt' in seed and 'structureScale' in seed,'foliage structure guidance missing')
    for n,tok in [('chroma_localMedian','IRIS_26532_FOLIAGE_LOCAL_MEDIAN_EDGE_GATE'),('chroma_directionalSmooth','IRIS_26532_NO_EDGE_DESATURATION'),('chroma_iirRgb','IRIS_26532_IIR_CHROMA_EDGE_RESET'),('chroma_blendChroma','IRIS_26532_BLEND_EDGE_CHROMA_PROTECT')]:
        need(tok in shaders[n][0],n+' missing edge gate')
    for name,(src,stage) in shaders.items(): compile_one(a.validator,name,src,stage)
    print('PASS: 26532 Spatial/SR/pink/foliage shaders compile and contract markers are active')
if __name__=='__main__':
    try: main()
    except Exception as e: print('ERROR:',e,file=sys.stderr); sys.exit(2)
