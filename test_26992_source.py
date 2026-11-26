#!/usr/bin/env python3
"""Fail-closed C OFF-only gain-map boundary and exact source seal."""
import argparse,importlib.util,pathlib,re
R=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('builder',R/'build_26992_incremental.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
p=argparse.ArgumentParser();p.add_argument('--payload',action='store_true');p.add_argument('--live',action='store_true');a=p.parse_args();assert a.payload!=a.live
changed,base,expected=b.scope();root=R if a.live else R/'handoff_payload_26992'
for rel in changed:assert b.sha(root/rel)==expected[rel],rel
K=root/'app/src/main/java/com/hinnka/mycamera/processor';H=K/'experimentc/original129/hdr';g=(H/'GpuReferenceGainmapProducer.kt').read_text();m=(H/'RawGainmapMath.kt').read_text()
for token in ('MIN_GAIN_RATIO = 1.0f','MAX_GAIN_RATIO = 2.0f','smoothStep(0.40f, 0.80f, safeSdr)','smoothStep(0f, 0.50f, excess)','(targetHdrLuma - 1f).coerceAtLeast(0f)','return 1f + highlightWeight * headroomWeight * boundedBoost'):
 assert token in m,token
assert m.count('val strengthRatio = highlightGainRatio(')==2
for token in ('RAW_MIN_GAIN_RATIO = RawGainmapMath.MIN_GAIN_RATIO','RAW_MAX_GAIN_RATIO = RawGainmapMath.MAX_GAIN_RATIO','max(targetHdrLuma - 1.0, 0.0)','smoothstep(0.40, 0.80, sdrLuma)','smoothstep(0.0, 0.50, excess)','1.0 + highlightWeight * headroomWeight * boundedBoost','setRatioMin(config.minGainRatio, config.minGainRatio, config.minGainRatio)','setRatioMax(config.maxGainRatio, config.maxGainRatio, config.maxGainRatio)','setGamma(1.0f, 1.0f, 1.0f)','setDisplayRatioForFullHdr(fullHdrRatio)','val fullHdrRatio = config.maxGainRatio'):
 assert token in g,token
assert 'float candidateRatio = clamp(' not in g
if a.live:
 b.exact(R,'26992_EXPECTED_FULL_APP.sha256','26992 live source')
 engine=K/'experimentc/Iris26975CPinnedDonorProEngine.kt';s=engine.read_text()
 for token in ('private val rawGpuGainmapProducer = GpuReferenceGainmapProducer()','rawGpuGainmapProducer.build(','sdrBase = checkNotNull(sdr)','HdrBuffer(hdrBitmap, HdrBufferEncoding.LINEAR_SRGB)','Jpeg444ExportEncoder.write(\n                checkNotNull(sdr)','gainmapResult = gainmap,','NoLookLutRawGainmapSidecar.create(checkNotNull(sdr))'):
  assert token in s,token
 owners=[f for f in (R/'app/src/main/java').rglob('*.kt') if 'GpuReferenceGainmapProducer()' in f.read_text(errors='strict')];assert owners==[engine],owners
 # Exact protected bytes prove no edits to the SDR renderer, encoder, capture, C ON or A/B.
 assert len(set(base)-changed)==2657 and all(base[x]==expected[x] for x in set(base)-changed)
print('PASS C OFF-only gain-map policy, SDR ingress and output contract, exact protected source')
