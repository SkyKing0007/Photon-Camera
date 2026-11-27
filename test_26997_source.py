#!/usr/bin/env python3
"""Exact source guard and C ON ownership checks. C OFF/Night verified against prior source."""
import argparse,json,hashlib,re
import build_26997_incremental as b
p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True);g.add_argument('--live',action='store_true');g.add_argument('--payload',action='store_true');o=p.parse_args();changed,base,expected=b.scope();R=b.R if o.live else b.R/'handoff_payload_26997'
if o.live:b.exact(R,'26997_EXPECTED_FULL_APP.sha256','26997 current physical source')
else:assert all(b.sha(R/f)==expected[f] for f in changed)
mp=json.loads((b.R/'26997_UPSTREAM_SOURCE_MAP.json').read_text());assert mp['donor_commit']=='969d2098ca374690e2646f3ca53ec01a54d7c686'
assert len(mp['files'])==len(set(x['candidate'] for x in mp['files']))
for x in mp['files']:
 assert expected[x['candidate']]==x['candidate_sha256']
 if x['classification']=='exact':assert x['upstream_sha256']==x['candidate_sha256']
 if o.live or x['candidate'] in changed:assert b.sha(R/x['candidate'])==x['candidate_sha256']
N='app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/'
assert set(k for k in expected if k.startswith(N))==set(x['candidate'] for x in mp['files'] if x['candidate'].startswith(N))
J='app/src/main/java/com/particlesdevs/photoncamera/';K='app/src/main/java/com/hinnka/mycamera/processor/'
def read(p):return (R/p).read_text()
cap=read(J+'capture/CaptureController.java');safe=read(J+'capture/Iris26983COnCaptureSafety.java');bridge=read(K+'GlesIris26983COnLkrBridge.java');j=read(N+'lkrl_jni.cpp')
assert 'C_DONOR_PHYSICAL_METER_NOT_READY' not in cap
assert all(x in cap for x in ('iris26996CConfirmedAtShutter(night)','iris26997COnConfirmedAtShutter()','cached.generation!=mIris26548CameraHealthGeneration','witness.session!=mCaptureSession','witness.reader!=mImageReaderRaw','iris26996CSameRequestGeometry(witness.total.getRequest(),current)','iris26983COnSelected() && mImageReaderRaw!=null && !iris26555PreviewOnlyRecoveryActive()','iris26997COnFinishAvailable(plan,"bounded_timeout")','iris26997COnFinishAvailable(iris26593Plan,"submit_unavailable")','iris26985PhysicalPairMatches(result,physicalID,targetNs,targetIso)','iris26983COn09UserManualExposure() || !mMotion26709ReferenceSettled','iris26713RecipeGenerationValid && !iris26997ConfirmedFallback','iris26997SealedBudget = iris26593Plan.iris26983COnOutput!=null ? actualCount : candidateCount','cfg.rawSaver,iris26997SealedBudget','iris26985CBracketEvs = new float[0]','actualCount<2','ticket.retire("C_ON_AVAILABLE_BATCH_"+reason)'))
assert all(x in safe for x in ('available>=2 && available<normals','normals<=24','!shortExpected && !longExpected && brackets==0 && total==normals','completedAttempt<3','ageMs<=2000L'))
assert all(x in bridge for x in ('T=3, DATA_STEPS=2, OUTPUT_SCALE=2','nativeSetPrior(false)','nativeSetDenoise(output.getSuperResDenoise())','nativeSetExposures(null)','nativeSetNoiseModel(noise==null?null:noise.getPath()','nativeSetNoiseModel(null,0f)','orderedRaw[0],w,h,orderedStrides[0]/2','release=2.4.58','nativeProfile.split("\\n")','IRIS_26997_C_LKR_NOISE_MODEL '))
assert bridge.index('nativeMerge(input') < bridge.index('nativeRecordRawNoise(') < bridge.index('output.consume(reconstructed')
assert all(x in j for x in ('g_noise_model = {};','rawlens_noise::combine(model, noise_model.iso','model.supports(noise_model.iso)','rawlens_noise::recordSample(store,shot)','Iris26997NoiseTelemetry noise_telemetry','[noise_model, &noise_telemetry]','int(st.noise_learned)','g_last_profile.insert(0','st.a, st.b, noise_telemetry.weight'))
assert j.index('if (!lkrl::MergeFull(')<j.index('LKR_LOG("IRIS_26997_C_LKR_NOISE_MODEL')
assert all(base[p]==expected[p] for p in base if p not in changed)
if o.live:
 f=read(N+'lkrl_full.cpp');assert f.index('prm.noise_refine(&S.a, &S.b, bins)')<f.index('noise_fit.join()')<f.index('if (st) *st = S')
 # Exact protected independent capture and processing. Historical replay separately executes original full 26996 host checks.
 for p in [J+'processing/experimentc/Iris26975CDonorExposurePolicy.java',K+'Iris26972CCamera2ShutterSession.kt',K+'Iris26972CPhysicalRawSpool.kt',K+'Iris26985CLinearOutput.kt',N+'iris26996_rawdn_noise.h',N+'lkrl_full.cpp']:
  assert p not in changed and b.sha(R/p)==base[p]
 if b.BASE.is_dir():
  prev=(b.BASE/(J+'capture/CaptureController.java')).read_text()
  # Independent C OFF/Night implementation starts after this entry; unchanged methods across the source delta.
  def method(s,name):
   m=re.search(r'(?m)^    (?:private|public|protected) [^\n]*\b'+name+r'\(',s);assert m,name
   start=m.start();a=s.index('{',m.end());depth=1;i=a+1
   while depth:
    depth+=(s[i]=='{')-(s[i]=='}');i+=1
   return s[start:i]
  for name in ('iris26972CStartIndependentCamera2','iris26996CConfirmedAtShutter','iris26996CPhysicalMeter','iris26996CSameRequestGeometry','iris26985FreezePhysicalRadiometry'):
   assert method(prev,name)==method(cap,name),name
  oldj=(b.BASE/(N+'lkrl_jni.cpp')).read_text();assert oldj[oldj.index('extern "C" JNIEXPORT jboolean JNICALL Java_com_hinnka_mycamera_processor_Iris26985CLkrNative_nativeRecordRawNoise'):]==j[j.index('extern "C" JNIEXPORT jboolean JNICALL Java_com_hinnka_mycamera_processor_Iris26985CLkrNative_nativeRecordRawNoise'):]
print('PASS exact C ON capture ownership, preserved independent C OFF/Night and training source, caller-thread noise profile')
