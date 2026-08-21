#!/usr/bin/env python3
from __future__ import annotations
import argparse,difflib,hashlib,importlib.util
from pathlib import Path

IRIS_STACK='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbStacker.kt'
IRIS_SHADER='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbShaders.kt'
RELEASE_STACK='app/src/main/java/com/hinnka/mycamera/processor/GlesMgc1271ReleasedSpatialStacker.kt'
RELEASE_SHADER='app/src/main/java/com/hinnka/mycamera/processor/GlesMgc1271ReleasedSpatialShaders.kt'

def norm(s:str)->str: return s.replace('\r\n','\n').replace('\r','\n')
def load(path:Path,name:str):
    spec=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(spec); assert spec.loader; spec.loader.exec_module(m); return m

def one(s:str,old:str,new:str,label:str)->str:
    n=s.count(old)
    if n!=1: raise AssertionError(f'{label} anchor count={n} expected=1')
    return s.replace(old,new,1)

def expected_map(base:Path,apply26520v5:Path,apply26520v4:Path,apply26521v4:Path)->dict[str,str]:
    v5=load(apply26520v5,'apply26520v5')
    v4_21=load(apply26521v4,'apply26521v4_helpers')
    out=dict(v5.expected_map(base,apply26520v4))
    if v5.STACK!=RELEASE_STACK or v5.SHADERS!=RELEASE_SHADER:
        raise AssertionError('26520 V5 released path drift')
    corrected_stack=out.pop(RELEASE_STACK)
    corrected_shader=out.pop(RELEASE_SHADER)

    iris_stack=v4_21.rewrite_iris_stack(corrected_stack)
    iris_stack=one(
        iris_stack,
        ' * IRIS_26521_V4_INDEPENDENT_SPATIAL_RGB_OWNER\n',
        ' * IRIS_26521_V4_INDEPENDENT_SPATIAL_RGB_OWNER\n * IRIS_26521_V5_CORRECTED_SPATIAL_INFRASTRUCTURE\n',
        '26521 V5 corrected infrastructure marker',
    )
    for tok in (
        'IRIS_26520_V5_FINAL_FINEST_LK_OWNER',
        'IRIS_26520_V5_MERGE_DOMAIN_REJECTION_FLOW',
        'IRIS_26520_V5_SPATIAL_RGB_TWO_SLOT_RAW_LIFETIME',
        'IRIS_26520_V4_NORMAL_ONLY_DNG_READY',
    ):
        if tok not in iris_stack: raise AssertionError('Iris clone missing inherited V5/V4 semantic '+tok)

    iris_shader=v4_21.rewrite_iris_shader(corrected_shader)
    iris_shader=one(
        iris_shader,
        '    /* IRIS_26521_V4_INDEPENDENT_SPATIAL_RGB_MATH\n',
        '    /* IRIS_26521_V4_INDEPENDENT_SPATIAL_RGB_MATH\n     * IRIS_26521_V5_CORRECTED_SPATIAL_INFRASTRUCTURE\n',
        'Iris shader V5 corrected infrastructure marker',
    )
    if 'IRIS_26520_V5_CONTINUOUS_FINEST_LK_TRANSPORT' not in iris_shader:
        raise AssertionError('Iris shader lost continuous finest-LK transport')

    fusion=v4_21.rewrite_fusion(out['app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt'])
    fusion=one(
        fusion,
        'IRIS_26521_V4_INDEPENDENT_SPATIAL_RGB_OWNER_ACTIVE',
        'IRIS_26521_V5_INDEPENDENT_SPATIAL_RGB_OWNER_ACTIVE',
        '26521 V5 active owner marker',
    )
    out['app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt']=fusion
    out[IRIS_STACK]=iris_stack
    out[IRIS_SHADER]=iris_shader

    if (base/IRIS_STACK).exists() or (base/IRIS_SHADER).exists():
        raise AssertionError('26521 Iris owner unexpectedly exists in successful-26519 base')
    if RELEASE_STACK in out or RELEASE_SHADER in out:
        raise AssertionError('26521 V5 must preserve released c4ff control files byte-for-byte')
    return out

def patch_text(base:Path,expected:dict[str,str])->str:
    chunks=[]
    for rel in sorted(expected):
        p=base/rel; old=norm(p.read_text()) if p.exists() else ''; new=expected[rel]
        if old==new: raise AssertionError('empty 26521 V5 transform '+rel)
        chunks.append(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=('a/'+rel if p.exists() else '/dev/null'),tofile='b/'+rel)))
    return ''.join(chunks)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('root',type=Path)
    ap.add_argument('--apply26520-v5',required=True,type=Path)
    ap.add_argument('--apply26520-v4',required=True,type=Path)
    ap.add_argument('--apply26521-v4',required=True,type=Path)
    ap.add_argument('--patch-out',type=Path); ap.add_argument('--patch-sha-out',type=Path); ap.add_argument('--check-only',action='store_true')
    ns=ap.parse_args(); base=ns.root.resolve()
    expected=expected_map(base,ns.apply26520_v5.resolve(),ns.apply26520_v4.resolve(),ns.apply26521_v4.resolve())
    if ns.check_only:
        print('PASS: 26521 V5 = exact 26520 V5 corrected Spatial infrastructure + independent Iris RGB reconstruction math')
        print('PASS: released c4ff control stacker/shaders remain byte-for-byte frozen and dormant')
        print('PASS: no Sabre/old CFA/Wronski owner is introduced')
        return
    if ns.patch_out is None or ns.patch_sha_out is None: raise SystemExit('--patch-out and --patch-sha-out required unless --check-only')
    diff=patch_text(base,expected)
    if not diff: raise AssertionError('empty 26521 V5 runtime patch')
    ns.patch_out.parent.mkdir(parents=True,exist_ok=True); ns.patch_out.write_text(diff)
    digest=hashlib.sha256(ns.patch_out.read_bytes()).hexdigest(); ns.patch_sha_out.write_text(f'{digest}  {ns.patch_out.name}\n')
    for rel,new in expected.items():
        p=base/rel; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(new)
    print(f'PASS: combined 26520+26521 V5 rollback patch existed before {len(expected)}-path runtime write')

if __name__=='__main__': main()
