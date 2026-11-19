#!/usr/bin/env python3
"""Compile & run exact 26964 pure Java allocation math with real javac; not a Gradle substitute."""
from pathlib import Path
import argparse,subprocess,tempfile,shutil,re
R=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--payload',action='store_true');p.add_argument('--live',action='store_true');args=p.parse_args()
java=(R if args.live else R/'handoff_payload_26964')/'app/src/main/java/com/particlesdevs/photoncamera/capture/Iris26909ShutterIsoMath.java'
s=java.read_text()
assert s.count('Plan solveSceneLensAware(')==1
assert s.count('MAX_AUTO_SHUTTER_NS = 100_000_000L')==1
assert 'sensorIsoMax' in s and 'analogIsoMax' in s and 'equivalentFocalMm' in s
assert 'double energy = (double)halShutterNs * (double)halIso;' in s
assert 'error >= 0.045' in s
assert shutil.which('javac') is not None and shutil.which('java') is not None,'real JDK is mandatory'
with tempfile.TemporaryDirectory(prefix='26964_real_java_') as t:
 subprocess.run(['javac','-d',t,str(java),str(R/'Exposure26964Test.java')],check=True)
 z=subprocess.run(['java','-cp',t,'Exposure26964Test'],capture_output=True,text=True,check=True)
 assert 'PASS 300' in z.stdout and 'tele=' in z.stdout and 'dark=' in z.stdout,z.stdout
 print(z.stdout.strip())
print('PASS real Java compiler and executable 26964 scene/lens/analog ISO regression')
