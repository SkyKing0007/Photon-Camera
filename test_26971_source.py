#!/usr/bin/env python3
"""26971 exact successful 26970 authority, A high-zoom-only redundant-tile correction."""
from pathlib import Path
import sys,hashlib,re
R=Path(__file__).resolve().parent
P=R if '--live' in sys.argv else R/'handoff_payload_26971'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def hashes(name):return {n:h for h,n in (line.split('  ',1) for line in (R/name).read_text().splitlines())}
a=hashes('26971_BASE_26970_FULL_APP.sha256');b=hashes('26971_EXPECTED_FULL_APP.sha256');protect=hashes('26971_PROTECTED_SOURCE.sha256')
changed=set((R/'26971_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines())
want={'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker26850.kt','app/src/main/java/com/hinnka/mycamera/processor/Iris26971HighZoomDetailIntegrity.kt','app/version.properties'}
added=set((R/'26971_ADDED_RUNTIME_PATHS.txt').read_text().splitlines())
assert len(a)==2056 and len(b)==2057 and len(protect)==2054
assert changed==want and added=={'app/src/main/java/com/hinnka/mycamera/processor/Iris26971HighZoomDetailIntegrity.kt'}
assert protect=={n:h for n,h in a.items() if n not in changed}
assert {n for n in set(a)|set(b) if a.get(n)!=b.get(n)}==want
assert (R/'26971_DELETED_RUNTIME_PATHS.txt').read_text()==''
for n in want: assert sha(P/n)==b[n],n
v=(P/'app/version.properties').read_text();assert 'VERSION_BUILD=26971' in v and 'VERSION_NAME=0.9726971' in v
k=(P/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker26850.kt').read_text()
helper=(P/'app/src/main/java/com/hinnka/mycamera/processor/Iris26971HighZoomDetailIntegrity.kt').read_text()
assert k.count('for (verificationPass in 0..1)')==1
assert k.count('Iris26971HighZoomDetailIntegrity.reconcile(')==1
assert k.count('writeHighZoomDetailTile26718(out,detail,localLeft,localTop,tileWidth,tileHeight,detailWidth,passPhaseHistogram,passReasonHistogram)')==1
assert 'GL_PACK_ROW_LENGTH, 0' in k and 'GL_PACK_SKIP_PIXELS, 0' in k and 'GL_PACK_SKIP_ROWS, 0' in k
assert 'GLES30.glReadBuffer(GLES30.GL_COLOR_ATTACHMENT0)' in k
assert 'diagnosticValue.isFinite()' in k and 'detailValue.isFinite()' in k
start=k.index('private fun runHighZoomDetailGpu26718(');stop=k.index('IRIS_26753_IPOL_PLAN_B_TRANSLATION_VALIDATION',start)
assert 'for (verificationPass in 0..1)' in k[start:stop]
assert 'if (verificationPass == 1 && localTop == 0) 64' in k[start:stop]
assert 'if (verificationPass == 1 && localLeft == 0) 256' in k[start:stop]
assert 'reconcileHighZoomDetail26971' in k[start:stop]
assert 'runHighZoomRgbGpu26720' not in k[start:stop]
assert 'enableSabreSuperRes' not in k[start:stop]
assert 'MAX_DETAIL_EV = 0.561f' in helper and 'INDEPENDENT_TOL_EV = 0.055f' in helper
assert 'zero-DC' in helper and 'fullNativeFallback' in helper
assert 'val original = readValues(primaryFile)' in k
assert 'if (result.affectedPixels > 0)' in k and 'Half.toHalf(result.detail[i])' in k
for n in ('app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt','app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders26850.kt','app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/assets/shaders/motionv2/gainmap.glsl','app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt','app/src/main/cpp/iris26864/bridge/Iris26970BOffGrainEven.comp'):
 assert a[n]==b[n],n
if '--live' in sys.argv:
 from importlib.machinery import SourceFileLoader
 m=SourceFileLoader('p26971',str(R/'build_26971_incremental.py')).load_module()
 assert m.scan(R)==b
print('PASS 26971 true 26970 successful compiled authority, 2 modified + 1 added, 2054 protected, only A high-zoom detail integrity, B/native/vendor/SDR/UHDR unchanged')
