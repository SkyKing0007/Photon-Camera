#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26764.py BASE CANDIDATE')
b,c=map(Path,sys.argv[1:])
post='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'
expected=[post,'app/version.properties']
def H(root): return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'app').rglob('*') if p.is_file()}
a,z=H(b),H(c); assert len(a)==len(z)==1823
changed=sorted(k for k in set(a)|set(z) if a.get(k)!=z.get(k)); assert changed==expected,changed
s=(c/post).read_text(); base=(b/post).read_text()
# Exact 26764 ownership-precedence correction must exist once in each active stage.
for token in [
'/* IRIS_26764_CONNECTED_HIGHLIGHT_HEADROOM_DIRECTION\n',
'/* IRIS_26764_CONNECTED_HIGHLIGHT_HEADROOM_MEDIAN\n',
'/* IRIS_26764_CONNECTED_HIGHLIGHT_HEADROOM_DIRECTIONAL_RESTORE\n']:
 assert s.count(token)==1,token
for token in [
'connectedHighlightHeadroom26764[i]=1.0-smoothstep(0.72,0.92,connectedPeakY26764)',
'materialStepProof * physicalTrust * highlightColorOwnershipPermission *\n                    connectedHighlightHeadroom26764[i]',
'connectedHighlightHeadroom26764=1.0-smoothstep(0.72,0.92,connectedPeakY26764)',
'materialStepProof*physicalTrust*ownershipColorPermission*connectedHighlightHeadroom26764',
'topologyHighlightHeadroom26764=1.0-smoothstep(0.72,0.92,topologyConnectedPeakY26764)',
'topologyProtection*=topologyHighlightHeadroom26764']:
 assert token in s,token
# The inherited 26727 headroom range remains exact and preVgnPeak restoration is untouched.
assert s.count('smoothstep(0.72,0.92') >= base.count('smoothstep(0.72,0.92') + 3
assert 'float highlightSafe = 1.0 - smoothstep(0.78, 0.92, max(preVgnPeak, centerLuma));' in s
# Preserve all established owner markers and the ineffective 26763 experiment byte-semantically around its block.
for token in ['IRIS_26763_NEUTRAL_CFA_OWNERSHIP_ADMISSION_VETO','IRIS_26729_COLOR_MATERIAL_DIRECTION_GATE',
              'IRIS_26730_PHYSICAL_VALIDITY_CONTAINMENT_AUTHORITY','IRIS_26731_FROZEN_RECIPROCAL_MATERIAL_OWNERSHIP',
              'IRIS_26733_INHERITED_HIGHLIGHT_HEADROOM_OWNER','IRIS_26707_VALID_CFA_NEUTRAL_SURFACE_LEAK_REJECT',
              'IRIS_26728_PHYSICALLY_SUPPORTED_CHROMA_MAGNITUDE']:
 assert s.count(token)==base.count(token) and s.count(token)>0,token
# 26731 IIR must remain frozen to ownership; do not reintroduce post-filter chroma reclassification.
iir=s.split('val iirRgb = """',1)[1].split('""".trimIndent()',1)[0]
assert 'IRIS_26731_FROZEN_IIR_MATERIAL_OWNERSHIP' in iir
assert 'frozenMaterialBoundary=i>0&&!transportFromPreviousAllowed(p,previousP)' in iir
assert 'colorOnlyMaterialBoundary' not in iir
# No changes to 26762 setting/control transport files.
for rel in [
'app/src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java',
'app/src/main/java/com/particlesdevs/photoncamera/ui/settings/SettingsActivity.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/hinnka/mycamera/raw/MgcFullResolutionDenoise.kt']:
 assert hashlib.sha256((b/rel).read_bytes()).digest()==hashlib.sha256((c/rel).read_bytes()).digest(),rel
# Permanent 26762 Java compiler regression.
settings=(c/'app/src/main/java/com/particlesdevs/photoncamera/ui/settings/SettingsActivity.java').read_text()
bad=re.compile(r'getBoolean\s*\(\s*SettingsManager\.SCOPE_GLOBAL\s*,\s*IrisMotionSettings\.KEY_RESIDUAL_CHROMA_CUSTOM\s*\)')
assert not bad.search(settings),'26762 regression: two-argument String-key getBoolean reintroduced'
assert 'IrisMotionSettings.KEY_RESIDUAL_CHROMA_CUSTOM, false)' in settings
v=(c/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726764' in v and 'VERSION_BUILD=26764' in v
print('PASS 26764 exact bright-boundary precedence + inherited owner/compiler regressions')
