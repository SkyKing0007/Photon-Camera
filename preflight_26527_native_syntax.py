#!/usr/bin/env python3
from __future__ import annotations
import argparse,os,shutil,subprocess,tempfile
from pathlib import Path
TINY=r'''#pragma once
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <string>
#include <vector>
namespace tinydngwriter {
static const int PHOTOMETRIC_CFA=32803, PHOTOMETRIC_RGB=2;
static const int PLANARCONFIG_CONTIG=1;
static const int COMPRESSION_NONE=1, COMPRESSION_NEW_JPEG=7;
static const int RESUNIT_CENTIMETER=2;
struct GainMap { unsigned int top=0,left=0,bottom=0,right=0; GainMap(){} GainMap(const float*,int,int,int,int,int,int,int=2){} };
class DNGImage { public:
 template<class... A> bool SetSubfileType(A&&...){return true;} template<class... A> bool SetBigEndian(A&&...){return true;}
 template<class... A> bool SetSamplesPerPixel(A&&...){return true;} template<class... A> bool SetPhotometric(A&&...){return true;}
 template<class... A> bool SetPlanarConfig(A&&...){return true;} template<class... A> bool SetDNGVersion(A&&...){return true;}
 template<class... A> bool SetExifVersion(A&&...){return true;} template<class... A> bool SetCompression(A&&...){return true;}
 template<class... A> bool SetBitsPerSample(A&&...){return true;} template<class... A> bool SetOrientation(A&&...){return true;}
 template<class... A> bool SetImageWidth(A&&...){return true;} template<class... A> bool SetImageLength(A&&...){return true;}
 template<class... A> bool SetRowsPerStrip(A&&...){return true;} template<class... A> bool SetActiveArea(A&&...){return true;}
 template<class... A> bool SetDefaultCrop(A&&...){return true;} template<class... A> bool SetResolutionUnit(A&&...){return true;}
 template<class... A> bool SetXResolution(A&&...){return true;} template<class... A> bool SetYResolution(A&&...){return true;}
 template<class... A> bool SetBlackLevelRepeatDim(A&&...){return true;} template<class... A> bool SetCFARepeatPatternDim(A&&...){return true;}
 template<class... A> bool SetCFAPattern(A&&...){return true;} template<class... A> bool SetLinearizationTable(A&&...){return true;}
 template<class... A> bool SetWhiteLevelRational(A&&...){return true;} template<class... A> bool SetBlackLevel(A&&...){return true;}
 template<class... A> bool SetColorMatrix1(A&&...){return true;} template<class... A> bool SetColorMatrix2(A&&...){return true;}
 template<class... A> bool SetForwardMatrix1(A&&...){return true;} template<class... A> bool SetForwardMatrix2(A&&...){return true;}
 template<class... A> bool SetCameraCalibration1(A&&...){return true;} template<class... A> bool SetCameraCalibration2(A&&...){return true;}
 template<class... A> bool SetAsShotNeutral(A&&...){return true;} template<class... A> bool SetAsShotWhiteXY(A&&...){return true;}
 template<class... A> bool SetAnalogBalance(A&&...){return true;} template<class... A> bool SetCalibrationIlluminant1(A&&...){return true;}
 template<class... A> bool SetCalibrationIlluminant2(A&&...){return true;} template<class... A> bool SetImageDataJpeg(A&&...){return true;}
 template<class... A> bool SetImageData(A&&...){return true;} template<class... A> bool SetCustomFieldULong(A&&...){return true;}
 template<class... A> bool SetUniqueCameraModel(A&&...){return true;} template<class... A> bool SetImageDescription(A&&...){return true;}
 template<class... A> bool SetSoftware(A&&...){return true;} template<class... A> bool SetIso(A&&...){return true;}
 template<class... A> bool SetExposureTime(A&&...){return true;} template<class... A> bool SetAperture(A&&...){return true;}
 template<class... A> bool SetFocalLength(A&&...){return true;} template<class... A> bool SetMake(A&&...){return true;}
 template<class... A> bool SetModel(A&&...){return true;} template<class... A> bool SetTimeCode(A&&...){return true;}
 template<class... A> bool SetDateTime(A&&...){return true;} template<class... A> bool SetNoiseProfile(A&&...){return true;}
 template<class... A> bool SetFrameRate(A&&...){return true;} template<class... A> bool SetGainMap(A&&...){return true;}
 size_t GetStripOffset() const {return 0;}
};
class DNGWriter { public: explicit DNGWriter(bool){} bool AddImage(const DNGImage*){return true;}
 void* WriteToMemory(size_t *size,std::string*,size_t*=nullptr) const {if(size)*size=16;return std::malloc(16);} };
}
'''.replace('size_t*=','size_t* =')
ANDROID='''#pragma once\n#define ANDROID_LOG_DEBUG 3\n#define ANDROID_LOG_ERROR 6\nstatic inline int __android_log_print(int,const char*,const char*,...){return 0;}\n'''
ARCHIVE='''#pragma once\n#include <sys/types.h>\n#include <cstddef>\nstruct archive; struct archive_entry;\ntypedef long long la_int64_t; typedef long la_ssize_t;\n#define ARCHIVE_OK 0\n#define AE_IFREG 0100000\n'''
ENTRY='''#pragma once\nstruct archive_entry;\n'''
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',required=True); a=ap.parse_args(); root=Path(a.root)
    cpp=root/'app/src/main/cpp/dngCreator.cpp'
    if not cpp.is_file(): raise SystemExit('dngCreator.cpp missing')
    compiler=shutil.which('clang++') or shutil.which('g++')
    if not compiler: raise SystemExit('no C++ compiler available for native syntax preflight')
    java_home=os.environ.get('JAVA_HOME','')
    candidates=[]
    if java_home: candidates.append(Path(java_home)/'include')
    candidates += list(Path('/usr/lib/jvm').glob('*/include')) if Path('/usr/lib/jvm').exists() else []
    jni=next((p for p in candidates if (p/'jni.h').is_file()),None)
    if jni is None: raise SystemExit('JNI include directory not found')
    with tempfile.TemporaryDirectory(prefix='iris26527-native-') as td:
        td=Path(td); (td/'deps').mkdir(); (td/'android').mkdir()
        (td/'deps/tiny_dng_writer.h').write_text(TINY); (td/'android/log.h').write_text(ANDROID)
        (td/'archive.h').write_text(ARCHIVE); (td/'archive_entry.h').write_text(ENTRY)
        cmd=[compiler,'-std=c++17','-fsyntax-only','-Werror=return-type','-I'+str(td),'-I'+str(jni)]
        if (jni/'linux').is_dir(): cmd.append('-I'+str(jni/'linux'))
        cmd.append(str(cpp))
        r=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        if r.returncode:
            print(r.stdout); raise SystemExit('native C++/JNI syntax preflight failed')
    print('PASS: dngCreator.cpp C++17/JNI syntax with deterministic API stubs')
    print('PASS: full pinned TinyDNG/Android native compile remains owned by guarded Gradle build')
if __name__=='__main__': main()
