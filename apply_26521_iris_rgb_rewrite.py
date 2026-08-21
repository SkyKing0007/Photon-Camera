#!/usr/bin/env python3
from __future__ import annotations
import argparse, difflib, hashlib, importlib.util
from pathlib import Path

CFA='app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2CfaReconstruction.java'
SHADER='app/src/main/assets/shaders/motionv2/iris_fused_bayer_rgb_26521.glsl'

def norm(s:str)->str:
    return s.replace('\r\n','\n').replace('\r','\n')

def load_module(path:Path):
    spec=importlib.util.spec_from_file_location('apply26520',path)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def one(s:str, old:str, new:str, label:str)->str:
    n=s.count(old)
    if n != 1:
        raise AssertionError(f'{label} anchor count={n}')
    return s.replace(old,new,1)

def replace_between(s:str,start:str,end:str,replacement:str,label:str)->str:
    a=s.find(start)
    if a<0: raise AssertionError(label+' start missing')
    b=s.find(end,a)
    if b<0: raise AssertionError(label+' end missing')
    return s[:a]+replacement+s[b:]

def remove_call_after(s:str,name:str,start_at:int):
    token=name+'('
    pos=s.find(token,start_at)
    removed=0
    while pos>=0:
        line_start=s.rfind('\n',0,pos)+1
        prefix=s[line_start:pos]
        if 'private static' in prefix or 'public static' in prefix:
            pos=s.find(token,pos+len(token))
            continue
        depth=0
        i=pos+len(name)
        saw=False
        while i<len(s):
            c=s[i]
            if c=='(':
                depth+=1; saw=True
            elif c==')':
                depth-=1
                if saw and depth==0:
                    j=i+1
                    while j<len(s) and s[j] in ' \t': j+=1
                    if j<len(s) and s[j]==';': j+=1
                    while j<len(s) and s[j] in ' \t': j+=1
                    if j<len(s) and s[j]=='\n': j+=1
                    s=s[:line_start]+s[j:]
                    removed+=1
                    start_at=line_start
                    break
            i+=1
        else:
            raise AssertionError('unterminated call '+name)
        pos=s.find(token,start_at)
    return s,removed

def replace_final_direct_bayer_block(s:str)->str:
    marker='                    /* IRIS_26501_PROPER_SPATIAL_RGB_FINAL_NORMALIZATION'
    m=s.find(marker)
    if m<0: raise AssertionError('old final RGB marker missing')
    start=s.rfind('                if (directBayer) {',0,m)
    if start<0: raise AssertionError('old final RGB if missing')
    brace=s.find('{',start)
    depth=0
    end=-1
    for i in range(brace,len(s)):
        if s[i]=='{': depth+=1
        elif s[i]=='}':
            depth-=1
            if depth==0:
                end=i+1
                break
    if end<0: raise AssertionError('old final RGB block unterminated')
    next_marker=s.find(
        '                /* IRIS_26488_TINY_DIAGNOSTICS_BEFORE_SINGLE_GPU_DRAIN',
        end)
    if next_marker<0: raise AssertionError('post RGB diagnostic marker missing')
    if s[end:next_marker].strip():
        raise AssertionError('unexpected text after old final RGB block')

    new=r'''                if (directBayer) {
                    /* IRIS_26521_INDEPENDENT_IRIS_RGB_OWNER
                     *
                     * Wronski still owns alignment/rejection and the persistent Bayer
                     * accumulator. RGB is reconstructed from that fused Bayer carrier
                     * with independently authored edge-directed color-difference math.
                     */
                    if (iris26480ReadbackOutput == null) {
                        throw new IllegalStateException(
                                "26521 Iris RGB owner missing fused Bayer carrier");
                    }

                    boolean iris26521HasLsc = parameters.hasGainMap
                            && parameters.mapSize != null
                            && parameters.mapSize.x > 0
                            && parameters.mapSize.y > 0
                            && parameters.gainMap != null
                            && parameters.gainMap.length
                                    >= parameters.mapSize.x
                                            * parameters.mapSize.y * 4;
                    Point iris26521LscSize = iris26521HasLsc
                            ? new Point(parameters.mapSize)
                            : new Point(1, 1);
                    float[] iris26521LscValues = iris26521HasLsc
                            ? parameters.gainMap
                            : new float[]{1f, 1f, 1f, 1f};
                    int iris26521LscFloatCount =
                            iris26521LscSize.x * iris26521LscSize.y * 4;
                    ByteBuffer iris26521LscUpload = ByteBuffer
                            .allocateDirect(iris26521LscFloatCount * Float.BYTES)
                            .order(ByteOrder.nativeOrder());
                    iris26521LscUpload.asFloatBuffer().put(
                            iris26521LscValues, 0, iris26521LscFloatCount);
                    iris26521LscUpload.position(0);
                    iris26521LensShading = new GLTexture(
                            iris26521LscSize,
                            new GLFormat(GLFormat.DataType.FLOAT_32, 4),
                            iris26521LscUpload,
                            GL_LINEAR,
                            GL_CLAMP_TO_EDGE);

                    iris26521RgbOutput = new GLTexture(
                            raw,
                            new GLFormat(GLFormat.DataType.FLOAT_16, 4),
                            null,
                            GL_NEAREST,
                            GL_CLAMP_TO_EDGE);
                    glProg.useAssetProgram(
                            "motionv2/iris_fused_bayer_rgb_26521");
                    glProg.setVar("rawSize", raw);
                    glProg.setVar("packedSize", rawHalf);
                    glProg.setVar("cfaPattern", (int) parameters.cfaPattern);
                    glProg.setVar(
                            "useLensShading", iris26521HasLsc ? 1 : 0);
                    glProg.setTexture(
                            "fusedCfa", iris26480ReadbackOutput);
                    glProg.setTexture(
                            "lensShadingMap", iris26521LensShading);
                    android.opengl.GLES30.glDisable(
                            android.opengl.GLES30.GL_BLEND);
                    iris26521RgbOutput.BufferLoad();
                    glProg.drawBlocks(raw.x, raw.y);
                    android.opengl.GLES30.glBindFramebuffer(
                            android.opengl.GLES30.GL_FRAMEBUFFER, 0);
                    iris26480ReadbackOutput = iris26521RgbOutput;

                    Log.i(TAG, "IRIS_26521_INDEPENDENT_IRIS_RGB_OWNER"
                            + " source=normalAlignedFusedBayer"
                            + " rgbMethod=edgeDirectedColorDifference"
                            + " directC4ffSpatialAccumulator=false"
                            + " c4ffOpponentColor=false"
                            + " c4ffCovarianceRgbKernel=false"
                            + " c4ffRgbConstants=false"
                            + " wronskiAlignmentPreserved=true"
                            + " wronskiBayerAccumulatorPreserved=true"
                            + " shortLongRemainSeparateBayerHdr=true"
                            + " dngBranchAlreadyFrozenBeforeRgb=true"
                            + " lensShadingAfterRgb=" + iris26521HasLsc
                            + " fullResolution=" + raw.x + "x" + raw.y);
                    try {
                        com.particlesdevs.photoncamera.util.MotionTrace
                                .processingState(
                                        "IRIS_26521_INDEPENDENT_IRIS_RGB_OWNER",
                                        "source=fusedBayer edgeDirected=true"
                                                + " c4ffActive=false"
                                                + " wronskiPreserved=true"
                                                + " lsc=" + iris26521HasLsc);
                    } catch (Throwable ignored) {}
                }
'''
    return s[:start]+new+s[next_marker:]

def rewrite_cfa(text:str)->str:
    s=norm(text)
    for tok in (
        'IRIS_26520_NORMAL_ONLY_FUSED_BAYER_DNG',
        'motionv2/dng_cfa_to_raw16_26520',
        'stackedDngRaw16Output',
    ):
        if tok not in s:
            raise AssertionError('26520 prerequisite missing: '+tok)

    decl='        GLTexture iris26501LensShading = null;\n'
    s=one(s,decl,decl+'''        /* IRIS_26521_INDEPENDENT_IRIS_RGB_OWNER */
        GLTexture iris26521RgbOutput = null;
        GLTexture iris26521LensShading = null;
''','new RGB declarations')

    s=replace_between(
        s,
        '                /* IRIS_26501_REFERENCE_SEMANTIC_CONTRIBUTION',
        '            /*\n             * IRIS_26440_REFERENCE_FIRST_TELEMETRY_INIT',
        '''                /* IRIS_26521_C4FF_RGB_REFERENCE_PATH_DISABLED
                 * RGB is deferred until the fused Bayer stack is complete.
                 */
                Log.i(TAG, "IRIS_26521_C4FF_RGB_REFERENCE_PATH_DISABLED"
                        + " activeRgbOwner=IrisFusedBayerRgb"
                        + " wronskiReferenceStillAuthoritative=true");
            }

''',
        'reference RGB block')

    run=s.find('    public void Run() {')
    if run<0: raise AssertionError('Run() missing')
    counts={}
    for name in (
        'iris26501RenderChromaGuide',
        'iris26501RenderRgbCovariance',
        'iris26501ContributeRgbFrame',
    ):
        s,n=remove_call_after(s,name,run)
        counts[name]=n
        run=s.find('    public void Run() {')
    if counts['iris26501ContributeRgbFrame'] < 2:
        raise AssertionError('not enough old RGB calls removed: '+str(counts))

    for line in (
        '                            iris26501SemanticContributedFrames++;\n',
        '                iris26501SemanticContributedFrames++;\n',
        '                        iris26501SemanticHdrContributedFrames++;\n',
        '                    iris26501SemanticHdrContributedFrames++;\n',
    ):
        s=s.replace(line,'')

    invariant_new=r'''            /* IRIS_26521_BAYER_ACCUMULATOR_INVARIANT */
            if (directBayer) {
                if (iris26489AdmittedFrames != iris26489ContributedFrames
                        || iris26489AdmittedFrames
                                != iris26489ExpectedAdmittedFrames) {
                    throw new IllegalStateException(
                            "IRIS_26521_BAYER_ACCUMULATOR_INVARIANT_FAILED admitted="
                                    + iris26489AdmittedFrames
                                    + " contributed="
                                    + iris26489ContributedFrames
                                    + " expected="
                                    + iris26489ExpectedAdmittedFrames);
                }
                Log.i(TAG, "IRIS_26521_BAYER_ACCUMULATOR_INVARIANT_PASS admitted="
                        + iris26489AdmittedFrames
                        + " contributed=" + iris26489ContributedFrames
                        + " expected=" + iris26489ExpectedAdmittedFrames
                        + " rgbOwner=IrisFusedBayerRgb"
                        + " c4ffSpatialRgbActive=false");
            }

'''
    s=replace_between(
        s,
        '            /* IRIS_26489_ADMISSION_EQUALS_ACCUMULATOR_CONTRIBUTION_INVARIANT',
        '            /* IRIS_26416_MOTION_V2_PROVEN_FLOAT32_BRIDGE',
        invariant_new,
        'invariant block')

    s=replace_final_direct_bayer_block(s)

    s=s.replace(
        '+ " properPerFrameSpatialRgb=" + directBayer',
        '+ " properPerFrameSpatialRgb=false"\n'
        '                    + " irisFusedBayerRgb=" + directBayer')
    s=s.replace(
        '+ " directMultiframeRgb=" + directBayer',
        '+ " directMultiframeRgb=false"\n'
        '                    + " alignedMultiframeBayer=" + directBayer')
    s=s.replace(
        '+ " helperBayerColorAuthority=false"',
        '+ " helperBayerColorAuthority=true"')
    s=s.replace(
        '+ " semanticAccumulator=2xRGBA16F_additive"',
        '+ " semanticAccumulator=disabled_26521"')
    s=s.replace(
        '+ " perFrameRgbEvidence=" + directBayer',
        '+ " perFrameRgbEvidence=false"')
    s=s.replace(
        '+ " anisotropicKernel=true"',
        '+ " irisEdgeDirectedDemosaic=true"')

    cleanup='            iris26488ReleaseReadbackFramebuffer(iris26501ChromaGuideScratch);\n'
    s=one(
        s,
        cleanup,
        '''            iris26488ReleaseReadbackFramebuffer(iris26521RgbOutput);
            if (iris26521RgbOutput != null) iris26521RgbOutput.close();
            if (iris26521LensShading != null) iris26521LensShading.close();
'''+cleanup,
        'new RGB cleanup')

    active=s[s.find('    public void Run() {'):]
    for token in (
        'iris26501ContributeRgbFrame(',
        'iris26501RenderChromaGuide(',
        'iris26501RenderRgbCovariance(',
        'mfsr_spatial_rgb_normalize_26501',
        'IRIS_26501_SPATIAL_RGB_CONTRIBUTION_INVARIANT',
    ):
        if token in active:
            raise AssertionError('old active RGB token survived: '+token)
    if 'IRIS_26521_INDEPENDENT_IRIS_RGB_OWNER' not in active:
        raise AssertionError('new RGB owner missing')
    return s

def expected_map(base:Path, apply26520_path:Path):
    mod=load_module(apply26520_path)
    out=dict(mod.expected_map(base))
    out[CFA]=rewrite_cfa(out[CFA])
    if (base/SHADER).exists():
        raise AssertionError('26521 shader unexpectedly exists in base')
    out[SHADER]=Path(__file__).with_name(
        'iris_fused_bayer_rgb_26521.glsl.txt').read_text()
    return out

def patch_text(base:Path, expected:dict[str,str])->str:
    chunks=[]
    for rel in sorted(expected):
        p=base/rel
        old=norm(p.read_text()) if p.exists() else ''
        new=expected[rel]
        if old==new: continue
        chunks.append(''.join(difflib.unified_diff(
            old.splitlines(True),
            new.splitlines(True),
            fromfile=('a/'+rel if p.exists() else '/dev/null'),
            tofile='b/'+rel)))
    return ''.join(chunks)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('root',type=Path)
    ap.add_argument('--apply26520',required=True,type=Path)
    ap.add_argument('--patch-out',required=True,type=Path)
    ap.add_argument('--patch-sha-out',required=True,type=Path)
    ns=ap.parse_args()

    base=ns.root.resolve()
    expected=expected_map(base,ns.apply26520.resolve())
    diff=patch_text(base,expected)
    if not diff:
        raise AssertionError('empty 26521 patch')
    ns.patch_out.parent.mkdir(parents=True,exist_ok=True)
    ns.patch_out.write_text(diff)
    digest=hashlib.sha256(ns.patch_out.read_bytes()).hexdigest()
    ns.patch_sha_out.write_text(
        f'{digest}  {ns.patch_out.name}\n')

    for rel,new in expected.items():
        p=base/rel
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(new)

    print('PASS: combined 26520 + 26521 patch existed before runtime writes')

if __name__=='__main__':
    main()
