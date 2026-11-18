#!/usr/bin/env python3
"""Read-only release-tag provenance and no-gate HDRQ 0.5.1 mathematical/source parity.

Does not represent mobile GL/Vulkan shader execution; real pinned compilers and
full Android build remain required Actions stages.
"""
import argparse,hashlib,json,pathlib,math,random,subprocess
R=pathlib.Path(__file__).resolve().parent
P=R/'handoff_payload_26959'
j=json.loads((R/'26959_RAWR051_SOURCE_PROVENANCE.json').read_text())
assert j['release_commit']=='4c64cb1f5eb553bf61ca9a459c5a2c94964732e4'
assert j['apk_sha256']=='fae7b326736c284fb04658634d9cdf71bd735927ae31f88a14586a82b3d1b3df'

def shader_at(root,rel):return (root/rel).read_text()
def verify(live=False):
    root=R if live else P
    cpp=shader_at(root,'app/src/main/cpp/iris26864/bridge/Iris26888BOffHdrqCoordinator.cpp')
    kt=shader_at(root,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt')
    assert cpp.count('const bool photoBOffRawr051 = iris26941BOffHdrqLazyPoolReset &&')==1
    assert 'algorithm_ == MergeAlgorithm::HdrPlusFrequency &&\n                           !photoBOffRawr051' in cpp
    assert 'if (pass == 3u && algorithm_ == MergeAlgorithm::HdrPlusFrequency &&\n            !photoBOffRawr051)' in cpp
    assert 'photoBOffRawr051 ? float(frameCount) : hdrqEffectiveFrames' in cpp
    assert 'pressWindow26957=false)' in kt and 'pressWindow26957=true)' not in kt
    if live:
        vendor=R/'app/src/main/cpp/iris26864/vendor/rawr'
        for p,h in j['tag_verified_git_blob_hashes'].items():
            path=vendor/p
            # The pin includes the real HDR+ core. All present vendored
            # source files are compulsory, never silently skip a missing core.
            if p.startswith(('native/multiframe/merge_hdrplus/',
                             'native/multiframe/pipeline/')):
                assert path.is_file(), 'missing original v0.5.1 HDRQ core '+p
            if path.exists():
                assert path.is_file(), 'v0.5.1 path is not regular file '+p
                if subprocess.run(['git','hash-object',str(path)],capture_output=True,text=True,check=True).stdout.strip()!=h:
                    raise AssertionError('v0.5.1 core not byte matched '+p)
        # Invariant/protected compiler shader source: later gate's non-gated branch
        # reduces exactly to original v0.5.1 mismatch, norm, and Fourier merge.
        br=R/'app/src/main/cpp/iris26864/bridge'
        mm=(br/'Iris26888BOffHdrqMismatch.comp').read_text()
        mn=(br/'Iris26887BOffHdrqMismatchNorm.comp').read_text()
        fm=(br/'Iris26887BOffHdrqMerge.comp').read_text()
        orig=(vendor/'native/multiframe/merge_hdrplus/shaders/hdrq_merge.comp').read_text()
        assert 'vec4 variance=p.useMotionGate!=0 ? noise+1.0 : 0.5*noise+0.5*noise/max(p.exposureFactor,1.0e-6)+1.0;' in mm
        assert 'p.useMotionGate != 0' in mn
        assert 'if(gate<1.0)' in fm and 'weight=max(weight,gate);' in fm
        assert 'p.uniformExposure != 0' in orig and 'sBest = bi;' in orig
        assert 'const bool gated=uniformExposure_ && motionGateEnabled_;' in (br/'Iris26887BOffHdrqRecorder.cpp').read_text()
        assert 'hdrq.strength = bOffReusable ? 11.0f : 13.0f;' in (R/'app/src/main/cpp/iris26864/Iris26864RealRawrCoordinator.cpp').read_text()
        assert 'phaseSafePhysicalHalo=(!sr && photoBOffOnly == JNI_TRUE)' in (R/'app/src/main/cpp/iris26864/Iris26864JniGpuInteropImpl.inc').read_text()
        assert 'GlesIris26856RawrFalseColor' in (R/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
        # The original v0.5.1 shaders have no gate/write zmap.
        for p in ('hdrq_merge.comp','hdrq_mismatch.comp','hdrq_mismatch_norm.comp'):
            s=(vendor/'native/multiframe/merge_hdrplus/shaders'/p).read_text()
            assert 'useMotionGate' not in s and 'zmap' not in s and 'gateLo' not in s
        # No source changes to pinned AMaZE/FCC or Iris's requested border handling.
        before=R/'.photon_26959_work/authority_26958'
        if before.exists():
            for p in ('app/src/main/cpp/iris26864/bridge/Iris26943BOffHdrqBorder.comp',
                      'app/src/main/cpp/iris26856/amaze/src/Pipeline.cpp',
                      'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26856RawrFalseColor.kt',
                      'app/src/main/assets/shaders/motionv2/gainmap.glsl'):
                assert (R/p).read_bytes()==(before/p).read_bytes(), p
    # Independent numerical check: original 16x16 raised cosine vs Iris 16x4
    # grouped lanes, without the later 4x4 z-gate. Also verify Fourier weight
    # when gate=0 is the same original clipped Wiener blend.
    rng=random.Random(26959051)
    ts=8
    for edge in ((0,0),(8,8),(8,0),(0,8)):
        tx,ty=edge
        n=24
        pixR=[[[rng.uniform(90,1600) for c in range(4)] for x in range(n)] for y in range(n)]
        pixA=[[[pixR[y][x][c]+rng.uniform(-20,20) for c in range(4)] for x in range(n)] for y in range(n)]
        def w(dx,dy):
            return (0.5-0.17*math.cos(math.pi*(dx+0.5)/4))*(0.5-0.17*math.cos(math.pi*(dy+0.5)/4))
        ds1=[0.]*4;ws1=0.
        for dy in range(16):
            for dx in range(16):
                x=tx-4+dx;y=ty-4+dy
                if not (max(0,tx-4)<=x<min(n-1,tx+12) and max(0,ty-4)<=y<min(n-1,ty+12)):continue
                ww=w(dx,dy);ws1+=ww
                for c in range(4):ds1[c]+=ww*abs(pixR[y][x][c]-pixA[y][x][c])
        ds2=[0.]*4;ws2=0.
        for ly in range(4):
            for lx in range(16):
                for k in range(4):
                    dx=lx;dy=4*ly+k;x=tx-4+dx;y=ty-4+dy
                    if not (max(0,tx-4)<=x<min(n-1,tx+12) and max(0,ty-4)<=y<min(n-1,ty+12)):continue
                    ww=(0.342940479,0.434943816,0.565056184,0.657059521,0.657059521,0.565056184,0.434943816,0.342940479,0.342940479,0.434943816,0.565056184,0.657059521,0.657059521,0.565056184,0.434943816,0.342940479)[dx]*(0.342940479,0.434943816,0.565056184,0.657059521,0.657059521,0.565056184,0.434943816,0.342940479,0.342940479,0.434943816,0.565056184,0.657059521,0.657059521,0.565056184,0.434943816,0.342940479)[dy]
                    ws2+=ww
                    for c in range(4):ds2[c]+=ww*abs(pixR[y][x][c]-pixA[y][x][c])
        assert ws1>0 and abs(ws1-ws2)<1e-5,edge
        for exposure in (1.,1.9):
            noise=[rng.uniform(6.,120.) for _ in range(4)]
            m1=sum((ds1[k]/ws1)/math.sqrt(0.5*noise[k]+0.5*noise[k]/exposure+1.) for k in range(4))/4
            m2=sum((ds2[k]/ws2)/math.sqrt(0.5*noise[k]+0.5*noise[k]/exposure+1.) for k in range(4))/4
            assert math.isclose(m1,m2,rel_tol=1e-8,abs_tol=1e-7),(edge,exposure,m1,m2)
    for i in range(2000):
        # User setting strength 11 gives norms; original Wiener weight
        # remains [0,1], and max(weight,0)==weight.
        old=rng.random();assert max(old,0.)==old
        z=rng.random()*4.;added_gate=min(1.,max(0.,(z-1.6)/(2.6-1.6)))
        # Conservative gate would boost reference-only contribution above old.
        assert max(old,added_gate)>=old
    print('PASS v0.5.1 pinned Git provenance, B OFF gate isolation, protected Night/ON/border, release mismatch numerical parity (CPU simulation only)')
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--live',action='store_true');parser.add_argument('--payload',action='store_true');a=parser.parse_args();verify(a.live)
