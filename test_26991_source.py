#!/usr/bin/env python3
"""Exact source gate; active C-only route, HDR OFF and text-only slider contract."""
import argparse,importlib.util,pathlib,xml.etree.ElementTree as ET
R=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('builder',R/'build_26991_incremental.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
p=argparse.ArgumentParser();p.add_argument('--payload',action='store_true');p.add_argument('--live',action='store_true');a=p.parse_args();assert a.payload!=a.live
changed,base,expected=b.scope();root=R if a.live else R/'handoff_payload_26991'
for rel in changed:assert b.sha(root/rel)==expected[rel],rel
K=root/'app/src/main/java/com/hinnka/mycamera/processor';J=root/'app/src/main/java/com/particlesdevs/photoncamera'
g=(K/'GlesIris26983COnGpuMerge.kt').read_text();j=(K/'GlesIris26983COnLkrBridge.java').read_text();l=(K/'Iris26985CLinearOutput.kt').read_text()
run=g[g.index('fun run(frames:'):g.index('private fun renderCOnPostLkr')]
post=g[g.index('private fun renderCOnPostLkr'):g.index('private fun ensureIris26859BLensMapTexture')]
for token in ('GlesIris26983COnSceneMotion.classify','GlesIris26983COnGpuSharpest.select','GlesIris26983COnHighlightReference.select','cfaPattern,highlight,','GlesIris26983COnLkrBridge.nativePublishRgba16f','renderCOnPostLkr(nativeRgb,nativeClip'):
 assert token in run,token
assert run.index('GlesIris26983COnSceneMotion.classify')<run.index('GlesIris26983COnGpuSharpest.select')<run.index('GlesIris26983COnHighlightReference.select')<run.index('GlesIris26983COnLkrBridge.run')
assert post.count('renderIris26932LkrMedian(')==1 and post.count('renderRawrLabDefringe26856(')==1
assert post.index('applyAmazeWbForLabFcc')<post.index('renderIris26932LkrMedian(')<post.index('renderRawrLabDefringe26856(')<post.index('GlesIris26983COnSmoothWhite.shader')
assert 'con_26986_rawlens_cleanup.frag' not in g and 'LkrLensShading.applyShadingMapped(pixels,w,h,model,0,f.iris26985CRawCropY,.5f,.5f)' in l
assert l.index('LkrLensShading.applyShadingMapped')<l.index('if(destination==null)return')<l.index('LinearRgbDngWriter.writeStriped')
for token in ('bracket.length!=0','Iris26985CLkrNative.nativeSetExposures(null)','stats[14]!=1f','stage=nativePrepare(orderedRaw,orderedStrides,orderedBlacks,orderedWhites,w,h)','orderedStrides[i]!=w*2','orderedWhites[i]!=orderedWhites[0]','orderedBlacks[i*4+phase]!=orderedBlacks[phase]','commonWhite=65535f','nativePublishClipR16f(raw[referenceIndex],strides[referenceIndex]','output.referenceWb(times[chosen])','T=3, DATA_STEPS=2, OUTPUT_SCALE=2'):
 assert token in j,token
assert 'nativeMergeStaged(' not in j and 'nativeStage(' not in j and 'nativeSetPrior(false)' in j
assert 'if(stage!=null)for(ByteBuffer b:stage)if(b!=null)Iris26985CLkrNative.nativeFree(b)' in j
assert 'if(reconstructed!=null)Iris26985CLkrNative.nativeFree(reconstructed)' in j
texts=[('Fine Detail','Controls microtexture such as fabric weave, hair, grass and fine foliage. Higher values may emphasize noise.'),('Medium Detail','Controls defined textures, leaf edges, facial features and small object boundaries.'),('Coarse Detail','Controls broader edges, local contrast and overall perceived clarity. Higher values may emphasize halos.')]
res=root/'app/src/main/res';strings={x.attrib['name']:x.text for x in ET.parse(res/'values/strings.xml').getroot() if 'name' in x.attrib};android='{http://schemas.android.com/apk/res/android}';custom='{http://schemas.android.com/apk/res-auto}'
xml=ET.parse(res/'xml/preferences.xml').getroot();activity=(J/'ui/settings/SettingsActivity.java').read_text()
for i,(title,desc) in enumerate(texts):
 key=f'iris_c_mgc_band_{i}';assert strings[key]==f'MGC Sharpening Band {i} — {title}' and strings[key+'_summary']==desc
 node=next(x for x in xml.iter() if x.get(android+'key')==f'pref_iris_26982_c_mgc_band_{i}')
 assert node.get(android+'title')=='@string/'+key and node.get(android+'summary')=='@string/'+key+'_summary'
 assert node.get(custom+'minValue')=='0.0' and node.get(custom+'maxValue')=='2.0' and node.get(custom+'stepPerUnit')=='10'
 assert 'R.string.'+key+'_summary' in activity
if a.live:
 b.exact(root,'26991_EXPECTED_FULL_APP.sha256','26991 live source')
 for rel in ('app/src/main/cpp/iris26864/Iris26983COnLkrAndroidInterop.cpp','app/src/main/java/com/hinnka/mycamera/processor/GlesIris26983COnRawLensMedian.kt','app/src/main/java/com/hinnka/mycamera/processor/GlesIris26983COnSmoothWhite.kt','app/src/main/java/com/hinnka/mycamera/processor/GlesIris26983COnHighlightReference.kt'):
  assert b.sha(root/rel)==base[rel]==expected[rel]
 capture=(J/'capture/CaptureController.java').read_text();assert 'final float[] iris26985CBracketEvs = new float[0]' in capture
print('PASS exact C-only legacy chroma path, per-frame normalization, HDR OFF, physical LSC, exact MGC texts and unchanged slider ranges')
