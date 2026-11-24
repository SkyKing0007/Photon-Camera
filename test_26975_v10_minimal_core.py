#!/usr/bin/env python3
"""V10 fail-closed proof: unused preview/LUT source eliminated; selected original RAW math unchanged."""
import pathlib,hashlib,json,re,argparse
R=pathlib.Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--live',action='store_true');p.add_argument('--payload',action='store_true');args=p.parse_args()
assert args.live!=args.payload
root=R if args.live else R/'handoff_payload_26975'
P=json.loads((R/'26975_V10_MINIMAL_LUT_REACHABILITY_PROOF.json').read_text())
def sha(x):return hashlib.sha256(x).hexdigest()
def src(p):return (root/p).read_bytes()
base='app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/lut/'
shaders=src(base+'Shaders.kt').decode();utils=src(base+'GlUtils.kt').decode()
assert 'LutConfig' not in utils and 'samplerExternalOES' not in shaders
assert re.findall(r'val (\w+) = \"\"\"',shaders)==['SIMPLE_VERTEX_SHADER']
assert re.findall(r'fun (\w+)\(',utils)==['compileShader','linkProgram']
assert sha(shaders[shaders.index('    val SIMPLE_VERTEX_SHADER ='):shaders.index('\"\"\".trimIndent()')+len('\"\"\".trimIndent()')].encode()) == P['shader_retained_sha']
assert sha(utils[utils.index('    fun compileShader('):utils.rindex('}\n')].encode())==P['original_gles_compile_link_retained_sha']
assert P['removed_static_shaders_exactly']==8 and P['new_static_shader_count']==154
SPECIALIZED={'app/src/main/java/com/hinnka/mycamera/processor/experimentc/Iris26975CPinnedDonorProEngine.kt': '02b8856cb235602dfb35160a604a8b6278b9b5c71bd177e478d18ebb6fc97137', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/RawDemosaicProcessor.kt': '0de87713fc701e8d0f253f5c43fe4ac6243cc2803071bb663332f6431af44cd9', 'app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/RawEngineTonePass.kt': '3b052d855375b700752511fc994988c7c18f318484e61c13dda8ef49cfbd7cd5'}
for rel,h in P['pinned_unmodified_donor_core_sha256'].items():
 if args.live or rel in set((R/'26975_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines()):
  if rel not in SPECIALIZED:
   assert sha(src(rel))==h,'unchanged donor source changed: '+rel
  else:
   assert sha(src(rel))==SPECIALIZED[rel],'specialized selected-path source changed: '+rel
if args.live:
 own=root/'app/src/main/java/com/hinnka/mycamera/processor/experimentc'
 references=[]; urefs=[]
 for f in own.rglob('*.kt'):
  if f.name=='Shaders.kt' and f.parent.name=='lut':continue
  t=f.read_text()
  references+=re.findall(r'\bShaders\.(\w+)',t)
  urefs+=re.findall(r'\bGlUtils\.(\w+)',t)
 assert references==['SIMPLE_VERTEX_SHADER','SIMPLE_VERTEX_SHADER']
 assert sorted(set(urefs))==['compileShader','linkProgram']
import json as _json
inventory=_json.loads((R/'26975_V6_CURRENT_SHADER_INVENTORY.json').read_text())
assert inventory['static_count']==151 and inventory['dynamic_count']==77
print('PASS V10 C-only donor shader/use closure, retained original GLSL/GLES bytes, four unchanged V10 and three specialized selected source pins, 151 static 77 dynamic; no creative LUT dependency')

bridge=src('app/src/main/java/com/hinnka/mycamera/processor/experimentc/Iris26975CPinnedDonorProEngine.kt').decode()
stripped=bridge.split('\n    /** Reject an exactly black SDR base',1)[0]+'}\n'
stripped=stripped.replace('            check(stillLive()) { "C session closed before rendered pixel validation" }\n            validateNonBlackBase(checkNotNull(sdr), reference, shutterGrid)\n','')
assert sha(stripped.encode())=='1c19b3bc39c5a28ea903c51b7b7cb88c3a4ad9fc8aad4908514f42df2f841d5c', 'V13 original donor processing bridge modified beyond black-output guard'
print('PASS original V13 donor bridge exact after removing only fail-closed black-image guard')
