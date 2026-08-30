#!/usr/bin/env python3
from pathlib import Path
import os, shutil, subprocess, sys, tempfile

if len(sys.argv)!=2: raise SystemExit('usage: compile_26565_cpp_contract.py <candidate-root>')
root=Path(sys.argv[1]).resolve()
cpp=root/'app/src/main/cpp/motionv2_jpeg444_jni.cpp'
if not cpp.is_file(): raise SystemExit('missing '+str(cpp))
clang=shutil.which('clang++')
if not clang: raise SystemExit('clang++ not found')
raw_java_home=os.environ.get('JAVA_HOME')
java_home=Path(raw_java_home).resolve() if raw_java_home else Path('/nonexistent')
if not java_home.is_dir():
    javac=shutil.which('javac')
    if javac: java_home=Path(javac).resolve().parents[1]
if not java_home.is_dir(): raise SystemExit('JAVA_HOME/javac not found')
with tempfile.TemporaryDirectory(prefix='iris26565_cpp_') as td:
    st=Path(td); (st/'android').mkdir()
    (st/'android/bitmap.h').write_text(r'''#pragma once
#include <stdint.h>
#include <jni.h>
#define ANDROID_BITMAP_RESULT_SUCCESS 0
#define ANDROID_BITMAP_FORMAT_RGBA_8888 1
#define ANDROID_BITMAP_FORMAT_A_8 8
typedef struct AndroidBitmapInfo { uint32_t width; uint32_t height; uint32_t stride; int32_t format; uint32_t flags; } AndroidBitmapInfo;
static inline int AndroidBitmap_getInfo(JNIEnv*, jobject, AndroidBitmapInfo*) { return 0; }
static inline int AndroidBitmap_lockPixels(JNIEnv*, jobject, void**) { return 0; }
static inline int AndroidBitmap_unlockPixels(JNIEnv*, jobject) { return 0; }
''')
    (st/'android/log.h').write_text(r'''#pragma once
#define ANDROID_LOG_INFO 4
#define ANDROID_LOG_ERROR 6
static inline int __android_log_print(int, const char*, const char*, ...) { return 0; }
''')
    # Use the actual pinned libjpeg-turbo and UltraHDR headers from the successful 26564 candidate.
    inc=[
        st,
        root/'app/src/main/cpp',
        root/'app/src/main/cpp/third_party_26507/libjpeg-turbo/src',
        root/'app/src/main/cpp/third_party_26507/libultrahdr',
        root/'app/src/main/cpp/third_party_26507/libultrahdr/lib/include',
        java_home/'include', java_home/'include/linux',
    ]
    cmd=[clang,'-std=c++17','-fsyntax-only','-Werror=return-type']
    for p in inc: cmd += ['-I',str(p)]
    cmd += [str(cpp)]
    print('RUN',' '.join(cmd))
    subprocess.run(cmd,check=True)
print('PASS 26565 C++17 syntax/API contract with actual pinned libjpeg/UltraHDR headers')
