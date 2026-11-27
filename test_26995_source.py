#!/usr/bin/env python3
"""Exact source ownership, native donor coverage, user settings and unchanged protected runtime."""
import argparse,json,re,pathlib,xml.etree.ElementTree as ET
import build_26995_incremental as b
p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True);g.add_argument('--live',action='store_true');g.add_argument('--payload',action='store_true');o=p.parse_args();changed,base,expected=b.scope();R=b.R if o.live else b.R/'handoff_payload_26995'
if o.live:b.exact(R,'26995_EXPECTED_FULL_APP.sha256','26995 current physical source')
else:assert all(b.sha(R/f)==expected[f] for f in changed)
mp=json.loads((b.R/'26995_UPSTREAM_SOURCE_MAP.json').read_text());assert mp['donor_commit']=='969d2098ca374690e2646f3ca53ec01a54d7c686'
assert len(mp['files'])==len(set(x['candidate'] for x in mp['files']))
for x in mp['files']:
 assert expected[x['candidate']]==x['candidate_sha256']
 if x['classification']=='exact':assert x['upstream_sha256']==x['candidate_sha256']
 if o.live or x['candidate'] in changed:assert b.sha(R/x['candidate'])==x['candidate_sha256']
N='app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/'
assert set(k for k in expected if k.startswith(N))==set(x['candidate'] for x in mp['files'] if x['candidate'].startswith(N))
J='app/src/main/java/com/particlesdevs/photoncamera/';K='app/src/main/java/com/hinnka/mycamera/processor/'
def read(p):return (R/p).read_text()
j=read(N+'lkrl_jni.cpp');a=read(N+'lkrl_adapter.cpp');f=read(N+'lkrl_full.cpp');pr=read(N+'lkrl_prior.cpp');api=read(N+'lkrl_api.h');cm=read(N+'CMakeLists.txt')
assert all(x in j for x in ('thread_local bool g_no_prior = true;','std::exchange(g_no_prior, true)','g_no_prior = enabled != JNI_TRUE;','prm.solve.no_prior = no_prior;','prm.solve.highlight_recovery = highlight_rec;','const bool npu_denoise = false;','iris26985c_lkrl_2458_pipelines.bin'))
assert 'bool align2 = true;' in api and 'bool dct_prior = false;' in api and 'bool dct_fallback = true;' in api
assert all(x in a for x in ('if (T.prm.no_prior)','T.prm.dct_prior = false;','T.prm.notch = false;','T.prm.grain = 0.0f;','T.prm.fallback_chroma = 0.0f;','T.prm.shadow_chroma = 0.0f;','!prm.no_prior && !prior'))
assert 'if (!sp.no_prior && lk > 0.0f)' in f and 'PatchSeed' in f and 'IRIS26985C_NO_NNAPI=1' in cm and 'lkrl_patchseed.cpp' in cm
assert 'NNAPI excluded' in pr and 'Existing Iris policy: learned network OFF' in pr
assert not any('denoiser.bin' in p for p in expected if 'iris26985c_lkr2420' in p)
bridge=read(K+'GlesIris26983COnLkrBridge.java');assert 'T=3, DATA_STEPS=2, OUTPUT_SCALE=2' in bridge and 'nativeSetPrior(false)' in bridge and 'nativeSetDenoise(output.getSuperResDenoise())' in bridge and 'nativeSetExposures(null)' in bridge and 'nativeSetNoiseModel(null,0f)' in bridge
assert 'stats[14]<1f' in bridge and 'hdrWhite.isFinite() && hdrWhite>=1f' in read(K+'GlesIris26983COnGpuMerge.kt')
assert 'val superResDenoise: Boolean' in read(K+'Iris26985CLinearOutput.kt')
assert 'native void nativeSetDenoise(boolean enabled)' in read(K+'Iris26985CLkrNative.java')
for p in ('capture/CaptureController.java','processing/DefaultSaver.java','processing/ImageSaver.java','processing/processor/Iris26983COnBatchPublication.java'):assert 'superResDenoise' in read(J+p),p
s=read(J+'settings/Iris26995SuperResDenoiseSettings.java');assert 'getBoolean(lens,false)' in s and 'putBoolean(lens,enabled)' in s
s=read(J+'ui/settings/custompreferences/Iris26995SuperResDenoisePreference.java');assert 'extends ManagedSwitchPreference' in s and 'PreferenceKeys.getCameraID()' in s
s=read(J+'ui/settings/SettingsActivity.java');assert 'lkrDenoise.setVisible(haveSelected && cameraMode==CameraMode.MOTION' in s
xml=ET.parse(R/'app/src/main/res/xml/preferences.xml');ns='{http://schemas.android.com/apk/res/android}'
for parent in xml.iter():
 children=list(parent)
 for i,node in enumerate(children):
  if node.get(ns+'key')=='@string/pref_hdrx_nr_key':
   d=children[i+1];assert d.get(ns+'key')=='pref_iris_26995_lkr_denoise' and d.get(ns+'title')=='Super Res Denoise' and d.get(ns+'defaultValue')=='false';assert d.get(ns+'layout')==node.get(ns+'layout') and d.get(ns+'icon')==node.get(ns+'icon');break
 else:continue
 break
else:raise AssertionError('missing Noise Reduction sibling')
print('PASS full donor runtime source coverage, frozen per-lens C ON denoise, native defaults, output and exclusive source allowlist')
