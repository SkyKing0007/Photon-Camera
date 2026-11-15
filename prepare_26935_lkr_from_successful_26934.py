#!/usr/bin/env python3
"""Mandatory original RawLens 2.2.86 JNI libraries restored exclusively from successful 26934 published APK.
Never use third-party GitHub release API or older APK, and never build the prior version.
"""
import pathlib,zipfile,tempfile,hashlib,subprocess,shutil,sys
from build_26935_incremental import R,ART,ART_SHA,TAR_SHA,ART_ID,RUN,COMMIT,PRIOR_APK_SHA,OUT,fail,sha
APK_NAME='IrisCamera-0.9726934-26934-iris-rawr-debug.apk'
TARGET=R/'app/build/verified_rawlens26931/jniLibs'
RECEIPT=OUT/'26935_INHERITED_LKR_NATIVE_RECEIPT.txt'
LIBRARY_SHA={
 'arm64-v8a': {'liblkrpipeline.so':'af1d4caff00b3b189d23d1d53c7c9d11256f5b050af2590c5407191ce32cd39b',
               'libsrpipeline.so':'a91e0a33226db0e08b5355e2fac189cc9b91af7106530f6577d5084f1f39865d'},
 'armeabi-v7a': {'liblkrpipeline.so':'46de04ea3b1d37fbcc9bb380f94d56e7d7ad74d110e990e8413589e4e7eb8450',
                 'libsrpipeline.so':'61fdaab8881684999c03bf6d9a3cbe1d9b3da63effe0f364eaca103f97efe78c'},
}
def main():
 if not ART.is_file() or sha(ART)!=ART_SHA:fail('successful 26934 official artifact missing/corrupted')
 if TARGET.is_symlink() or any(TARGET.glob('**/*.so')):fail('stale/native APK binaries pre-existing at destination')
 OUT.mkdir(exist_ok=True,parents=True)
 report=[f'26935 native origin=SUCCESSFUL 26934 Actions run={RUN} commit={COMMIT} artifact={ART_ID}',
         '26934 artifact sha256='+ART_SHA,'26934 compiled source TAR sha256='+TAR_SHA,
         '26934 prior APK sha256='+PRIOR_APK_SHA,
         'mode=ORIGINAL_RAWLENS_2_2_86_EXACT_OFFLINE_VERIFIED_SUCCESSFUL_26934_APK',
         'external GitHub release API/download=NOT USED','previous APK rebuild=NOT USED',
         'new 26935 real Kotlin/Java/GLSL/NDK/CMake/dual-ABI/assemble=MANDATORY']
 with tempfile.TemporaryDirectory(prefix='26935_orig_rawlens_') as d:
  apkfile=pathlib.Path(d)/APK_NAME
  with zipfile.ZipFile(ART) as artifact:
   if artifact.testzip():fail('prior artifact CRC mismatch')
   if APK_NAME not in artifact.namelist():fail('exact successful 26934 APK absent')
   with artifact.open(APK_NAME) as src,apkfile.open('wb') as dst:
    shutil.copyfileobj(src,dst,length=4*1024*1024)
   if PRIOR_APK_SHA not in artifact.read('photon_26934_outputs/26934_APK.sha256').decode():
    fail('official 26934 APK compiler receipt mismatch')
  if sha(apkfile)!=PRIOR_APK_SHA:fail('26934 APK actual byte checksum mismatched')
  with zipfile.ZipFile(apkfile) as apk:
   if apk.testzip():fail('26934 APK ZIP CRC mismatch')
   for abi,libs in LIBRARY_SHA.items():
    for name,expected in libs.items():
     arc='lib/'+abi+'/'+name
     if arc not in apk.namelist():fail('missing compiled authentic original RawLens '+arc)
     data=apk.read(arc)
     if hashlib.sha256(data).hexdigest()!=expected:fail('exact original RawLens SHA mismatch '+arc)
     dst=TARGET/abi/name;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(data)
     if sha(dst)!=expected:fail('materialized original ABI checksum mismatch '+arc)
     p=subprocess.run(['readelf','-h',str(dst)],capture_output=True,text=True)
     markers=('ELF64','AArch64') if abi=='arm64-v8a' else ('ELF32','ARM')
     if p.returncode or any(x not in p.stdout for x in markers):fail('wrong original RawLens ABI/ELF '+arc)
     report.append(f'PASS original RawLens 2.2.86 {arc} sha256={expected} bytes={len(data)}')
   if 'assets/licenses/rawlens_2_2_86_lkr_apache_notice.txt' not in apk.namelist():
    fail('prior original RawLens attribution absent')
 RECEIPT.write_text('\n'.join(report)+'\n')
 print('\n'.join(report))
if __name__=='__main__':
 try:main()
 except Exception as e:print('26935 AUTHENTIC RAWLENS RESTORE BLOCKED',e,file=sys.stderr);sys.exit(1)
