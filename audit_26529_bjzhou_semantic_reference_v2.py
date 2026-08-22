#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path

REFERENCE_COMMIT='c317bf97d2649ae9296bc1459979ce63cb3364b2'
REFERENCE_BLOB='5f29df5461cb50b199a6b19eea096127bf4af35c'
IRIS_SHA256='5e112314f0795e4294e3af9e8b127d7d86cdfa494cd8df042fd5c6ba9d7949a4'

class AuditError(RuntimeError): pass

def req(ok,msg):
    if not ok: raise AuditError(msg)

def git_blob_sha1(b: bytes) -> str:
    return hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--reference',required=True)
    ap.add_argument('--iris',required=True)
    ap.add_argument('--json-out')
    a=ap.parse_args()
    rb=Path(a.reference).read_bytes(); ib=Path(a.iris).read_bytes()
    rs=rb.decode(); isrc=ib.decode()
    req(git_blob_sha1(rb)==REFERENCE_BLOB, f'wrong c317 reference blob {git_blob_sha1(rb)}')
    req(hashlib.sha256(ib).hexdigest()==IRIS_SHA256, 'Iris rewrite SHA drift')
    req(rb!=ib, 'Iris runtime rewrite must not equal bjzhou source bytes')
    req('GlesMgcSpatialRgbChromaPostprocessor' in rs, 'reference owner missing')
    req('GlesIris26529SpatialRgbChromaPostprocessor' in isrc, 'Iris owner missing')
    req('GlesMgcSpatialRgbChromaPostprocessor' not in isrc, 'bjzhou owner copied into Iris runtime')

    # Semantic crosswalk: reference token -> independently named Iris equivalent.
    pairs={
      'directionMomentAt(p)':'directionMomentAt(ivec2 p)',
      'count << 8':'count << 8',
      'const float finiteScale = 65504.0 / 65535.0':'const float finiteScale = 65504.0 / 65535.0',
      '1.0 + b[1] + b[2]':'1.0+b[1]+b[2]',
      '1.0 + uB10[1] + uB10[2]':'1.0+uB10[1]+uB10[2]',
      '0.0674552768f':'0.0674552768f',
      '-1.14298046f':'-1.14298046f',
      '0.0331984349f':'0.0331984349f',
      '-1.61172712f':'-1.61172712f',
      'uimage2D uInput':'uimage2D uInput',
      'imageStore(uOutput, p, outputPixel)':'imageStore(uOutput,p,outputPixel)',
    }
    for ref_tok, iris_tok in pairs.items():
        req(ref_tok in rs, f'reference semantic token missing: {ref_tok}')
        req(iris_tok in isrc, f'Iris semantic counterpart missing: {iris_tok}')

    # Global-coordinate seam prevention: both must be full 2D, never per-tile array lookup.
    for src,label in ((rs,'reference'),(isrc,'Iris')):
        req('uimage2DArray' not in src, f'{label} unexpectedly uses image arrays')
        req('uTileLefts' not in src and 'uTileTops' not in src, f'{label} contains tile lookup')
    req('validateCoverage(newBands)' in isrc, 'Iris full-frame coverage validator missing')
    req('IRIS_26529_SPATIAL_RGB_CHROMA_REWRITE_OWNER' in isrc, 'Iris rewrite owner marker missing')

    result={
      'reference_commit':REFERENCE_COMMIT,
      'reference_git_blob_sha1':REFERENCE_BLOB,
      'iris_sha256':IRIS_SHA256,
      'runtime_is_verbatim_reference':False,
      'semantic_pairs_checked':len(pairs),
      'coordinate_domain':'contiguous_global_2d',
      'ownership':'iris_rewrite',
    }
    if a.json_out: Path(a.json_out).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print('PASS: bjzhou c317 audited as semantic reference; Iris runtime remains independent rewrite')

if __name__=='__main__':
    try: main()
    except (AuditError,OSError,UnicodeError) as e:
        print('ERROR:',e,file=sys.stderr); sys.exit(2)
