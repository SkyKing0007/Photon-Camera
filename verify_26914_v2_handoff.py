#!/usr/bin/env python3
"""Fail-closed 26914 V2 successor: preserve FAILED V1 as historical evidence.

26914 V2 has exactly one corrected Kotlin runtime file relative to original
26914 V1; the V1 14-path scope is still measured against successful 26913.
"""
from pathlib import Path
import hashlib,re
R=Path(__file__).resolve().parent
BRIDGE='app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt'
WF='.github/workflows/build-26914-v2-change-aware.yml'
TRIGGER=b'RUN_26914_V2_KOTLIN_FROZEN_CUSTOM_NOISE_SCOPE_CORRECTION\n'
V1_BUILDER_SHA='9a47e6a863a7e4ca302c0c1cefa3233f4dfd91d7e328d02aa6f026a1a29ef7fd'
V1_WORKFLOW_SHA='2208342bf3c3485427f3514ae82ff44118aaaec0a7a4f68e577fd03d9616670c'
V1_TEST_SHA='ce76739d4c7f1795a766a05742a9c322479080b4306c284cbad86434f3ccb424'
V1_VALIDATOR_SHA='4537b14bde41a6d8a6c49f265457a6adf2e322b1bf54489079df2ba85cdf9b84'
V1_HASHES_SHA='dfb90c850d8700eb38cba518f54693fb0df720f78763904166816226b0bdd561'

def need(cond,msg):
 if not cond:raise AssertionError('26914 V2 BLOCKED '+msg)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def manifest(p):
 result={}
 for row in (R/p).read_text().splitlines():
  h,k=row.split('  ',1)
  need(re.fullmatch('[0-9a-f]{64}',h) is not None and k.startswith('app/')
       and k not in result and '..' not in Path(k).parts,'bad source manifest row')
  result[k]=h
 return result

def verify():
 # First assert the original failed runtime generation is still sealed exactly,
 # including its compiled 26913 authority and all prior targeted regressions.
 for n,h in [('build_26914_incremental.py',V1_BUILDER_SHA),
             ('.github/workflows/build-26914-change-aware.yml',V1_WORKFLOW_SHA),
             ('test_26914_source.py',V1_TEST_SHA),
             ('verify_26914_handoff.py',V1_VALIDATOR_SHA),
             ('26914_HANDOFF_HASHES.sha256',V1_HASHES_SHA)]:
  need((R/n).is_file() and sha(R/n)==h,'historical V1 bytes modified '+n)
 from verify_26914_handoff import verify as verify_v1
 verify_v1()
 # New stage1+workflow+trigger are independently SHA-sealed.
 paths=(R/'26914_V2_STAGE1_PATHS.txt').read_text().splitlines()
 need(len(paths)==len(set(paths)) and len(paths)>4
      and '26914_V2_HANDOFF_HASHES.sha256' in paths,'invalid V2 Stage1 list')
 entries={}
 for row in (R/'26914_V2_HANDOFF_HASHES.sha256').read_text().splitlines():
  h,p=row.split('  ',1)
  need(re.fullmatch('[0-9a-f]{64}',h) is not None and p not in entries,'duplicate/invalid seal')
  entries[p]=h
 need(set(entries)==(set(paths)-{'26914_V2_HANDOFF_HASHES.sha256'})|{WF,'TRIGGER_26914_V2.txt'},'wrong V2 SHA-sealed inventory')
 need({p for p in paths if p.startswith('handoff_payload_26914_v2/')}=={'handoff_payload_26914_v2/'+BRIDGE},'not one V2 Kotlin file')
 for p,h in entries.items():
  need((R/p).is_file() and not (R/p).is_symlink() and sha(R/p)==h,'V2 corrupted '+p)
 need((R/'TRIGGER_26914_V2.txt').read_bytes()==TRIGGER,'V2 last trigger altered')
 old=manifest('26914_PRECOMPILE_EXPECTED_FULL_APP.sha256')
 new=manifest('26914_V2_PRECOMPILE_EXPECTED_FULL_APP.sha256')
 base=manifest('26914_BASE_26913_FULL_APP.sha256')
 allow=(R/'26914_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines()
 deleted=(R/'26914_DELETED_RUNTIME_PATHS.txt').read_text().splitlines()
 need(len(base)==2036 and len(new)==len(old)==2035 and len(allow)==14 and len(deleted)==1
      and BRIDGE in allow and not set(new)-set(old) and not set(old)-set(new)
      and {p for p in old if old[p]!=new[p]}=={BRIDGE},'V2 changed more than one original runtime source')
 need({p for p in base if p in new and base[p]!=new[p]}==set(allow)-set(deleted)
      and set(base)-set(new)==set(deleted),'changed-file source allowlist drift')
 need(len(base)-len(allow)==2022,'2022 protected unchanged drift')
 need(sha(R/'handoff_payload_26914_v2'/BRIDGE)==new[BRIDGE],'corrected Kotlin payload not manifest exact')
 # Exact single ownership repair: no computation/input/JNI/algorithm change.
 prior=(R/'handoff_payload_26914'/BRIDGE).read_text()
 fixed=(R/'handoff_payload_26914_v2'/BRIDGE).read_text()
 original='''                                true, rgb2x, clip2x, physicalIdentity, customNoise26914,
                            )
                        }
                        PLog.i(TAG, "IRIS_26864_REAL_WRONSKI_B_2X_DISPATCH " +
                            "selectedReference=$refIndex normals=${normals.size} " +
                            "nativeTrue2x=true noiseProfile=${if (customNoise26914 == null) "RAW_BURST_FIT" else "IMPORTED_CALIBRATION"} " +
                            "glRgb=$rgb2x originalSensorClip=$clip2x")
'''
 corrected='''                                true, rgb2x, clip2x, physicalIdentity, customNoise26914,
                            )
                            // Both the profile and its diagnostic are owned by the same
                            // frozen JNI ingress scope; never reference a closed-scope local.
                            PLog.i(TAG, "IRIS_26864_REAL_WRONSKI_B_2X_DISPATCH " +
                                "selectedReference=$refIndex normals=${normals.size} " +
                                "nativeTrue2x=true noiseProfile=${if (customNoise26914 == null) "RAW_BURST_FIT" else "IMPORTED_CALIBRATION"} " +
                                "glRgb=$rgb2x originalSensorClip=$clip2x")
                        }
'''
 need(prior.count(original)==1 and fixed==prior.replace(original,corrected),'V2 Kotlin fix exceeds documented scope')
 builder=(R/'build_26914_v2_incremental.py').read_text()
 workflow=(R/WF).read_text()
 for x in ['RUN=42543642399',"COMMIT='b14f6dda1eae08677469e67cff8cab18f6bf96a6'",
           'ART_ID=13642374414','9b6fe38e3a337c0a2f834d459777340330ae339eb0ae834c095da4573f6e710d',
           V1_TEST_SHA[:0]+'26914_PRECOMPILE_EXPECTED_FULL_APP.sha256',
           '26914_V2_PRECOMPILE_EXPECTED_FULL_APP.sha256',
           '26914 original V1 historical candidate before correction',
           '26914 V2 corrected candidate source SHA',
           'if len(apks)!=1',"'REAL KOTLIN COMPILE: PASS'",'RUNTIME SOURCE INVARIANCE: PASS']:
  need(x in builder,'V2 builder missing mandatory historical gate '+x)
 need("'26914_v2_candidate_app_source.tar.gz.sha256'" in builder and "  26914_v2_candidate_app_source.tar.gz" in builder,'stale final TAR SHA receipt')
 need("'26914_V2_PREBUILD_SEALED_APP.sha256'" in builder and "'26914_V2_COMPILER_STATUS.txt'" in builder,'V2 output source/compiler receipts missing')
 need("workflow=R/'.github/workflows/build-26914-v2-change-aware.yml'" in builder,'wrong actual executed workflow archived')
 need("sha(R/'build_26914_v2_incremental.py')+'  build_26914_v2_incremental.py" in builder,'wrong actual executed builder archived')
 need('build_26914_incremental.py seal' not in workflow and workflow.count('build_26914_v2_incremental.py')==5,'stale V1 runner executed by V2')
 for token in ['verify_26914_handoff.py','verify_26914_v2_handoff.py',
               'test_26914_source.py --payload','test_26914_v2_source.py --live',
               'test_26914_v2_sealed_negatives.py',
               'test_26914_kotlin_owner.py handoff_payload_26914/',
               'test_26914_kotlin_owner.py handoff_payload_26914_v2/',
               'verify_26904_v3_safety.py','verify_26904_v2_safety.py',
               'verify_26906_native_cache.py preflight','verify_26906_native_cache.py postflight',
               'compile_26904_shaders_v2.sh','verify_26904_v3_cmake_handoff.py --handoff',
               'compile_26906_tone_glsl.sh','compile_26907_hue_glsl.sh',
               'compile_26908_render_glsl.sh','./gradlew --no-daemon --build-cache :app:assembleDebug',
               'actions/upload-artifact@v4']:
  need(token in workflow,'historical/actions/kotlin gate missing '+token)
 need(workflow.count('TRIGGER_26914_V2.txt')==1 and 'TRIGGER_26914.txt' not in workflow,'wrong event trigger')
 need(workflow.count(':app:assembleDebug')==1 and workflow.count('actions/upload-artifact@v4')==1,'Android assembly/publication weakened')
 need(workflow.index('test_26914_v2_source.py --live')<workflow.index('compile_26904_shaders_v2.sh')<workflow.index(':app:assembleDebug')<workflow.index('verify_26906_native_cache.py postflight')<workflow.index('build_26914_v2_incremental.py finalize')<workflow.index('actions/upload-artifact@v4'),'stale/incorrect stage order')
 for term in ('photon_26914_outputs/','26914_gradle_assemble.log','TRIGGER_26913.txt','build_26913_incremental.py seal'):
  need(term not in workflow,'stale prior workflow output/trigger reference '+term)
 print('PASS 26914 V2 SHA seal, V1 immutability, exact one-production-file Kotlin repair, 2035 candidates/2022 protected, strict 26913 17-gate inheritance')
if __name__=='__main__':verify()
