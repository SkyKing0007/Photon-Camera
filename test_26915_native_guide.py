#!/usr/bin/env python3
"""Compiles the ORIGINAL 26915 C++ JNI function and production pure row packer.
Exercised both main and tele padded rows, exact RGB and all clip half bits,
negative tests, lock/unlock lifetime; no fake replacement source algorithm.
Android NDK compilers still mandatory in Actions.
"""
from pathlib import Path
import os,subprocess,tempfile,re,sys
ROOT=Path(__file__).resolve().parent
USE_LIVE='--live' in sys.argv
prefix=(ROOT if (ROOT/'app/src').is_dir() else ROOT/'candidate_26915') if USE_LIVE else ROOT/'handoff_payload_26915'
CPP=prefix/'app/src/main/cpp/motionv2_jpeg444_jni.cpp'
HEADER=prefix/'app/src/main/cpp/iris26915_rgba16f_guide.h'
assert CPP.is_file() and HEADER.is_file()
s=CPP.read_text()
needle='/* IRIS_26915_FINAL_1X_STRIDE_AWARE_CPU_PACK'
start=s.index(needle);stop=s.index('extern "C" JNIEXPORT jobject JNICALL Java_com_particlesdevs_photoncamera_processing_processor_MotionV2SharedRgba16fCarrier_lockCpuNative',start)
actual=s[start:stop]
assert actual.count('AHardwareBuffer_unlock')==1 and actual.count('AHardwareBuffer_lock')==1
assert 'iris26915guide::pack(' in actual and 'desc.stride' in actual
fake='''#include <vector>
#include <cstring>
#include <cstdint>
#include <cstddef>
#include <cstdio>
#include <cassert>
#include <climits>
#include <algorithm>
#include "iris26915_rgba16f_guide.h"
#define JNIEXPORT
#define JNICALL
#define JNI_TRUE true
#define JNI_FALSE false
#define ANDROID_LOG_WARN 5
#define ANDROID_LOG_INFO 4
#define AHARDWAREBUFFER_USAGE_CPU_WRITE_OFTEN 0x100
using jboolean=bool;using jint=int;using jlong=long long;using jclass=void*;using jobject=void*;
const char* TAG="TEST";
int __android_log_print(int,const char*,const char*,...){return 0;}
struct FakeJBuf {std::vector<uint8_t> bytes;};
struct JNIEnv { jlong GetDirectBufferCapacity(jobject o){return ((FakeJBuf*)o)->bytes.size();}
 void* GetDirectBufferAddress(jobject o){return ((FakeJBuf*)o)->bytes.data();}};
struct AHardwareBuffer {int width, height;size_t stride;bool lockFail=false,locked=false;std::vector<uint8_t> data;};
struct AHardwareBuffer_Desc {uint32_t width=0,height=0,layers=1,format=1,stride=0;};
bool iris26826Describe(JNIEnv*,jobject o,AHardwareBuffer** out,AHardwareBuffer_Desc* d,int w,int h){
 if(!o)return false;
 auto* b=(AHardwareBuffer*)o;
 if(b->width!=w||b->height!=h)return false;
 *out=b;d->width=b->width;d->height=b->height;d->stride=b->stride;return true;}
int AHardwareBuffer_lock(AHardwareBuffer*b,int,long,void*,void**ptr){if(b->lockFail)return -12;
 assert(!b->locked);b->locked=true;*ptr=b->data.data();return 0;}
int AHardwareBuffer_unlock(AHardwareBuffer*b,void*){if(!b->locked)return -1;b->locked=false;return 0;}
'''
test='''
int main(){
 JNIEnv env;
 for(int width:{4096,4080,3}) {
  int height=3;size_t stride=(width==4080 ? 4096 : (size_t)width);
  AHardwareBuffer h{width,height,stride,false,false,std::vector<uint8_t>(stride*height*8,0xA5)};
  FakeJBuf rgb,mask;rgb.bytes.resize((size_t)width*height*8);mask.bytes.resize((size_t)width*height*2);
  for(size_t j=0;j<rgb.bytes.size();++j)rgb.bytes[j]=(uint8_t)(j*37u+11u);
  for(int i=0;i<width*height;++i){uint16_t bits=(i%3==0?0x0000:(i%3==1?0x8000:0x3c00));std::memcpy(mask.bytes.data()+2u*i,&bits,2);}
  auto run=[&](){return Java_com_particlesdevs_photoncamera_processing_processor_MotionV2SharedRgba16fCarrier_writeFinal1xGuideNative(&env,nullptr,&h,&rgb,&mask,width,height);};
  assert(run());assert(!h.locked);
  for(int y=0;y<height;++y){
   for(int x=0;x<width;++x){size_t in=((size_t)y*width+x)*8;size_t out=((size_t)y*stride+x)*8;
    assert(std::memcmp(h.data.data()+out,rgb.bytes.data()+in,6)==0);
    assert(std::memcmp(h.data.data()+out+6,mask.bytes.data()+((size_t)y*width+x)*2,2)==0);}
   for(size_t x=width;x<stride;++x)for(int k=0;k<8;++k)assert(h.data[((size_t)y*stride+x)*8+k]==0xA5);
  }
  h.lockFail=true;assert(!run());assert(!h.locked);h.lockFail=false;
  auto original=h.data;
  uint16_t invalid=0x7e00;std::memcpy(mask.bytes.data(),&invalid,2);
  assert(!run());assert(h.data==original);assert(!h.locked);
  invalid=0xbc00;std::memcpy(mask.bytes.data(),&invalid,2);
  assert(!run());assert(h.data==original);
  invalid=0x3c01;std::memcpy(mask.bytes.data(),&invalid,2);
  assert(!run());assert(h.data==original);
  invalid=0x0000;std::memcpy(mask.bytes.data(),&invalid,2);
  mask.bytes.pop_back();assert(!run());assert(h.data==original);
  mask.bytes.push_back(0);rgb.bytes.pop_back();assert(!run());
 }
 size_t a=0,b=0,c=0;
 assert(!iris26915guide::sizes(4080,6144,4079,&a,&b,&c));
 assert(iris26915guide::sizes(4080,3072,4096,&a,&b,&c));
 assert(a==(size_t)4080*3072*8 && b==(size_t)4080*3072*2 && c==(size_t)4096*8);
 std::puts("PASS 26915 real JNI method compiled + 4096/4080-padded pixel, mask, guards, and exact unlock");
}
'''
with tempfile.TemporaryDirectory() as td:
 p=Path(td);(p/'iris26915_rgba16f_guide.h').write_bytes(HEADER.read_bytes());(p/'test.cpp').write_text(fake+actual+test)
 subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror','-O2','-I',str(p),str(p/'test.cpp'),'-o',str(p/'a.out')],check=True)
 subprocess.run([str(p/'a.out')],check=True)
