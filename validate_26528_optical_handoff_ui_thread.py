#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

CAP="app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java"
BASE_SHA="7d1657f8d10048e8f4381e020c9d7ce1ea9a2e362518887ad774106006a33578"
TARGET_SHA="b702d150b14cd66f8bd37dab42502815a2c41f21c30004ec75dd7d8920e1bb08"
FWD_SHA="b2c269cf140ae1e6b8178fdfbf9b3b6ca8991740a26c24806e5edf3413131126"
ROLLBACK_SHA="9bb697e6a8a1dab7e240f7c9c94cdcab005880151650f56f2a19180955899883"

def sha(p:Path)->str: return hashlib.sha256(p.read_bytes()).hexdigest()

def tree_files(root:Path):
    return sorted(p.relative_to(root) for p in (root/'app/src/main').rglob('*') if p.is_file())

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--base',required=True,type=Path)
    ap.add_argument('--candidate',required=True,type=Path)
    ap.add_argument('--patch',required=True,type=Path)
    ap.add_argument('--patch-sha',required=True,type=Path)
    ap.add_argument('--rollback',required=True,type=Path)
    ap.add_argument('--rollback-sha',required=True,type=Path)
    ap.add_argument('--postbuild',action='store_true')
    ap.add_argument('--json-out',type=Path)
    a=ap.parse_args()
    b,c=a.base,a.candidate
    bf,cf=tree_files(b),tree_files(c)
    if bf!=cf: raise SystemExit('runtime file-set drift')
    changed=[]
    for rel in bf:
        if sha(b/rel)!=sha(c/rel): changed.append(str(rel))
    if changed != [CAP]: raise SystemExit('changed-owner allowlist drift: '+repr(changed))
    if sha(b/CAP)!=BASE_SHA: raise SystemExit('base CaptureController SHA drift')
    if sha(c/CAP)!=TARGET_SHA: raise SystemExit('candidate CaptureController SHA drift')
    if sha(a.patch)!=FWD_SHA or sha(a.rollback)!=ROLLBACK_SHA:
        raise SystemExit('runtime patch hash drift')
    for hp,expected,target in ((a.patch_sha,FWD_SHA,a.patch.name),(a.rollback_sha,ROLLBACK_SHA,a.rollback.name)):
        line=hp.read_text().strip().split()
        if len(line)<2 or line[0]!=expected or line[-1]!=target:
            raise SystemExit('patch sidecar drift '+hp.name)
    s=(c/CAP).read_text(encoding='utf-8')
    required=[
        'IRIS_26528_OPTICAL_HANDOFF_UI_THREAD_RESTART',
        'Runnable restart = () -> activity.runOnUiThread(() -> {',
        'IRIS_26527_ROUTE_RESTART_ORDER',
        'startBackgroundThread();',
        'mCameraManager.openCamera(irisRoute.openedDeviceId, mStateCallback, mBackgroundHandler)',
        'IRIS_26527_ZOOM_CURTAIN_FAILSAFE',
        'IRIS_26527_SESSION_ROUTE_ACTIVE',
    ]
    for t in required:
        if t not in s: raise SystemExit('required ownership marker missing: '+t)
    if 'processExecutor.execute(this::restartCamera)' in s:
        raise SystemExit('worker-thread optical restart survived')
    block=s[s.index('public void restartCamera()'):s.index('private Size getAspect',s.index('public void restartCamera()'))]
    if block.index('startBackgroundThread();') > block.index('mCameraManager.openCamera'):
        raise SystemExit('background handler starts after openCamera')
    vb=(b/'app/version.properties').read_text()
    vc=(c/'app/version.properties').read_text()
    if 'VERSION_NAME=0.9726527' not in vb or 'VERSION_BUILD=26527' not in vb:
        raise SystemExit('base version drift')
    if a.postbuild:
        if 'VERSION_NAME=0.9726528' not in vc or 'VERSION_BUILD=26528' not in vc:
            raise SystemExit('postbuild version drift')
    else:
        if vc!=vb: raise SystemExit('version changed before guarded build')
    # Frozen high-risk owners from 26527 must remain byte-identical.
    frozen=[
      'app/src/main/java/com/particlesdevs/photoncamera/control/IrisZoomController.java',
      'app/src/main/java/com/particlesdevs/photoncamera/control/Swipe.java',
      'app/src/main/java/com/particlesdevs/photoncamera/api/CameraManager2.java',
      'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbStacker.kt',
      'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbShaders.kt',
      'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java',
      'app/src/main/java/com/particlesdevs/photoncamera/processing/DngCreator.java',
      'app/src/main/cpp/dngCreator.cpp',
      'app/src/main/cpp/dngCreator.h',
    ]
    for rel in frozen:
        if sha(b/rel)!=sha(c/rel): raise SystemExit('frozen 26527 owner changed: '+rel)
    out={
      'changedOwners': changed,
      'baseCaptureSha': BASE_SHA,
      'candidateCaptureSha': TARGET_SHA,
      'forwardPatchSha': FWD_SHA,
      'rollbackPatchSha': ROLLBACK_SHA,
      'uiThreadRestart': True,
      'workerRestartRemoved': True,
      'inherited26527RouteOrdering': True,
      'postbuild': a.postbuild,
    }
    if a.json_out:
        a.json_out.write_text(json.dumps(out,indent=2)+'\n')
    print('PASS: 26528 independent one-owner validator')

if __name__=='__main__': main()
