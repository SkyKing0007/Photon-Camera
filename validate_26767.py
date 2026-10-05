#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,re,xml.etree.ElementTree as ET,math
if len(sys.argv)!=3: raise SystemExit('usage: validate_26767.py BASE26766 CAND26767')
base,cand=map(Path,sys.argv[1:])
expected=[p for p in (Path(__file__).with_name('26767_RUNTIME_CHANGED_PATHS.txt')).read_text().splitlines() if p]

def H(root): return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'app').rglob('*') if p.is_file()}
a,b=H(base),H(cand)
assert len(a)==len(b)==1823,(len(a),len(b))
changed=sorted(k for k in set(a)|set(b) if a.get(k)!=b.get(k))
assert changed==sorted(expected),(changed,expected)
assert not (set(b)-set(a)) and not (set(a)-set(b))
print('PASS 26767 exact 9-file runtime allowlist / zero additions')

# Version is part of the frozen candidate.
version=(cand/'app/version.properties').read_text()
assert 'VERSION_NAME=0.9726767' in version and 'VERSION_BUILD=26767' in version
print('PASS 26767 version/build')

# VGN scope: only localMedian and directionalSmooth shader bodies are changed.
rel='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'
bs=(base/rel).read_text(); cs=(cand/rel).read_text()
def raw(src,name):
    anchors=[f'val {name} = """',f'private val {name} = """']
    for anchor in anchors:
        if anchor in src:
            i=src.index(anchor)+len(anchor); j=src.index('""".trimIndent()',i); return src[i:j]
    raise AssertionError(name)
shader_names=['common','universalAdaptiveColor26561','seed','localClamp','localMedian','directionalSmooth','restoreDirection','iirRgb','calculateError','iirError','blendChroma','finalCameraRgb']
shader_changed=[]
for n in shader_names:
    if raw(bs,n)!=raw(cs,n): shader_changed.append(n)
assert shader_changed==['localMedian','directionalSmooth'],shader_changed
assert hashlib.sha256(raw(bs,'seed').encode()).hexdigest()=='621a54fbdace51a1c38902d1ea3f058ae66dfac5b934333185e0e016fa48a532'
assert hashlib.sha256(raw(bs,'localMedian').encode()).hexdigest()=='d373525e6407020b131e2f817a03fff200ccaeb66d2e01cc0fb4741c3cded299'
assert hashlib.sha256(raw(bs,'directionalSmooth').encode()).hexdigest()=='0a1d47e40720adee1279f4e58c416eb8dcde7ceb9895157534ecaaa6351e8b6c'
assert hashlib.sha256(raw(bs,'iirRgb').encode()).hexdigest()=='864514ec018e5bd826f08a28c0f4202656c8c9f4a757795fe5b9fe5b7f777086'
assert hashlib.sha256(raw(cs,'localMedian').encode()).hexdigest()=='645888cf113955f8c5173b7b6f29da69a16c00c4bb0300474e26330ee522adeb'
assert hashlib.sha256(raw(cs,'directionalSmooth').encode()).hexdigest()=='96a87bd3830bcdeed68843161934aca4d68f4e6c1c98173bcb80e75a3f61a3ee'
for marker in ['IRIS_26767_LOCAL_MEDIAN_CHROMA_TOPOLOGY_OWNER','IRIS_26767_DIRECTIONAL_CHROMA_TOPOLOGY_OWNER','IRIS_26767_LOCAL_MEDIAN_SLIDER_ISOLATION']:
    assert cs.count(marker)==1,marker
assert 'max(topologyProtection,chromaTopologyProtection)' in raw(cs,'localMedian')
assert 'selectedChroma=mix(selectedChroma,originalChroma,chromaTopologyProtection26767);' in raw(cs,'directionalSmooth')
assert '1.0-smoothstep(0.72,0.92,centerY)' in raw(cs,'localMedian')
assert '1.0-smoothstep(0.72,0.92,centerY)' in raw(cs,'directionalSmooth')
# Slider carrier may affect localMedian only; the later inherited blend stays fixed at 1.0.
assert 'dispatchLocalMedian(' in cs and 'chromaCorrectionStrength' in cs
blend_host=cs[cs.index('private fun dispatchBlend'):cs.index('private fun dispatchFinal')]
assert 'glUniform1f(host.uniformLocation(blendProgram, "uChromaStrength"), 1f)' in blend_host
assert 'chromaCorrectionStrength' not in blend_host
print('PASS VGN scope: only localMedian + directionalSmooth shader bodies changed; other VGN bodies protected')

# Synthetic topology regression for the exact new equations: isolated/pair false color stays unprotected,
# 3-pixel coherent line and arbitrary two-material boundary earn containment, highlight center veto remains.
def smoothstep(a,b,x):
    t=max(0.0,min(1.0,(x-a)/(b-a)))
    return t*t*(3.0-2.0*t)
def norm(v): return math.hypot(v[0],v[1])
def dist(a,b): return math.hypot(a[0]-b[0],a[1]-b[1])/max(norm(a),norm(b),512.0)
dirs=[(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,-1),(1,-1),(-1,1)]
def evidence(grid,p=(0,0),center_y=0.40):
    c=grid.get(p,(0.0,0.0)); support=0.0; boundary=0.0
    for dx,dy in dirs:
        n=grid.get((p[0]+dx,p[1]+dy),(0.0,0.0)); f=grid.get((p[0]+2*dx,p[1]+2*dy),(0.0,0.0))
        cn,cf,nf=dist(c,n),dist(c,f),dist(n,f)
        same_i=1.0-smoothstep(.18,.42,cn); same_f=1.0-smoothstep(.18,.42,cf)
        support += same_i*(.75+.75*same_f)
        ncont=1.0-smoothstep(.18,.42,nf)
        boundary=max(boundary,smoothstep(.35,.70,cn)*ncont)
    continuity=smoothstep(.90,1.50,support)
    highlight=1.0-smoothstep(.72,.92,center_y)
    interior=continuity*smoothstep(128.0,512.0,norm(c))*highlight
    border=continuity*smoothstep(.35,.70,boundary)*highlight
    return support,continuity,max(interior,border)
red=(8000.0,2000.0); blue=(-6000.0,5000.0); neutral=(0.0,0.0)
assert evidence({(0,0):red})[2]==0.0
assert evidence({(0,0):red,(1,0):red})[2]==0.0
assert evidence({(-1,0):red,(0,0):red,(1,0):red})[2]>.99
half={}
for x in range(-3,4):
  for y in range(-3,4): half[(x,y)]=red if x<=0 else blue
assert evidence(half,(0,0))[2]>.99 and evidence(half,(1,0))[2]>.99
half_neutral={}
for x in range(-3,4):
  for y in range(-3,4): half_neutral[(x,y)]=neutral if x>=0 else red
assert evidence(half_neutral,(0,0))[2]>.99 and evidence(half_neutral,(-1,0))[2]>.99
assert evidence({(-1,0):red,(0,0):red,(1,0):red},center_y=.92)[2]==0.0
print('PASS VGN synthetic regressions: isolated/pair cleanup retained; 3px coherent chroma + arbitrary border containment protected; flattened-highlight center veto retained')

# Fresh experimental preference, direct placement/range, per-lens seeding, Motion-only visibility, Night firewall.
settings_rel='app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java'
settings=(cand/settings_rel).read_text()
assert 'KEY_CHROMA_CORRECTION_STRENGTH = "pref_iris_chroma_correction_strength"' in settings
assert 'snap01(getFloat(sm, KEY_CHROMA_CORRECTION_STRENGTH, 1.0f), 0.0f, 1.0f)' in settings
assert 'boolean correctionSlider = KEY_CHROMA_CORRECTION_STRENGTH.equals(key);' in settings
assert 'float max = correctionSlider ? 1.0f' in settings
bridge=(cand/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
assert 'irisSettings.chromaCorrectionStrength.coerceIn(0.0f, 1.0f)' in bridge
assert 'if (parameters.irisNightActive)' in bridge and 'localMedianOnly26767=true' in bridge
assert 'fixedPolicy26630=true userSetting=false' not in bridge
prefs=(cand/'app/src/main/res/xml/preferences.xml').read_text()
old_i=prefs.index('ns0:key="pref_iris_chroma_denoise"')
new_i=prefs.index('ns0:key="pref_iris_chroma_correction_strength"')
adaptive_i=prefs.index('ns0:key="pref_iris_adaptive_snr_chroma_denoise"')
assert old_i<new_i<adaptive_i
new_tag=prefs[new_i-150:new_i+700]
for token in ['ns1:maxValue="1.0"','ns1:minValue="0.0"','ns1:isFloat="true"','ns1:stepPerUnit="10"']:
    assert token in new_tag,token
ET.parse(cand/'app/src/main/res/xml/preferences.xml')
ET.parse(cand/'app/src/main/res/values/strings.xml')
ET.parse(cand/'app/src/main/res/values/default_prefs.xml')
prefkeys=(cand/'app/src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java').read_text()
assert prefkeys.count('pref_iris_chroma_correction_strength')==2
activity=(cand/'app/src/main/java/com/particlesdevs/photoncamera/ui/settings/SettingsActivity.java').read_text()
assert 'removePreferenceAnywhere(IrisMotionSettings.KEY_CHROMA_CORRECTION_STRENGTH);' in activity
# Retired key remains retired; fresh key avoids stale historical values.
assert 'KEY_CHROMA_CORRECTION_STRENGTH = "pref_iris_vgn_chroma_correction"' not in settings
print('PASS Chroma Correction Strength UI/setting ownership: fresh 0.0..1.0 per-lens Motion control below Chroma Denoise; Night forced 1.0')

# Frozen domains and resource-only scope sanity.
for rel in changed:
    assert not rel.startswith('app/src/main/cpp/'),rel
    assert rel not in [
      'app/src/main/java/com/particlesdevs/photoncamera/processing/DngCreator.java',
      'app/src/main/java/com/particlesdevs/photoncamera/processing/IrisSabreSuperResDngWriter.java',
      'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2DngColorShadow.java',
      'app/src/main/java/com/particlesdevs/photoncamera/api/VendorTagUtils.java']
assert not any(rel.startswith('app/src/main/assets/shaders/') for rel in changed)
print('PASS native/DNG/vendor/asset-shader domains outside 26767 runtime allowlist')
