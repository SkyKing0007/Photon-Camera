#!/usr/bin/env python3
"""26898 guarded real-source validator: exact successful 26897 compiled TAR bytes.

Pure source and CLI-contract check, not a substitute for Kotlin/Javac/NDK/device.
"""
from pathlib import Path
import hashlib,sys,subprocess,shutil,tempfile,re
R=Path(__file__).resolve().parent
H=lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
def manifest(name):
    d={}
    for line in (R/name).read_text().splitlines():
        h,rel=line.split('  ',1)
        assert re.fullmatch('[a-f0-9]{64}',h) and rel not in d,(name,rel)
        d[rel]=h
    return d
OLD=manifest('26898_BASE_FULL_APP.sha256')
NEW=manifest('26898_EXPECTED_CANDIDATE_FULL_APP.sha256')
PRO=manifest('26898_UNCHANGED_PROTECTED.sha256')
ALW=(R/'26898_CHANGED_ALLOWLIST.txt').read_text().splitlines()
PAY=R/'handoff_payload_26898'
assert len(OLD)==len(NEW)==2025 and len(PRO)==2020
assert set(OLD)==set(NEW)
assert ALW==sorted(p for p in OLD if OLD[p]!=NEW[p])
assert ALW==[
'app/src/main/cpp/iris26856/amaze/src/AmazeGlVulkanJni.cpp',
'app/src/main/cpp/iris26864/Iris26864JniGpuInteropImpl.inc',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/version.properties']
assert set(PRO)==set(OLD)-set(ALW)
assert all(OLD[p]==NEW[p]==v for p,v in PRO.items())
assert not (R/'26898_ADDITIONS.txt').read_bytes() and not (R/'26898_DELETIONS.txt').read_bytes()
assert {f.relative_to(PAY).as_posix() for f in PAY.rglob('*') if f.is_file()}=={p[4:] for p in ALW}
assert all(H(PAY/p[4:])==NEW[p] for p in ALW)
assert 'VERSION_NAME=0.9726898' in (PAY/'version.properties').read_text()
assert 'VERSION_BUILD=26898' in (PAY/'version.properties').read_text()
def checked(path,m):
    d={p.relative_to(path).as_posix():H(p) for p in (path/'app').rglob('*') if p.is_file()}
    assert len(d)==len(m) and d==m, (len(d),len(m),[(p,d.get(p),m.get(p)) for p in m if d.get(p)!=m[p]][:8])
def candidate(base,cand,transform):
    checked(base,OLD)
    if transform:
        assert not cand.exists(),('candidate must be new',cand)
        shutil.copytree(base,cand)
        for p in ALW:
            dest=cand/p
            dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(PAY/p[4:],dest)
    checked(cand,NEW)
    print('PASS 26898 actual compiled 26897 -> exact 2025 candidate / 5 changes / 2020 protected')
def semantics(base,cand):
    checked(base,OLD);checked(cand,NEW)
    b=(cand/ALW[3]).read_text();h=(cand/ALW[2]).read_text()
    native=(cand/ALW[0]).read_text();interop=(cand/ALW[1]).read_text()
    oldb=(base/ALW[3]).read_text();oldh=(base/ALW[2]).read_text()
    required=[
        ('precise DNG context boundary',b.count('val dngEgl = IsolatedDngEgl.enter()')==1 and
            b.count('dngEgl.close()')==1 and b.index('dngEgl.close()')<b.index('val stackB26856 = fusion.processFrames(frames)')),
        ('same initialized EGL display, no-sharing and restore',all(x in b for x in (
            'EGL14.eglGetCurrentDisplay()', 'EGL14.eglGetCurrentContext()',
            'EGL14.eglGetCurrentSurface(EGL14.EGL_DRAW)',
            'EGL14.eglGetCurrentSurface(EGL14.EGL_READ)',
            'GlesGpuScheduler.createBackgroundContext(display, config, TAG)',
            'EGL14.eglMakeCurrent(display, previousDraw,',
            'EGL14.eglDestroyContext(display, isolatedContext)'))),
        ('no termination of shared EGL display', 'eglTerminate(display)' not in b[b.index('private class IsolatedDngEgl'):b.index('private class EglOwner')]),
        ('isolated DNG only original B path',b.count('val isolatedADng26868: RawStackResult? = if (')==1 and
            'experiment26856 == Iris26856ABSettings.Mode.AMAZE_26855 &&' in b and
            '!parameters.irisNightActive && produceNormalStackedDng' in b),
        ('same original Sabre A DNG parameters/math',all(x in b for x in (
            'useCurrentGlContext = true,exportGpuLinearRgbSource = true,',
            'exportNormalStackedDng = true,',
            'exactHistorical26850 = true,','earlyDngPublisher.publish(originalDng)'))),
        ('DNG saved before and external to B',b.index('earlyDngPublisher.publish(originalDng)')<
            b.index('val stackB26856 = fusion.processFrames(frames)')),
        ('DNG-only no B, intentional stop after teardown',b.index('if (independentDngOnlyDone)')>
            b.index('dngEgl.close()') and b.index('if (independentDngOnlyDone)')<
            b.index('val stackB26856 = fusion.processFrames(frames)') and
            'throw DngOnlyPublished()' in b),
        ('safe sentinel not wrapped as failure', 'if (error is DngOnlyPublished) throw error' in b),
        ('DNG-only Java toggle enters same callback and passes early stop flag',
            h.count('saveRAW >= 1 ? originalDng ->')==1 and
            'saveRAW == 2);' in h and 'e instanceof PhotonMotionMgc1271Bridge.DngOnlyPublished' in h),
        ('independent DNG writer unchanged', 'ImageSaver.Util.saveNormalized16StackedRaw(' in h and
            'IrisSabreSuperResDngWriter.write(' in h and
            'mIrisDngIndependentSaved = saved;' in h),
        ('single publication, no pair duplicate',h.count('mIrisDngIndependentAttempted = true;')==1 and
            'if (!mIrisDngIndependentAttempted)' in h and
            h.count('IRIS_DNG_INDEPENDENT_PRE_B_PUBLISHED')==1),
        ('native GL operation-specific failure code',native.count('assertGl("')>=4 and
            'glEGLImageTargetTexture2DOES' in native and 'glCode=' in native and
            'AHardwareBuffer_describe(ahb, &desc)' in native),
        ('distinguish JPEG RGB vs clipping AHB roles', '"B_HDRQ_RGB"' in interop and
            '"B_HDRQ_SENSOR_CLIP"' in interop),
        ('no change to GL import target or shader math', 'targetImage(GL_TEXTURE_2D, image);' in native and
            'glBindTexture(GL_TEXTURE_2D, texture);' in native),
        ('real original A and B paths remain unchanged', 'IRIS_26868_B_EXISTING_A_DNG_ONLY' in b and
            'IRIS_26864_REAL_RAWR_B_HDRQ_NORMAL_EXCLUSIVE_PUBLICATION' in b),
        ('regression has new marker in each intended source',all('26898' in (cand/p).read_text() for p in ALW)),
    ]
    for k,v in required: assert v,k
    # Base retains early DNG publication. No new DNG reconstruction / writer bytes.
    assert 'IRIS_DNG_INDEPENDENT_PRE_B' in oldb and 'IRIS_DNG_INDEPENDENT_PRE_B' in oldh
    for k in PRO:
        if any(t in k for t in ('Dng','DNG','ImageSaver','VulkanDeviceOwner','RawMergeHdrPlus','Wronski','Shader','/assets/shaders/')):
            assert OLD[k]==NEW[k]
    print('PASS 26898 B-only no-share DNG EGL, early DNG-only stop, stage-specific native GL receipts, A/Night/Wiener/DNG protected')
def patch(base,cand,forward,rollback):
    checked(base,OLD);checked(cand,NEW)
    assert forward.is_file() and rollback.is_file()
    for n in (7,12,40):
        with tempfile.TemporaryDirectory(prefix='26898_patch_') as td:
            x=Path(td)
            for p in ALW:
                f=x/p;f.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(base/p,f)
            def run(*args):
                result=subprocess.run(['git','-c',f'core.abbrev={n}','-C',str(x),'apply',*args],capture_output=True,text=True)
                assert result.returncode==0,(args,result.stdout,result.stderr)
            run('--check',str(forward));run(str(forward))
            assert all((x/p).read_bytes()==(cand/p).read_bytes() for p in ALW)
            run('--check',str(rollback));run(str(rollback))
            assert all((x/p).read_bytes()==(base/p).read_bytes() for p in ALW)
    print('PASS 26898 4-operand full-index patch forward/backward at 7/12/40 zero-fuzz exact bytes')
def tamper(base,cand):
    checked(base,OLD);checked(cand,NEW)
    with tempfile.TemporaryDirectory(prefix='26898_tamper_') as t:
        p=Path(t)/'candidate';shutil.copytree(cand,p)
        f=p/ALW[3];f.write_bytes(f.read_bytes()+b'\n// NEGATIVE GL CONTRACT TAMPER\n')
        try: checked(p,NEW)
        except AssertionError: pass
        else: raise AssertionError('source modification undetected')
    print('PASS 26898 negative actual compiled-source tamper')
if __name__=='__main__':
    a=sys.argv[1:];assert a
    if a[0]=='candidate':
        assert len(a) in (3,4);candidate(Path(a[1]),Path(a[2]),len(a)==4 and a[3]=='--transform')
    elif a[0]=='semantics':
        assert len(a)==3;semantics(Path(a[1]),Path(a[2]))
    elif a[0]=='patch':
        assert len(a)==5;patch(Path(a[1]),Path(a[2]),R/a[3],R/a[4])
    elif a[0]=='tamper':
        assert len(a)==3;tamper(Path(a[1]),Path(a[2]))
    else: raise AssertionError(('unknown stage',a))
