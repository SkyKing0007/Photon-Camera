#!/usr/bin/env python3
from __future__ import annotations
import argparse, os, shutil, subprocess, tempfile
from pathlib import Path

ANDROID_BITMAP = r'''#pragma once
#include <cstdint>
#include <jni.h>
#define ANDROID_BITMAP_RESULT_SUCCESS 0
#define ANDROID_BITMAP_FORMAT_RGBA_8888 1
#define ANDROID_BITMAP_FORMAT_A_8 8
struct AndroidBitmapInfo { uint32_t width=0,height=0,stride=0,format=0,flags=0; };
static inline int AndroidBitmap_getInfo(JNIEnv*, jobject, AndroidBitmapInfo*) { return ANDROID_BITMAP_RESULT_SUCCESS; }
static inline int AndroidBitmap_lockPixels(JNIEnv*, jobject, void**) { return ANDROID_BITMAP_RESULT_SUCCESS; }
static inline int AndroidBitmap_unlockPixels(JNIEnv*, jobject) { return ANDROID_BITMAP_RESULT_SUCCESS; }
'''
ANDROID_LOG = r'''#pragma once
#define ANDROID_LOG_DEBUG 3
#define ANDROID_LOG_ERROR 6
static inline int __android_log_print(int,const char*,const char*,...){return 0;}
'''
TURBO = r'''#pragma once
#include <cstddef>
typedef void* tjhandle;
#define TJINIT_COMPRESS 1
#define TJPARAM_QUALITY 1
#define TJPARAM_SUBSAMP 2
#define TJPARAM_OPTIMIZE 3
#define TJSAMP_444 0
#define TJSAMP_GRAY 3
#define TJPF_RGBA 7
#define TJPF_GRAY 6
static inline tjhandle tj3Init(int){return (void*)1;}
static inline int tj3Set(tjhandle,int,int){return 0;}
static inline int tj3Compress8(tjhandle,const unsigned char*,int,int,int,int,unsigned char**,size_t*){return 0;}
static inline void tj3Free(void*){}
static inline void tj3Destroy(tjhandle){}
'''
JPEG = r'''#pragma once
#include <cstdio>
#include <cstddef>
#define TRUE 1
#define JCS_RGB 2
typedef unsigned char JSAMPLE; typedef JSAMPLE* JSAMPROW; typedef unsigned int JDIMENSION;
struct jpeg_error_mgr{}; struct jpeg_component_info{int h_samp_factor=1,v_samp_factor=1;};
struct jpeg_compress_struct { jpeg_error_mgr* err=nullptr; JDIMENSION image_width=0,image_height=0,next_scanline=0; int input_components=0,in_color_space=0,num_components=3; jpeg_component_info ci[3]; jpeg_component_info* comp_info=ci; };
static inline jpeg_error_mgr* jpeg_std_error(jpeg_error_mgr* e){return e;}
static inline void jpeg_create_compress(jpeg_compress_struct*){}
static inline void jpeg_stdio_dest(jpeg_compress_struct*,FILE*){}
static inline void jpeg_set_defaults(jpeg_compress_struct*){}
static inline void jpeg_set_quality(jpeg_compress_struct*,int,int){}
static inline void jpeg_start_compress(jpeg_compress_struct*,int){}
static inline JDIMENSION jpeg_write_scanlines(jpeg_compress_struct* c,JSAMPROW*,JDIMENSION n){c->next_scanline+=n; return n;}
static inline void jpeg_finish_compress(jpeg_compress_struct*){}
static inline void jpeg_destroy_compress(jpeg_compress_struct*){}
'''
MOTION = r'''#pragma once
#include <array>
#include <string>
namespace iris26507 {
struct GainmapMetadata { std::array<float,3> ratioMin{},ratioMax{},gamma{},epsilonSdr{},epsilonHdr{}; float displaySdr=1.f,displayHdr=1.f; bool useBaseColorSpace=false; };
static inline bool packageJpegR(const char*,const char*,const char*,int,const GainmapMetadata&,std::string*){return true;}
static inline bool isJpegR(const char*){return true;}
}
'''

def need(v,msg):
    if not v: raise SystemExit('FAIL: '+msg)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',required=True); a=ap.parse_args(); root=Path(a.root)
    src=root/'app/src/main/cpp/motionv2_jpeg444_jni.cpp'
    need(src.is_file(),'missing motionv2_jpeg444_jni.cpp')
    text=src.read_text(encoding='utf-8')
    for tok in ('writeSuperResNative','jpeg_write_scanlines','detailLog2Q8','finalToUnrotated'):
        need(tok in text,'missing native SR contract '+tok)
    need('outW=(int)info.width*2' in text and 'outH=(int)info.height*2' in text,'native output is not fixed 2x')
    compiler=shutil.which('clang++') or shutil.which('g++'); need(compiler,'no C++ compiler')
    java_home=os.environ.get('JAVA_HOME',''); candidates=[]
    if java_home: candidates.append(Path(java_home)/'include')
    if Path('/usr/lib/jvm').exists(): candidates += list(Path('/usr/lib/jvm').glob('*/include'))
    jni=next((p for p in candidates if (p/'jni.h').is_file()),None); need(jni,'JNI headers missing')
    with tempfile.TemporaryDirectory(prefix='iris26532-jpeg-native-') as td:
        td=Path(td); (td/'android').mkdir()
        (td/'android/bitmap.h').write_text(ANDROID_BITMAP)
        (td/'android/log.h').write_text(ANDROID_LOG)
        (td/'turbojpeg.h').write_text(TURBO)
        (td/'jpeglib.h').write_text(JPEG)
        (td/'motionv2_jpeg_r_encoder.h').write_text(MOTION)
        cmd=[compiler,'-std=c++17','-fsyntax-only','-Werror=return-type','-I'+str(td),'-I'+str(jni)]
        if (jni/'linux').is_dir(): cmd.append('-I'+str(jni/'linux'))
        cmd.append(str(src))
        cp=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        if cp.returncode:
            print(cp.stdout); raise SystemExit('FAIL: 26532 native JPEG/JNI syntax')
    print('PASS: 26532 native JPEG/JNI syntax + fixed-2x scanline contract')

if __name__=='__main__': main()
