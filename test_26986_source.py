#!/usr/bin/env python3
import argparse,importlib.util,json,pathlib,subprocess,sys,hashlib,re
R=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('builder',R/'build_26986_incremental.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
p=argparse.ArgumentParser();p.add_argument('--live',action='store_true');p.add_argument('--payload',action='store_true');o=p.parse_args();assert o.live!=o.payload
changed,base,expected=b.scope();root=R if o.live else R/'handoff_payload_26986'
if o.live:b.exact(root,'26986_EXPECTED_FULL_APP.sha256','26986 live exact scope')
else:
 for q in changed:assert b.sha(root/q)==expected[q],q
k=root/'app/src/main/java/com/hinnka/mycamera/processor';j=root/'app/src/main/java/com/particlesdevs/photoncamera'
bridge=(k/'GlesIris26983COnLkrBridge.java').read_text();merge=(k/'GlesIris26983COnGpuMerge.kt').read_text();output=(k/'Iris26985CLinearOutput.kt').read_text();pub=(j/'processing/processor/Iris26983COnBatchPublication.java').read_text();jni=(k/'Iris26985CLkrNative.java').read_text();off=(k/'Iris26986COffDng.kt').read_text();transfer=(k/'Iris26972CCaptureToGallery.kt').read_text();session=(k/'Iris26972CCamera2ShutterSession.kt').read_text()
assert 'T=3, DATA_STEPS=2, OUTPUT_SCALE=2' in bridge and 'TILE=0, OVERLAP=16' in bridge
assert bridge.count('Iris26985CLkrNative.nativeMerge(')==1 and bridge.count('Iris26985CLkrNative.nativeMergeStaged(')==1
assert 'Iris26985CLkrNative.nativeSetExposures(hdrExposures)' in bridge and 'output.actualExposure(times[order[i]])' in bridge and 'Math.log(2.0)/6.0' in bridge
assert 'Iris26985CLkrNative.nativeSetPrior(false)' in bridge and 'Iris26985CLkrNative.nativeSetNoiseModel(null,0f)' in bridge
assert bridge.index('output.consume(reconstructed')<bridge.index('jpegTargets.publish(reconstructed') and 'Iris26985CLkrNative.nativeFree(reconstructed)' in bridge
assert 'Math.multiplyExact(w,2),Math.multiplyExact(h,2)' in bridge and 'stats[11]' in bridge and 'stats[12]' in bridge
assert 'commonBlack,commonWhite,reconstructionWb,OUTPUT_SCALE,TILE,OVERLAP,null' in bridge
assert 'check(!consumed);consumed=true' in output and 'LinearRgbDngWriter.writeStriped' in output and 'LkrLensShading.applyShadingMapped' in output
assert output.index('LkrLensShading.applyShadingMapped')<output.index('if(destination==null)return')<output.index('LinearRgbDngWriter.writeStriped')
assert 'effectiveFrames=accepted.toDouble()' in output and 'result.get(CaptureResult.SENSOR_TIMESTAMP)' in output
assert 'System.loadLibrary("iris26985clkr2420")' in jni
assert 'renderRawLens2420Cleanup(rgb,nativeRgb,w,h,wb,hdrWhite)' in merge and merge.count('renderCOnPostLkr(')==1 and 'val sensorRgb=nativeRgb' in merge
assert 'uniform1i(program,"u_fc_median",1)' in merge and 'GLES30.glUniform1f(uniformLocation(program,"u_defringe"),1f)' in merge
assert 'minOf(h,rows+4)' in merge and 'maxOf(0,y-2)' in merge and 'minOf(h,end+2)' in merge
assert 'rawSaver!=2' in pub and 'rawSaver>=1' in pub and 'PhotonMotionMgc1271Bridge' not in pub
assert 'if (rawSaver != 0) dng = Iris26986COffDng.save' in transfer and 'if (rawSaver != 2) jpeg = requireNotNull(executeOriginal(' in transfer and 'Publication(jpeg, dng).revoke(context)' in transfer
assert 'frozenSharpenBands, offDng, rawSaver) { !cancelled }' in session and 'sharpenBands[0], sharpenBands[1], sharpenBands[2]' in transfer
assert 'C26986GlesMgcRawSpatialStacker26850(' in off and 'exportNormalStackedDng=true' in off and 'writer.setCFAPattern(meta.cfaPattern)' in off and 'writer.setBitsPerSample(16)' in off and 'writer.setWhiteLevel(65535.0)' in off
assert 'Iris26986COffDngGeometry.rebaseGains' in off and 'writer.setDefaultCropZoom(defaultCropZoom)' in off
assert not any(x.startswith(('app/src/main/cpp/','app/src/main/jniLibs/')) for x in changed)
audit=json.loads((R/'26986_DONOR_AUDIT.json').read_text());assert audit['donor_commit']=='b8de711d26d61eeb2362ba1cb647328f437b55b3';assert len(audit['native'])==123
for row in audit['native']:
 assert expected[row['path']]==row['iris_sha256']==base[row['path']]
 if row['relation']=='exact':assert row['iris_sha256']==row['donor_sha256']
 if o.live:assert b.sha(root/row['path'])==row['iris_sha256']
row=audit['jpeg_cleanup'];assert b.sha(root/row['path'])==row['iris_sha256'];shader=(root/row['path']).read_text();body=shader[shader.index('// Post-demosaic chroma cleanup'):shader.index('\nvoid main(){')].strip();assert hashlib.sha256(body.encode()).hexdigest()==row['body_sha256']
for row in audit['off_copies']:
 assert expected[row['original']]==base[row['original']]==row['original_sha256'] and b.sha(root/row['copy'])==row['copy_sha256']
if o.live:
 pipeline=(k/'GlesIris26983COnPipeline.kt').read_text();assert 'GlesIris26983COnLkrBridge.run' in pipeline and 'return linearOutput.dngSaved' in pipeline
 subprocess.run([sys.executable,'-S',str(R/'verify_26986_con_glsl.py')],check=True)
print('PASS exact source scope, 123 pinned native donor files, exact cleanup body, 3x2, HDR reference, shared RGB and independent C OFF Bayer DNG/MGC routing')
