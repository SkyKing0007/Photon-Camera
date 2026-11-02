#!/usr/bin/env python3
"""Host javac real-byte regression, including original 26896 Actions failure reproduction.
Not a substitute for Android project Kotlin/Java/NDK/assemble compiler gates.
"""
from pathlib import Path
import tempfile,sys,subprocess,shutil
R=Path(__file__).resolve().parent
assert len(sys.argv)==2
base=Path(sys.argv[1]).resolve()/'app/src/main/java/com/unspektrawesome/camera'
assert all((base/p).is_file() for p in ('RawFormat.java','RawOutput.java','Size2d.java','IntRange.java','RawPreviewPolicy.java'))
with tempfile.TemporaryDirectory(prefix='spektra26896_javac_') as t:
    t=Path(t)
    polluted=t/'checkout_root'; polluted.mkdir()
    # Prefer the actual repo-root legacy source when running in Actions. The
    # candidate is also an exact class-name collision witness in clean-extract.
    legacy=R/'RawPreviewPolicy.java'
    shutil.copyfile(legacy if legacy.is_file() else base/'RawPreviewPolicy.java', polluted/'RawPreviewPolicy.java')
    sources=[str(R/'java_26896/android/graphics/ImageFormat.java'),str(R/'java_26896/SpektraRawPolicyTest.java')]+[str(base/p) for p in ('RawFormat.java','RawOutput.java','Size2d.java','IntRange.java','RawPreviewPolicy.java')]
    # Exact original Actions command fails because javac searches cwd=. and
    # discovers the unrelated root RawPreviewPolicy.java in the repo checkout.
    broken=subprocess.run(['javac','-d',str(t/'broken_classes'),*sources],cwd=polluted,capture_output=True,text=True)
    assert broken.returncode!=0 and 'duplicate class: com.unspektrawesome.camera.RawPreviewPolicy' in broken.stderr and 'bad source file: ./RawPreviewPolicy.java' in broken.stderr, broken.stderr[:1600]
    print('PASS actual original Actions javac wrong-sourcepath error reproduced on matching class collision')
    # Supply the exact frozen 26896 production Java sources, but never allow
    # javac to discover any competing repository-local .java/.class by default.
    isolated=t/'empty_sourcepath';isolated.mkdir()
    classes=t/'classes';classes.mkdir()
    cmd=['javac','--release','17','-encoding','UTF-8','-sourcepath',str(isolated),'-classpath',str(classes),'-d',str(classes),*sources]
    subprocess.run(cmd,cwd=polluted,check=True)
    subprocess.run(['java','-cp',str(classes),'SpektraRawPolicyTest'],cwd=polluted,check=True)
    print('PASS 26896 corrected exact real javac under polluted repository-root conditions, no implicit sources')
print('PASS 26896 focused javac; full Android project compiler NOT RUN locally')
