#!/usr/bin/env python3
"""26912 source-exact, production Java grammar, and regression policy checks.
These are ADDITIONAL to, not replacements for, the original 26911 Actions
real GLSL/SPIRV/Kotlin/Java/NDK/:app:assembleDebug compiler gates.
"""
import argparse, hashlib, os, pathlib, subprocess, tempfile, xml.etree.ElementTree as ET
R=pathlib.Path(__file__).resolve().parent
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def must(p,why):
 if not p:raise AssertionError('26912 fail-closed: '+why)
def rows(name):
 d={}
 for line in (R/name).read_text().splitlines():
  digest,p=line.split('  ',1)
  must(p.startswith('app/') and p not in d and len(digest)==64 and '..' not in pathlib.PurePosixPath(p).parts,'bad sha row')
  d[p]=digest
 return d
def run(mode):
 base=rows('26912_BASE_26911_FULL_APP.sha256');expected=rows('26912_PRECOMPILE_EXPECTED_FULL_APP.sha256')
 changed=(R/'26912_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines()
 added=(R/'26912_ADDED_RUNTIME_PATHS.txt').read_text().splitlines()
 must(len(base)==2034 and len(expected)==2036,'wrong source count')
 must(len(changed)==18 and len(set(changed))==18 and changed==sorted(changed),'runtime allowlist')
 must(len(added)==2 and len(set(added))==2 and added==sorted(added),'new runtime paths')
 must(set(expected)-set(base)==set(added) and not set(base)-set(expected),'no unexpected added/removed source')
 must({p for p in base if expected[p]!=base[p]}==set(changed)-set(added),'source modifications not exact allowlist')
 must(sum(1 for p in base if p not in changed)==2018,'protected source count')
 for p in base:
  if p not in changed: must(base[p]==expected[p],'protected source modified '+p)
 for p in changed:
  must(p.startswith(('app/src/','app/version.properties')),'unapproved source path '+p)
  must(not p.startswith(('app/src/main/jniLibs/','app/src/main/assets/')),'protected vendor/asset mutation '+p)
  must(not p.endswith(('.comp','.frag','.vert','.spv')),'uncompiled shader edit '+p)
 root=R/'handoff_payload_26912' if mode=='payload' else R
 src=lambda p:(root/p).read_text()
 for p in changed:must((root/p).is_file() and h(root/p)==expected[p],'actual candidate byte drift '+p)
 cap=src('app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
 bridge=src('app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt')
 settings=src('app/src/main/java/com/particlesdevs/photoncamera/ui/settings/SettingsActivity.java')
 native=src('app/src/main/cpp/iris26864/bridge/Iris26888BOffHdrqCoordinator.cpp')
 mgc=src('app/src/main/cpp/iris26864/Iris26864JniGpuInteropImpl.inc')
 java=src('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26864NativeRawr.java')
 profile=src('app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNoiseProfileStore.kt')
 highlight=src('app/src/main/java/com/hinnka/mycamera/processor/GlesIris26912HighlightReference.kt')
 owner=src('app/src/main/java/com/particlesdevs/photoncamera/settings/Iris26856ABSettings.java')
 xml=src('app/src/main/res/xml/preferences.xml')
 must('iris26911DeferBShutterForPhysicalPair(' not in cap,'old 4.5 sec shutter wait persists')
 must('motion26676DeferShutterUntilProtectedGeneration(' not in cap,'old 1.5 sec shutter wait persists')
 for needle in ['iris26912MustAcquireExactNormals','iris26911ExactBManualFrame(iris26593NormalReference)',
     'iris26713TargetMatchesHal = !iris26912MustAcquireExactNormals',
     'iris26598PreShutterNormals.closeAll()', 'mMotion26709HalBaselineExposureNs = iris26912BaselineExposureNs',
     'iris26912AltHighlightsAtShutter','iris26912PreviewP995','motionV2PreviewHighlightP99526912',
     'if (desiredOffsetEv < -0.03f && !iris26912AltHighlightAtPress)',
     'IRIS_26912_ALT_HIGHLIGHT_NO_GLOBAL_DARKENING']:
  must(needle in cap,'shutter/exposure/preview safety lost '+needle)
 must('#include <optional>' in native and 'Iris26912BOffNoiseOverride.hpp' not in native,
      'B shadow compile must not include unresolvable Iris-local header')
 must('iris26912BOffNoiseOverride' in native and 'measured && iris26912BOffNoiseOverride' in native,
      'must not use custom noise absent valid RAW-burst evidence')
 for needle in ['javaBOffNoise','bOffNoiseByPhase','if(sr||bOffNoise.size()!=8u)']:
  must(needle in mgc,'JNI native B noise contract missing '+needle)
 must('bOffNoiseByPhase' in java and 'wronskiTrue2x || bOffNoiseByPhase.length != 8' in java,
      'Java B OFF noise API missing length/scope')
 must('loadBOffForPhysical' in profile and 'importBOffForPhysical' in profile and
      'parseGcamC' in profile and 'physicalId' in profile and 'getOrNull()' in profile,
      'per-physical noise import/parser/fallback missing')
 must('loadBOffForPhysical' in bridge and 'nativeNormalFrames[nativeReferenceIndex].sensitivityIso' in bridge and
      'RAW_BURST_26911' in bridge and 'bOffNoise26912' in bridge,
      'real B OFF lens/noise/RAW burst fallback route missing')
 must('GlesIris26912HighlightReference.select' in bridge and 'mgcBase.motionV2AlternativeHighlight26912' in bridge
      and 'recoveredRef26912' in bridge,'pre-fusion highlight reference arbitration absent')
 for needle in ['previewP995 < 0.94f','staticTrusted','originalClip < 16','saved >= 24',
                'exposure[i] / refExposure','whiteByFrame','return original']:
  must(needle in highlight,'highlight source evidence/safety missing '+needle)
 must('alternativeHighlight(' in owner and 'getBoolean(HIGHLIGHT_PREFIX + id, false)' in owner,
      'per-lens default-OFF preference missing')
 must('setAlternativeHighlight' in settings and 'Iris26912PerLensHighlightSwitch' in xml,
      'highlight UI not physical-lens owned')
 must(xml.index('pref_iris_saturation') < xml.index('pref_iris_alternative_highlight_recovery'),
      'highlight must appear below Iris Saturation')
 must('getPersistedBoolean(boolean defaultValue)' in src(
      'app/src/main/java/com/particlesdevs/photoncamera/ui/settings/custompreferences/Iris26912PerLensHighlightSwitch.java')
      and 'persistBoolean(boolean value) { return false; }' in src(
      'app/src/main/java/com/particlesdevs/photoncamera/ui/settings/custompreferences/Iris26912PerLensHighlightSwitch.java'),
      'global preference pollution')
 must('VERSION_BUILD=26912' in src('app/version.properties'),'wrong build version')
 ET.fromstring(xml);ET.fromstring(src('app/src/main/res/values/strings.xml'))
 java_paths=[p for p in changed if p.endswith('.java')]
 must(len(java_paths)==6,'unexpected Java change count')
 with tempfile.TemporaryDirectory(prefix='photon_26912_java_') as t:
  subprocess.run(['javac','--release','17','-d',t,str(R/'tests_26912/SourceGrammar26912.java')],check=True)
  subprocess.run(['java','-cp',t,'SourceGrammar26912']+[str(root/p) for p in java_paths],check=True)
 print('PASS 26912',mode,'source exact 18 allowlisted +2 added, 2018 protected, Java production grammar 6, XML, B noise physical native JNI, no artificial shutter gate, default-OFF preview/RAW highlight')
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('mode',choices=['--payload','--live'])
 # argparse cannot use options as positional, accept explicit non-option mode
 import sys
 must(len(sys.argv)==2 and sys.argv[1] in ('--payload','--live'),'mode must be --payload or --live')
 run(sys.argv[1][2:])
