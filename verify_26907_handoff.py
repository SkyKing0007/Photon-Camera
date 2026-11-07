#!/usr/bin/env python3
"""26907 independent three-stage, 26906 successful authority and real-compiler guard."""
from pathlib import Path
import hashlib,re,sys
R=Path(__file__).resolve().parent
WF='.github/workflows/build-26907-change-aware.yml'
PARENTWF='.github/workflows/build-26906-change-aware.yml'
PARENTWF_SHA='b939ce0866e3b811fa9590ed5a721ae80fdd57d6e7ddf425b0b55f5a2e070fa1'
TRIGGER=b'RUN_26907_PREVIEW_MEASURED_HUE_ONLY_B_PHOTO_V1\n'
CHANGED='26907_CHANGED_RUNTIME_ALLOWLIST.txt'
ADDED='26907_ADDED_RUNTIME_PATHS.txt'

def must(cond,message):
    if not cond:raise AssertionError('26907 HANDOFF BLOCKED: '+message)
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def parse(name):
    rows={}
    for line in (R/name).read_text().splitlines():
        h,path=line.split('  ',1)
        must(re.fullmatch('[0-9a-f]{64}',h)!=None and path.startswith('app/')
             and '..' not in Path(path).parts and path not in rows,'bad manifest row '+path)
        rows[path]=h
    return rows

def verify():
    inventory=(R/'26907_STAGE1_PATHS.txt').read_text().splitlines()
    must(len(inventory)==len(set(inventory)) and '26907_HANDOFF_HASHES.sha256' in inventory,'Stage1 inventory invalid')
    changes=(R/CHANGED).read_text().splitlines()
    additions=(R/ADDED).read_text().splitlines()
    must(len(changes)==7 and len(set(changes))==7,'wrong seven-path allowlist')
    must(len(additions)==3 and len(set(additions))==3 and set(additions).issubset(changes),'wrong three-file additions')
    must(changes[-1]=='app/version.properties','version not included')
    must({p for p in inventory if p.startswith('handoff_payload_26907/')}==
         {'handoff_payload_26907/'+p for p in changes},'runtime staged path mismatch')
    seals={}
    for line in (R/'26907_HANDOFF_HASHES.sha256').read_text().splitlines():
        h,p=line.split('  ',1)
        must(p not in seals and re.fullmatch('[0-9a-f]{64}',h)!=None,'bad sealing row')
        seals[p]=h
    must(set(seals)==set(inventory)-{'26907_HANDOFF_HASHES.sha256'}|{WF,'TRIGGER_26907.txt'},'seal file scope mismatch')
    for p,h in seals.items():must((R/p).is_file() and sha(R/p)==h,'SHA mismatch '+p)
    must((R/'TRIGGER_26907.txt').read_bytes()==TRIGGER,'wrong trigger bytes')
    before=parse('26907_BASE_26906_FULL_APP.sha256');after=parse('26907_PRECOMPILE_EXPECTED_FULL_APP.sha256')
    must(len(before)==2027 and len(after)==2030 and set(after)-set(before)==set(additions)
         and not(set(before)-set(after)),'actual compiled source universe wrong')
    must({p for p in before if before[p]!=after[p]}==set(changes)-set(additions),'protected source changed')
    for p in changes:must(sha(R/'handoff_payload_26907'/p)==after[p],'runtime payload unsealed '+p)
    must(after['app/src/main/assets/iris26856/rawr/amaze/spv/amaze_export.spv']==
         '5853f1a0da12bab4b8c9489b6b298f3710f90fb6e51660204ed43f49963809f1','protected compiled SPV changed')
    for p in before:
        if p.startswith('app/src/main/cpp/'):
            must(before[p]==after[p],'native/vendor modified '+p)
    must((R/PARENTWF).is_file() and sha(R/PARENTWF)==PARENTWF_SHA,'wrong 26906 successful workflow authority')
    w=(R/WF).read_text()
    must(w.count('TRIGGER_26907.txt')==1 and 'experimental-clean-photon-rebuild' in w,'wrong trigger/branch')
    must(w.count('./gradlew --no-daemon --build-cache :app:assembleDebug')==1,'full Android assemble missing or repeated')
    must(w.count('python3 -S build_26907_incremental.py')==5,'builder CLI uses wrong release')
    stages=[
       'build_26907_incremental.py seal','test_26906_native_cache.py',
       'test_26907_hue_source.py','verify_26904_v3_safety.py','verify_26904_v2_safety.py',
       'build_26904_incremental.py seal','build_26907_incremental.py fetch',
       'build_26907_incremental.py prepare',
       'verify_26906_native_cache.py preflight','compile_26904_shaders_v2.sh',
       'verify_26904_v3_cmake_handoff.py --handoff','compile_26906_tone_glsl.sh',
       'compile_26907_hue_glsl.sh','build_26907_incremental.py verify-compiled',
       ':app:assembleDebug','verify_26906_native_cache.py postflight',
       'build_26907_incremental.py finalize','actions/upload-artifact@v4'
    ]
    must(w.count('test_26907_hue_source.py')==2,'missing second source regression after authority seeding')
    positions=[w.index(s) for s in stages]
    must(positions==sorted(positions),'native/compiler/historical stage order changed')
    must(w.count('verify_26906_native_cache.py preflight')==1 and
         w.count('verify_26906_native_cache.py postflight')==1,'V3 native cache replay omitted')
    must(w.index('id: native-cache') < w.index('verify_26906_native_cache.py preflight') <
         w.index('compile_26904_shaders_v2.sh'),'unsafe native cache sequence')
    must(w.index(':app:assembleDebug') < w.index('verify_26906_native_cache.py postflight') <
         w.index('build_26907_incremental.py finalize'),'native cache postflight wrong order')
    runner=(R/'build_26907_incremental.py').read_text()
    must("prefix='photon_26906_outputs/'" in runner and
         'photon_26906_incremental_outputs/' not in runner,'stale prior artifact folder')
    must('RUN=42326224775' in runner and 'ART_ID=13554978914' in runner and
         '37f80237361357a52f9774fd51c4bfb55ba6276f' in runner,'wrong successful 26906 authority identity')
    must('ACTUAL_EXECUTED_build_26906_incremental.py' in runner and
         'ACTUAL_EXECUTED_build-26906-change-aware.yml' in runner,'executed parent runner provenance omitted')
    must('26907_HUE_SHADER_REAL_COMPILER.txt' in runner and
         '26907_HUE_SHADER_SPIRV_VALIDATED.txt' in runner,'new real shader compiler gate missing')
    must('26906_TONE_SHADER_REAL_COMPILER.txt' in runner and
         '26906_TONE_SHADER_SPIRV_VALIDATED.txt' in runner,'inherited real tone shader gate missing')
    must('2023' in runner and '2030' in runner and 'added=3' in runner,'wrong scoped proof numbers')
    must('26906_success.zip' in runner and '26906_PREBUILD_SEALED_APP.sha256' in runner,'wrong parent compiled ZIP/receipt')
    shader_compiler=(R/'compile_26907_hue_glsl.sh').read_text()
    must('spirv-val --target-env opengl4.5' in shader_compiler and 'spirv-opt' in shader_compiler and
         'probe.frag' in shader_compiler and 'hue.frag' in shader_compiler,
         'actual probe/hue shaders not compiled in release')
    print('PASS 26907 three-stage exact bytes, successful 26906 source+builder+workflow, 7 scoped edits, 2023 protected, V3 native replay, pinned real shader/NDK/Java/Kotlin/assemble gates')

if __name__=='__main__':
    try:verify()
    except Exception as e:print('26907 HANDOFF FAIL',e,file=sys.stderr);sys.exit(1)
