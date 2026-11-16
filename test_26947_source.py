#!/usr/bin/env python3
"""Exact 26946 compiled candidate and limited camera lifecycle allowlist."""
from build_26947_incremental import R,scope,sha,fail
import sys,re
P='app/src/main/java/com/particlesdevs/photoncamera/'
def main():
    changed,old,new=scope(); live='--live' in sys.argv
    def txt(p):
        path=(R if live else R/'handoff_payload_26947')/p
        if not path.is_file():fail('missing actual candidate source '+p)
        if sha(path)!=new[p]:fail('altered '+p)
        return path.read_text()
    f=txt(P+'ui/camera/CameraFragment.java')
    c=txt(P+'capture/CaptureController.java')
    g=txt(P+'ui/camera/views/viewfinder/GLPreview.java')
    v=txt('app/version.properties')
    start=f.index('private boolean iris26562ApplyForegroundResetIfReady()')
    end=f.index('    @Override\n    public void onResume()',start)
    reset=f[start:end]
    ordered=('if (!ActivityLifecycleMonitor.isCameraResetPending())','if (CaptureController.isProcessing)',
             'ActivityLifecycleMonitor.consumeCameraResetPending()',
             'IrisZoomController.resetForForegroundSession()',
             'irisZoomController.onLensInventoryReady()',
             'PhotonCamera.getSettings().loadCache()')
    i=0
    for snippet in ordered:
        j=reset.find(snippet,i)
        if j<0:fail('foreground 1x reset missing/out of order '+snippet)
        i=j+len(snippet)
    if 'if (irisZoomController != null)' not in reset:fail('null zoom owner guard missing')
    p=c.index('if (session == mCaptureSession && mTextureView != null')
    q=c.index('if (!mIris26548FirstCaptureResult)',p)
    bound=c[p:q]
    for s in ('result.get(CaptureResult.SENSOR_TIMESTAMP)',
             'mIrisSessionRoutes.get(session)', 'mCameraCharacteristicsMap.get(iris26947Route.characteristicsId)',
             'iris26947Active.get(', 'CameraCharacteristics.SENSOR_ORIENTATION',
             'CameraCharacteristics.LENS_FACING','mTextureView.setOrientation(iris26947Sensor + 90)',
             'mTextureView.setMirror(iris26947Facing',
             'mTextureView.confirmFrontRearPreviewResult(iris26945NewFrameNs)'):
        if s not in bound:fail('missing active result orientation authority '+s)
    if not bound.index('mTextureView.setOrientation(')<bound.index('mTextureView.setMirror(')<bound.index('mTextureView.confirmFrontRearPreviewResult('):fail('orientation must be published before result release')
    for s in ('beginFrontRearPreviewHandoff();', 'IRIS_26947_LIFECYCLE_PREVIEW_HOLD state=resume',
              'IRIS_26947_LIFECYCLE_PREVIEW_HOLD state=pause'):
        if s not in g:fail('lifecycle hold absent '+s)
    if g.count('beginFrontRearPreviewHandoff();')!=2:fail('lifecycle must hold on pause and resume')
    if not re.search(r'(?m)^VERSION_BUILD=26947$',v) or 'VERSION_NAME=0.9726947' not in v:fail('version incorrect')
    print('PASS 26947 exact 4-file source, 2050 protected, main rear 1x foreground re-inventory, timestamp-bound matrix before release')
if __name__=='__main__':
    try:main()
    except Exception as e:print(e,file=sys.stderr);sys.exit(1)
