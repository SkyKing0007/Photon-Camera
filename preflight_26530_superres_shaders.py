#!/usr/bin/env python3
import argparse,re,subprocess,tempfile
from pathlib import Path

def extract(text,name):
    m=re.search(r'val\s+'+re.escape(name)+r'\s*=\s*"""(.*?)"""\.trimIndent\(\)',text,re.S)
    if not m: raise SystemExit('FAIL: cannot extract '+name)
    return m.group(1)

def sr_merge(base):
    pairs=[
      ('uniform ivec2 uOutputSize;','uniform ivec2 uOutputSize;\nuniform float uReconstructionZoom;\nuniform float uLumaTemporalScale;'),
      ('vec2 referenceRaw = (vec2(outputPixel) + vec2(0.5)) *\n                vec2(uRawSize) / vec2(uOutputSize) - vec2(0.5);','vec2 fullRaw = (vec2(outputPixel) + vec2(0.5)) *\n                vec2(uRawSize) / vec2(uOutputSize) - vec2(0.5);\n            vec2 rawCenter = (vec2(uRawSize) - vec2(1.0)) * 0.5;\n            vec2 referenceRaw = rawCenter + (fullRaw - rawCenter) / max(uReconstructionZoom, 1.0);'),
      ('frameWeight *= uGlobalFrameWeight;\n            vec2 directionMoment = greenDirectionMoment(anchor, targetGreen);\n            oColorAndRWeight = vec4(semanticSums * frameWeight, weights.r * frameWeight);\n            oGbWeights = vec4(\n                weights.gb * frameWeight,\n                directionMoment * weights.r * frameWeight\n            );','frameWeight *= uGlobalFrameWeight;\n            float lumaFrameWeight = frameWeight * clamp(uLumaTemporalScale, 0.0, 1.0);\n            vec2 directionMoment = greenDirectionMoment(anchor, targetGreen);\n            oColorAndRWeight = vec4(\n                semanticSums.r * lumaFrameWeight,\n                semanticSums.g * frameWeight,\n                semanticSums.b * frameWeight,\n                weights.r * lumaFrameWeight\n            );\n            oGbWeights = vec4(\n                weights.gb * frameWeight,\n                directionMoment * weights.r * lumaFrameWeight\n            );')]
    for old,new in pairs:
        if base.count(old)!=1: raise SystemExit('FAIL: SR merge replacement anchor drift')
        base=base.replace(old,new,1)
    return base

def sr_norm(base):
    pairs=[
      ('uniform ivec2 uOutputSize;','uniform ivec2 uOutputSize;\nuniform ivec2 uRawSize;\nuniform float uReconstructionZoom;'),
      ('vec2 uv = (vec2(outputPixel) + vec2(0.5)) / vec2(uOutputSize);','vec2 fullRaw = (vec2(outputPixel) + vec2(0.5)) * vec2(uRawSize) / vec2(uOutputSize) - vec2(0.5);\n                vec2 rawCenter = (vec2(uRawSize) - vec2(1.0)) * 0.5;\n                vec2 referenceRaw = rawCenter + (fullRaw - rawCenter) / max(uReconstructionZoom, 1.0);\n                vec2 uv = (referenceRaw + vec2(0.5)) / vec2(uRawSize);')]
    for old,new in pairs:
        if base.count(old)!=1: raise SystemExit('FAIL: SR normalize replacement anchor drift')
        base=base.replace(old,new,1)
    return base

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',required=True); ap.add_argument('--validator',default='glslangValidator'); a=ap.parse_args()
    p=Path(a.root)/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbShaders.kt'; t=p.read_text()
    legacy_merge=extract(t,'mergeRgb'); legacy_norm=extract(t,'normalizeRgb16')
    shaders={'legacy_merge':legacy_merge,'superres_merge':sr_merge(legacy_merge),'legacy_normalize':legacy_norm,'superres_normalize':sr_norm(legacy_norm)}
    required={'superres_merge':['uReconstructionZoom','uLumaTemporalScale','semanticSums.r * lumaFrameWeight','semanticSums.g * frameWeight','semanticSums.b * frameWeight'],'superres_normalize':['uRawSize','uReconstructionZoom','referenceRaw + vec2(0.5)']}
    for name,toks in required.items():
        for tok in toks:
            if tok not in shaders[name]: raise SystemExit(f'FAIL: {name} missing {tok}')
    with tempfile.TemporaryDirectory(prefix='iris26530_glsl_') as td:
        for name,src in shaders.items():
            q=Path(td)/(name+'.frag'); q.write_text(src+'\n')
            cp=subprocess.run([a.validator,'-S','frag',str(q)],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            if cp.returncode:
                print(cp.stdout); raise SystemExit('FAIL: GLSL compile '+name)
            print('PASS: GLSL '+name)
    print('PASS: 26530 legacy + high-zoom shader preflight')
if __name__=='__main__': main()
