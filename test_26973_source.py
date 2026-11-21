#!/usr/bin/env python3
"""26973 C UI + independent shutter and save-owner static regression; no Android compiler replacement."""
from pathlib import Path
import sys,subprocess,tempfile,re,hashlib
sys.path.insert(0,str(Path(__file__).resolve().parent))
import build_26973_incremental as build
R=build.R
changed,base,expected=build.scope()
root=R if '--live' in sys.argv else R/'handoff_payload_26973'
for name in changed:
 assert (root/name).is_file() and build.sha(root/name)==expected[name],name
con=(root/'app/src/main/java/com/particlesdevs/photoncamera/processing/experimentc/Iris26972CContract.java').read_text()
assert 'PRODUCTION_READY = false' in con and 'ACTUAL_CAMERA2_CALLBACK_WIRED = false' in con
assert con.count('CONTROLLED_DEVICE_TRIAL_ENABLED = true')==1
assert 'MAX_NORMAL_FRAMES = 30' in con and 'ALLOW_ALTERNATE_RECONSTRUCTOR = false' in con and 'ALLOW_ALTERNATE_FINISHER = false' in con
ui=(root/'app/src/main/java/com/particlesdevs/photoncamera/ui/settings/SettingsActivity.java').read_text()
assert 'new CharSequence[]{"A", "B", "C"}' in ui and ui.count('Iris26972CContract.CONTROLLED_DEVICE_TRIAL_ENABLED')==1
assert 'Iris26856ABSettings.write(mContext, active, next)' in ui
assert 'framePreference.setRuntimeMaxValue(cap30 ? 30.0f : 50.0f)' in ui
assert 'CameraMode.MOTION || cChosen' in ui
assert 'Iris26856ABSettings.read(mContext, active, active).id' in ui
mode=(root/'app/src/main/java/com/particlesdevs/photoncamera/processing/experimentc/Iris26972CModeGate.java').read_text()
assert '"C".equals(frozenModeId)' in mode and '!Iris26972CContract.CONTROLLED_DEVICE_TRIAL_ENABLED' in mode
assert 'throw new IllegalStateException("26972_C_INDEPENDENT_BACKEND_REQUIRED owner="' in mode
camera=(root/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text()
assert 'if ("C".equals(iris26972RequestedAtShutter.id)) {' in camera
assert 'iris26972CStartIndependentCamera2(false);' in camera
assert 'iris26972CStartIndependentCamera2(true);' in camera
assert 'return; // C cannot ever enter old Motion ZSL/26905/B processing.' in camera
assert 'C_PHYSICAL_RAW_OUTPUT_NOT_PROVEN' in camera and 'C_PHYSICAL_LENS_SHADING_UNAVAILABLE' in camera
assert 'C_ARM64_RAISR_DONOR_REQUIRED' in camera
assert 'final int frames = Math.min(requestedFrames,' in camera and 'IRIS_26973_C_LOCAL_30_FRAME_CAP' in camera
assert camera.count('Iris26972CContract.CONTROLLED_DEVICE_TRIAL_ENABLED')==1
sources=('app/src/main/java/com/hinnka/mycamera/processor/Iris26972CCamera2ShutterSession.kt',
'app/src/main/java/com/hinnka/mycamera/processor/Iris26972CCaptureToGallery.kt',
'app/src/main/java/com/hinnka/mycamera/processor/Iris26972CStreamingFinish.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/experimentc/Iris26972CUltraHdr.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/experimentc/Iris26972CJpeg444.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/experimentc/Iris26972CMediaStorePublisher.java')
for rel in sources:
 s=(root/rel).read_text()
 assert 'Iris26972CContract.CONTROLLED_DEVICE_TRIAL_ENABLED' in s,rel
 assert not re.search(r'if\s*\(\s*!Iris26972CContract.PRODUCTION_READY',s),rel
assert 'Iris26972CContract.PRODUCTION_READY' not in camera
# Unchanged per-lens A/B/C identity, original native, exact shader source and 2,121 other files.
assert 'app/src/main/java/com/particlesdevs/photoncamera/settings/Iris26856ABSettings.java' not in changed
p='app/src/main/java/com/particlesdevs/photoncamera/settings/Iris26856ABSettings.java'
assert base[p]==expected[p]
assert (root/'app/version.properties').read_text()=='VERSION_MAJOR=0\nVERSION_MINOR=9726440\nVERSION_NAME=0.9726973\nVERSION_BUILD=26973\n'
if '--live' in sys.argv:
 assert build.scan(root)==expected
 assert build.scan(build.BASE)==base
# Independently compile and execute C gate contract on real host javac if available.
if '--host-java' in sys.argv:
 import shutil
 if not shutil.which('javac') or not shutil.which('java'):build.fail('host java unavailable')
 # Host proof uses candidate whole sources, since Java contract imports no Android.
 croot=build.CAND if '--live' in sys.argv else build.CAND
 with tempfile.TemporaryDirectory() as td:
  d=Path(td);d.joinpath('C26973HostGateTest.java').write_text('''import com.particlesdevs.photoncamera.processing.experimentc.*;
public class C26973HostGateTest {
 public static void main(String[] a) {
  if (!Iris26972CContract.CONTROLLED_DEVICE_TRIAL_ENABLED || Iris26972CContract.PRODUCTION_READY || Iris26972CContract.ACTUAL_CAMERA2_CALLBACK_WIRED) throw new AssertionError();
  if (Iris26972CModeGate.mustRejectAtShutter("A") || Iris26972CModeGate.mustRejectAtShutter("B") || Iris26972CModeGate.mustRejectAtShutter("C")) throw new AssertionError();
  try {Iris26972CModeGate.requireIndependentBackend("C","host");throw new AssertionError();}catch(IllegalStateException required) {}
  System.out.println("PASS C trial gate, A/B mode untouched, C A/B fallback rejected");
 }
}
''')
  subprocess.run(['javac','-d',td,str(croot/'app/src/main/java/com/particlesdevs/photoncamera/processing/experimentc/Iris26972CContract.java'),str(croot/'app/src/main/java/com/particlesdevs/photoncamera/processing/experimentc/Iris26972CModeGate.java'),str(d/'C26973HostGateTest.java')],check=True)
  subprocess.run(['java','-cp',td,'C26973HostGateTest'],check=True)
print('PASS 26973 exact C-only UI+shutter+save owner, 30 frame bound, no A/B fallback, 2121 protected originals')
