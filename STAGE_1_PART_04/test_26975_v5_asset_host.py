#!/usr/bin/env python3
"""V5 physically verifies 26975 donor Pro Sabre AdobeCurve no optional style asset dependencies.
No source implementation edits, no A/B changes. This is not an Android compilation test.
"""
from pathlib import Path
import hashlib,json,sys,importlib.util
R=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('builder26975',R/'build_26975_incremental.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
changed,base,candidate=b.scope()
manifest=json.loads((R/'26975_V5_REMOVED_OPTIONAL_ASSETS.json').read_text())
removed=manifest['removed']
assert len(removed)==253
assert sum(e['bytes'] for e in removed)==48319061
assert len({x['path'] for x in removed})==len(removed)
assert all(x['path'].startswith('app/src/main/assets/experimentc/original129/') for x in removed)
assert not set(x['path'] for x in removed)&set(candidate), 'optional film/depth asset unexpectedly included'
for name in ('luts','spektrafilm','fotufilm','canon','lumix','leica','hncs','dcp','u2netp'):
 assert not any('/'+name+'/' in p for p in candidate if p.startswith('app/src/main/assets/experimentc/original129/')),name
roots={'mgc_denoise','mgc_ae','mgc_hdrnet','noise_profiles','internal'}
for root in roots:
 assert any(p.startswith('app/src/main/assets/experimentc/original129/'+root+'/') for p in candidate),root
# V6: all five unused frame_glass source assets were pruned; original GLSL
# program text remains in the physical source tree, never replaced by a stub.
assert not any(p.startswith('app/src/main/assets/experimentc/original129/shaders/') for p in candidate)
assert any('original129/processor/GlesMgcRawSpatialShaders.kt' in p for p in candidate)
assert any('original129/raw/RawOutputPass.kt' in p for p in candidate)
# Confirm exact original engine choice and no style, imported DCP or optional ML entry.
engine_path='app/src/main/java/com/hinnka/mycamera/processor/experimentc/Iris26975CPinnedDonorProEngine.kt'
scope=sys.argv[1] if len(sys.argv)>1 else '--payload'
assert scope in ('--payload','--live')
path=R/('handoff_payload_26975/'+engine_path if scope=='--payload' else engine_path)
s=path.read_text()
assert 'rawRenderingEngine = RawRenderingEngine.AdobeCurve' in s
assert 'embeddedDngRenderPlan = embeddedPlan' in s
assert 'MultiFrameStacker.processBurstRaw' in s
assert 'renderer.processMgcSpatialGpuLinearRgb' in s
assert 'GpuReferenceGainmapProducer' in s and 'NoLookLutRawGainmapSidecar.create' in s and 'HdrGainmapStrength.DEFAULT' in s
assert 'rawDcpId' not in s
assert 'prewarmDepthEstimator' not in s
assert 'RawOutputUpscaleMode.LANCZOS3' in (R/('handoff_payload_26975/app/src/main/java/com/hinnka/mycamera/processor/experimentc/Iris26975CProSabre1xSelection.kt' if scope=='--payload' else 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/Iris26975CProSabre1xSelection.kt')).read_text()
if scope=='--live':
 a=R/'app/src/main/assets/experimentc/original129'
 for e in removed:assert not (R/e['path']).exists(),e['path']
 for root in roots:assert (a/root).is_dir(),root
else:
 for x in removed:assert not (R/'handoff_payload_26975'/x['path']).exists(),x['path']
print('PASS V5 C original Sabre/Adobe embedded-DNG/no optional LUT assets,',len(removed),'removed,',sum(x['bytes'] for x in removed),'bytes pruned; all required original models retained')
