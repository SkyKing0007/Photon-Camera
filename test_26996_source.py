#!/usr/bin/env python3
"""Exact candidate, protected domains, physical ownership, and private donor noise integration."""
import argparse,json,hashlib
import build_26996_incremental as b
p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True);g.add_argument('--live',action='store_true');g.add_argument('--payload',action='store_true');o=p.parse_args();changed,base,expected=b.scope();R=b.R if o.live else b.R/'handoff_payload_26996'
if o.live:b.exact(R,'26996_EXPECTED_FULL_APP.sha256','26996 current physical source')
else:assert all(b.sha(R/f)==expected[f] for f in changed)
mp=json.loads((b.R/'26996_UPSTREAM_SOURCE_MAP.json').read_text());assert mp['donor_commit']=='969d2098ca374690e2646f3ca53ec01a54d7c686'
assert len(mp['files'])==len(set(x['candidate'] for x in mp['files']))
for x in mp['files']:
 assert expected[x['candidate']]==x['candidate_sha256']
 if x['classification']=='exact':assert x['upstream_sha256']==x['candidate_sha256']
 if o.live or x['candidate'] in changed:assert b.sha(R/x['candidate'])==x['candidate_sha256']
N='app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/'
assert set(k for k in expected if k.startswith(N))==set(x['candidate'] for x in mp['files'] if x['candidate'].startswith(N))
J='app/src/main/java/com/particlesdevs/photoncamera/';K='app/src/main/java/com/hinnka/mycamera/processor/'
def read(p):return (R/p).read_text()
cap=read(J+'capture/CaptureController.java');pol=read(J+'processing/experimentc/Iris26975CDonorExposurePolicy.java');session=read(K+'Iris26972CCamera2ShutterSession.kt');spool=read(K+'Iris26972CPhysicalRawSpool.kt');bridge=read(K+'GlesIris26983COnLkrBridge.java');out=read(K+'Iris26985CLinearOutput.kt');j=read(N+'lkrl_jni.cpp');h=read(N+'iris26996_rawdn_noise.h')
assert 'C_DONOR_PHYSICAL_METER_NOT_READY' not in cap
assert all(x in cap for x in ('iris26996CConfirmedAtShutter(night)','witness.session!=mCaptureSession','witness.reader!=mImageReaderRaw','witness.motion==night','iris26996CSameRequestGeometry','mIris26980CWaitingForLock=false','manualRequestMatches','freezeConfirmed(','if (!night && cCurrentRaw)','Math.min(missing,owner.attemptsRemaining())','owner.onSequenceReady();','C_PHYSICAL_SENSOR_RESULT_UNAVAILABLE'))
assert 'return new Pair(actualShutter,actualIso);' in pol and 'return freeze(userShutter,userIso,actualShutter,actualIso' in pol
assert all(x in session for x in ('private var sequenceReady = night','if (!sequenceEnded) return','requireAllAccepted = true','requireAllAccepted = false','check(actualCount in 2..frameCount)','maxAttempts = frameCount * 3'))
assert all(x in spool for x in ('raws.size < 2','!results.keys.containsAll(raws.keys)','results.keys.retainAll(raws.keys)','paired.first().metadata.sensorTimestampNs','paired.size, shutter.night','check(hasCompletePhysicalBurst())'))
assert all(x in bridge for x in ('T=3, DATA_STEPS=2, OUTPUT_SCALE=2','nativeSetPrior(false)','nativeSetDenoise(output.getSuperResDenoise())','nativeSetExposures(null)','nativeSetNoiseModel(noise==null?null:noise.getPath()','nativeSetNoiseModel(null,0f)','orderedRaw[0],w,h,orderedStrides[0]/2','release=2.4.58'))
assert bridge.index('nativeMerge(input') < bridge.index('nativeRecordRawNoise(') < bridge.index('output.consume(reconstructed')
assert all(x in out for x in ('frame.motionV2ActualIso','frame.iris26985CBracketEv != 0f','Build.FINGERPRINT','iris26996c-wavelet-noise','SENSOR_PIXEL_MODE','SENSOR_MAX_ANALOG_SENSITIVITY'))
assert all(x in j for x in ('std::exchange(g_no_prior, true)','g_noise_model = {};','rawlens_noise::combine(model, noise_model.iso','model.supports(noise_model.iso)','GetDirectBufferCapacity(raw)','iris26996_noise::rawdn_estimate_noise(data','rawlens_noise::recordSample(store,shot)','const bool npu_denoise = false;'))
frag='int rawdn_estimate_noise'+h.split('inline int rawdn_estimate_noise',1)[1].rsplit('\n}',1)[0]
assert hashlib.sha256(frag.encode()).hexdigest()==next(x['upstream_fragment_sha256'] for x in mp['files'] if x['candidate']==N+'iris26996_rawdn_noise.h')
assert 'native boolean nativeRecordRawNoise' in read(K+'Iris26985CLkrNative.java')
assert not any('denoiser.bin' in p for p in expected if 'iris26985c_lkr2420' in p)
assert all(base[p]==expected[p] for p in base if p not in changed)
print('PASS C capture-only ownership, exact protected image pipeline, actual single-frame learned-noise training and donor coverage')
