#!/usr/bin/env python3
"""Strict cross-owner shader <-> Vulkan descriptor-layout ABI regression.

The 26920 V3 APK crashed for BOTH toggle states before GPU dispatch because
VulkanExecutor's eager vkCreateComputePipelines() used 26917 layouts without
26920's new, unconditionally declared storage buffer bindings (4 and 9).
Do not remove this test or accept source-only SPIR-V-validation as ABI proof.
"""
from __future__ import annotations
from pathlib import Path
import re,struct,sys
R=Path(__file__).resolve().parent
ROOT=R if '--live' in sys.argv or '--compiled' in sys.argv or '--cmake' in sys.argv else R/'handoff_payload_26920'
CP='app/src/main/cpp/iris26864/vendor/rawr/native/multiframe/pipeline/src/'
EXEC=ROOT/CP/'VulkanExecutor.cpp'
REC=ROOT/CP/'MultiframeRecorder.cpp'
SCR=ROOT/CP/'ScratchLayout.cpp'
ANDROID=ROOT/CP/'AndroidBurstCoordinator.cpp'
NATIVE_CMAKE=ROOT/'app/src/main/cpp/iris26864/vendor/rawr/native/multiframe/pipeline/CMakeLists.txt'
# CRITICAL 26920 V5: the successful 26917 CMake path clones vendor source
# to a private HDRq shadow and then REPLACES these exact two files. Checking
# only the vendor originals produced the V4 false-positive and phone crash.
BUILD_CMAKE=ROOT/'app/src/main/cpp/iris26864/Iris26864VendorRawr.cmake'
BRIDGE_ROOT='app/src/main/cpp/iris26864/bridge/'
BRIDGE_EX=ROOT/(BRIDGE_ROOT+'Iris26888BOffVulkanExecutor.cpp')
BRIDGE_CO=ROOT/(BRIDGE_ROOT+'Iris26888BOffHdrqCoordinator.cpp')
MODS={
 'lk_refine': {
  'shader':'app/src/main/cpp/iris26864/vendor/rawr/native/multiframe/alignment/shaders/lk_refine.comp',
  'next':'flow_dense_smooth',
  'binding':4,
  'expected':{0:'image',1:'image',2:'image',3:'image',4:'buffer'},
  'push_fields':['int ts;','int tilesX;','int tilesY;','int iterations;','float eps;','float clipRadius;','float noiseSlope;','float noiseOffset;','int iris26920Active;'],
  'push_cpp':'struct LkPc',
 },
 'robust_photometric':{
  'shader':'app/src/main/cpp/iris26864/vendor/rawr/native/multiframe/merge_wronski/shaders/robust_photometric.comp',
  'next':'robust_erode5',
  'binding':9,
  'expected':{0:'image',1:'image',2:'image',3:'image',4:'image',5:'image',6:'buffer',7:'buffer',8:'image',9:'buffer'},
  'push_fields':['float t;','int clampNoise;','int tileSize;','int w;','int h;','int iris26920Active;'],
  'push_cpp':'struct PhotoPc',
 },
}

def validate_shadow_ownership():
    shadow_ex=BRIDGE_EX.read_text()
    shadow_co=BRIDGE_CO.read_text()
    native_ex=EXEC.read_text()
    native_co=ANDROID.read_text()
    for source,label in ((native_ex,'vendor source'),(shadow_ex,'CMake compiled shadow')):
        for name,spec in MODS.items():
            section=source.split('{"'+name+'",',1)[1].split('{"'+spec['next']+'",',1)[0]
            entries=re.findall(r'\{(\d+), VK_DESCRIPTOR_TYPE_(STORAGE_IMAGE|STORAGE_BUFFER)\}',section)
            actual={int(n):'image' if t=='STORAGE_IMAGE' else 'buffer' for n,t in entries}
            assert len(entries)==len(actual) and actual==spec['expected'],(label,name,actual)
        assert 'mf compute pipeline shader=' in source and ' variant=' in source,(label,'unidentified failed pipeline')
    for co,label in ((native_co,'vendor'),(shadow_co,'CMake compiled shadow')):
        for expected in ('VK_BUFFER_USAGE_STORAGE_BUFFER_BIT | VK_BUFFER_USAGE_TRANSFER_DST_BIT',
                         'destroyHostBuffer(iris26920Counts_)',
                         'if (merge_.iris26920Active) ensureHostBuffer(iris26920Counts_, 16u);',
                         'vkCmdCopyBuffer(command_',
                         'arena_.buffer("iris26920_stats").buffer',
                         'result.iris26920Enabled = true',
                         'result.iris26920Counts[0] != tileMax'):
            assert expected in co,(label,'missing active Wronski counter owner',expected)
    # Old B OFF/HDRq specializations must remain selected by CMake, but the
    # overlay sources must now also support the common Wronski ON executor.
    if ROOT==R:
        cm=BUILD_CMAKE.read_text()
        for path in ('Iris26888BOffVulkanExecutor.cpp','Iris26888BOffHdrqCoordinator.cpp'):
            assert 'configure_file("${CMAKE_CURRENT_SOURCE_DIR}/iris26864/bridge/'+path+'"' in cm,('CMake build-shadow wiring lost',path)
        assert 'file(COPY "${IRIS26864_VENDOR_ROOT}/" DESTINATION "${IRIS26887_VENDOR_SHADOW}")' in cm
        assert 'add_subdirectory("${IRIS26887_VENDOR_SHADOW}/multiframe/pipeline"' in cm
        assert 'add_subdirectory("${IRIS26864_VENDOR_ROOT}/multiframe/pipeline"' not in cm
        for path in ('AndroidBurstCoordinator.cpp','VulkanExecutor.cpp'):
            assert '  src/'+path in NATIVE_CMAKE.read_text(),('missing compiled shadow target',path)
    print('PASS 26920 V5 ACTUAL-CMAKE-SHADOW-OWNER: copied bridge Vulkan descriptor ABI and Wronski GPU counter ownership match active source; no unused-vendor-source false PASS')

def validate_generated_shadow():
    """After real NDK build, prove CMake's effective per-ABI copies contain fixes."""
    root=R/'app/.cxx'
    for abi in ('arm64-v8a','armeabi-v7a'):
        for file,source in (('VulkanExecutor.cpp',BRIDGE_EX),('AndroidBurstCoordinator.cpp',BRIDGE_CO)):
            matches=[p for p in root.glob('**/iris26887_b_only_vendor/native/multiframe/pipeline/src/'+file)
                     if abi in p.parts]
            assert len(matches)==1,(abi,file,'expected exactly one actual CMake generated shadow source; got',matches)
            assert matches[0].read_bytes()==source.read_bytes(),(abi,file,'actual CMake shadow source diverges from SHA-sealed runtime')
    print('PASS 26920 V5 ACTUAL-CMAKE-SHADOW-BINARY-OWNER: both ABI configured copies byte-identical to guarded bridge files; real APK compilation required')

def validate_source():
 validate_shadow_ownership()
 executor=EXEC.read_text();record=REC.read_text();scratch=SCR.read_text();android=ANDROID.read_text()
 if ROOT==R:
  assert 'src/VulkanExecutor.cpp' in NATIVE_CMAKE.read_text(), 'actual CMake executor not checked'
 assert 'VkResult=' in executor and 'shader=' in executor and 'variant=' in executor, 'failure not identifiable on device'
 assert 'for (const auto expected : s.b)' in executor and 'missing/duplicate required binding' in executor
 assert 'if (wantTrace) bs.push_back({31, VK_DESCRIPTOR_TYPE_STORAGE_BUFFER' in executor
 for name,spec in MODS.items():
  source=(ROOT/spec['shader']).read_text()
  section=executor.split('{"'+name+'",',1)[1].split('{"'+spec['next']+'",',1)[0]
  entries=re.findall(r'\{(\d+), VK_DESCRIPTOR_TYPE_(STORAGE_IMAGE|STORAGE_BUFFER)\}',section)
  observed={int(num): 'image' if kind=='STORAGE_IMAGE' else 'buffer' for num,kind in entries}
  assert len(entries)==len(observed), 'duplicate executor descriptor binding '+name
  assert observed==spec['expected'],f'executor {name} expected={spec["expected"]}, actual={observed}'
  source_entries=re.findall(r'layout\([^)]*?\bbinding\s*=\s*(\d+)\b[^)]*\)\s*(?:readonly|writeonly|uniform|buffer|\s)*',source)
  keys=set(map(int,source_entries))
  assert keys==set(observed)|{31},f'{name} GLSL bindings diverged from executor, got {keys}'
  assert '#ifdef RAWR_PARITY_TRACE' in source and 'binding = 31' in source
  assert all(x in source for x in spec['push_fields']),name+' push constants diverged'
  assert spec['push_cpp'] in record and 'iris26920Active' in record
  assert f'bb({spec["binding"]}, arena_.buffer("iris26920_stats"))' in record,name+' runtime dispatch missing SSBO'
  if name=='lk_refine':
   assert 'ShaderId::LkRefine' in record and 'sizeof(lp)' in record
  else:
   assert 'ShaderId::RobustPhotometric' in record and 'sizeof(pp)' in record
  assert 'iris26920Active' in source and 'atomicAdd(iris26920.counters' in source
 assert 'buf("iris26920_stats", 4u * sizeof(std::uint32_t), Lifetime::Burst)' in scratch
 assert 'vkCmdCopyBuffer(command_,arena_.buffer("iris26920_stats").buffer' in android
 assert 'vkCmdFillBuffer(c, arena_.buffer("iris26920_stats").buffer, 0, 16u, 0u)' in record
 if ROOT==R:
  assert 'VK_BUFFER_USAGE_STORAGE_BUFFER_BIT | VK_BUFFER_USAGE_TRANSFER_SRC_BIT' in (ROOT/CP/'ResourceArena.cpp').read_text(), 'stats buffer lacks STORAGE+TRANSFER_SRC'
 assert 'if (merge_.iris26920Active)' in android and 'iris26920Counts_' in android
 # Neither the OFF toggle nor trace mode removes the SSBO from compiled shaders;
 # descriptor layouts must therefore contain these bindings in BOTH modes.
 print('PASS 26920 V5 source Vulkan ABI: LK SSBO binding4, photo SSBO binding9, prod/trace 31, runtime resources, count=16 bytes, push constants, eager initialization')

def parse_spv(path):
 data=path.read_bytes()
 assert len(data)>=20 and len(data)%4==0 and struct.unpack_from('<I',data)[0]==0x07230203,(path,'SPIR-V magic')
 words=struct.unpack('<'+'I'*(len(data)//4),data)
 ids={}; ptr={}; variables={}; types={};decor={}
 i=5
 while i<len(words):
  head=words[i];n=head>>16;op=head&0xffff
  assert n>=1 and i+n<=len(words),(path,i,op)
  w=words[i+1:i+n]
  if op==71 and len(w)>=2: # OpDecorate
   if w[1] in (33,34,2,3):decor.setdefault(w[0],{})[w[1]]=w[2] if len(w)>=3 else True
  elif op==32: # OpTypePointer, result-id, storageclass, pointee
   ptr[w[0]]=(w[1],w[2])
  elif op==59: # OpVariable
   variables[w[1]]=(w[0],w[2])
  elif op in (25,26,27,30):
   types[w[0]]=op
  i+=n
 out={}
 for var,(pointer,storage) in variables.items():
  d=decor.get(var,{})
  if 33 not in d:continue
  assert d.get(34)==0,(path,var,'non-zero descriptor set',d)
  binding=d[33]
  pclass,pointee=ptr[pointer]
  assert pclass==storage,(path,var,'pointer storageclass mismatch')
  if storage==0:kind='image' # UniformConstant: actual source storage images
  elif storage==12:kind='buffer' # StorageBuffer
  elif storage==2 and decor.get(pointee,{}).get(3):kind='buffer' # Uniform with BufferBlock
  else:raise AssertionError(f'{path}: unhandled {binding=} {storage=} {decor.get(pointee)}')
  assert binding not in out,(path,'duplicate binding',binding)
  out[binding]=kind
 return out

def validate_compiled(paths):
 for (name,variant),path in paths.items():
  actual=parse_spv(path)
  exp=MODS[name]['expected'] | ({31:'buffer'} if variant=='trace' else {})
  assert actual==exp,f'{path}: binary SPIR-V interface differs, expected={exp} actual={actual}'
 print('PASS 26920 V5 compiled SPIR-V REFLECTION: exact descriptor sets/binding types, production+trace for BOTH LK shaders; count='+str(len(paths)))

if __name__=='__main__':
 validate_source()
 if '--compiled' in sys.argv:
  folder=R/'photon_26920_outputs/26920_lk_shaders'
  validate_compiled({(n,v):folder/f'{n}_{v}.spv' for n in MODS for v in ('prod','trace')})
  validate_compiled({(n,v):folder/f'{n}_{v}.opt.spv' for n in MODS for v in ('prod','trace')})
 if '--cmake' in sys.argv:
  validate_generated_shadow()
  cxx=R/'app/.cxx'
  found={}
  for abi in ('arm64-v8a','armeabi-v7a'):
   for name in MODS:
    for variant in ('prod','trace'):
     candidates=list(cxx.glob(f'**/{abi}/**/generated/multiframe/{variant}/{name}.spv'))
     assert len(candidates)==1,(abi,name,variant,candidates)
     found[(abi,name,variant)]=candidates[0]
  for abi in ('arm64-v8a','armeabi-v7a'):
   validate_compiled({(n,v):found[(abi,n,v)] for n in MODS for v in ('prod','trace')})
