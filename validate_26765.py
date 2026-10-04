#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26765.py BASE CANDIDATE')
b,c=map(Path,sys.argv[1:])
post='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'
expected=[post,'app/version.properties']
def H(root): return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'app').rglob('*') if p.is_file()}
a,z=H(b),H(c); assert len(a)==len(z)==1823
changed=sorted(k for k in set(a)|set(z) if a.get(k)!=z.get(k)); assert changed==expected,changed
base=(b/post).read_text(); s=(c/post).read_text()
def body(src,name):
 anchor=f'val {name} = """'; i=src.index(anchor)+len(anchor); j=src.index('""".trimIndent()',i); return src[i:j]
authority={
'seed':'621a54fbdace51a1c38902d1ea3f058ae66dfac5b934333185e0e016fa48a532',
'localMedian':'d373525e6407020b131e2f817a03fff200ccaeb66d2e01cc0fb4741c3cded299',
'directionalSmooth':'0a1d47e40720adee1279f4e58c416eb8dcde7ceb9895157534ecaaa6351e8b6c',
'iirRgb':'864514ec018e5bd826f08a28c0f4202656c8c9f4a757795fe5b9fe5b7f777086',
}
for name,want in authority.items():
 got=hashlib.sha256(body(s,name).encode()).hexdigest(); assert got==want,(name,got,want)
# Prove the postprocessor delta is ONLY the four exact 26727 shader bodies.
reconstructed=s
for name in authority:
 cb=body(base,name); anchor=f'val {name} = """'; i=reconstructed.index(anchor)+len(anchor); j=reconstructed.index('""".trimIndent()',i); reconstructed=reconstructed[:i]+cb+reconstructed[j:]
assert reconstructed==base,'postprocessor changed outside exact four VGN shader bodies'
# Explicitly prove 26729 color/material topology family is absent from restored protection shaders.
joined='\n'.join(body(s,n) for n in authority)
for token in ['IRIS_26729_COLOR_MATERIAL_DIRECTION_GATE','IRIS_26729_COLOR_MATERIAL_MEDIAN_GATE','colorOnlyMaterialBoundary','colorMaterialBoundary','centerMaterialContinuation','materialChromaAt']:
 assert token not in joined,token
# 26727 inherited highlight permission must be exact in restored IIR protection.
assert 'float highlightPreservePermission=1.0-smoothstep(47162.88,60263.68,max(currentY,previousY));' in body(s,'iirRgb')
# Current non-VGN controls and runtime areas remain byte-identical.
for rel in [
'app/src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java',
'app/src/main/java/com/particlesdevs/photoncamera/ui/settings/SettingsActivity.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/hinnka/mycamera/raw/MgcFullResolutionDenoise.kt']:
 assert hashlib.sha256((b/rel).read_bytes()).digest()==hashlib.sha256((c/rel).read_bytes()).digest(),rel
settings=(c/'app/src/main/java/com/particlesdevs/photoncamera/ui/settings/SettingsActivity.java').read_text()
bad=re.compile(r'getBoolean\s*\(\s*SettingsManager\.SCOPE_GLOBAL\s*,\s*IrisMotionSettings\.KEY_RESIDUAL_CHROMA_CUSTOM\s*\)')
assert not bad.search(settings),'26762 regression: two-argument String-key getBoolean reintroduced'
assert 'IrisMotionSettings.KEY_RESIDUAL_CHROMA_CUSTOM, false)' in settings
v=(c/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726765' in v and 'VERSION_BUILD=26765' in v
print('PASS 26765 exact successful-26727 VGN protection bodies; no other postprocessor delta')
