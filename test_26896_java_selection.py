#!/usr/bin/env python3
"""Host-JVM focused real javac compile, NOT full Android Java/Kotlin compiler proof."""
from pathlib import Path
import tempfile,sys,subprocess
R=Path(__file__).resolve().parent
assert len(sys.argv)==2
base=Path(sys.argv[1])/'app/src/main/java/com/unspektrawesome/camera'
with tempfile.TemporaryDirectory(prefix='spektra26896_javac_') as t:
 cmd=['javac','-d',t,str(R/'java_26896/android/graphics/ImageFormat.java'),str(R/'java_26896/SpektraRawPolicyTest.java')]+[str(base/p) for p in ('RawFormat.java','RawOutput.java','Size2d.java','IntRange.java','RawPreviewPolicy.java')]
 subprocess.run(cmd,check=True)
 subprocess.run(['java','-cp',t,'SpektraRawPolicyTest'],check=True)
print('PASS 26896 focused actual javac Spektra RAW selector; full Android project compiler NOT RUN locally')
