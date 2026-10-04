#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26766.py BASE CANDIDATE')
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
assert 'float highlightPreservePermission=1.0-smoothstep(47162.88,60263.68,max(currentY,previousY));' in body(s,'iirRgb')
# Prove the only postprocessor byte delta is the one RGB-authority line.
old='            vec3 correctedRgb = clamp(vec3(centerLuma) + correctedChroma, 0.0, 1.0);'
new='            vec3 correctedRgb = center; // IRIS_26766_BJZHOU_CAMERA_RGB_CONTRACT: preserve VGN camera RGB; alpha metadata remains unchanged.'
assert base.count(old)==1 and new not in base
assert s.count(new)==1 and old not in s
assert s.replace(new,old,1)==base,'26766 postprocessor changed outside exact RGB pass-through line'
# Domain contract: temporary calculation WB is owned only inside VGN and inverted exactly at final camera RGB.
seed=body(s,'seed'); final=body(s,'finalCameraRgb'); universal=body(s,'universalAdaptiveColor26561')
assert '*uCalculationGains' in seed
assert '/max(uCalculationGains,vec3(1e-6))' in final
assert 'uCalculationGains' not in universal
assert 'imageStore(uDestination, p, uvec4(encodedRgb, encodedProtection));' in universal
assert new.strip() in universal
# The stage remains dispatched so alpha/protection metadata carrier semantics are preserved; only RGB ownership is neutralized.
assert 'dispatchUniversalAdaptiveColor(' in s
# Downstream calibrated color owner remains untouched.
color='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java'
postpipe='app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java'
for rel in (color,postpipe):
 assert hashlib.sha256((b/rel).read_bytes()).digest()==hashlib.sha256((c/rel).read_bytes()).digest(),rel
assert 'add(new MotionV2ColorTransform());' in (c/postpipe).read_text()
# Keep the successful 26762 settings regression guard inherited from 26765.
settings_rel='app/src/main/java/com/particlesdevs/photoncamera/ui/settings/SettingsActivity.java'
settings=(c/settings_rel).read_text(); bad=re.compile(r'getBoolean\s*\(\s*SettingsManager\.SCOPE_GLOBAL\s*,\s*IrisMotionSettings\.KEY_RESIDUAL_CHROMA_CUSTOM\s*\)')
assert not bad.search(settings),'26762 regression: two-argument String-key getBoolean reintroduced'
assert 'IrisMotionSettings.KEY_RESIDUAL_CHROMA_CUSTOM, false)' in settings
v=(c/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726766' in v and 'VERSION_BUILD=26766' in v
print('PASS 26766 bjzhou camera-RGB contract: duplicate post-VGN RGB/chroma owner neutralized; 26765/26727 VGN protection exact')
