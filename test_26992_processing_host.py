#!/usr/bin/env python3
"""Actual candidate Kotlin gain policy, with optional emitted reference for exact GLES replay."""
import argparse,pathlib,subprocess,tempfile,hashlib,re
R=pathlib.Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--root',type=pathlib.Path,required=True);p.add_argument('--base',type=pathlib.Path,required=True);p.add_argument('--gpu-reference',type=pathlib.Path);a=p.parse_args();root=a.root.resolve();base=a.base.resolve()
H=pathlib.Path('app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/hdr');math=H/'RawGainmapMath.kt';strength=H/'HdrGainmapStrength.kt';gpu=H/'GpuReferenceGainmapProducer.kt'
assert (root/strength).read_bytes()==(base/strength).read_bytes()
# All other embedded shaders and the gain-map metadata/upload/readback block are byte-identical.
old=(base/gpu).read_text();new=(root/gpu).read_text();a1=re.findall(r'""".*?"""',old,re.S);a2=re.findall(r'""".*?"""',new,re.S);assert len(a1)==len(a2) and sum(x!=y for x,y in zip(a1,a2))==1
assert old[old.index('val gainmap = Gainmap(gainmapBitmap)'):old.index('return GainmapResult(gainmap, source.sourceKind, source.confidence)')]==new[new.index('val gainmap = Gainmap(gainmapBitmap)'):new.index('return GainmapResult(gainmap, source.sourceKind, source.confidence)')]
with tempfile.TemporaryDirectory(prefix='26992-host-') as td:
 jar=pathlib.Path(td)/'test.jar';subprocess.run(['kotlinc',str(root/math),str(root/strength),str(R/'26992_GAINMAP_HOST.kt'),'-include-runtime','-d',str(jar)],check=True)
 data=subprocess.check_output(['java','-jar',str(jar)],text=True);lines=data.splitlines();assert lines[0].startswith('PASS Kotlin physical policy 1270251 cases') and len(lines)==4097
 print(lines[0]);
 if a.gpu_reference:a.gpu_reference.write_text(data)
print('PASS actual Kotlin and single exact shader delta; Android gain-map metadata code preserved')
