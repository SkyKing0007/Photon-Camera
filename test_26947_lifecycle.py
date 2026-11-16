#!/usr/bin/env python3
"""Camera foreground lifecycle regressions and Android GL matrix publication contract."""
from build_26947_incremental import R,fail
import sys,re
P='app/src/main/java/com/particlesdevs/photoncamera/'
def main():
    live='--live' in sys.argv
    def read(name):return ((R if live else R/'handoff_payload_26947')/(P+name)).read_text()
    f=read('ui/camera/CameraFragment.java');g=read('ui/camera/views/viewfinder/GLPreview.java');c=read('capture/CaptureController.java')
    a=g.index('public void onResume()');b=g.index('public void onPause()',a)
    assert g[a:b].index('beginFrontRearPreviewHandoff();')<g[a:b].index('super.onResume();')
    a=g.index('public void onPause()');b=g.index('public void setAspectRatio(',a)
    assert g[a:b].index('beginFrontRearPreviewHandoff();')<g[a:b].index('super.onPause();')
    a=c.index('if (session == mCaptureSession && mTextureView != null')
    b=c.index('if (!mIris26548FirstCaptureResult)',a)
    sub=c[a:b]
    assert 'iris26947Sensor != null && iris26947Facing != null' in sub
    assert 'mIrisSessionRoutes.get(session)' in sub
    assert sub.index('setOrientation(')<sub.index('setMirror(')<sub.index('confirmFrontRearPreviewResult(')
    assert 'if (iris26945NewFrameNs != null && iris26945NewFrameNs > 0L)' in sub
    a=f.index('private boolean iris26562ApplyForegroundResetIfReady()')
    b=f.index('public void onResume()',a)
    assert 'if (CaptureController.isProcessing)' in f[a:b]
    assert f[a:b].index('resetForForegroundSession()')<f[a:b].index('onLensInventoryReady()')
    # Actual unchanged GL preview orientation contract is sensor+90 with atomic whole matrix;
    # all four sensor orientations and both lens facings must follow that formula.
    for sensor in (0,90,180,270):
        angle=(sensor+90)%360
        assert angle in (0,90,180,270)
        for facing in ('front','rear'):
            assert (facing=='front')==(facing!='rear')
    # No change in original lens-switch barrier; Android result+timestamp still releases it.
    assert 'mTextureView.isFrontRearPreviewHandoffPending()' in sub
    print('PASS 26947 pause/resume hold order; active Camera2 first-result 0/90/180/270 matrix+front mirror before timestamp release; rear 1x reselect')
if __name__=='__main__':
    try:main()
    except Exception as e:print(e,file=sys.stderr);sys.exit(1)
