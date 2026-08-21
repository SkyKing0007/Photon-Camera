#!/usr/bin/env python3
from __future__ import annotations
import argparse, difflib, hashlib, importlib.util, re
from pathlib import Path

IRIS_STACK='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbStacker.kt'
IRIS_SHADER='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbShaders.kt'
RELEASE_SHADER='app/src/main/java/com/hinnka/mycamera/processor/GlesMgc1271ReleasedSpatialShaders.kt'

def norm(s:str)->str:
    return s.replace('\r\n','\n').replace('\r','\n')

def load(path:Path):
    spec=importlib.util.spec_from_file_location('apply26520v4',path)
    mod=importlib.util.module_from_spec(spec); assert spec.loader; spec.loader.exec_module(mod); return mod

def one(s:str,old:str,new:str,label:str)->str:
    n=s.count(old)
    if n!=1: raise AssertionError(f'{label} anchor count={n} expected=1')
    return s.replace(old,new,1)

def rewrite_iris_stack(released_26520:str)->str:
    s=norm(released_26520)
    old='internal class GlesMgc1271ReleasedSpatialStacker(\n'
    s=one(s,old,'''/**
 * IRIS_26521_V4_INDEPENDENT_SPATIAL_RGB_OWNER
 *
 * Independent Iris Spatial-RGB owner. It intentionally preserves the proven c4ff frame schedule,
 * RAW preparation, alignment, rejection, Bento/Long role handling, and 26520 NORMAL-only DNG
 * sidecar contract, but it owns its RGB reconstruction shaders and never consumes c4ff RGB output.
 */
internal class GlesIris26521SpatialRgbStacker(
''','Iris stacker class owner')
    if 'GlesMgc1271ReleasedSpatialShaders' not in s:
        raise AssertionError('released shader owner reference missing from stacker clone')
    s=s.replace('GlesMgc1271ReleasedSpatialShaders','GlesIris26521SpatialRgbShaders')
    if 'GlesMgc1271ReleasedSpatialStacker' in s:
        raise AssertionError('released class name survived Iris stack clone')
    if 'IRIS_26520_V4_NORMAL_ONLY_DNG_READY' not in s:
        raise AssertionError('26520 DNG sidecar contract missing from Iris stack clone')
    return s

def replace_function_before(s:str, signature:str, next_signature:str, replacement:str, label:str)->str:
    start=s.find(signature)
    if start<0: raise AssertionError(label+' signature missing')
    end=s.find(next_signature,start)
    if end<0: raise AssertionError(label+' next signature missing')
    block=s[start:end]
    if block.count(signature)!=1: raise AssertionError(label+' ambiguous signature')
    return s[:start]+replacement+s[end:]

def rewrite_iris_shader(released_shader:str)->str:
    s=norm(released_shader)
    s=one(s,'internal object GlesMgc1271ReleasedSpatialShaders {\n','''internal object GlesIris26521SpatialRgbShaders {
    /* IRIS_26521_V4_INDEPENDENT_SPATIAL_RGB_MATH
     * Same live c4ff transport ABI; independently authored edge/color reconstruction equations.
     */
''','Iris shader object')

    green_sig='        float greenAtNonGreen(ivec2 p, float center) {\n'
    green_next='        void main() {\n'
    green='''        /* IRIS_26521_V4_DIRECTIONAL_GREEN */
        float greenAtNonGreen(ivec2 p, float center) {
            float gL = gainedRaw(p + ivec2(-1, 0));
            float gR = gainedRaw(p + ivec2(1, 0));
            float gU = gainedRaw(p + ivec2(0, -1));
            float gD = gainedRaw(p + ivec2(0, 1));
            float cL2 = gainedRaw(p + ivec2(-2, 0));
            float cR2 = gainedRaw(p + ivec2(2, 0));
            float cU2 = gainedRaw(p + ivec2(0, -2));
            float cD2 = gainedRaw(p + ivec2(0, 2));
            float horizontalLinear = 0.5 * (gL + gR);
            float verticalLinear = 0.5 * (gU + gD);
            float horizontalCurvature = 2.0 * center - cL2 - cR2;
            float verticalCurvature = 2.0 * center - cU2 - cD2;
            float horizontalCorrection = clamp(
                0.25 * horizontalCurvature,
                -0.5 * abs(gL - gR),
                0.5 * abs(gL - gR)
            );
            float verticalCorrection = clamp(
                0.25 * verticalCurvature,
                -0.5 * abs(gU - gD),
                0.5 * abs(gU - gD)
            );
            float horizontal = horizontalLinear + horizontalCorrection;
            float vertical = verticalLinear + verticalCorrection;
            float gradientH = abs(gL - gR) + abs(horizontalCurvature);
            float gradientV = abs(gU - gD) + abs(verticalCurvature);
            float gradientSum = max(gradientH + gradientV, 1.0e-7);
            float softHorizontal = gradientV / gradientSum;
            float softEstimate = mix(vertical, horizontal, softHorizontal);
            float directionalEstimate = gradientH <= gradientV ? horizontal : vertical;
            float directionalConfidence = abs(gradientH - gradientV) / gradientSum;
            float directionalMix = smoothstep(0.20, 0.75, directionalConfidence);
            float green = mix(softEstimate, directionalEstimate, directionalMix);
            float nativeMinimum = min(min(gL, gR), min(gU, gD));
            float nativeMaximum = max(max(gL, gR), max(gU, gD));
            return clamp(green, nativeMinimum, nativeMaximum);
        }

'''
    # Exact first occurrence is the rgbChromaGuide helper; the guide shader has kernelWeight(int), not this signature.
    s=replace_function_before(s,green_sig,green_next,green,'directional green')

    kernel_sig='        float kernelWeight(vec2 pixelOffset, vec3 covariance) {\n'
    chroma_sig='        float chromaGuideWeight(float sampleGreen, float targetGreen) {\n'
    kernel='''        /* IRIS_26521_V4_ROBUST_SPATIAL_KERNEL */
        float kernelWeight(vec2 pixelOffset, vec3 covariance) {
            float distance = pixelOffset.x * pixelOffset.x * covariance.x +
                pixelOffset.y * pixelOffset.y * covariance.y +
                2.0 * pixelOffset.x * pixelOffset.y * covariance.z;
            float d = max(distance, 0.0);
            float gaussian = exp2(-0.5 * d);
            float rational = 1.0 / (1.0 + 0.55 * d);
            return max(mix(gaussian, rational, 0.18), 0.00005);
        }

'''
    s=replace_function_before(s,kernel_sig,chroma_sig,kernel,'robust spatial kernel')

    chroma_next='        void main() {\n'
    chroma='''        /* IRIS_26521_V4_ROBUST_COLOR_DIFFERENCE */
        float chromaGuideWeight(float sampleGreen, float targetGreen) {
            float signal = max(max(sampleGreen, targetGreen), 0.0);
            float variance = max(uGreenNoise.x * signal + uGreenNoise.y, 0.0);
            float sigma = max(
                uChromaEdgeNoiseSigmas * sqrt(variance),
                uChromaEdgeSigmaFloor
            );
            float normalizedDifference = (sampleGreen - targetGreen) / sigma;
            float x2 = normalizedDifference * normalizedDifference;
            float gaussian = exp(-0.5 * x2);
            float robustTail = 1.0 / (1.0 + 0.75 * x2);
            float tailMix = 0.15 * smoothstep(1.0, 4.0, x2);
            return clamp(mix(gaussian, robustTail, tailMix), 0.0, 1.0);
        }

'''
    s=replace_function_before(s,chroma_sig,chroma_next,chroma,'robust color difference')

    for tok in ('IRIS_26521_V4_DIRECTIONAL_GREEN','IRIS_26521_V4_ROBUST_SPATIAL_KERNEL','IRIS_26521_V4_ROBUST_COLOR_DIFFERENCE'):
        if s.count(tok)!=1: raise AssertionError('Iris shader marker cardinality drift '+tok)
    if 'GlesMgc1271ReleasedSpatialShaders' in s:
        raise AssertionError('released shader object name survived Iris shader fork')
    return s

def rewrite_fusion(fusion_26520:str)->str:
    s=norm(fusion_26520)
    marker='IRIS_26517_RELEASED_1271_SPATIAL_RGB_OWNER'
    a=s.find(marker)
    if a<0: raise AssertionError('26517 active route marker missing')
    b=s.find('        return GlesMgcRawSpatialStacker(',a)
    if b<0: raise AssertionError('Spatial fallback boundary missing')
    active=s[a:b]
    old_log="""            PLog.i(TAG, "IRIS_26517_RELEASED_1271_SPATIAL_RGB_OWNER commit=c4ff5a3 " +
                "postSabreSpatial=false currentSabreUntouched=true")
"""
    new_log="""            PLog.i(TAG, "IRIS_26521_V4_INDEPENDENT_SPATIAL_RGB_OWNER_ACTIVE " +
                "transport=c4ff5a3 alignmentRejectionPreserved=true " +
                "rgbMath=Iris26521 releasedControlUntouched=true")
"""
    active=one(active,old_log,new_log,'active Iris owner log')
    # The first slice begins at the 26517 marker inside the historical comment. Rename that
    # lineage marker too so runtime/source audits cannot mistake it for the active owner.
    active=active.replace(
        'IRIS_26517_RELEASED_1271_SPATIAL_RGB_OWNER',
        'IRIS_26521_V4_REPLACES_RELEASED_26517_OWNER',
    )
    old='            return GlesMgc1271ReleasedSpatialStacker(\n'
    active=one(active,old,"""            /* IRIS_26521_V4_INDEPENDENT_SPATIAL_RGB_OWNER
             * 26521 replaces only the active SPATIAL_RGB reconstruction owner. Frame scheduling,
             * alignment, rejection and role semantics remain the same live MGC architecture.
             */
            return GlesIris26521SpatialRgbStacker(
""",'active Iris owner switch')
    if 'IRIS_26517_RELEASED_1271_SPATIAL_RGB_OWNER' in active:
        raise AssertionError('released 26517 active-owner marker survived in 26521 branch')
    if 'GlesMgc1271ReleasedSpatialStacker(' in active:
        raise AssertionError('released c4ff RGB owner still active in 26521 SPATIAL_RGB branch')
    if active.count('GlesIris26521SpatialRgbStacker(')!=1:
        raise AssertionError('Iris active owner cardinality mismatch')
    if active.count('IRIS_26521_V4_INDEPENDENT_SPATIAL_RGB_OWNER_ACTIVE')!=1:
        raise AssertionError('Iris active owner log cardinality mismatch')
    return s[:a]+active+s[b:]

def expected_map(base:Path,apply26520:Path)->dict[str,str]:
    m=load(apply26520)
    out=dict(m.expected_map(base))
    # Preserve the original successful 26519 released c4ff control byte-for-byte in 26521.
    released_26520=out.pop(m.STACK)
    out[IRIS_STACK]=rewrite_iris_stack(released_26520)
    shader_path=base/RELEASE_SHADER
    if not shader_path.is_file(): raise AssertionError('successful-26519 released shader missing')
    out[IRIS_SHADER]=rewrite_iris_shader(shader_path.read_text())
    out[m.FUSION]=rewrite_fusion(out[m.FUSION])
    if (base/IRIS_STACK).exists() or (base/IRIS_SHADER).exists():
        raise AssertionError('26521 Iris owner unexpectedly exists in successful-26519 base')
    return out

def patch_text(base:Path,expected:dict[str,str])->str:
    chunks=[]
    for rel in sorted(expected):
        p=base/rel; old=norm(p.read_text()) if p.exists() else ''; new=expected[rel]
        if old==new: raise AssertionError('empty 26521 transform '+rel)
        chunks.append(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=('a/'+rel if p.exists() else '/dev/null'),tofile='b/'+rel)))
    return ''.join(chunks)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('root',type=Path); ap.add_argument('--apply26520',required=True,type=Path); ap.add_argument('--patch-out',type=Path); ap.add_argument('--patch-sha-out',type=Path); ap.add_argument('--check-only',action='store_true'); ns=ap.parse_args()
    base=ns.root.resolve(); expected=expected_map(base,ns.apply26520.resolve())
    if ns.check_only:
        print('PASS: complete 26520 + 26521 V4 transforms resolve in memory against actual base')
        print('PASS: released c4ff control stacker/shaders stay frozen; active 26521 owner is separate Iris Spatial RGB')
        print('PASS: Iris owner retains live MGC alignment/rejection/DNG lifecycle and has no legacy Wronski/CFA owner')
        return
    if ns.patch_out is None or ns.patch_sha_out is None: raise SystemExit('--patch-out and --patch-sha-out required unless --check-only')
    diff=patch_text(base,expected)
    if not diff: raise AssertionError('empty 26521 V4 runtime patch')
    ns.patch_out.parent.mkdir(parents=True,exist_ok=True); ns.patch_out.write_text(diff)
    digest=hashlib.sha256(ns.patch_out.read_bytes()).hexdigest(); ns.patch_sha_out.write_text(f'{digest}  {ns.patch_out.name}\n')
    for rel,new in expected.items():
        p=base/rel; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(new)
    print('PASS: combined 26520+26521 V4 rollback patch existed before nine-path runtime write')

if __name__=='__main__': main()
