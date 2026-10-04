#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26763.py BASE CANDIDATE')
b,c=map(Path,sys.argv[1:])
expected=[
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/version.properties',
]
def H(root): return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'app').rglob('*') if p.is_file()}
a,z=H(b),H(c); assert len(a)==len(z)==1823
changed=sorted(k for k in set(a)|set(z) if a.get(k)!=z.get(k)); assert changed==expected,changed
s=(c/expected[0]).read_text(); base=(b/expected[0]).read_text()
assert s.count('IRIS_26763_NEUTRAL_CFA_OWNERSHIP_ADMISSION_VETO')==1
for token in [
'neutralSameSurfaceSupport26763','phasePatternSupport26763','nearMaterialSupport26763',
'contourMaterialSupport26763','neutralCfaOwnershipVeto26763','ownershipContinuation26763',
'centerTrust*neutralSurfaceEvidence26763*neutralLeakOutlier26763*',
'neutralLeakPhase26763*(1.0-realMaterialTopology26763)',
'smoothstep(0.55,0.82,ownershipContinuation26763)',
'smoothstep(0.35,0.75,ownershipContinuation26763)',
'if(ownershipContinuation26763>0.35)']:
 assert token in s,token
# Preserve established owners in the modified file.
for token in ['IRIS_26729_COLOR_MATERIAL_DIRECTION_GATE','IRIS_26730_PHYSICAL_VALIDITY_CONTAINMENT_AUTHORITY',
              'IRIS_26731_FROZEN_RECIPROCAL_MATERIAL_OWNERSHIP','IRIS_26733_INHERITED_HIGHLIGHT_HEADROOM_OWNER',
              'IRIS_26707_VALID_CFA_NEUTRAL_SURFACE_LEAK_REJECT','IRIS_26728_PHYSICALLY_SUPPORTED_CHROMA_MAGNITUDE']:
 assert s.count(token)==base.count(token) and s.count(token)>0,token
# No RGB/luma repaint in the 26763 admission block.
block=s.split('IRIS_26763_NEUTRAL_CFA_OWNERSHIP_ADMISSION_VETO',1)[1].split('IRIS_26733_INHERITED_HIGHLIGHT_HEADROOM_OWNER',1)[0]
for forbidden in ['imageStore(','correctedChroma','mix(center','uCalculationGains=']:
 assert forbidden not in block,forbidden
v=(c/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726763' in v and 'VERSION_BUILD=26763' in v
# Exact 26762 Actions compiler regression: never reintroduce String key into two-argument getBoolean.
settings=(c/'app/src/main/java/com/particlesdevs/photoncamera/ui/settings/SettingsActivity.java').read_text()
bad=re.compile(r'getBoolean\s*\(\s*SettingsManager\.SCOPE_GLOBAL\s*,\s*IrisMotionSettings\.KEY_RESIDUAL_CHROMA_CUSTOM\s*\)')
assert not bad.search(settings),'26762 regression: two-argument String-key getBoolean reintroduced'
assert 'IrisMotionSettings.KEY_RESIDUAL_CHROMA_CUSTOM, false)' in settings
print('PASS 26763 semantics/ownership + permanent 26762 Java compiler regression')
