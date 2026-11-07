#!/usr/bin/env python3
"""26906 cache-only libheif FetchContent replay guard.

No application/native/vendor source is changed. The script reverts patches ONLY in
cached CMake FetchContent source, so the real CMake step can apply them once.
A successful compile must reproduce exactly the originally cached patched bytes.
"""
import hashlib, json, os, pathlib, subprocess, sys

R=pathlib.Path(__file__).resolve().parent
OUT=R/'photon_26906_outputs'
RECEIPT=OUT/'26906_NATIVE_CACHE_PATCH_REPLAY.json'
AOSP=R/'app/src/main/cpp/iris26643_libheif_aosp_contract.patch'
ABI=('arm64-v8a','armeabi-v7a')
ARGS=('--ignore-space-change','--whitespace=nowarn')

def fail(s): raise RuntimeError('26906 NATIVE CACHE BLOCKED: '+s)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def apply(src,patch,action):
    cmd=['git','apply',*ARGS]
    if action=='reverse':cmd+=['--reverse']
    if action=='forward':pass
    if action=='check':cmd+=['--check']
    if action=='reverse-check':cmd+=['--reverse','--check']
    cmd.append(str(patch))
    p=subprocess.run(cmd,cwd=src,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    return p.returncode==0,p.stderr

def touched(patch):
    ans=[]
    for line in patch.read_text().splitlines():
        if line.startswith('+++ b/'):
            path=line[6:].strip()
            pure=pathlib.PurePosixPath(path)
            if pure.is_absolute() or '..' in pure.parts or not pure.parts: fail('patch path escape: '+path)
            ans.append(path)
    if not ans:fail('empty patch '+str(patch))
    return ans

def snapshot(src,paths):
    out={}
    for p in sorted(paths):
        target=src/p
        if target.is_symlink():fail('cached libheif symlink '+str(target))
        out[p]=digest(target) if target.is_file() else None
    return out

def paths():
    return sorted((R/'app/.cxx').glob('*/*/*/_deps/iris26636_libheif-src'))

def preflight():
    OUT.mkdir(exist_ok=True)
    cache=os.environ.get('PHOTON_26906_NATIVE_CACHE_HIT')
    if cache!='true':
        RECEIPT.write_text(json.dumps({'mode':'cold','sources':[],'script_sha256':digest(pathlib.Path(__file__))},sort_keys=True,indent=2)+'\n')
        print('PASS native cache cold; normal complete NDK build remains required')
        return
    if not AOSP.is_file():fail('original libheif AOSP patch missing')
    found=paths()
    if len(found)!=2 or {p.parent.parent.name for p in found}!=set(ABI):
        fail('native cache missing exact two ABI libheif sources; reject cache instead of trusting it: '+str(found))
    records=[]
    for src in found:
        abi=src.parent.parent.name
        root=src.parent.parent
        pr=root/'iris26636_libheif_pr1503.patch'
        if not pr.is_file():fail('missing cached upstream libheif patch '+str(pr))
        stamp=root/'_deps/iris26636_libheif-subbuild/iris26636_libheif-populate-prefix/src/iris26636_libheif-populate-stamp/iris26636_libheif-populate-patch'
        if not stamp.is_file():fail('missing successful cached libheif patch stamp '+str(stamp))
        targetpaths=set(touched(pr)+touched(AOSP))
        original=snapshot(src,targetpaths)
        if not apply(src,AOSP,'reverse-check')[0]:
            fail('successful native cache does not have complete AOSP patch: '+abi)
        if not apply(src,AOSP,'reverse')[0]:fail('cannot revert cached AOSP patch '+abi)
        if not apply(src,pr,'reverse-check')[0]:fail('upstream patch not completely applied after AOSP reversal '+abi)
        if not apply(src,pr,'reverse')[0]:fail('cannot revert cached upstream libheif patch '+abi)
        if not apply(src,pr,'check')[0]:fail('upstream patch cannot reapply exactly '+abi)
        if not apply(src,pr,'forward')[0]:fail('test upstream patch apply failed '+abi)
        if not apply(src,AOSP,'check')[0]:fail('AOSP contract cannot reapply after upstream patch '+abi)
        if not apply(src,pr,'reverse')[0]:fail('could not return source to pristine state '+abi)
        # CMake's real patch step must execute again. Only invalidate its specific stamp.
        stamp.unlink()
        records.append({'abi':abi,'source':src.relative_to(R).as_posix(),
                        'upstream_patch_sha256':digest(pr),'aosp_patch_sha256':digest(AOSP),
                        'expected_patched_files':original,'removed_patch_stamp':stamp.relative_to(R).as_posix()})
    RECEIPT.write_text(json.dumps({'mode':'cached-replay','sources':records,'script_sha256':digest(pathlib.Path(__file__))},sort_keys=True,indent=2)+'\n')
    print('PASS native cache two-ABI libheif patches safely reversed, verified reapplicable; CMake real patch stage required')

def postflight():
    if not RECEIPT.is_file():fail('missing native cache preflight evidence')
    a=json.loads(RECEIPT.read_text())
    if a.get('script_sha256')!=digest(pathlib.Path(__file__)):fail('native cache verifier changed mid-build')
    if a['mode']=='cold':
        print('PASS native cold-build provenance receipt (real native build verified by assemble gate)')
        return
    if a['mode']!='cached-replay' or len(a['sources'])!=2:fail('invalid cache provenance receipt')
    for r in a['sources']:
        src=R/r['source'];root=src.parent.parent
        pr=root/'iris26636_libheif_pr1503.patch'
        if digest(pr)!=r['upstream_patch_sha256'] or digest(AOSP)!=r['aosp_patch_sha256']:
            fail('libheif patch inputs drifted '+r['abi'])
        if snapshot(src,r['expected_patched_files'].keys())!=r['expected_patched_files']:
            fail('libheif patched source differs from successful native cache '+r['abi'])
        if not (R/r['removed_patch_stamp']).is_file():fail('real CMake did not complete libheif patch step '+r['abi'])
    print('PASS native cached libheif re-patched byte-identically by real CMake in both ABIs')

if __name__=='__main__':
    try:
        if len(sys.argv)!=2 or sys.argv[1] not in ('preflight','postflight'):fail('expected preflight or postflight')
        globals()[sys.argv[1]]()
    except Exception as e:
        print('ERROR',e,file=sys.stderr)
        sys.exit(1)
