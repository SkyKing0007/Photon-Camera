#!/usr/bin/env python3
from pathlib import Path
import argparse, hashlib, subprocess, sys

BASE_HASHES = {
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java':'752ad4365ac5a2f4da67832c08f0062b55b2cb5e8b0436b11bedf2f30d8c422a',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java':'e7ea6a8809af0ee2ee6b416b64eec6b9fdad2653cf7e23d2c1513f48bf246860',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java':'86fe7ce870b32690f797d589ffb8e779965391399768b9000a98ca2ce3d5bdfa',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightMgc1271Bridge.kt':'f7c1c6639f1d242ef09832d91a4f1d9b3390bb4de662d173db2910f3bb3da570',
}
AFTER_HASHES = {
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java':'cf9cad601bde9354754ba6d9c5f12a75ef7de1c77921c943f2ec926eb1212c8e',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java':'f4de605df17c1e8ca5ec91b4a8aa2c81cea38014c0bfcab4923a4246c6aa12b7',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java':'e9d1bd2258da3d53d75d1a9344b257b6a92cdd7cedff2e11bab8f8499567664b',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightMgc1271Bridge.kt':'1842bacaaa8e735110b3778f60cd647930a80c7805edbc29fcaaa286ea26a9a4',
}
PATCH_NAME='26534_RUNTIME_DELTA_FROM_V16.patch'
PATCH_SHA='82c27d2c962c1a67e89e45dacb65ef4de36e639f2cf577e2490dc8e0e7c203af'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def fail(m): raise SystemExit('FAIL: '+m)
def require(c,m):
    if not c: fail(m)

def verify(root, table, label):
    for rel,expected in table.items():
        p=root/rel
        require(p.is_file(),f'{label}: missing {rel}')
        actual=sha(p)
        require(actual==expected,f'{label}: hash drift {rel}: {actual}')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('root',nargs='?'); ap.add_argument('--self-test',action='store_true'); a=ap.parse_args()
    if a.self_test:
        require(len(BASE_HASHES)==4 and set(BASE_HASHES)==set(AFTER_HASHES),'anchor set drift')
        require(len(PATCH_SHA)==64,'patch SHA malformed')
        print('PASS: 26534 transform self-test')
        return
    require(a.root,'candidate root required')
    root=Path(a.root).resolve(); require((root/'app/src/main').is_dir(),'candidate root missing app/src/main')
    patch=Path(__file__).resolve().parent/PATCH_NAME
    require(patch.is_file(),'handoff patch missing')
    require(sha(patch)==PATCH_SHA,'handoff patch SHA mismatch')
    verify(root,BASE_HASHES,'exact V1.6 base')
    dry=subprocess.run(['patch','-d',str(root),'-p1','--batch','--forward','--fuzz=0','--dry-run','--no-backup-if-mismatch'],input=patch.read_bytes(),stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    require(dry.returncode==0,'zero-fuzz dry-run failed:\n'+dry.stdout.decode(errors='replace'))
    run=subprocess.run(['patch','-d',str(root),'-p1','--batch','--forward','--fuzz=0','--no-backup-if-mismatch'],input=patch.read_bytes(),stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    require(run.returncode==0,'zero-fuzz apply failed:\n'+run.stdout.decode(errors='replace'))
    verify(root,AFTER_HASHES,'26534 candidate')
    print('PASS: 26534 exact V1.6 -> Motion Spatial-RGB / Night Spatial-Bayer routing transform applied')

if __name__=='__main__': main()
