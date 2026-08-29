#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, math, re, sys
from pathlib import Path

RUNTIME_FILES=[
'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightNeuralEnhancer.java',
'app/version.properties',
]

def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def text(root:Path,rel:str)->str:return (root/rel).read_text()
def need(c,msg):
    if not c: raise AssertionError(msg)
def clamp(v,a,b):return max(a,min(b,v))
def smooth01(t):
    t=clamp(t,0.0,1.0);return t*t*(3.0-2.0*t)
def edge_scalar(bilinear,edge_gate):
    peak=max(abs(x) for x in bilinear)
    residual_gate=smooth01((peak-.015)/(.080-.015))
    return clamp(1.0-.65*edge_gate*residual_gate,.35,1.0)
def transfer(bilinear,edge_gate):
    s=edge_scalar(bilinear,edge_gate);return [x*s for x in bilinear],s

def self_test():
    # Smooth-region invariant: exact 26555 bilinear residual.
    fixtures=[[.04,.01,-.02],[.08,.08,.08],[-.03,.02,.01],[0.0,0.0,0.0]]
    for b in fixtures:
        o,s=transfer(b,0.0)
        need(s==1.0 and o==b,'smooth Jin residual drift')
    # Small corrections are preserved even on a strong edge; guidance is not a blanket Jin disable.
    b=[.008,.006,.004];o,s=transfer(b,1.0)
    need(s==1.0 and o==b,'small edge correction was unnecessarily attenuated')
    # Permanent 26556 device-runtime failure regression: a neutral correction near a bright edge
    # must remain neutral. Per-channel suppression may not rotate it toward magenta/green/etc.
    b=[.12,.12,.12];o,s=transfer(b,1.0)
    need(abs(o[0]-o[1])<1e-12 and abs(o[1]-o[2])<1e-12,'neutral edge residual rotated hue')
    need(s<=.3500001 and s>=.3499999,'strong edge maximum attenuation changed')
    # General RGB-vector direction/sign ratio must be preserved by one shared scalar.
    for b in ([.08,.02,-.04],[.03,-.06,.09],[-.10,-.04,-.02]):
        o,s=transfer(list(b),.83)
        for i in range(3):
            need(abs(o[i])<=abs(b[i])+1e-12,'guided residual magnitude increased')
            need((o[i]==0.0 and b[i]==0.0) or o[i]*b[i]>=0.0,'guided residual sign changed')
        for i in range(3):
            for j in range(i+1,3):
                need(abs(o[i]*b[j]-o[j]*b[i])<1e-12,'RGB residual direction/hue rotated')
    # Segmented-edge failure class must still be strongly reduced versus 26555 bilinear.
    b=[.16,.16,.16];o,s=transfer(b,1.0)
    need(sum(abs(x) for x in o)<.40*sum(abs(x) for x in b),'segmented edge residual not reduced enough')
    print('PASS self-test: smooth exactness + no blanket edge disable + 26556 pink/hue regression + edge-glow reduction')

def tree_map(root:Path):
    return {p.relative_to(root).as_posix():sha(p) for p in root.rglob('*') if p.is_file() and '.git' not in p.parts}
def extract_method(src:str,signature:str)->str:
    i=src.index(signature);b=src.index('{',i);depth=0
    for j in range(b,len(src)):
        if src[j]=='{':depth+=1
        elif src[j]=='}':
            depth-=1
            if depth==0:return src[i:j+1]
    raise AssertionError('unterminated method '+signature)

def validate(base:Path,cand:Path):
    B,C=tree_map(base),tree_map(cand)
    changed=sorted(k for k in set(B)|set(C) if B.get(k)!=C.get(k))
    need(changed==sorted(RUNTIME_FILES),f'changed-file allowlist mismatch: {changed}')
    print('PASS exact three-file localized scope: Jin C++, Jin Java timing/plumbing, version')

    # The entire rest of the proven 26556 candidate is byte-identical: this is the localized-audit proof.
    for rel,h in B.items():
        if rel not in RUNTIME_FILES: need(C.get(rel)==h,'unintended drift '+rel)
    print('PASS all non-Jin 26556 runtime bytes unchanged (Motion30/Night50/natural1x/Sabre/VGN/UHDR included)')

    bj=text(base,RUNTIME_FILES[1]);cj=text(cand,RUNTIME_FILES[1]);cpp=text(cand,RUNTIME_FILES[0])
    # Official model/session/inference/output semantics are byte-identical method bodies.
    for sig in ['private static synchronized File ensureModelFile()','private static synchronized OrtSession ensureCpuSession()','private static void fillReferenceResidual(']:
        need(extract_method(bj,sig)==extract_method(cj,sig),'Jin official method changed '+sig)
    for tok in ['N = 512','MODEL_BYTES = 42571162L','residual[i * 3 + ch] = 0.5f * (out - input[ch * plane + i])']:
        need(tok in cj,'Jin reference semantic missing '+tok)
    model='app/src/main/assets/models/iris_night_jin_lol_512.onnx'
    need(sha(base/model)==sha(cand/model),'Jin ONNX model drift')
    print('PASS Jin model/session/512 normalization/output-residual semantics unchanged')

    # 26557 chroma-safe adapter contract.
    for tok in ['IRIS_26557_JIN_CHROMA_SAFE_EDGE_ATTENUATION','std::vector<float> guideGate','float rr=bilinear[c]*scale','scale=clampf(scale,0.35f,1.f)','residualPeak','0.65f*edgeGate*residualGate']:
        need(tok in cpp,'missing 26557 adapter token '+tok)
    for forbidden in ['guideDistance2ToNative','suppressedComponents','float reduced[3]','before*mean','lroundf(fx)']:
        need(forbidden not in cpp,'26556 per-channel/3x3 suppression survived '+forbidden)
    # Native loop may not recompute guide sqrt or run a 3x3 guide search.
    loop=cpp.index('for(uint32_t y=0;y<info.height;y++)',cpp.index('IRIS_26557_JIN_CHROMA_SAFE_EDGE_ATTENUATION'))
    need('std::sqrt' not in cpp[loop:cpp.index('AndroidBitmap_unlockPixels',loop)],'sqrt survived inside native-pixel Jin loop')
    need('for(int yy=' not in cpp[loop:cpp.index('AndroidBitmap_unlockPixels',loop)],'3x3 guide search survived native-pixel loop')
    self_test()
    print('PASS 26557 shared-RGB scalar prevents hue rotation and retains edge-glow attenuation')
    print('PASS guide structural work precomputed once at 512-domain; no per-native sqrt/3x3 search')

    # Only two critical timing markers, in the actual fix build.
    need(cj.count('IRIS_26557_JIN_TIMING')==2,'expected exactly two 26557 Jin timing marker statements')
    for tok in ['stage=inference ms=','stage=nativeTransfer ms=','System.nanoTime()']:
        need(tok in cj,'Jin timing proof missing '+tok)
    print('PASS minimal decision-relevant Jin timing markers: inference + nativeTransfer')

    # Production reachability and no legacy Jin substitute.
    np=text(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightProcessor.java')
    cm=text(cand,'app/src/main/cpp/CMakeLists.txt')
    need('IrisNightNeuralEnhancer.enhanceInPlace(img)' in np,'Jin enhancer not production-reachable')
    need('motionv2_jpeg444_jni.cpp' in cm,'Jin native translation unit not compiled')
    for forbidden in ['applyRgbGridInPlace','32 * 32 * 3']:
        need(forbidden not in cj,'legacy Jin implementation active '+forbidden)
    print('PASS active Night Jin ownership and legacy grid/hybrid rejection')

    # No GLSL/Kotlin modification: exact inherited compiled 26556 proof.
    for rel,h in B.items():
        if rel.endswith('.glsl') or rel.endswith('.kt'):need(C.get(rel)==h,'GLSL/Kotlin drift '+rel)
    print('PASS all GLSL/Kotlin exact successful-26556 bytes')

    vp=text(cand,'app/version.properties')
    need(re.search(r'(?m)^VERSION_NAME=0\.9726557\s*$',vp)!=None,'VERSION_NAME wrong')
    need(re.search(r'(?m)^VERSION_BUILD=26557\s*$',vp)!=None,'VERSION_BUILD wrong')
    print('PASS target version 0.9726557 / 26557')
    print('VALIDATION PASS')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--self-test',action='store_true');ap.add_argument('--base');ap.add_argument('--candidate');a=ap.parse_args()
    if a.self_test:self_test();return
    need(a.base and a.candidate,'--base and --candidate required')
    validate(Path(a.base),Path(a.candidate))
if __name__=='__main__':
    try:main()
    except Exception as e:
        print('VALIDATION FAIL:',e,file=sys.stderr);raise
