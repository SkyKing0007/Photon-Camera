#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26622_r1.py BASE CAND')
B=Path(sys.argv[1]); C=Path(sys.argv[2])
def H(root): return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((root/'app').rglob('*')) if p.is_file()}
bh,ch=H(B),H(C)
assert len(bh)==1713 and len(ch)==1713,(len(bh),len(ch))
changed=sorted(p for p in set(bh)|set(ch) if bh.get(p)!=ch.get(p))
expected=sorted([
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/version.properties'])
assert changed==expected,(changed,expected)
ver=(C/'app/version.properties').read_text()
assert 'VERSION_NAME=0.9726622' in ver and 'VERSION_BUILD=26622' in ver
b=(B/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text()
c=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text()
old_insert="""            /* IRIS_26621_LOCAL_LAPLACIAN_PEAK_LIFETIME
             * The remap pyramid is already gone. Once reconstruction is complete, guide/band
             * pyramids are no longer needed; release them before the optional full-resolution
             * true-2x readback so the direct R16F map does not overlap those transient allocations. */"""
new_insert="""            /* IRIS_26622_LOCAL_LAPLACIAN_TELEMETRY_LIFETIME
             * Device regression from 26621: telemetry dereferenced guide[last].mSize after the
             * guide pyramid had been released and nulled, aborting every Motion capture after the
             * Local-Laplacian reconstruction had already completed. Snapshot diagnostic dimensions
             * before release; telemetry must never retain or dereference a freed GLTexture. */
            final int coarsestWidth = guide[IRIS_26621_LAPLACIAN_LEVELS - 1].mSize.x;
            final int coarsestHeight = guide[IRIS_26621_LAPLACIAN_LEVELS - 1].mSize.y;

            /* IRIS_26621_LOCAL_LAPLACIAN_PEAK_LIFETIME
             * The remap pyramid is already gone. Once reconstruction is complete, guide/band
             * pyramids are no longer needed; release them before the optional full-resolution
             * true-2x readback so the direct R16F map does not overlap those transient allocations. */"""
old_log="""                    + " coarsest=" + guide[IRIS_26621_LAPLACIAN_LEVELS - 1].mSize.x
                        + "x" + guide[IRIS_26621_LAPLACIAN_LEVELS - 1].mSize.y"""
new_log="""                    + " coarsest=" + coarsestWidth
                        + "x" + coarsestHeight"""
expected_c=b.replace(old_insert,new_insert,1).replace(old_log,new_log,1)
assert expected_c==c,'MotionV2Render delta exceeds exact telemetry-lifetime repair'
for tok in [
'IRIS_26621_NEW_SIMPLIFIED_PRESENTATION_OWNER',
'iris26621BuildLocalLaplacianTone(extendedLinearHdr)',
'IRIS_26621_LAPLACIAN_LEVELS = 7',
'IRIS_26621_REFERENCE_COUNT = 12',
'detailAlpha=1.0',
'absoluteFullResolutionToneMap=true',
'correctionMap=false',
'rgbScalarOnly=true']:
    assert tok in c,tok
assert c.count('iris26621BuildLocalLaplacianTone(extendedLinearHdr)')==1
release=c.index('guide[level] = null;')
log=c.index('Log.i(Name, "IRIS_26621_NEW_SIMPLIFIED_LOCAL_LAPLACIAN"')
assert release < log
post=c[release:]
assert 'guide[IRIS_26621_LAPLACIAN_LEVELS - 1].mSize' not in post
assert c.index('final int coarsestWidth') < release
assert c.index('final int coarsestHeight') < release
assert 'coarsest=" + coarsestWidth' in c and '"x" + coarsestHeight' in c
print('PASS 26622 semantic/ownership/domain: exact 2-path runtime delta; 26621 tone/Local-Laplacian math preserved except telemetry lifetime repair; no post-release guide dereference')
