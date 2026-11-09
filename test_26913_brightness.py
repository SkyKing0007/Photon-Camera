#!/usr/bin/env python3
"""Run actual production 26913 pure Java AE solver, exact source and scope, grammar.
Historical 26912 original tests remain targeted at their immutable own source.
These tests never replace full Actions Kotlin/Java/NDK/Gradle/shader compilation.
"""
import hashlib,pathlib,re,subprocess,tempfile,sys
R=pathlib.Path(__file__).resolve().parent
SHA=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def parse(p):
 d={}
 for line in (R/p).read_text().splitlines():
  h,f=line.split('  ',1)
  assert re.fullmatch('[0-9a-f]{64}',h) and f.startswith('app/') and '..' not in pathlib.PurePosixPath(f).parts and f not in d
  d[f]=h
 return d

def run(which):
 before=parse('26913_BASE_26912_FULL_APP.sha256');after=parse('26913_PRECOMPILE_EXPECTED_FULL_APP.sha256')
 changed=(R/'26913_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines()
 assert len(before)==len(after)==2036 and len(changed)==3 and len(set(changed))==3 and changed==sorted(changed)
 assert set(before)==set(after) and {p for p in before if before[p]!=after[p]}==set(changed)
 assert sum(p not in changed for p in before)==2033
 assert (R/'26913_ADDED_RUNTIME_PATHS.txt').read_text().strip()==''
 assert all(before[p]==after[p] for p in before if p not in changed)
 assert all(before[p]==after[p] for p in before if p.startswith(('app/src/main/cpp/','app/src/main/assets/','app/src/main/jniLibs/')))
 root=R/'handoff_payload_26913' if which=='payload' else R
 assert all((root/p).is_file() and SHA(root/p)==after[p] for p in changed)
 math=root/'app/src/main/java/com/particlesdevs/photoncamera/capture/Iris26909ShutterIsoMath.java'
 cap=(root/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text()
 java=math.read_text()
 assert 'solveBrightnessAware(' in java and 'final double energy = (double)halShutterNs * (double)halIso;' in java
 assert 'quietIso * 2.5' in java and 'MAX_AUTO_SHUTTER_NS' in java and 'flickerPeriodNs' in java
 assert 'Iris26909ShutterIsoMath.solveBrightnessAware(' in cap
 assert 'Iris26909ShutterIsoMath.solve(' not in cap
 assert 'IRIS_26909_B_SHUTTER_FIRST_ENGAGED' in cap and 'allocator=26913_low_iso_brightness_curve' in cap
 assert 'noMotionDecision=true' in cap
 for needle in ['iris26911ExactBManualFrame(iris26593NormalReference)',
                'iris26912MustAcquireExactNormals','iris26912AltHighlightsAtShutter',
                'if (mIris26909ManualUnavailable) return;',
                'if (mZslCapturing || burst || isProcessing || mState != STATE_PREVIEW',
                'iris26909ReleaseBManualToHal("raw_highlight_full_well_guard", true);',
                'mMotion26380RawHighlightFraction > 0.015f',
                'motion26713CancelRecipe("26909-manual-rejected")']:
  assert needle in cap,needle
 assert 'VERSION_BUILD=26913' in (root/'app/version.properties').read_text()
 with tempfile.TemporaryDirectory(prefix='photon26913_java_') as t:
  program=R/'tests_26913/Photon26913BrightnessRegression.java'
  subprocess.run(['javac','--release','17','-d',t,str(math),str(program)],check=True)
  subprocess.run(['java','-cp',t,'Photon26913BrightnessRegression'],check=True)
  grammar=R/'tests_26913/SourceGrammar26913.java'
  subprocess.run(['javac','--release','17','-d',t,str(grammar)],check=True)
  subprocess.run(['java','-cp',t,'SourceGrammar26913',str(root/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java'),str(math)],check=True)
 print('PASS 26913',which,'2036 source, three-file exact allowlist, 2033 protected, actual tested Java math and grammar, historic capture gates')
if __name__=='__main__':
 assert len(sys.argv)==2 and sys.argv[1] in ('--payload','--live')
 run(sys.argv[1][2:])
