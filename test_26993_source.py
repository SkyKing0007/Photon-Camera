#!/usr/bin/env python3
"""Exact new scope, active path and inherited highlight/SDR invariants."""
import argparse,pathlib,importlib.util,re
R=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('builder',R/'build_26993_incremental.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
p=argparse.ArgumentParser();p.add_argument('--payload',action='store_true');p.add_argument('--live',action='store_true');a=p.parse_args();assert a.payload!=a.live
changed,base,expected=b.scope();root=R if a.live else R/'handoff_payload_26993'
for rel in changed:assert b.sha(root/rel)==expected[rel],rel
K=root/'app/src/main/java/com/hinnka/mycamera/processor/experimentc';J=root/'app/src/main/java/com/particlesdevs/photoncamera';RAW=K/'original129/raw'
engine=(K/'Iris26975CPinnedDonorProEngine.kt').read_text();d=(RAW/'RawDemosaicProcessor.kt').read_text();adj=(RAW/'RawAdjustmentPass.kt').read_text()
assert engine.count('iris26993COffShadowLift = true,')==1 and 'rawRenderingEngine = RawRenderingEngine.AdobeCurve,\n                iris26993COffShadowLift = true,' in engine
assert d.count('iris26993COffShadowLift: Boolean = false,')==3
assert d.count('iris26993COffShadowLift = iris26993COffShadowLift,')==2
assert 'return shadowsHighlightsParams.iris26993COffShadowLift ||' in d and 'iris26993COffShadowLift = shadowsHighlightsParams.iris26993COffShadowLift,' in d
part=d[d.index('private fun renderCombinedPass('):d.index('private fun renderEngineTonePass(')];assert part.index('renderEngineTonePass(')<part.index('renderAdjustmentPass(')<part.index('renderSrgbPass(')
for token in ('uniform int uIris26993COffShadowLift;','if (input.iris26993COffShadowLift) 1 else 0','if (y <= 0.0005 || y >= 0.65) return 0.0;','if (uIris26993COffShadowLift != 0) color = iris26993LiftShadows(color);','float gain = min(exp2(ev), max(1.0, 1.0 / max(peak, 0.00000001)));'):
 assert token in adj,token
assert adj.index('color = applyBlackWhiteLevels(color);')<adj.index('color = iris26993LiftShadows(color);')
for token in ('private val rawGpuGainmapProducer = GpuReferenceGainmapProducer()','rawGpuGainmapProducer.build(','sdrBase = checkNotNull(sdr)','HdrBuffer(hdrBitmap, HdrBufferEncoding.LINEAR_SRGB)','Jpeg444ExportEncoder.write(\n                checkNotNull(sdr)','gainmapResult = gainmap,','NoLookLutRawGainmapSidecar.create(checkNotNull(sdr))'):
 assert token in engine,token
c=(J/'capture/CaptureController.java').read_text();m=(J/'processing/MotionBatch.java').read_text();pub=(J/'processing/processor/Iris26983COnBatchPublication.java').read_text()
assert c.count('iris26593Plan.iris26983COnOutput == null ? null : iris26593Plan.physicalCameraId')==1
assert 'iris26985FreezePhysicalRadiometry(frame,frameResult,iris26593Plan.physicalCameraId)' in c
assert 'this.iris26524OwnerCameraId = iris26993COnPhysicalOwner == null\n                ? iris26524Zoom.ownerCameraId : iris26993COnPhysicalOwner;' in m
assert 'failure.printStackTrace(new java.io.PrintWriter(trace));' in pub and 'IRIS_26993_C_ON_FAILURE stage=' in pub
p=(root/'app/src/main/java/com/unspektrawesome/camera/RawPreviewPolicy.java').read_text();sel=p[p.index('public static RawOutput selectCaptureOutput('):p.index('static Size2d scaledEven(')];assert '.filter(output -> !output.maximumResolutionMode && output.format == format)' in sel and 'RawFormat.RAW10, RawFormat.RAW12, RawFormat.RAW_SENSOR' in sel
assert not any('/cpp/' in rel or '/jniLibs/' in rel or '/assets/' in rel for rel in changed)
if a.live:
 b.exact(R,'26993_EXPECTED_FULL_APP.sha256','26993 live source')
 owners=[f for f in (R/'app/src/main/java').rglob('*.kt') if 'iris26993COffShadowLift = true,' in f.read_text()];assert owners==[K/'Iris26975CPinnedDonorProEngine.kt'],owners
 h=K/'original129/hdr';g=(h/'GpuReferenceGainmapProducer.kt').read_text();m=(h/'RawGainmapMath.kt').read_text()
 for token in ('MIN_GAIN_RATIO = 1.0f','MAX_GAIN_RATIO = 2.0f','smoothStep(0.40f, 0.80f, safeSdr)','smoothStep(0f, 0.50f, excess)','(targetHdrLuma - 1f).coerceAtLeast(0f)','return 1f + highlightWeight * headroomWeight * boundedBoost'):assert token in m,token
 for token in ('max(targetHdrLuma - 1.0, 0.0)','smoothstep(0.40, 0.80, sdrLuma)','smoothstep(0.0, 0.50, excess)','1.0 + highlightWeight * headroomWeight * boundedBoost'):assert token in g,token
 for f in [h/'GpuReferenceGainmapProducer.kt',h/'RawGainmapMath.kt',h/'HdrGainmapStrength.kt']:
  rel=f.relative_to(R).as_posix();assert b.sha(f)==base[rel]==expected[rel]
 assert len(set(base)-changed)==2652 and all(base[x]==expected[x] for x in set(base)-changed)
print('PASS 26993 exact active C OFF shadow, frozen physical C ON admission, binned Spektra and protected gain map/native/A-B scope')
