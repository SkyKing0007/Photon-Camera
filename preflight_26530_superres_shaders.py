#!/usr/bin/env python3
from __future__ import annotations
import argparse,re,subprocess,tempfile,sys
from pathlib import Path

SHADER_REL='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbShaders.kt'

def extract(text,name):
    m=re.search(r'\b(?:private\s+)?val\s+'+re.escape(name)+r'\s*=\s*"""(.*?)"""(?:\.trimIndent\(\))?',text,re.S)
    if not m:
        raise RuntimeError('missing shader string '+name)
    # Match the successful 26529 embedded-shader procedure: Kotlin formatting
    # whitespace is not GLSL source. #version must be the first emitted token.
    s=m.group(1).strip()+"\n"
    if not s.startswith('#version '):
        raise RuntimeError(f'{name}: canonicalized shader does not start with #version')
    if s.splitlines()[0].strip() not in ('#version 310 es','#version 300 es'):
        raise RuntimeError(f'{name}: unexpected GLSL version line {s.splitlines()[0]!r}')
    return s

def replace_once(base,old,new,label):
    if base.count(old)!=1:
        raise RuntimeError(f'{label}: replacement anchor count={base.count(old)}')
    return base.replace(old,new,1)

def sr_merge(base):
    base=replace_once(base,
      'uniform ivec2 uOutputSize;',
      'uniform ivec2 uOutputSize;\nuniform float uReconstructionZoom;\nuniform float uLumaTemporalScale;',
      'SR merge uniforms')
    base=replace_once(base,
      'vec2 referenceRaw = (vec2(outputPixel) + vec2(0.5)) *\n                vec2(uRawSize) / vec2(uOutputSize) - vec2(0.5);',
      'vec2 fullRaw = (vec2(outputPixel) + vec2(0.5)) *\n                vec2(uRawSize) / vec2(uOutputSize) - vec2(0.5);\n            vec2 rawCenter = (vec2(uRawSize) - vec2(1.0)) * 0.5;\n            vec2 referenceRaw = rawCenter + (fullRaw - rawCenter) / max(uReconstructionZoom, 1.0);',
      'SR merge geometry')
    base=replace_once(base,
      'frameWeight *= uGlobalFrameWeight;\n            vec2 directionMoment = greenDirectionMoment(anchor, targetGreen);\n            oColorAndRWeight = vec4(semanticSums * frameWeight, weights.r * frameWeight);\n            oGbWeights = vec4(\n                weights.gb * frameWeight,\n                directionMoment * weights.r * frameWeight\n            );',
      'frameWeight *= uGlobalFrameWeight;\n            float lumaFrameWeight = frameWeight * clamp(uLumaTemporalScale, 0.0, 1.0);\n            vec2 directionMoment = greenDirectionMoment(anchor, targetGreen);\n            oColorAndRWeight = vec4(\n                semanticSums.r * lumaFrameWeight,\n                semanticSums.g * frameWeight,\n                semanticSums.b * frameWeight,\n                weights.r * lumaFrameWeight\n            );\n            oGbWeights = vec4(\n                weights.gb * frameWeight,\n                directionMoment * weights.r * lumaFrameWeight\n            );',
      'SR merge luma/chroma weighting')
    return base

def sr_norm(base):
    base=replace_once(base,
      'uniform ivec2 uOutputSize;',
      'uniform ivec2 uOutputSize;\nuniform ivec2 uRawSize;\nuniform float uReconstructionZoom;',
      'SR normalize uniforms')
    base=replace_once(base,
      'vec2 uv = (vec2(outputPixel) + vec2(0.5)) / vec2(uOutputSize);',
      'vec2 fullRaw = (vec2(outputPixel) + vec2(0.5)) * vec2(uRawSize) / vec2(uOutputSize) - vec2(0.5);\n                vec2 rawCenter = (vec2(uRawSize) - vec2(1.0)) * 0.5;\n                vec2 referenceRaw = rawCenter + (fullRaw - rawCenter) / max(uReconstructionZoom, 1.0);\n                vec2 uv = (referenceRaw + vec2(0.5)) / vec2(uRawSize);',
      'SR normalize sensor-coordinate LSC')
    return base

def compile_one(validator,name,source):
    if not source.startswith('#version '):
        raise RuntimeError(f'{name}: #version is not first byte before glslang')
    with tempfile.TemporaryDirectory(prefix='iris26530_glsl_') as td:
        p=Path(td)/(name+'.frag')
        p.write_text(source)
        r=subprocess.run([validator,'-S','frag',str(p)],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        if r.returncode!=0:
            raise RuntimeError(f'{name} failed:\n{r.stdout}')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',required=True); ap.add_argument('--validator',default='glslangValidator'); a=ap.parse_args()
    text=(Path(a.root)/SHADER_REL).read_text()
    legacy_merge=extract(text,'mergeRgb')
    legacy_norm=extract(text,'normalizeRgb16')
    shaders={
      'legacy_merge':legacy_merge,
      'superres_merge':sr_merge(legacy_merge),
      'legacy_normalize':legacy_norm,
      'superres_normalize':sr_norm(legacy_norm),
    }
    required={
      'superres_merge':['uReconstructionZoom','uLumaTemporalScale','semanticSums.r * lumaFrameWeight','semanticSums.g * frameWeight','semanticSums.b * frameWeight'],
      'superres_normalize':['uRawSize','uReconstructionZoom','referenceRaw + vec2(0.5)'],
    }
    for name,toks in required.items():
        for tok in toks:
            if tok not in shaders[name]:
                raise RuntimeError(f'{name}: missing {tok}')
    for name,source in shaders.items():
        compile_one(a.validator,name,source)
        print('PASS: GLSL '+name)
    print('PASS: 26530 legacy + high-zoom shader preflight')

if __name__=='__main__':
    try: main()
    except Exception as e:
        print('ERROR:',e,file=sys.stderr)
        sys.exit(2)
