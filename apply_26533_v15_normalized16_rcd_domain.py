#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
REL='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/IrisRcdBayerInput.java'; BASE_SHA='23226417056d2c3d0c0413df737400e5ad3fb3df4e85279e02d9271c2cdb6c33'; POST_SHA='708b859ed1a676c8e2b8d789d2eb857187a23e46175fecb8803d57b1c571960a'; OLD='glProg.useAssetProgram("irisnight/raw16_to_packed_linear_bayer"); glProg.setTexture("InputBuffer",in); glProg.setVar("blackLevel",basePipeline.mParameters.blackLevel); glProg.setVar("whiteLevel",(float)basePipeline.mParameters.whiteLevel);'; NEW='glProg.useAssetProgram("irisnight/raw16_to_packed_linear_bayer"); glProg.setTexture("InputBuffer",in); glProg.setVar("blackLevel",new float[]{0f,0f,0f,0f}); glProg.setVar("whiteLevel",65535.0f); com.particlesdevs.photoncamera.util.Log.d("IrisRcdBayerInput","IRIS_26533_V15_NORMALIZED16_RCD_DOMAIN blackLevel=0 whiteLevel=65535 sensorBlackWhiteIgnored=true");'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def patch_text(s):
    if s.count(OLD)!=1: raise RuntimeError("V1.4 normalized16 RCD anchor count != 1")
    o=s.replace(OLD,NEW)
    if o.count("IRIS_26533_V15_NORMALIZED16_RCD_DOMAIN")!=1: raise RuntimeError("V1.5 marker count !=1")
    return o
def self_test():
    o=patch_text("prefix\n"+OLD+"\nsuffix\n")
    assert OLD not in o and 'new float[]{0f,0f,0f,0f}' in o and 'setVar("whiteLevel",65535.0f)' in o
    print("26533 V1.5 NORMALIZED16 RCD TRANSFORM SELF-TEST PASSED")
def main():
    if len(sys.argv)==2 and sys.argv[1]=='--self-test': self_test(); return
    if len(sys.argv)!=2: raise SystemExit('usage: apply_26533_v15_normalized16_rcd_domain.py ROOT | --self-test')
    p=Path(sys.argv[1])/REL
    if not p.is_file(): raise RuntimeError('missing '+REL)
    if sha(p)!=BASE_SHA: raise RuntimeError('V1.4 IrisRcdBayerInput base SHA mismatch: '+sha(p)+' != '+BASE_SHA)
    p.write_text(patch_text(p.read_text()),encoding='utf-8')
    if sha(p)!=POST_SHA: raise RuntimeError('V1.5 IrisRcdBayerInput post SHA mismatch')
    print('IRIS_26533_V15_NORMALIZED16_RCD_DOMAIN_APPLIED')
if __name__=='__main__': main()
