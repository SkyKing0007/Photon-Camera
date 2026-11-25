#!/usr/bin/env python3
import argparse,importlib.util,pathlib,subprocess,sys
R=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('builder26984',R/'build_26984_incremental.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
p=argparse.ArgumentParser();m=p.add_mutually_exclusive_group(required=True);m.add_argument('--live',action='store_true');m.add_argument('--payload',action='store_true');o=p.parse_args()
changes,base,expected=b.scope();root=R if o.live else R/'handoff_payload_26984'
if o.live:b.exact(root,'26984_EXPECTED_FULL_APP.sha256','26984 live full source')
else:
 for q in changes:assert b.sha(root/q)==expected[q],q
j=root/'app/src/main/java/com/particlesdevs/photoncamera';k=root/'app/src/main/java/com/hinnka/mycamera/processor'
ui=(j/'ui/settings/SettingsActivity.java').read_text();store=(j/'settings/Iris26982CSharpenSettings.java').read_text();controller=(j/'capture/CaptureController.java').read_text();session=(k/'Iris26972CCamera2ShutterSession.kt').read_text()
assert 'Reopen settings after the physical lens is ready' not in ui
assert 'preference.setEnabled(haveSelected);' in ui and 'preference.setSummary((CharSequence) null);' in ui and 'forSelectedLens(' in ui
assert 'freezeSelectedLens(applicationContext, selectedLensId, physicalId)' in session
assert 'mCameraDevice.getId(), physicalID, cActualRoute.requestedOwnerId, frames, night, mImageReaderRaw,' in controller
assert 'private static String selectedKey(String selectedId, int band)' in store
assert 'iris26972CStartIndependentCamera2(false);' in controller and 'iris26486ImageSaver.runIris26983COnRaw(' in controller
assert len(changes)==5 and all(not p.startswith(('app/src/main/cpp/','app/src/main/assets/','app/src/main/jniLibs/','app/src/main/java/com/hinnka/mycamera/processor/experimentc/')) for p in changes)
if o.live:subprocess.run([sys.executable,'-S',str(R/'verify_26984_con_glsl.py'),'--root',str(root/'app')],check=True)
print('PASS exact 26984 C settings/shutter path and protected original donor, C ON LKR, DNG and GPU source')
