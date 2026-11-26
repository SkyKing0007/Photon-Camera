#!/usr/bin/env python3
"""Verify exact runtime scope and C-only owner, immutable request/timestamp binding and shader ownership."""
import argparse,importlib.util,pathlib,subprocess,sys
R=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('builder',R/'build_26988_incremental.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
p=argparse.ArgumentParser();p.add_argument('--live',action='store_true');p.add_argument('--payload',action='store_true');o=p.parse_args();assert o.live!=o.payload
changed,base,expected=b.scope();root=R if o.live else R/'handoff_payload_26988'
if o.live:b.exact(root,'26988_EXPECTED_FULL_APP.sha256','26988 live exact scope')
else:
 for q in changed:assert b.sha(root/q)==expected[q],q
j=root/'app/src/main/java/com/particlesdevs/photoncamera';c=(j/'capture/CaptureController.java').read_text();r=(j/'ui/camera/views/viewfinder/MainRenderer.java').read_text();d=j/'processing/experimentc';plan=(d/'Iris26988CExposurePlan.java').read_text();m=(d/'Iris26975CRawHighlightMeter.java').read_text();s=(d/'Iris26988CPreviewContinuity.java').read_text();f=(root/'app/src/main/assets/shaders/preview/main_fs.glsl').read_text()
assert 'return isZslMode() && getAuthoritativeCameraMode() == CameraMode.MOTION && iris26975CSelectedForCapture();' in c
assert '!PreferenceKeys.isIrisSuperResOn()) || mode == CameraMode.NIGHT)' in c
assert c.count('Iris26988CExposurePlan.plan(')==1 and c.count('mIris26988CPreview.beginManual(')==1
assert c.index('session.setRepeatingRequest(next,mCaptureCallback,mBackgroundHandler);')<c.index('mIris26988CPreview.beginManual(paired.getRequest(),next,ts);')<c.index('mIris26976CLockedPreviewRequest=next;')
assert 'owner==mIris26975CProvenRawPreviewRequest && mIris26975CZslPreviewSelected && iris26975CSelectedForMotion()' in c
assert 'mIris26988CKeepTapAnchor=biasChanged && !sceneChanged && touch' in c and 'mIris26988CPreview.reset(); // each genuine tap/reset' in c
assert 'paired.getRequest()!=mIris26975CProvenRawPreviewRequest' in c and 'Arrays.equals(paired.getRequest().get(CaptureRequest.CONTROL_AE_REGIONS),mIris26980CTouchRegion)' in c
assert 'mIris26980CReferenceRequest==paired.getRequest() && mIris26980CReference!=null' in c
assert 'mIris26980CReferenceMean=(float)(refMean*((double)chosen.shutterNs*chosen.iso/((double)ss*iso)))' in c
assert 'Iris26981CManualExposure.plan(' in plan and 'clipped!=0f' in plan and 'residualDemand>.03f' in plan and 'gain==minIso && iso==minIso && appearanceReady' in plan
assert 'sensorPeak = Math.max(sensorPeak, signal);' in m
assert 'request==owner' in s and 'Evidence e=evidence.get(ts);Float y=samples.get(ts);' in s and 'ratio<.67||ratio>1.50' in s
assert 'cProbeOwner=iris26872Eligible || iris26872Controller==null' in r and 'iris26988CDisplaySample(cProbeOwner,iris26553FrameTimestamp,level)' in r
assert 'if(Float.isFinite(cDisplayGain))' in r and 'iris26667PreviewGain=cDisplayGain;' in r
assert 'iris26662ReferencePreviewGain > 0.0' in f and 'iris26662Gain > 1.0001 || iris26662Gain < 0.9999' in f
native_exact={'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/lkrl_solver.cpp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/lkrl_finish.cpp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/lkrl_full.cpp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/lkrl_adapter.cpp', 'app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/lkrl_jni.cpp'}
assert {x for x in changed if '/cpp/' in x}==native_exact
assert not any('/cpp/' in x or '/jniLibs/' in x or 'Dng' in x or 'COn' in x or '/com/hinnka/' in x for x in changed-native_exact)
if o.live:
 subprocess.run([sys.executable,'-S','verify_26988_con_glsl.py'],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','verify_26988_preview_glsl.py','--audit'],cwd=R,check=True)
print('PASS exact C OFF exposure/touch/preview ownership and exact additional C ON private highlight allowlist; protected Night, B, DNG, renderer source paths')
