#!/usr/bin/env python3
"""Exact current source and byte-for-byte removal of only watermark plumbing."""
import argparse,pathlib,importlib.util,subprocess,tempfile,shutil
R=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('builder',R/'build_26994_incremental.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
p=argparse.ArgumentParser();p.add_argument('--payload',action='store_true');p.add_argument('--live',action='store_true');a=p.parse_args();assert a.payload!=a.live
changed,base,expected=b.scope();root=R if a.live else R/'handoff_payload_26994'
for rel in changed:assert b.sha(root/rel)==expected[rel],rel
K=root/'app/src/main/java/com/hinnka/mycamera/processor';engine=K/'experimentc/Iris26975CPinnedDonorProEngine.kt';session=K/'Iris26972CCamera2ShutterSession.kt';gallery=K/'Iris26972CCaptureToGallery.kt';wm=K/'experimentc/Iris26994COffWatermark.kt'
e=engine.read_text();s=session.read_text();g=gallery.read_text();w=wm.read_text()
assert s.count('private val frozenWatermark = rawSaver != 2 &&')==1 and 'PreferenceKeys.isShowWatermarkOn()' in s and 'frozenSharpenBands, offDng, rawSaver, frozenWatermark)' in s
assert 'val watermarkEnabled: Boolean,' in g and 'watermarkEnabled: Boolean,' in g and 'if (rawSaver != 2) jpeg = requireNotNull(executeOriginal(' in g and 'watermarkEnabled,\n                    ), stillLive,' in g
assert e.count('Iris26994COffWatermark.apply(')==1 and e.count('Jpeg444ExportEncoder.write(')==1
assert e.index('rawGpuGainmapProducer.build(')<e.index('if (transaction.watermarkEnabled)')<e.index('Jpeg444ExportEncoder.write(')
assert 'iris26993COffShadowLift = true,' in e and 'gainmapResult = gainmap,' in e
for token in ('source::getPixel','width * 0.115f','minOf(width, height) * 0.025f','luma/5f >= 0.55f','if (coverage == 0) continue','if (a == 0) continue','if (changed != 0) gm.copyPixelsFromBuffer','target.setPixels('):assert token in w,token
assert not any('/cpp/' in rel or '/jniLibs/' in rel or '/assets/' in rel for rel in changed)
if a.live:
 b.exact(R,'26994_EXPECTED_FULL_APP.sha256','26994 live source')
 # Revert EXACT watermark-only inserted blocks in memory; verify restored originals against physical authority hashes.
 import hashlib
 def original(f,text):assert hashlib.sha256(text.encode()).hexdigest()==base[f.relative_to(R).as_posix()],f
 original(session,s.replace('    // Freeze only the C OFF JPEG overlay preference at shutter ownership. DNG-only does not read it.\n    private val frozenWatermark = rawSaver != 2 &&\n        com.particlesdevs.photoncamera.settings.PreferenceKeys.isShowWatermarkOn()\n','').replace('frozenSharpenBands, offDng, rawSaver, frozenWatermark)','frozenSharpenBands, offDng, rawSaver)'))
 original(gallery,g.replace('        val watermarkEnabled: Boolean,\n','').replace('        watermarkEnabled: Boolean,\n','').replace('                        watermarkEnabled,\n',''))
 start=e.index('            // All donor processing and gain generation are complete.');end=e.index('            val info = CaptureInfo(',start);original(engine,e[:start]+e[end:])
 for p in (K/'experimentc/original129').rglob('*.kt'):
  rel=p.relative_to(R).as_posix();assert base[rel]==expected[rel]
 assert len(set(base)-changed)==2656 and all(base[x]==expected[x] for x in set(base)-changed)
 owner=[f for f in (R/'app/src/main/java').rglob('*.kt') if 'Iris26994COffWatermark.apply(' in f.read_text()];assert owner==[engine]
print('PASS exact C OFF watermark-only plumbing and original processing source preservation')
