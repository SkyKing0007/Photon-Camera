#!/usr/bin/env python3
"""B-only toe, settings default, JPEG name and UHDR SDR-denominator ownership."""
import pathlib,hashlib,re,sys,json
assert len(sys.argv)==3,'base candidate'
B=pathlib.Path(sys.argv[1])/'app';C=pathlib.Path(sys.argv[2])/'app';R=pathlib.Path(__file__).resolve().parent
r=lambda base,x:(base/x).read_text()
settings='src/main/java/com/particlesdevs/photoncamera/settings/Iris26856ABSettings.java'
s=r(C,settings);old=r(B,settings)
assert 'return Mode.ORIGINAL_26850;\n    }\n    public static void write' in old
assert 'return Mode.AMAZE_26855;\n    }\n    public static void write' in s
assert s.count('return ORIGINAL_26850;')==1 and s.count('if ("AB".equals(id)) return AMAZE_26855;')==1
assert s.count('return Mode.parse(preferences.getString(PREFIX + physical, "A"));')==1
assert s.count('return Mode.parse(preferences.getString(PREFIX + logicalId, "A"));')==1
name='src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java'
q=r(C,name)
assert q.count('iris26856BRequestedOnly ? "_B" : ""')==0
assert 'Paths.get(iris26856BasePath + iris26856Extension)' in q
assert 'java.nio.file.Files.exists(imageFile)' in q and 'iris26890Collision++' in q
assert 'mIris26856BOnlyJpegRollbackPath = imageFile;' in q
render='src/main/assets/shaders/motionv2/render.glsl'
local='src/main/assets/shaders/motionv2/local_laplacian_global_log_26621.glsl'
gain='src/main/assets/shaders/motionv2/gainmap.glsl'
procs=[r(C,p) for p in (render,local,gain)]
marker='/* IRIS_26890_B_ONLY_USER_EXPORTED_SHADOW_TOE'
blocks=[t[t.index(marker):t.index('float iris26623',t.index(marker))] if i<2 else t[t.index(marker):t.index('float iris26640',t.index(marker))] for i,t in enumerate(procs)]
assert blocks[0]==blocks[1]==blocks[2], 'render/Local Laplacian/UHDR gainmap toe mismatch'
assert all('uniform int iris26890BToeEnabled;' in p for p in procs)
assert [p.count("iris26890BSourceToe(") for p in procs]==[3,2,2]
assert 'if(iris26890BToeEnabled==0 || iris26653HighlightCompressionEnabled!=0' in blocks[0]
assert 'sourceGuide>=0.25)return originalMappedGuide' in blocks[0]
java=r(C,'src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java')
assert java.count('glProg.setVar("iris26890BToeEnabled",')==1
assert 'basePipeline.mParameters.motionV2ReconstructionOwner\n                   == Parameters.MOTION_V2_RECONSTRUCTION_RAWR_AMAZE ? 1 : 0' in java
assert 'basePipeline.mParameters.motionV2Active' in java
assert procs[0].count('iris26890BSourceToe(sourceGuide,iris26653MapMotionSdrFinalGuide(sourceGuide))')==2
assert 'iris26890BSourceToe(sourceGuide,iris26653MapMotionSdrGuide(sourceGuide))' in procs[2]
assert 'iris26890BSourceToe(sourceGuide,iris26653MapMotionSdrFinalGuide(sourceGuide))' in procs[1]
assert 'VERSION_BUILD=26890' in r(C,'version.properties')
jsonpath=R/'26890_USER_EDITOR_POINTS_EXACT.json'
assert jsonpath.is_file()
data=json.loads(jsonpath.read_text()); assert data['editor_defaults']['compress']==data['user_exported']['compress']
assert all(data['editor_defaults'][c][-1]==data['user_exported'][c][-1] for c in ('darker','brighter'))
assert 'IRIS_26890_B_ONLY_USER_EXPORTED_SHADOW_TOE' not in r(B,render)
# The 26890 strength-floor amendment applies ONLY to B/OFF's active private
# Vulkan HDRQ merge. Vendor remains protected, original motion/reject decisions
# must be byte-identical, and 11.5 is continuous (not rounded to 12).
shader='src/main/cpp/iris26864/bridge/Iris26887BOffHdrqMerge.comp'
before=r(B,shader);after=r(C,shader)
assert before.count('const float strength8Robustness = 0.29730178;')==1
assert after.count('const float strength115Robustness = 1.0;')==1
assert after.count('const float strength115ReadNoise = 16.0;')==1
assert after.count('const float strength115MaxMotion = 2.50496541;')==1
assert all(x not in after for x in ('strength8Robustness','strength8ReadNoise','strength8MaxMotion'))
assert after.count('float localMotion = p.uniformExposure == 0 ? 0.0 :')==1
# A token-tight reversible source transform establishes the only substantive
# changes are three strength norms and the accurate explanatory comment.
reversed_shader=(after.replace('strength-11.5-equivalent','strength-8-equivalent')
 .replace('    // Exact strength 11.5 uses the continuous RAWR HDRQ frequencyNorms\n    // equations, rather than frequencyNorms(11.5), which rounds to 12.\n','')
 .replace('strength115Robustness = 1.0','strength8Robustness = 0.29730178')
 .replace('strength115ReadNoise = 16.0','strength8ReadNoise = 2.29739671')
 .replace('strength115MaxMotion = 2.50496541','strength8MaxMotion = 1.58270825')
 .replace('strength115Robustness','strength8Robustness')
 .replace('strength115ReadNoise','strength8ReadNoise')
 .replace('strength115MaxMotion','strength8MaxMotion'))
assert reversed_shader==before, 'motion/fusion/FFT/companion veto or anything else modified'
import math
rev=.5*(26.5-11.5)
for actual, expected in zip((2.**(-rev+7.5), (2.**(-rev+10.))**1.6, 1.3**(11.-rev)),(1.,16.,2.50496541)):
 assert abs(actual-expected)<1e-7, 'incorrect exact 11.5 norms'
print('PASS 26890 B-only source toe mirror across render/Local Laplacian/UHDR, default-B unset preferences, A/B JPEG collision-safe same naming')
