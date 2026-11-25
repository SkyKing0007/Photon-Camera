#!/usr/bin/env python3
"""Compile actual private Kotlin writer/HDR and C TinyDNG JNI; no Android/toolchain substitution."""
import pathlib,subprocess,tempfile,shutil,os,struct,sys
R=pathlib.Path(__file__).resolve().parent;F=R/'26985_host_fixtures';K=R/'app/src/main/java/com/hinnka/mycamera/processor';N=R/'app/src/main/cpp/iris26985c_lkr2420';LK=N/'tools/lkr-lite/src/main/cpp';TD=N/'app/src/main/cpp/deps/tinydng'
def run(*a):subprocess.run(list(map(str,a)),check=True)
def tags(p):
 with p.open('rb') as f:
  assert f.read(4)==b'II*\0';offset=struct.unpack('<I',f.read(4))[0];f.seek(offset);count=struct.unpack('<H',f.read(2))[0];d={}
  for _ in range(count):
   tag,typ,n=struct.unpack('<HHI',f.read(8));data=f.read(4);pos=f.tell();size={1:1,2:1,3:2,4:4,5:8,7:1,9:4,10:8,11:4,12:8}[typ]*n
   if size>4:f.seek(struct.unpack('<I',data)[0]);data=f.read(size);f.seek(pos)
   else:data=data[:size]
   if typ in (3,4,9,11,12):d[tag]=struct.unpack('<'+{3:'H',4:'I',9:'i',11:'f',12:'d'}[typ]*n,data)
   elif typ in (5,10):v=struct.unpack('<'+('I' if typ==5 else 'i')*(2*n),data);d[tag]=tuple(v[i]/v[i+1] for i in range(0,len(v),2))
   else:d[tag]=data
  return d
with tempfile.TemporaryDirectory(prefix='26985_native_host_') as td:
 t=pathlib.Path(td);exe=t/'stability';run('g++','-O3','-ffp-contract=off','-fno-fast-math','-std=c++17','-I'+str(LK),F/'update_stability.cpp',LK/'lkrl_image.cpp',LK/'lkrl_mhc.cpp','-o',exe);run(exe);assert subprocess.run([str(exe),'--baseline']).returncode==1
 # Exercise the actual corrected C++ statement block against a mock API26 loader.
 # The loader deliberately does not export the Vulkan 1.1 core symbol. The old
 # direct call must fail real host linking, and the new code must compile/link
 # and preserve properties in all three runtime capability cases.
 srp=N/'tools/sr-pipeline/src/main/cpp/srp_context.cpp';src=srp.read_text()
 a=src.index('  VkPhysicalDeviceSubgroupProperties subgroup{};');z=src.index('  auto* ctx = new Context();',a)
 block=src[a:z];assert 'vkGetPhysicalDeviceProperties2(chosen,' not in block
 assert 'vkGetInstanceProcAddr(instance, "vkGetPhysicalDeviceProperties2")' in block
 stub=r'''
#include <cassert>
#include <cstdint>
#include <cstring>
#define VK_API_VERSION_1_1 11
#define VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SUBGROUP_PROPERTIES 1
#define VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_PROPERTIES_2 2
using VkInstance=int; using VkPhysicalDevice=int;
struct VkPhysicalDeviceProperties {uint32_t apiVersion; char deviceName[32];};
struct VkPhysicalDeviceSubgroupProperties {int sType; uint32_t subgroupSize;};
struct VkPhysicalDeviceProperties2 {int sType; void* pNext; VkPhysicalDeviceProperties properties;};
using PFN_vkGetPhysicalDeviceProperties2=void(*)(VkPhysicalDevice,VkPhysicalDeviceProperties2*);
extern void vkGetPhysicalDeviceProperties2(VkPhysicalDevice,VkPhysicalDeviceProperties2*);
static int api=10;static bool available=false;static int calls=0,queries=0;
void vkGetPhysicalDeviceProperties(VkPhysicalDevice, VkPhysicalDeviceProperties* p){p->apiVersion=api;std::strcpy(p->deviceName,"API26 device");}
void resolved(VkPhysicalDevice d,VkPhysicalDeviceProperties2* p){++calls;vkGetPhysicalDeviceProperties(d,&p->properties);static_cast<VkPhysicalDeviceSubgroupProperties*>(p->pNext)->subgroupSize=32;}
void (*vkGetInstanceProcAddr(VkInstance,const char* n))(){++queries;assert(!std::strcmp(n,"vkGetPhysicalDeviceProperties2"));return available?reinterpret_cast<void(*)()>(resolved):nullptr;}
void test(){VkPhysicalDevice chosen=1;VkInstance instance=1;
'''
 main=r'''
assert(!std::strcmp(props2.properties.deviceName,"API26 device"));assert(subgroup.subgroupSize==(api>=11&&available?32u:0u));}
int main(){test();assert(queries==0&&calls==0);api=11;test();assert(queries==1&&calls==0);available=true;test();assert(queries==2&&calls==1);}
'''
 f=t/'vulkan_api26.cpp';f.write_text(stub+block+main);run('g++','-std=c++17','-O0','-Wl,--no-undefined',f,'-o',t/'vulkan_api26');run(t/'vulkan_api26')
 assert ' U vkGetPhysicalDeviceProperties2' not in subprocess.check_output(['nm','-u',str(t/'vulkan_api26')],text=True)
 old=t/'v1.cpp';old.write_text(stub+block[:block.index('  // Android API 26')]+ '  vkGetPhysicalDeviceProperties2(chosen, &props2);\n'+main)
 neg=subprocess.run(['g++','-std=c++17','-O0','-Wl,--no-undefined',str(old),'-o',str(t/'v1')],capture_output=True,text=True);assert neg.returncode!=0 and 'vkGetPhysicalDeviceProperties2' in neg.stderr,neg.stderr
 # No neural work in prewarming. The actual Java entry point and controller
 # must retain both C-ON ownership and nonblocking, current-session checks.
 jni=(LK/'lkrl_jni.cpp').read_text();start=jni.index('JNIEXPORT jlong JNICALL Java_com_hinnka_mycamera_processor_Iris26985CLkrNative_nativePrewarm');end=jni.index('JNIEXPORT void JNICALL Java_com_hinnka_mycamera_processor_Iris26985CLkrNative_nativeFree',start);warm=jni[start:end]
 assert 'lkrl::Solver solver(&gpu)' in warm and 'PriorPrewarm(' not in warm and 'iris26985c_lkrl_2420_pipelines.bin' in warm
 br=(K/'GlesIris26983COnLkrBridge.java').read_text();cc=(R/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text();assert br.count('Iris26985CLkrNative.nativePrewarm(')==1 and 'VULKAN_PREWARM.compareAndSet(false, true)' in br and 'THREAD_PRIORITY_BACKGROUND' in br and 'if (!success) VULKAN_PREWARM.set(false)' in br
 start=cc.index('// C ON preview has its own Vulkan cache');end=cc.index('}, 1400L);',start);warm_call=cc[start:end];assert 'iris26983COnSelected()' in warm_call and 'mCaptureSession == cameraCaptureSession' in warm_call and 'iris26983CanChangeSrOwner()' in warm_call and '!CaptureController.isProcessing' in warm_call and '.prewarmAsync(' in warm_call
 print('PASS V1 API26 undefined-symbol link reproduced; V2 runtime resolution on 1.0 / missing / available 1.1 entry; C ON Vulkan-only idle cache warmup source gates')
 java=pathlib.Path(shutil.which('javac')).resolve().parent.parent;objs=[]
 for name in ('tinydng_api.c','tinydng_io.c','tinydng_tiff.c','tinydng_dng.c','tinydng_codec.c','tinydng_write.c','tinydng_psd.c','tinydng_psd_write.c','tiny_dng_ljpeg92_v2.c'):
  obj=t/(name+'.o');run('gcc','-std=gnu11','-O2','-fPIC','-DTINYDNG_NO_ZIP','-DTINYDNG_NO_BASELINE_JPEG','-DTINYDNG_NO_PSD','-DTINYDNG_DISABLE_THREADS','-I'+str(TD),'-c',TD/name,'-o',obj);objs.append(obj)
 run('g++','-shared','-std=c++17','-fPIC','-I'+str(TD),'-I'+str(java/'include'),'-I'+str(java/'include/linux'),N/'app/src/main/cpp/tinydng_jni.cpp',*objs,'-o',t/'libiris26985clkr2420.so')
 jar=t/'tests.jar';run('kotlinc',*sorted((K/'experimentc/lkr2420').glob('*.kt')),*sorted(F.glob('*.kt')),*sorted((F/'stubs').glob('*.kt')),'-include-runtime','-d',jar)
 for cls,args in [('HdrTestKt',[]),('WriterTestKt',[t]),('Full50TestKt',[t/'full50.dng'])]:run('java','-Xmx256m','-Djava.library.path='+str(t),'-cp',jar,'com.hinnka.mycamera.processor.experimentc.lkr2420.'+cls,*args)
 d=tags(t/'full50.dng');assert d[256]==(8192,) and d[257]==(6144,) and d[258]==(16,16,16) and d[259]==(1,) and d[262]==(34892,) and d[277]==(3,) and d[278]==(256,) and len(d[273])==len(d[279])==24
 assert d[50730]==(1.0,) and 33421 not in d and 33422 not in d and 50721 in d and 50728 in d
 with (t/'full50.dng').open('rb') as f:
  for off in (d[273][0],d[273][-1]+d[279][-1]-6):f.seek(off);assert struct.unpack('<HHH',f.read(6))==(8192,16384,49151)
 lo=tags(t/'linear-1.0.dng');hi=tags(t/'linear-2.0.dng');assert hi[50730]==(1.0,) and all(abs(v-u*(.5 if i%2==0 else .25))<1e-10 for i,(u,v) in enumerate(zip(lo[51041],hi[51041])))
 run('javac','-d',t,F/'ParseJava.java');changed=(R/'26985_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines();run('java','-cp',t,'ParseJava',*(R/p for p in changed if p.endswith('.java')));run('javac','-d',t,K/'Iris26985CLkrNative.java')
print('PASS real host C++ stability + negative, TinyDNG JNI, Kotlin HDR + full 50MP striped RGB TIFF samples and Java syntax; Android real compilation remains mandatory in Actions')
