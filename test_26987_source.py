#!/usr/bin/env python3
import argparse,importlib.util,json,pathlib,hashlib,subprocess,sys,tempfile
R=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('builder',R/'build_26987_incremental.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
p=argparse.ArgumentParser();p.add_argument('--live',action='store_true');p.add_argument('--payload',action='store_true');o=p.parse_args();assert o.live!=o.payload
changed,base,expected=b.scope();root=R if o.live else R/'handoff_payload_26987'
if o.live:b.exact(root,'26987_EXPECTED_FULL_APP.sha256','26987 live exact scope')
else:
 for q in changed:assert b.sha(root/q)==expected[q],q
k=root/'app/src/main/java/com/hinnka/mycamera/processor';j=root/'app/src/main/java/com/particlesdevs/photoncamera'
merge=(k/'GlesIris26983COnGpuMerge.kt').read_text();output=(k/'Iris26985CLinearOutput.kt').read_text();pipeline=(k/'GlesIris26983COnPipeline.kt').read_text();params=(j/'processing/render/Parameters.java').read_text();pub=(j/'processing/processor/Iris26983COnBatchPublication.java').read_text()
assert merge.count('renderCOnPostLkr(')==2 and merge.count('renderIris26932LkrMedian(')==1
assert merge.index('renderRawLens2420Cleanup(rgb,nativeRgb,w,h,wb,hdrWhite)')<merge.index('linearOutput.refreshJpegColor(parameters)')<merge.index('renderCOnPostLkr(nativeRgb,nativeClip,jpegColor,outputW,outputH)')<merge.index('packed.packWronskiRgbAndClip26876(sensorRgb,nativeClip)')
assert 'lab=renderRawrLabDefringe26856(temporary,snapshot.postWbCameraToSrgb,1f,w,h)' in merge
assert 'bindTexture(program,"uPreLabWbRgb",1,temporary)' in merge and 'bindTexture(program,"uWbRgb",0,lab)' in merge
assert 'check(input!=temporary && input!=lab && temporary!=lab)' in merge and 'draw(program,w,h,intArrayOf(input))' in merge and 'return input' in merge
assert 'uniform1i(program,"u_fc_median",1)' in merge and 'GLES30.glUniform1f(uniformLocation(program,"u_defringe"),1f)' in merge and 'GLES30.glUniform1f(uniformLocation(program,"u_white_scale"),hdrWhite)' in merge
assert 'check(f.iris26985CBracketEv==0f)' in output and 'referenceTimestamp=ts' in output
assert 'parameters.recalculateCOnColor26987(characteristics,result)' in output and 'val result=capture(ts)' in output and 'checkNotNull(referenceTimestamp)' in output
assert 'ReCalcColor(customNeutr, result, CaptureController.mCameraCharacteristics);' in params and 'ReCalcColor(false, result, characteristics);' in params
assert 'if (!iris26983COnSelected || iris26906ExperimentBSelected || !motionV2Active ||' in params
assert 'Camera2ApiAutoFix.ApplyRes(' not in pub and 'PhotonMotionMgc1271Bridge' not in pub and 'rawSaver>=1' in pub
assert 'val exactClipWb=calculationWhiteBalance26836(parameters.motionV2ColorGains)' in pipeline and 'val exactExif=linearOutput.referenceExif(exif)' in pipeline and pipeline.count('98,exactExif,packed')==2
assert 'return linearOutput.dngSaved' in pipeline and 'check(!consumed);consumed=true' in output and output.index('LkrLensShading.applyShadingMapped')<output.index('if(destination==null)return')<output.index('LinearRgbDngWriter.writeStriped')
# Exact old protection source hashes were read from the 26984 compiled authority.
audit=json.loads((R/'26987_COLOR_RESTORATION_AUDIT.json').read_text());assert audit['native_files_verified']==123
for q,h in audit['old_verified_protected'].items():
 assert base[q]==expected[q]==h
 if o.live:assert b.sha(root/q)==h
frag=(root/'app/src/main/assets/shaders/iris26983/con_fused_final_p3_gain.frag').read_text();start=frag.index('    float mask=max(clamp(guide.a,0.0,1.0),physical.a);');end=frag.index('\n}',start)
assert hashlib.sha256(frag[start:end].encode()).hexdigest()==audit['restored_clip_block_sha256']
# Preserve all actual donor, RAW/DNG and OFF-specific code except named reference metadata additions.
donor=json.loads((R/'26987_DONOR_AUDIT.json').read_text());assert donor['donor_commit']=='b8de711d26d61eeb2362ba1cb647328f437b55b3' and len(donor['native'])==123
for row in donor['native']+[donor['jpeg_cleanup']]:
 assert base[row['path']]==expected[row['path']]==row['iris_sha256']
 if o.live:assert b.sha(root/row['path'])==row['iris_sha256']
for row in donor['off_copies']:
 for kind in ('original','copy'):
  assert expected[row[kind]]==base[row[kind]]==row[kind+'_sha256']
assert not any('COff' in x or 'LkrBridge' in x or '/cpp/' in x or '/jniLibs/' in x for x in changed)
if o.live:
 bridge=(k/'GlesIris26983COnLkrBridge.java').read_text();assert 'T=3, DATA_STEPS=2, OUTPUT_SCALE=2' in bridge and 'Iris26985CLkrNative.nativeSetPrior(false)' in bridge and 'Iris26985CLkrNative.nativeSetNoiseModel(null,0f)' in bridge
 assert bridge.index('output.consume(reconstructed')<bridge.index('jpegTargets.publish(reconstructed')
 subprocess.run([sys.executable,'-S',str(R/'verify_26987_con_glsl.py')],check=True)
 print('PASS live source routes, exact reference, existing donor/DNG source and latest cleanup -> calibrated Lab -> neutral veto -> physical clip guide')
else:print('PASS payload source, calibrated Lab and white restoration, reference ownership, exact donor and protected source manifests')
