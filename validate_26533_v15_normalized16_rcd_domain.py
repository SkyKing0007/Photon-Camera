#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib
REL='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/IrisRcdBayerInput.java'; BASE_SHA='23226417056d2c3d0c0413df737400e5ad3fb3df4e85279e02d9271c2cdb6c33'; POST_SHA='708b859ed1a676c8e2b8d789d2eb857187a23e46175fecb8803d57b1c571960a'; SHADER_REL='app/src/main/assets/shaders/irisnight/raw16_to_packed_linear_bayer.glsl'; SHADER_SHA='3e70f4a91fdc0c1c8f8af600671fecc5270b52210ae1372976ef79dbb6ee3a9d'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rows(path):
    out=[]
    for raw in Path(path).read_text().splitlines():
        if not raw.strip() or raw.lstrip().startswith('#'): continue
        h,r=raw.split(None,1); out.append((h,r.strip()))
    return out
def manifest(root):
    out={}
    for top in ('app/src/main','app/version.properties','app/build.gradle'):
        p=root/top
        if p.is_file(): out[top]=sha(p)
        elif p.is_dir():
            for f in p.rglob('*'):
                if not f.is_file(): continue
                rel=str(f.relative_to(root))
                if rel.startswith('app/src/main/cpp/third_party_26507/'): continue
                if rel.startswith('app/src/main/cpp/deps/') and rel!='app/src/main/cpp/deps/.gitignore': continue
                out[rel]=sha(f)
    return out
def validate(base,candidate,anchors):
    b=Path(base); c=Path(candidate)
    if sha(b/REL)!=BASE_SHA: raise RuntimeError('base IrisRcdBayerInput SHA drift')
    if sha(c/REL)!=POST_SHA: raise RuntimeError('candidate IrisRcdBayerInput SHA drift')
    if sha(b/SHADER_REL)!=SHADER_SHA or sha(c/SHADER_REL)!=SHADER_SHA: raise RuntimeError('raw16 adapter shader drift')
    t=(c/REL).read_text()
    for x in ('IRIS_26533_V15_NORMALIZED16_RCD_DOMAIN','setVar("blackLevel",new float[]{0f,0f,0f,0f})','setVar("whiteLevel",65535.0f)','sensorBlackWhiteIgnored=true'):
        if t.count(x)!=1: raise RuntimeError('required V1.5 token count !=1: '+x)
    for x in ('setVar("blackLevel",basePipeline.mParameters.blackLevel)','setVar("whiteLevel",(float)basePipeline.mParameters.whiteLevel)'):
        if x in t: raise RuntimeError('V1.4 sensor-domain adapter survived: '+x)
    post=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java').read_text()
    if post.count('add(new IrisRcdBayerInput())')!=2 or post.count('add(new IrisRcdDemosaic())')!=2: raise RuntimeError('shared Motion/Night RCD route drift')
    for x in ('RunIrisNightBayer','RunMotionV2FusedBayerRcd','V2_POST_SHORT_A_CHROMA_AFTER_RCD'):
        if x not in post: raise RuntimeError('V1.4 RCD architecture missing: '+x)
    hdr=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java').read_text()
    for x in ('dngDomain=normalized16 blackLevel=0 whiteLevel=65535','stackedDngRaw16','RunMotionV2FusedBayerRcd','RunIrisNightBayer'):
        if x not in hdr: raise RuntimeError('normalized16 ownership evidence missing: '+x)
    for h,r in rows(anchors):
        if sha(b/r)!=h: raise RuntimeError('base V1.4 anchor drift: '+r)
        if sha(c/r)!=h: raise RuntimeError('candidate changed protected V1.4 anchor: '+r)
    mb,mc=manifest(b),manifest(c); changed=sorted(k for k in set(mb)|set(mc) if mb.get(k)!=mc.get(k))
    if changed!=[REL]: raise RuntimeError('V1.5 runtime delta not exactly one file: '+repr(changed))
    vp=(c/'app/version.properties').read_text()
    if 'VERSION_NAME=0.9726533' not in vp or 'VERSION_BUILD=26533' not in vp: raise RuntimeError('V1.5 build ID drift')
    print('26533 V1.5 NORMALIZED16->RCD DOMAIN + EXACT V1.4 SCOPE PROOF PASSED')
def self_test():
    wrong=(50009.0-64.0)/(1023.0-64.0); correct=50009.0/65535.0
    assert wrong>50 and 0<correct<1
    print('26533 V1.5 VALIDATOR DOMAIN SELF-TEST PASSED wrongScale=%.3f correctScale=%.6f'%(wrong,correct))
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--self-test',action='store_true'); ap.add_argument('--base'); ap.add_argument('--candidate'); ap.add_argument('--anchors'); a=ap.parse_args()
    if a.self_test: self_test(); return
    if not a.base or not a.candidate or not a.anchors: raise SystemExit('--base --candidate --anchors required')
    validate(a.base,a.candidate,a.anchors)
if __name__=='__main__': main()
