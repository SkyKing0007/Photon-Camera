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
