#!/usr/bin/env python3
"""26931 exact RawLens 2.2.86 Apache-2.0 native release binaries.

No substitution or recompilation of upstream LKR: this gives Iris the EXACT
published full LKR engine, including all pinned SPIR-V and motion/noise passes.
Downloaded APKs are ephemeral Actions inputs, NEVER pushed/uploaded in Git.
The CI run still recompiles Iris native JNI (both ABIs) with its pinned NDK.
"""
from __future__ import annotations
import hashlib,json,os,pathlib,subprocess,sys,zipfile

ROOT=pathlib.Path(__file__).resolve().parent
OUT=ROOT/'app/build/verified_rawlens26931/jniLibs'
RECEIPT=ROOT/'photon_26931_outputs/26931_ORIGINAL_LKR_NATIVE_RECEIPT.txt'
UPSTREAM='matthew777777/RawLens'
TAG='2.2.86'
COMMIT='36e5141df568e74e2708dd4f50413b3aa51dab20'
APK={
 'arm64-v8a': ('RawLens-2.2.86-release-arm64-v8a.apk',84926392,
    '2b322a75bab31c08d8b9a0bcc3b9ae884db7d98f7bba9ffe82924faa5fb8a1eb'),
 'armeabi-v7a': ('RawLens-2.2.86-release-armeabi-v7a.apk',68654366,
    'fd87e68aa5644a761808e2a23a2e51be0e0e3b951bef43705696cb183ff50e9a'),
}
SHA64={
 'liblkrpipeline.so':'af1d4caff00b3b189d23d1d53c7c9d11256f5b050af2590c5407191ce32cd39b',
 'libsrpipeline.so':'a91e0a33226db0e08b5355e2fac189cc9b91af7106530f6577d5084f1f39865d',
}

def fail(s): raise RuntimeError('26931 RAWLENS EXACT NATIVE BLOCKED: '+str(s))
def sha(data):return hashlib.sha256(data).hexdigest()
def cmd(args):
 r=subprocess.run(args,capture_output=True,text=True)
 if r.returncode:fail(' '.join(args)+'\n'+r.stdout+'\n'+r.stderr)
 return r.stdout

def main():
 if (ROOT/'app/src/main/java/com/matthew/rawlens/LkrBridge.java').is_file() is False:
  fail('Iris JNI bridge not installed from source-sealed candidate')
 # This is the sole allowed output: build-generated jniLibs (outside app/src).
 OUT.mkdir(parents=True,exist_ok=True)
 receipt=[f'RawLens tag={TAG} pinnedCommit={COMMIT}',
          'mode=EXACT_UNMODIFIED_UPSTREAM_RELEASE_NATIVE_APKS',
          'user_selected_LKR_tuning=T3_Z2_prior_at_t1',
          'exact_source_sha_validation=SHA256_ORIGINAL_PUBLISHED_RELEASE_APK',
          'source_native_glsl=BUILT_IN_UPSTREAM_RELEASE_BINARY',
          'Iris_native_NDK_ABI=REAL_ANDROID_ACTIONS_COMPILATION_REQUIRED',
          'Iris_vendor_tree=UNCHANGED']
 # Asset digests are published by GitHub and frozen into this source-sealed script.
 # Do not accept a re-tagged or wrong release.
 api=f'https://api.github.com/repos/{UPSTREAM}/releases/tags/{TAG}'
 metadata=ROOT/'.photon_26931_work/rawlens_release.json'
 metadata.parent.mkdir(parents=True,exist_ok=True)
 cmd(['curl','--fail','--location','--retry','3','--silent','--show-error',
      '-H','Accept: application/vnd.github+json','-o',str(metadata),api])
 release=json.loads(metadata.read_text())
 if release.get('tag_name')!=TAG or release.get('target_commitish')!=COMMIT:fail('tag/commit drift')
 names={a['name']:a for a in release.get('assets',[])}
 cache=ROOT/'.photon_26931_work/rawlens_release'
 cache.mkdir(parents=True,exist_ok=True)
 for abi,(name,size,digest) in APK.items():
  asset=names.get(name)
  if not asset or asset.get('size')!=size or asset.get('digest')!='sha256:'+digest:
   fail('release asset identity/digest drift '+abi)
  path=cache/name
  if not path.is_file() or sha(path.read_bytes())!=digest:
   url=f'https://github.com/{UPSTREAM}/releases/download/{TAG}/{name}'
   cmd(['curl','--fail','--location','--retry','3','--silent','--show-error',
        '-o',str(path),url])
  if path.stat().st_size!=size or sha(path.read_bytes())!=digest:
   fail('downloaded official APK SHA-256 mismatch '+abi)
  receipt.append(f'PASS {abi} apk={name} size={size} sha256={digest}')
  with zipfile.ZipFile(path) as apk:
   if apk.testzip() is not None:fail('release APK ZIP CRC failure '+abi)
   for name0 in ('liblkrpipeline.so','libsrpipeline.so'):
    entry=f'lib/{abi}/{name0}'
    if entry not in apk.namelist():fail('release did not contain necessary native LKR dependency '+entry)
    original=apk.read(entry)
    native=OUT/abi/name0
    native.parent.mkdir(parents=True,exist_ok=True)
    native.write_bytes(original)
    expected=SHA64.get(name0) if abi=='arm64-v8a' else None
    if expected and sha(original)!=expected:fail('original arm64 native library hash differs from pinned reference '+name0)
    h=cmd(['readelf','-h',str(native)])
    machine='AArch64' if abi=='arm64-v8a' else 'ARM'
    elfclass='ELF64' if abi=='arm64-v8a' else 'ELF32'
    if machine not in h or elfclass not in h:fail('wrong ELF/ABI '+entry)
    deps=cmd(['readelf','-d',str(native)])
    if name0=='liblkrpipeline.so' and 'libsrpipeline.so' not in deps:fail('LKR dependency link missing '+entry)
    receipt.append(f'PASS {entry} bytes={len(original)} sha256={sha(original)} ELF={elfclass}/{machine}')
  # Native LKR JNI symbols must be in BOTH ABIs. No missing-stage fallbacks.
  symbols=cmd(['readelf','-Ws',str(OUT/abi/'liblkrpipeline.so')])
  for needle in ('Java_com_matthew_rawlens_LkrBridge_nativeMerge',
                 'Java_com_matthew_rawlens_LkrBridge_nativeTuningDefaults',
                 'Java_com_matthew_rawlens_LkrBridge_nativeSetNoiseModel',
                 'Java_com_matthew_rawlens_LkrBridge_nativeSetCacheDir'):
   if needle not in symbols:fail('LKR upstream JNI symbol absent '+abi+' '+needle)
  free=cmd(['readelf','-Ws',str(OUT/abi/'libsrpipeline.so')])
  if 'Java_com_rawlens_srpipeline_SrpBridge_nativeFreeDirect' not in free:fail('native direct-buffer free ABI missing '+abi)
 receipt.append('PASS liblkrpipeline.so and libsrpipeline.so both ABIs, real ELF/dep/JNI symbol contracts')
 RECEIPT.parent.mkdir(exist_ok=True)
 RECEIPT.write_text('\n'.join(receipt)+'\n')
 print('\n'.join(receipt))

if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
