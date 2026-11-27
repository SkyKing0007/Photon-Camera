#!/usr/bin/env python3
import argparse,json,xml.etree.ElementTree as ET
import build_26998_incremental as b
p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True);g.add_argument('--live',action='store_true');g.add_argument('--payload',action='store_true');o=p.parse_args();changed,base,expected=b.scope();R=b.R if o.live else b.R/'handoff_payload_26998'
if o.live:b.exact(R,'26998_EXPECTED_FULL_APP.sha256','26998 current physical source')
else:assert all(b.sha(R/f)==expected[f] for f in changed)
mp=json.loads((b.R/'26998_UPSTREAM_SOURCE_MAP.json').read_text());assert mp['donor_commit']=='ce0581b5a3a535d062957eec7fb3415747084516'
assert len(mp['files'])==len({x['candidate'] for x in mp['files']})==29
for x in mp['files']:assert expected[x['candidate']]==x['candidate_sha256']==b.sha(R/x['candidate'])
assert not any('/cpp/' in p or '/jniLibs/' in p or '/assets/' in p for p in changed)
J='app/src/main/java/com/particlesdevs/photoncamera/';K='app/src/main/java/com/hinnka/mycamera/processor/';D=K+'experimentc/original129/'
def read(p):return (R/p).read_text()
s=read(K+'Iris26972CCamera2ShutterSession.kt');assert 'if (!night && rawSaver != 2)' in s and 'Iris26998CDenoiseSettings.freeze(applicationContext, selectedLensId)' in s
s=read(K+'Iris26972CCaptureToGallery.kt');assert 'require((denoise1291 != null) == !shutter.night)' in s
s=read(K+'experimentc/Iris26975CPinnedDonorProEngine.kt');assert all(x in s for x in ('val photo1291 = !transaction.shutter.night','check(photo1291 == (denoise1291 != null))','rawRenderingEngine = RawRenderingEngine.AdobeCurve','photo1291 = photo1291','photoCalibration1291 = photoCalibration1291','lumaBands1291 = denoise1291?.lumaBands()','chromaBands1291 = denoise1291?.chromaBands()'))
s=read(D+'processor/GlesMgcRawSabreProcessor.kt');assert 'if (photo1291)' in s and 'return Iris26998GlesMgcRawSpatialStacker(' in s and 'return GlesMgcRawSpatialStacker(' in s
s=read(D+'raw/RawDemosaicProcessor.kt');assert all(x in s for x in ('if (applyDefaultDenoise && photo1291)','else if (applyDefaultDenoise)','observeRawStackNoise(workingFloatTexture','observedStackNoise = observedStackNoise','mgcDenoise1291?.release()','MgcFullResolutionDenoise.ensureInitialized(context)'))
s=read(D+'raw/Iris26998MgcGpuDenoiseConfig.kt');assert '.multiplyLevels(captureScales?.lumaStrength).multiplyLevels(lumaBands1291)' in s and '.multiplyLevels(captureScales?.chromaStrength).multiplyLevels(chromaBands1291)' in s and 'MgcRawMaxDenoiseTuning.atSnr(effectiveSnr)' in s
s=read(J+'settings/Iris26998CDenoiseSettings.java');assert all(x in s for x in ('getBoolean(key(lens,chroma)+"_enabled",false)','value>=0f && value<=16f','KEY_LUMA_DENOISE,0f','KEY_CHROMA_DENOISE,1f','lumaBands.clone()','chromaBands.clone()'))
s=read(J+'ui/settings/custompreferences/Iris26998CAdvancedDenoisePreference.java');assert all(x in s for x in ('extends ManagedSwitchPreference','R.layout.preference_seekbar','setMax(1600)','"RESET"','"CANCEL"','"SET"','saveEnabledBands(c,selected,isChroma,draft)'))
for p in changed:
 if p.endswith('.xml'):ET.parse(R/p)
if o.live:
 for p in [J+'capture/CaptureController.java',J+'capture/Iris26983COnCaptureSafety.java',K+'GlesIris26983COnLkrBridge.java',K+'Iris26972CPhysicalRawSpool.kt',K+'Iris26985CLinearOutput.kt',D+'processor/GlesMgcRawSpatialStacker.kt',D+'raw/MgcFullResolutionDenoise.kt']:
  assert p not in changed and b.sha(R/p)==base[p]
print('PASS exact C OFF source scope, explicit Photo ownership, measured SNR controls, unchanged independent legacy capture and native sources')
