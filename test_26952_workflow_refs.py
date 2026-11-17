#!/usr/bin/env python3
"""Exact 26951 successful historical workflow prefix, correct new Actions refs,
real shader/NDK/compiler and release gates, no unused/obsolete executable refs.
"""
import re,subprocess,sys
from build_26952_incremental import R,fail,STAGE1_FILES,sha
PREV_SHA='40980c9badbe157fab569971f063966360ca9f0b6020792df1f1dd2be069966b'
OLD=R/'26951_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml'
NEW=R/'.github/workflows/build-26952-change-aware.yml'
if sha(OLD)!=PREV_SHA:fail('original successful 26951 executed workflow reference modified')
old=OLD.read_text();new=NEW.read_text();cut='      - name: Fetch SUCCESSFUL 26949 Actions run'
if old.count(cut)!=1:fail('old workflow anchor missing')
prefix=old[:old.index(cut)].replace('name: Photon 26951 - successful 26949 RAWR HDRQ compatibility and matched SDR','name: Photon 26952 - successful 26951 LKR color parity, 3x2 preserved and SDR halo guard',1).replace('      - TRIGGER_26951.txt','      - TRIGGER_26952.txt',1)
if not new.startswith(prefix):fail('actual successful 26951 historical verification steps/command graph weakened')
if new.count('      - name: Fetch exact successful 26951 run')!=1 or new.count('actions/upload-artifact@v4')!=1:fail('wrong actual historical provenance/artifact output')
if new.count('./gradlew --no-daemon --build-cache :app:assembleDebug --stacktrace')!=1:fail('actual real full Android compile omitted/duplicated')
for p in ('test_26903_v3_archive_receipt.py','test_26925_sealed_negatives.py','compile_26904_shaders_v2.sh','verify_26904_v3_cmake_handoff.py','verify_26906_native_cache.py','test_26931_native_integrity.py','replay_26952_inherited_glsl.py','replay_26952_26943_contract.py','compile_26952_shaders.sh','build_26952_incremental.py','prepare_26952_native.py','test_26952_native.py','test_26952_source.py','test_26952_chroma.py','test_26952_halo.py','test_26952_patches.py','test_26952_sealed_negatives.py'):
 if p not in new and p!='replay_26952_26943_contract.py':fail('mandatory historical/current executable missing '+p)
for p in ('python3 -S prepare_26952_native.py original','python3 -S test_26931_native_integrity.py --native','python3 -S prepare_26952_native.py official','python3 -S test_26952_native.py --native','python3 -S test_26952_native.py --cmake','python3 -S test_26952_native.py --apk','python3 -S build_26952_incremental.py verify-compiled','python3 -S build_26952_incremental.py finalize','python3 -S build_26952_incremental.py fetch','python3 -S build_26952_incremental.py prepare','bash compile_26952_shaders.sh'):
 if new.count(p)!=1:fail('missing or duplicated required action '+p)
if new.find('prepare_26952_native.py original')>new.find('prepare_26952_native.py official') or new.find('prepare_26952_native.py official')>new.find('compile_26952_shaders.sh'):fail('historical/new native verification order broken')
if new.find('verify-compiled')>new.find(':app:assembleDebug --stacktrace'):fail('compiler proofs run after assemble')
if 'photon_26951_outputs/26951_gradle_assemble.log' in new or 'TRIGGER_26951.txt' in new.split('jobs:',1)[0] or new.find('26952-SUCCESSFUL')>=0:fail('stale root workflow or invented success')
if new.count('photon-26952-rawlens-2394-two-radius-3x2-sdr-rim')!=1:fail('wrong publication name')
# Actual GitHub checkout already contains old 26951 files and all historical scripts.
# Only newly introduced scripts/stage files need be in the handoff.
oldinv=set(re.findall(r'\b(?:python3\s+-S\s+|bash\s+|\./)([\w.-]+\.(?:py|sh))\b',old))
newinv=set(re.findall(r'\b(?:python3\s+-S\s+|bash\s+|\./)([\w.-]+\.(?:py|sh))\b',new))
if not oldinv<=newinv|{'compile_26939_shaders.sh','compile_26941_shaders.sh','compile_26942_shaders.sh','build_26951_incremental.py','test_26951_source.py','test_26951_highlight.py','test_26951_descriptor_abi.py','test_26951_patch_proof.py','test_26951_math.py','replay_26951_inherited_26949_glsl.py','replay_26951_inherited_26948_glsl.py','replay_26951_inherited_26943_glsl.py','replay_26951_inherited_26944_glsl.py','compile_26951_shaders.sh','compile_26951_sdr_shaders.sh','prepare_26951_lkr_from_successful_26949.py'}:fail('historical execution unexpectedly removed')
listed=(R/'26952_EXPECTED_ACTION_EXECUTABLES.txt').read_text().splitlines()
if listed!=sorted(newinv) or len(listed)!=len(set(listed)):fail('missing/unused executable list '+repr(sorted(newinv^set(listed))[:20]))
if '--on-actions' in sys.argv:
 for script in listed:
  if not (R/script).is_file():fail('missing actual GitHub Actions executable '+script)
# The known 26950 V3 SPIR-V optimizer CLI regression must FAIL, including if
# source text is resealed, and both current and inherited real compiler gates exist.
shell=(R/'compile_26952_shaders.sh').read_text()
if shell.count('spirv-opt --target-env=opengl4.5 -O')!=1 or 'spirv-opt --target-env opengl4.5' in shell:fail('26904 V2/26950 V3 malformed optimizer CLI')
if not re.search(r'^\s*spirv-val --target-env opengl4.5',shell,re.M):fail('real validator absent')
for name in ('compile_26952_shaders.sh',):
 ret=subprocess.run(['bash','-n',str(R/name)],capture_output=True,text=True)
 if ret.returncode:fail('real shader bash syntax invalid '+ret.stderr)
negative=shell.replace('--target-env=opengl4.5','--target-env opengl4.5',1)
if negative==shell or 'spirv-opt --target-env opengl4.5' not in negative:fail('historical SPIR-V negative malformed')
# 26952 V1 production failure 44154665517: the newly invented urllib
# cross-host artifact ZIP transport returned HTTP 401. 26951 used curl -L.
# This regression is checked BEFORE network access, even on a resealed build.
fetch_script=(R/'build_26952_incremental.py').read_text()
fetch_region=fetch_script.split('def fetch():',1)[1].split('def safe_tar(',1)[0]
assert_curl="subprocess.run(['curl','--fail','--location','--retry','3','--silent','--show-error',"
if fetch_region.count(assert_curl)!=1 or "'-H','Authorization: Bearer '+token" not in fetch_region or "'-o',str(ART)" not in fetch_region:
 fail('26952 V1 HTTP 401 regression: not exact successful 26951 curl -L credentialed artifact fetch')
if 'with urllib.request.urlopen(req,timeout=180)' in fetch_region or "'/zip',headers=" in fetch_region:
 fail('26952 V1 HTTP 401 regression: untested urllib cross-host artifact stream')
release_script=(R/'prepare_26952_native.py').read_text()
if release_script.count("subprocess.run(['curl','--fail','--location','--retry','3',")!=1 or "'--max-time','600',RELEASE,'-o',str(apkfile)" not in release_script:
 fail('official large release must use redirect-safe curl with full SHA proof')
if 'with urllib.request.urlopen(req,timeout=180)' in release_script:
 fail('unverified native release cross-host urllib streaming restored')
# Negative: reconstruct the rejected V1 downloader in memory. The transport
# checker MUST fail even if a future handoff is independently SHA re-sealed.
def transport_valid(code):
 region=code.split('def fetch():',1)[1].split('def safe_tar(',1)[0]
 return region.count(assert_curl)==1 and "'-H','Authorization: Bearer '+token" in region and "'-o',str(ART)" in region and 'with urllib.request.urlopen(req,timeout=180)' not in region
broken=fetch_script.replace(assert_curl,"subprocess.run(['python','urllib-download','no-location',",1)
if broken==fetch_script or transport_valid(broken):fail('26952 V1 401 negative control unexpectedly accepted')
print('PASS 26952 V2 actual successful 26951 artifact curl -L transport restored; V1 401 reintroduction rejected')
# 26952 V2 Actions 44157366678 failed at step 44: the 26939 live-only
# historical median contract incorrectly rejected the valid NEW 26952 two-
# radius source at the obsolete single-radius p4=c.rb-c.g exact string.
# The actual original 26939/41/42 compiler bodies remain mandatory, but their
# historical source assertions use immutable --payload while the extracted
# shader inputs are the exact ACTIVE 26952 source, SHA-tested and compiled.
adapter=(R/'replay_26952_current_legacy_glsl.py').read_text()
for n,original_blob in (('39','1d5b72ca3b815a44f9ebd907f6d60737df00af99'),
                        ('41','b9590e3891ff1eeb8f622239967ee3f17039703a'),
                        ('42','7aaef0de4202005e686caa4ed53a37e18b7bc591')):
 if new.count('python3 -S replay_26952_current_legacy_glsl.py '+n)!=1:fail('missing actual current 26952 historical real shader compiler '+n)
 if 'compile_269'+n+'_shaders.sh' not in adapter or original_blob not in adapter:
  fail('unpinned original real glslang/SPIR-V command body '+n)
 if 'python3 -S test_269'+n+'_shader_contract.py --live --extract' not in adapter:
  fail('original stale 269'+n+' historical source contract not explicitly migrated')
 if 'python3 -S test_269'+n+'_shader_contract.py --payload' not in adapter:
  fail('269'+n+' historical regression no longer sealed payload checked')
 if 'bash compile_269'+n+'_shaders.sh' in new:fail('26952 V2 stale historical source live checker returned '+n)
if 'source SHA' not in adapter and 'sha(src)!=cur[path]' not in adapter:fail('live current shader SHA not pinned')
if 'out.replace(newcall,oldcall,1)!=txt' not in adapter:fail('original compiler bodies no longer reversible')
# Static negative: old 26939 literal is intentionally absent in the new
# two-radius GLSL, yet the new compiler adapter must select the newer source.
median=(R/'handoff_payload_26952/app/src/main/java/com/hinnka/mycamera/processor/GlesIris26932RawLensMedian.kt').read_text()
if 'highp vec2 p4=center' not in median or 'p4=c.rb-c.g' in median:
 fail('26952 V2 old-live median rejection negative fixture cannot be reconstructed')
if 'cc_median(p,m0,2)' not in median or 'cc_median(p,m0,1)' not in median:
 fail('current median is not the explicitly changed live 26952 source')
print('PASS 26952 V3 historical 26939 old-live BLOCKED regression corrected; pinned 39/41/42 real compiler bodies now target current source')
print('PASS 26952 successful 26951 historical graph unchanged, exact live executable manifest, original 26904 V2/V3 regressions and full real compile + two ABI native gates')
