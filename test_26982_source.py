#!/usr/bin/env python3
"""Exact successor scope & integration owner guards, payload and complete installed app."""
import argparse,importlib.util,pathlib,re,xml.etree.ElementTree as ET
R=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('b82',R/'build_26982_incremental.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
p=argparse.ArgumentParser();p.add_argument('--payload',action='store_true');p.add_argument('--live',action='store_true');a=p.parse_args();assert a.payload!=a.live
b.scope();root=R/'handoff_payload_26982' if a.payload else R
if a.live:b.exact(root,'26982_EXPECTED_FULL_APP.sha256','26982 installed full source')
base='app/src/main/java/'
def read(path):return (root/(base+path)).read_text()
xml=(root/'app/src/main/res/xml/preferences.xml').read_text();ET.fromstring(xml)
strings=(root/'app/src/main/res/values/strings.xml').read_text();ET.fromstring(strings)
assert xml.index('pref_iris_saturation')<xml.index('pref_iris_26982_c_mgc_band_0')<xml.index('pref_iris_26982_c_mgc_band_1')<xml.index('pref_iris_26982_c_mgc_band_2')<xml.index('pref_iris_exposure_ev')
for i in range(3):
 assert ('pref_iris_26982_c_mgc_band_'+str(i)) in xml
 assert 'iris_c_mgc_band_'+str(i) in strings
 assert xml.count('ns1:stepPerUnit="10"')>=3
impl=read('com/particlesdevs/photoncamera/settings/Iris26982CSharpenSettings.java')
for s in ('Float.isFinite(v)','Math.round(v * 10f)','private Iris26982CSharpenSettings()','return new float[]','physicalId'):
 assert s in impl,s
ui=read('com/particlesdevs/photoncamera/ui/settings/SettingsActivity.java')
for s in ('Iris26982CSharpenSettings.safeValue','Iris26982CSharpenSettings.key','Mode.BJZHOU_26972C','pref_iris_26982_c_mgc_band_','setupIris26982CSharpening'):
 assert s in ui,s
seek=read('com/particlesdevs/photoncamera/ui/settings/custompreferences/Iris26982CBandPreference.java')
assert 'extends UniversalSeekBarPreference' in seek and 'persistString' in seek
session=read('com/hinnka/mycamera/processor/Iris26972CCamera2ShutterSession.kt')
assert 'freeze(applicationContext, physicalId)' in session and 'frozenSharpenBands)' in session
bridge=read('com/hinnka/mycamera/processor/Iris26972CCaptureToGallery.kt')
assert 'PhotonSharpenBands(' in bridge and 'val sharpenBands:' in bridge
engine=read('com/hinnka/mycamera/processor/experimentc/Iris26975CPinnedDonorProEngine.kt')
assert 'PhotonSharpenTuning.DEFAULT.copy(amount = transaction.sharpenBands)' in engine and 'photonSharpenTuning = sharpenTuning' in engine
assert 'IRIS_26982_C_MGC_SHARPEN' in engine
original=read('com/hinnka/mycamera/processor/experimentc/original129/raw/RawDemosaicProcessor.kt')
assert original.count('photonSharpenTuning =')>=3 and 'tuning = photonSharpenTuning' in original
assert 'photonSharpenTuning = config.photonSharpenTuning' in original
hist=read('com/particlesdevs/photoncamera/ui/camera/views/IrisLiveHistogramView.java')
assert 'Iris26935BOnSession.isActive()' in hist and 'PixelCopy=false' in hist
renderer=read('com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java')
assert 'setIris26982SuperResProcessing(iris26935Busy)' in renderer and 'Iris26935BOnSession.isActive()' in renderer
preview=read('com/particlesdevs/photoncamera/ui/camera/views/viewfinder/GLPreview.java')
assert 'RENDERMODE_WHEN_DIRTY' in preview and 'RENDERMODE_CONTINUOUSLY' in preview and 'directIsp=false' in preview
if a.live:
 math=read('com/hinnka/mycamera/processor/experimentc/original129/raw/MgcSharpenCurveBuilder.kt')
 assert 'x + amount * (y - x)' in math
 assert '0f -> x' in math and '1f -> y' in math
 assert (R/'app/src/main/java/com/particlesdevs/photoncamera/capture/Iris26935BOnSession.java').is_file()
print('PASS 26982 exact C/MGC band plumbing, per-lens UI, donor curves, B/ON fail-closed camera stream guard ('+('payload' if a.payload else 'live')+')')
